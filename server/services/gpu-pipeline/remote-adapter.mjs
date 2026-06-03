import JSZip from 'jszip';

import {
  createRemoteGpuPipelineClient,
  isRemoteGpuFailureStatus,
  isRemoteGpuSuccessStatus,
  RemoteGpuPipelineError,
} from './client.mjs';
import { loadRemoteGpuPipelineConfig, sanitizeRemoteGpuPipelineConfig } from './config.mjs';
import { MineruStillProcessingError, MineruSubmitUnreachableError } from '../mineru/local-adapter.mjs';

export class RemoteGpuPipelineStillProcessingError extends MineruStillProcessingError {
  constructor(remoteTaskId, status) {
    super(remoteTaskId, status);
    this.name = 'RemoteGpuPipelineStillProcessingError';
  }
}

export async function processWithRemoteGpuPipeline({
  task,
  material,
  fileStream,
  fileName,
  mimeType,
  timeoutMs,
  minioContext,
  updateProgress,
  client = null,
}) {
  const options = task.optionsSnapshot || {};
  const config = loadRemoteGpuPipelineConfig();
  const remoteClient = client || createRemoteGpuPipelineClient({ config });

  await updateProgress({
    progress: 10,
    message: '已连接远端 GPU Pipeline，准备提交任务...',
    metadata: {
      ...(task.metadata || {}),
      mineruExecutionProfile: buildExecutionProfile(task, material, config, options),
    },
  });

  let submitted;
  try {
    submitted = await remoteClient.submitTask({
      luceonTaskId: task.id,
      materialId: String(task.materialId || ''),
      fileName,
      mimeType,
      fileStream,
      options: {
        ...options,
        pipeline: config.pipeline,
        keepIntermediate: config.keepIntermediate,
      },
    });
  } catch (error) {
    throw normalizeRemoteSubmitError(error);
  }

  const remoteTaskId = submitted.task_id;
  if (!remoteTaskId) {
    throw new MineruSubmitUnreachableError('远端 GPU Pipeline 未返回 task_id', {
      endpoint: config.baseUrl,
      dependencyBlocking: true,
    });
  }

  await updateProgress({
    stage: 'remote-gpu-queued',
    state: 'running',
    progress: 20,
    message: `远端 GPU Pipeline 已提交，内部ID: ${remoteTaskId}`,
    metadata: {
      ...(task.metadata || {}),
      mineruTaskId: remoteTaskId,
      mineruStatus: normalizeMineruStatus(submitted.status),
      mineruSubmittedAt: new Date().toISOString(),
      mineruExecutionProfile: buildExecutionProfile(task, material, config, options),
      remoteGpuPipeline: {
        taskId: remoteTaskId,
        status: submitted.status,
        baseUrlConfigured: Boolean(config.baseUrl),
      },
    },
  });

  const completed = await waitRemoteGpuTask({
    client: remoteClient,
    task,
    remoteTaskId,
    timeoutMs,
    updateProgress,
    config,
  });

  await updateProgress({
    stage: 'remote-gpu-result-fetching',
    state: 'running',
    progress: 80,
    message: '远端 GPU Pipeline 已完成，正在拉取并保存产物...',
    metadata: {
      ...(task.metadata || {}),
      mineruStatus: 'completed',
      mineruLastStatusAt: new Date().toISOString(),
      remoteGpuPipeline: {
        taskId: remoteTaskId,
        status: completed.status,
        metrics: completed.metrics || null,
      },
    },
  });

  const outputs = completed.outputs || await remoteClient.getOutputs(remoteTaskId);
  return await saveRemoteOutputs({
    task,
    material,
    remoteTaskId,
    outputs,
    minioContext,
    client: remoteClient,
  });
}

export async function resumeWithRemoteGpuPipeline({
  task,
  material,
  mineruTaskId,
  timeoutMs,
  minioContext,
  updateProgress,
  client = null,
}) {
  const config = loadRemoteGpuPipelineConfig();
  const remoteClient = client || createRemoteGpuPipelineClient({ config });

  const completed = await waitRemoteGpuTask({
    client: remoteClient,
    task,
    remoteTaskId: mineruTaskId,
    timeoutMs,
    updateProgress,
    config,
  });

  const outputs = completed.outputs || await remoteClient.getOutputs(mineruTaskId);
  return await saveRemoteOutputs({
    task,
    material,
    remoteTaskId: mineruTaskId,
    outputs,
    minioContext,
    client: remoteClient,
  });
}

export function isRemoteGpuPipelineTask(task) {
  const profile = task?.metadata?.mineruExecutionProfile || {};
  const options = task?.optionsSnapshot || {};
  return profile.backendEffective === 'remote-gpu-pipeline'
    || profile.backendRequested === 'remote-gpu'
    || options.mineruBackend === 'remote-gpu'
    || options.remoteGpuPipeline === true
    || String(process.env.MINERU_BACKEND || '').toLowerCase() === 'remote-gpu';
}

async function waitRemoteGpuTask({ client, task, remoteTaskId, timeoutMs, updateProgress, config }) {
  const deadline = Date.now() + timeoutMs;
  let lastStatus = 'queued';
  let lastPayload = null;

  while (Date.now() < deadline) {
    const payload = await client.queryTask(remoteTaskId);
    lastPayload = payload;
    lastStatus = String(payload.status || '').toLowerCase();

    if (isRemoteGpuSuccessStatus(lastStatus)) return payload;
    if (isRemoteGpuFailureStatus(lastStatus)) {
      const message = payload.error?.message || payload.message || `remote GPU Pipeline failed with status=${lastStatus}`;
      const error = new Error(message);
      error.remoteGpuPipeline = payload;
      throw error;
    }

    await updateProgress({
      stage: mapRemoteStage(lastStatus),
      state: 'running',
      progress: mapRemoteProgress(lastStatus, payload),
      message: buildRemoteProgressMessage(payload),
      metadata: {
        ...(task.metadata || {}),
        mineruTaskId: remoteTaskId,
        mineruStatus: normalizeMineruStatus(lastStatus),
        mineruLastStatusAt: new Date().toISOString(),
        mineruExecutionProfile: {
          ...(task.metadata?.mineruExecutionProfile || {}),
          backendRequested: 'remote-gpu',
          backendEffective: 'remote-gpu-pipeline',
          remoteBaseUrlConfigured: Boolean(config.baseUrl),
        },
        remoteGpuPipeline: {
          taskId: remoteTaskId,
          status: lastStatus,
          progress: payload.progress || null,
          resource: payload.resource || null,
          metrics: payload.metrics || null,
        },
      },
    });

    await new Promise((resolve) => setTimeout(resolve, config.pollIntervalMs || 10_000));
  }

  throw new RemoteGpuPipelineStillProcessingError(remoteTaskId, lastStatus || lastPayload?.status || 'unknown');
}

async function saveRemoteOutputs({ task, remoteTaskId, outputs = {}, minioContext, client }) {
  if (!minioContext) throw new Error('Remote GPU Pipeline result storage requires MinIO context');

  const materialId = String(task.materialId || task.id);
  const parsedPrefix = `parsed/${materialId}/`;
  const fullMdObjectName = `${parsedPrefix}full.md`;
  const parsedArtifacts = [];
  const seen = new Set();

  const pushArtifact = (relativePath, objectName, size, mimeType) => {
    const key = `${relativePath}::${objectName}`;
    if (seen.has(key)) return;
    seen.add(key);
    parsedArtifacts.push({ objectName, relativePath, size, mimeType });
  };

  const pushZipEntry = (zipObjName, entryName, relativePath, size, mimeType) => {
    const key = `zip::${zipObjName}::${entryName}`;
    if (seen.has(key)) return;
    seen.add(key);
    parsedArtifacts.push({
      source: 'zip-entry',
      zipObjectName: zipObjName,
      zipEntryPath: entryName,
      relativePath,
      size: typeof size === 'number' ? size : null,
      mimeType: mimeType || undefined,
    });
  };

  const markdown = await readMarkdownOutput(outputs, client);
  if (!markdown) {
    return {
      markdown: '',
      markdownEmpty: true,
      mineruTaskId: remoteTaskId,
      objectName: fullMdObjectName,
      parsedPrefix,
      parsedFilesCount: 0,
      parsedArtifacts,
      zipObjectName: null,
      artifactIncomplete: true,
      artifactStorageMode: 'remote-gpu-empty',
      artifactExportModes: ['user', 'mineru-raw', 'diagnostic'],
    };
  }

  await minioContext.saveMarkdown(fullMdObjectName, markdown);
  pushArtifact('full.md', fullMdObjectName, Buffer.byteLength(markdown, 'utf-8'), 'text/markdown');

  const zipBuffer = await readZipOutput(outputs, client);
  let zipObjectName = null;
  let primaryMarkdownPath = null;
  if (zipBuffer) {
    zipObjectName = `${parsedPrefix}mineru-result.zip`;
    await minioContext.saveObject(zipObjectName, zipBuffer, 'application/zip');
    pushArtifact('mineru-result.zip', zipObjectName, zipBuffer.length, 'application/zip');

    const zip = await JSZip.loadAsync(zipBuffer);
    const entries = Object.entries(zip.files).filter(([, entry]) => !entry.dir);
    for (const [name, entry] of entries) {
      const relativePath = sanitizeRelativePath(name);
      if (!relativePath) continue;
      if (relativePath === 'full.md') primaryMarkdownPath = primaryMarkdownPath || relativePath;
      if (relativePath === 'full.md' || relativePath === 'mineru-result.zip') continue;
      pushZipEntry(
        zipObjectName,
        name,
        relativePath,
        entry?._data?.uncompressedSize ?? null,
        inferContentTypeByExt(relativePath)
      );
    }
  }

  for (const artifact of normalizeOutputArtifactRefs(outputs)) {
    pushArtifact(
      artifact.relativePath,
      artifact.objectName,
      artifact.size ?? null,
      artifact.mimeType || inferContentTypeByExt(artifact.relativePath)
    );
  }

  return {
    markdown,
    mineruTaskId: remoteTaskId,
    objectName: fullMdObjectName,
    parsedPrefix,
    parsedFilesCount: parsedArtifacts.length,
    parsedArtifacts,
    zipObjectName,
    artifactIncomplete: !zipObjectName && parsedArtifacts.length <= 1,
    artifactStorageMode: zipObjectName ? 'zip-source' : 'remote-gpu-expanded',
    artifactExportModes: ['user', 'mineru-raw', 'diagnostic'],
    primaryMarkdownPath,
  };
}

function buildExecutionProfile(task, material, config, options) {
  return {
    ...(task.metadata?.mineruExecutionProfile || {}),
    backendRequested: 'remote-gpu',
    backendEffective: 'remote-gpu-pipeline',
    pipeline: config.pipeline,
    parseMethod: options.parseMethod || options.parse_method || 'auto',
    enableOcr: enabledFlag(options.enableOcr),
    enableFormula: enabledFlag(options.enableFormula),
    enableTable: enabledFlag(options.enableTable),
    ocrLanguage: options.ocrLanguage || options.language || 'ch',
    maxPages: Number(options.maxPages || 1000),
    fileSize: material?.fileSize || null,
    remoteConfig: sanitizeRemoteGpuPipelineConfig(config),
  };
}

function normalizeRemoteSubmitError(error) {
  if (error instanceof RemoteGpuPipelineError) {
    return new MineruSubmitUnreachableError(error.message, {
      status: error.status,
      endpoint: error.endpoint,
      dependencyBlocking: error.dependencyBlocking,
      retryAfterMs: 60_000,
    });
  }
  return error;
}

function mapRemoteStage(status) {
  if (status === 'queued' || status === 'pending') return 'remote-gpu-queued';
  if (status === 'running_mineru') return 'remote-gpu-mineru';
  if (status === 'running_normalization') return 'remote-gpu-normalization';
  if (status === 'running_inference') return 'remote-gpu-inference';
  if (status === 'running_build_tree') return 'remote-gpu-build-tree';
  return 'remote-gpu-processing';
}

function mapRemoteProgress(status, payload) {
  if (typeof payload.progress?.percent === 'number') return Math.max(20, Math.min(79, payload.progress.percent));
  if (status === 'queued' || status === 'pending') return 20;
  if (status === 'running_mineru') return 35;
  if (status === 'running_normalization') return 50;
  if (status === 'running_inference') return 65;
  if (status === 'running_build_tree') return 75;
  return 50;
}

function buildRemoteProgressMessage(payload) {
  const stage = payload.progress?.stage || payload.status || 'processing';
  const message = payload.progress?.message || payload.message || '';
  return `远端 GPU Pipeline 正在处理：${stage}${message ? `，${message}` : ''}`;
}

function normalizeMineruStatus(status) {
  const value = String(status || '').toLowerCase();
  if (value === 'queued' || value === 'pending') return 'queued';
  if (value === 'succeeded' || value === 'success' || value === 'completed' || value === 'done') return 'completed';
  if (value === 'failed' || value === 'error') return 'failed';
  return 'processing';
}

async function readMarkdownOutput(outputs, client) {
  const candidates = [
    outputs.markdown,
    outputs.mineru_markdown,
    outputs.mineruMarkdown,
    outputs.mineru_markdown_content,
    outputs.full_md,
  ];
  const inline = candidates.find((value) => typeof value === 'string' && value.trim());
  if (inline && !looksLikePathOrUrl(inline)) return inline.trim();

  const url = outputs.mineru_markdown_url || outputs.markdown_url || outputs.full_md_url;
  if (url && /^https?:\/\//i.test(url)) {
    return (await client.download(url)).toString('utf-8').trim();
  }
  return '';
}

async function readZipOutput(outputs, client) {
  const b64 = outputs.mineru_result_zip_base64 || outputs.artifact_bundle_base64 || outputs.zip_base64;
  if (typeof b64 === 'string' && b64.trim()) {
    return Buffer.from(b64, 'base64');
  }
  const url = outputs.mineru_result_zip_url || outputs.artifact_bundle_url || outputs.zip_url;
  if (url && /^https?:\/\//i.test(url)) return await client.download(url);
  return null;
}

function normalizeOutputArtifactRefs(outputs) {
  const refs = outputs.artifact_refs || outputs.artifacts || [];
  if (!Array.isArray(refs)) return [];
  return refs
    .map((item) => {
      const objectName = item.objectName || item.object || item.key;
      const relativePath = sanitizeRelativePath(item.relativePath || item.path || objectName);
      if (!objectName || !relativePath) return null;
      return {
        objectName,
        relativePath,
        size: typeof item.size === 'number' ? item.size : item.size_bytes,
        mimeType: item.mimeType || item.content_type,
      };
    })
    .filter(Boolean);
}

function looksLikePathOrUrl(value) {
  return /^https?:\/\//i.test(value) || value.startsWith('/workspace/') || value.endsWith('.md');
}

function enabledFlag(value) {
  return value === true || value === 'true' || value === '1' || value === 1 || value === 'yes' || value === 'on';
}

function sanitizeRelativePath(input) {
  const raw = String(input || '').replace(/\\/g, '/').replace(/^\/+/, '').trim();
  if (!raw) return '';
  const parts = raw.split('/').filter(Boolean);
  const safe = [];
  for (const part of parts) {
    if (part === '.' || part === '') continue;
    if (part === '..') return '';
    safe.push(part.replace(/\0/g, ''));
  }
  return safe.join('/');
}

function inferContentTypeByExt(filePath) {
  const lower = String(filePath || '').toLowerCase();
  if (lower.endsWith('.md')) return 'text/markdown; charset=utf-8';
  if (lower.endsWith('.json')) return 'application/json; charset=utf-8';
  if (lower.endsWith('.txt')) return 'text/plain; charset=utf-8';
  if (lower.endsWith('.png')) return 'image/png';
  if (lower.endsWith('.jpg') || lower.endsWith('.jpeg')) return 'image/jpeg';
  if (lower.endsWith('.pdf')) return 'application/pdf';
  if (lower.endsWith('.zip')) return 'application/zip';
  return 'application/octet-stream';
}
