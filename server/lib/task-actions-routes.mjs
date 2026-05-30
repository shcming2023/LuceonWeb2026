/**
 * task-actions-routes.mjs — 任务动作 API 与 SSE 流
 *
 * 落实 PRD v0.4 §8.2 的"必须补齐"API：
 *   POST /tasks/:id/retry       → 将 failed 任务整体重跑：克隆新 ParseTask（retryOf 指向原任务）
 *   POST /tasks/:id/reparse     → 仅重跑解析阶段：保留原文件，当前任务置回 pending
 *   POST /tasks/:id/re-ai       → 仅重跑 AI 阶段：当前任务置回 ai-pending，原 AI Job 置失效
 *   POST /tasks/:id/cancel      → 将 pending/ai-pending/review-pending 任务置为 canceled
 *   POST /tasks/:id/review      → 人工审核：接受修正后的元数据，写回 Material 并置 completed
 *   POST /tasks/batch/retry     → 批量重试 failed 任务
 *   GET  /tasks/stream          → SSE：实时推送任务状态变更与事件日志
 *
 * 所有写动作都会：
 *   1) 通过 db-server REST 更新状态；
 *   2) 调用 logTaskEvent 写入 taskEvents；
 *   3) 通过事件总线 emit('task-update', ...) 广播，使订阅者（SSE）即时感知。
 *
 * v0.4.1 防护增强：
 *   - reparse/retry/re-ai 执行前必须通过资源前置校验（Material 存在 + MinIO 原文件存在）
 *   - 校验失败返回 409 Conflict，不得修改任务状态
 *   - 杜绝"已完成任务因 Reparse 降级为失败"的数据污染问题
 */

import { taskEventBus } from './task-events-bus.mjs';
import { logTaskEvent } from '../services/logging/task-events.mjs';
import { createOrphanHelpers } from './consistency-routes.mjs';
import { createAiMetadataJob } from '../services/ai/metadata-job-client.mjs';
import { loadCleanServiceConfig } from '../services/cleanservice/config.mjs';
import { createCleanServiceClientWithTransport } from '../services/cleanservice/worker-factory.mjs';
import { verifyCleanServiceOutputArtifacts } from '../services/cleanservice/output-verifier.mjs';
import { buildVerifiedCleanOutputMetadataCandidate } from '../services/cleanservice/metadata-summary.mjs';
import { buildCleanMetadataPersistencePlan } from '../services/cleanservice/metadata-persistence.mjs';
import { applyCleanMetadataPersistencePlan } from '../services/cleanservice/metadata-apply-executor.mjs';
import { createHash } from 'crypto';

const DB_BASE_URL = process.env.DB_BASE_URL || 'http://localhost:8789';
const activeTocRebuildJobs = new Map();

// ─── db-server REST 小封装 ───────────────────────────────────
async function dbGet(path) {
  const resp = await fetch(`${DB_BASE_URL}${path}`);
  if (resp.status === 404) return null;
  if (!resp.ok) throw new Error(`GET ${path} failed: HTTP ${resp.status}`);
  return await resp.json();
}
async function dbPost(path, body) {
  const resp = await fetch(`${DB_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`POST ${path} failed: HTTP ${resp.status}`);
  return await resp.json().catch(() => ({}));
}
async function dbPatch(path, body) {
  const resp = await fetch(`${DB_BASE_URL}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`PATCH ${path} failed: HTTP ${resp.status}`);
  return await resp.json().catch(() => ({}));
}

function sha256Hex(input) {
  return createHash('sha256').update(input).digest('hex');
}

async function streamToBuffer(stream) {
  const chunks = [];
  for await (const chunk of stream) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}

function jsonBuffer(value) {
  return Buffer.from(`${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function objectRef(bucket, object, buffer, contentType) {
  return {
    bucket,
    object,
    size_bytes: buffer.length,
    content_type: contentType,
    sha256: sha256Hex(buffer),
  };
}

function extractMarkdownOutline(markdown, fallbackTitle) {
  const headings = [];
  const lines = String(markdown || '').split(/\r?\n/);
  for (const [index, line] of lines.entries()) {
    const match = /^(#{1,6})\s+(.+?)\s*$/.exec(line);
    if (!match) continue;
    headings.push({
      id: `h${headings.length + 1}`,
      level: match[1].length,
      title: match[2].replace(/\s+/g, ' ').trim(),
      line: index + 1,
    });
  }

  if (headings.length === 0) {
    const firstText = lines.map((line) => line.trim()).find(Boolean);
    headings.push({
      id: 'h1',
      level: 1,
      title: fallbackTitle || firstText || 'Untitled Material',
      line: firstText ? Math.max(1, lines.findIndex((line) => line.trim() === firstText) + 1) : 1,
    });
  }

  return headings;
}

function buildLogicTree(headings) {
  const root = { id: 'root', title: 'root', level: 0, children: [] };
  const stack = [root];
  for (const heading of headings) {
    const node = { id: heading.id, title: heading.title, level: heading.level, line: heading.line, children: [] };
    while (stack.length > 1 && stack[stack.length - 1].level >= node.level) stack.pop();
    stack[stack.length - 1].children.push(node);
    stack.push(node);
  }
  return root;
}

function flattenTree(node, depth = 0) {
  const rows = [];
  for (const child of node.children || []) {
    rows.push(`${'  '.repeat(depth)}- ${child.title}`);
    rows.push(...flattenTree(child, depth + 1));
  }
  return rows;
}

function buildRebuiltMarkdown({ title, readableTree, markdown }) {
  const sourceMarkdown = String(markdown || '').trim();
  const outline = String(readableTree || '').trim();
  return [
    `# ${title}`,
    '## 重建目录',
    outline.replace(/^# .+?(\r?\n)+/, '').trim() || `- ${title}`,
    '---',
    '## 正文',
    sourceMarkdown || '_原 Markdown 为空_',
    '',
  ].join('\n\n');
}

function buildManualTocArtifacts({ task, material, markdown, sourceRef, sourceSha256, sourceSizeBytes, cleanBucket }) {
  const serviceName = 'toc-rebuild';
  const assetVersion = 'v1';
  const jobId = `luceon-${task.id}-${serviceName}-${assetVersion}`;
  const prefix = `${serviceName}/${task.materialId}/${assetVersion}/`;
  const now = new Date().toISOString();
  const title = material?.title || material?.metadata?.title || task?.metadata?.title || material?.metadata?.fileName || `Material ${task.materialId}`;
  const headings = extractMarkdownOutline(markdown, title);
  const logicTree = buildLogicTree(headings);
  const readableTree = `# ${title}\n\n${flattenTree(logicTree).join('\n') || `- ${title}`}\n`;
  const rebuiltMarkdown = buildRebuiltMarkdown({ title, readableTree, markdown });
  const floodedContent = headings.map((heading, index) => ({
    id: heading.id,
    order: index + 1,
    type: 'heading',
    level: heading.level,
    title: heading.title,
    source: {
      bucket: sourceRef.bucket,
      object: sourceRef.object,
      line: heading.line,
    },
  }));
  const skeleton = {
    schema: 'luceon-toc-skeleton/v1',
    materialId: String(task.materialId),
    assetVersion,
    nodes: headings.map((heading, index) => ({
      id: heading.id,
      parentId: null,
      order: index + 1,
      level: heading.level,
      title: heading.title,
      sourceLine: heading.line,
    })),
  };
  const unresolvedAnchors = [];
  const approxTokens = Math.max(1, Math.ceil(String(markdown || '').length / 4));
  const metrics = {
    schema: 'luceon-toc-metrics/v1',
    stats: {
      tokens: {
        prompt: approxTokens,
        completion: Math.max(1, headings.length * 8),
        total: approxTokens + Math.max(1, headings.length * 8),
      },
      heading_count: headings.length,
      unresolved_anchor_count: 0,
    },
  };
  const provenance = {
    schema: 'luceon-provenance/v1',
    service: {
      name: serviceName,
      protocol_version: 'v1',
      runner: 'luceon-manual-local-toc-rebuild',
    },
    job: {
      job_id: jobId,
      submitted_at: now,
      finished_at: now,
      trigger: 'operator-manual',
    },
    asset: {
      material_id: String(task.materialId),
      parse_task_id: task.id,
      asset_version: assetVersion,
    },
    inputs: [{
      bucket: sourceRef.bucket,
      object: sourceRef.object,
      sha256: sourceSha256,
      size_bytes: sourceSizeBytes,
    }],
  };

  const payloads = {
    flooded_content: { object: `${prefix}flooded_content.json`, buffer: jsonBuffer(floodedContent), contentType: 'application/json; charset=utf-8' },
    logic_tree: { object: `${prefix}logic_tree.json`, buffer: jsonBuffer(logicTree), contentType: 'application/json; charset=utf-8' },
    readable_tree: { object: `${prefix}readable_tree.md`, buffer: Buffer.from(readableTree, 'utf8'), contentType: 'text/markdown; charset=utf-8' },
    rebuilt_markdown: { object: `${prefix}rebuilt_markdown.md`, buffer: Buffer.from(rebuiltMarkdown, 'utf8'), contentType: 'text/markdown; charset=utf-8' },
    skeleton: { object: `${prefix}skeleton.json`, buffer: jsonBuffer(skeleton), contentType: 'application/json; charset=utf-8' },
    unresolved_anchors: { object: `${prefix}unresolved_anchors.json`, buffer: jsonBuffer(unresolvedAnchors), contentType: 'application/json; charset=utf-8' },
    metrics: { object: `${prefix}metrics.json`, buffer: jsonBuffer(metrics), contentType: 'application/json; charset=utf-8' },
    provenance: { object: `${prefix}provenance.json`, buffer: jsonBuffer(provenance), contentType: 'application/json; charset=utf-8' },
  };
  const artifacts = Object.fromEntries(
    Object.entries(payloads).map(([role, item]) => [role, objectRef(cleanBucket, item.object, item.buffer, item.contentType)]),
  );

  return {
    serviceName,
    assetVersion,
    jobId,
    prefix,
    now,
    payloads,
    artifacts,
    stats: metrics.stats,
    sourceInput: {
      bucket: sourceRef.bucket,
      object: sourceRef.object,
      sha256: sourceSha256,
      size_bytes: sourceSizeBytes,
    },
  };
}

/**
 * 资源前置校验：检查任务关联的 Material 和 MinIO 文件是否存在
 * @param {Object} task - ParseTask 对象
 * @param {Object} deps - 依赖注入对象 { getMinioClient, getMinioBucket, getStorageBackend, getParsedBucket }
 * @param {Object} options - 校验选项 { needOriginal: boolean, needMarkdown: boolean }
 * @returns {{ ok: boolean, reason?: string, materialMissing?: boolean, originalMissing?: boolean, markdownMissing?: boolean }}
 */
async function validateResources(task, deps, options = {}) {
  const { needOriginal = true, needMarkdown = false } = options;
  const result = { ok: true };

  // 1) Material 存在性校验
  if (!task.materialId) {
    result.ok = false;
    result.reason = '任务缺少 materialId，无法定位关联资料';
    result.materialMissing = true;
    return result;
  }
  const material = await dbGet(`/materials/${encodeURIComponent(task.materialId)}`);
  if (!material) {
    result.ok = false;
    result.reason = `关联的 Material (${task.materialId}) 已被删除，无法重跑。请重新上传文件创建新任务`;
    result.materialMissing = true;
    return result;
  }

  // 2) 原始文件（MinIO objectName）存在性校验
  if (needOriginal && deps.getStorageBackend() === 'minio') {
    const objectName = material.metadata?.objectName;
    if (!objectName) {
      result.ok = false;
      result.reason = `Material (${task.materialId}) 缺少 objectName，原始文件路径已丢失`;
      result.originalMissing = true;
      return result;
    }
    try {
      const minio = deps.getMinioClient();
      const bucket = deps.getMinioBucket();
      await minio.statObject(bucket, objectName);
    } catch (e) {
      result.ok = false;
      result.reason = `原始文件 (${material.metadata.objectName}) 在 MinIO 中不存在，无法重新解析。请重新上传文件`;
      result.originalMissing = true;
      return result;
    }
  }

  // 3) Markdown 产物存在性校验（Re-AI 需要）
  if (needMarkdown && deps.getStorageBackend() === 'minio') {
    const mdObjectName = material.metadata?.markdownObjectName || task.metadata?.markdownObjectName;
    if (!mdObjectName) {
      result.ok = false;
      result.reason = '缺少 Markdown 产物路径，无法重跑 AI 识别。请先执行 Reparse';
      result.markdownMissing = true;
      return result;
    }
    try {
      const minio = deps.getMinioClient();
      const parsedBucket = deps.getParsedBucket();
      await minio.statObject(parsedBucket, mdObjectName);
    } catch (e) {
      result.ok = false;
      result.reason = `Markdown 产物 (${mdObjectName}) 在 MinIO 中不存在，无法重跑 AI 识别。请先执行 Reparse`;
      result.markdownMissing = true;
      return result;
    }
  }

  return result;
}

async function emitAndLog({ taskId, taskType = 'parse', level = 'info', event, message, update = {}, payload = {} }) {
  await logTaskEvent({ taskId, taskType, level, event, message, payload });
  try {
    taskEventBus.emit('task-update', {
      taskId,
      event,
      level,
      update,
      at: new Date().toISOString(),
    });
  } catch (e) {
    console.warn(`[task-actions] eventBus emit failed: ${e.message}`);
  }
}

function newTaskId() {
  return `task-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`;
}

const NEW_RUN_METADATA_CLEAR_KEYS = [
  'mineruTaskId',
  'mineruStatus',
  'mineruSubmittedAt',
  'mineruQueuedAhead',
  'mineruStartedAt',
  'mineruLastStatusAt',
  'mineruObservedProgress',
  'localTimeoutOccurred',
  'localTimeoutAt',
  '_synthetic_warn',
  '_synthetic_warn_msg',
  'submitRetries',
  'lastSubmitError',
  'recoveredFromMisjudgedFailed',
  'previousState',
  'previousErrorMessage',
  'recoveredAt',
  'markdownObjectName',
  'parsedPrefix',
  'parsedFilesCount',
  'artifactManifestObjectName',
  'zipObjectName',
  'artifactIncomplete',
  'parsedAt',
  'aiJobId',
  'emptyMarkdownRetryAttempted',
  'emptyMarkdownRetryMineruTaskId',
  'emptyMarkdownRetryError',
  'emptyMarkdownRetryProfile',
];

export function buildMetadataForNewParseRun(metadata = {}, extra = {}) {
  const next = { ...(metadata || {}) };
  for (const key of NEW_RUN_METADATA_CLEAR_KEYS) {
    delete next[key];
  }
  return {
    ...next,
    ...extra,
  };
}

// ─── 核心动作实现 ────────────────────────────────────────────

/**
 * retry: failed → 克隆出新 ParseTask，指向原任务
 * 成功后：原任务仍保留为 failed（可审计），新任务进入 pending
 * @param {Object} task - ParseTask 对象
 * @param {Object} deps - 依赖注入对象（用于资源校验）
 * @returns {Object} 克隆的新任务
 */
async function retryTask(task, deps) {
  if (task.state !== 'failed') {
    throw new Error(`Only failed tasks can be retried (current: ${task.state})`);
  }
  // 前置校验：Retry 需要原始文件存在
  const validation = await validateResources(task, deps, { needOriginal: true, needMarkdown: false });
  if (!validation.ok) {
    const err = new Error(validation.reason);
    err.statusCode = 409;
    err.resourceCheck = validation;
    throw err;
  }
  const newId = newTaskId();
  const clone = {
    ...task,
    id: newId,
    state: 'pending',
    stage: 'upload',
    progress: 0,
    message: `Retry of ${task.id}`,
    errorMessage: null,
    retryOf: task.id,
    aiJobId: null,
    metadata: buildMetadataForNewParseRun(task.metadata, {
      retryOf: task.id,
      aiJobId: null,
      submitRetries: 0,
      manualRetryRequestedAt: new Date().toISOString(),
    }),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    completedAt: null,
  };
  await dbPost('/tasks', clone);
  await emitAndLog({
    taskId: newId,
    event: 'retry-requested',
    message: `由任务 ${task.id} 克隆而来，重新进入 pending`,
    update: { state: 'pending' },
    payload: { retryOf: task.id },
  });
  return clone;
}

/**
 * reparse: 将当前任务从 failed/completed/review-pending 置回 pending
 * 适用于希望"同一任务 ID 重新解析"的场景，保留任务血缘
 * 前置校验：Material 必须存在且 MinIO 原始对象必须存在，否则返回 409 不修改状态
 * @param {Object} task - ParseTask 对象
 * @param {Object} deps - 依赖注入对象（用于资源校验）
 * @returns {Object} 更新后的任务
 */
async function reparseTask(task, deps) {
  const allowed = new Set(['failed', 'completed', 'review-pending', 'canceled']);
  if (!allowed.has(task.state)) {
    throw new Error(`Task state ${task.state} cannot be reparsed`);
  }
  // 前置校验：Reparse 需要原始文件存在
  const validation = await validateResources(task, deps, { needOriginal: true, needMarkdown: false });
  if (!validation.ok) {
    const err = new Error(validation.reason);
    err.statusCode = 409;
    err.resourceCheck = validation;
    throw err;
  }
  const update = {
    state: 'pending',
    stage: 'upload',
    progress: 0,
    message: '用户发起 Reparse，任务已置回 pending',
    errorMessage: null,
    metadata: buildMetadataForNewParseRun(task.metadata, {
      reparseOf: task.id,
      submitRetries: 0,
      manualReparseRequestedAt: new Date().toISOString(),
    }),
    updatedAt: new Date().toISOString(),
    completedAt: null,
  };
  await dbPatch(`/tasks/${encodeURIComponent(task.id)}`, update);
  await emitAndLog({
    taskId: task.id,
    event: 'reparse-requested',
    message: update.message,
    update,
  });
  return { ...task, ...update };
}

/**
 * re-ai: 仅重跑 AI 阶段
 *   - 将当前 aiJobId 对应的 Job 置为 failed（若存在且非终态）
 *   - ParseTask 状态置回 ai-pending
 *   - 下一轮 tick 由 task-worker/ai-worker 自动重新创建 AI Job
 *
 * 前置：任务已产出 markdown（metadata.markdownObjectName 应存在）
 * 前置校验：Material 必须存在且 Markdown 产物必须存在，否则返回 409 不修改状态
 * @param {Object} task - ParseTask 对象
 * @param {Object} deps - 依赖注入对象（用于资源校验）
 * @returns {Object} 更新后的任务
 */
export async function reAiTask(task, deps) {
  const allowed = new Set(['completed', 'review-pending', 'failed']);
  if (!allowed.has(task.state)) {
    throw new Error(`Task state ${task.state} cannot trigger Re-AI`);
  }
  // 前置校验：Re-AI 需要 Material 存在 + Markdown 产物存在
  const validation = await validateResources(task, deps, { needOriginal: false, needMarkdown: true });
  if (!validation.ok) {
    const err = new Error(validation.reason);
    err.statusCode = 409;
    err.resourceCheck = validation;
    throw err;
  }
  // 让旧 AI Job 失效（不阻塞主流程）
  if (task.aiJobId) {
    try {
      await dbPatch(`/ai-metadata-jobs/${encodeURIComponent(task.aiJobId)}`, {
        state: 'failed',
        message: '被 Re-AI 动作标记为失效',
        updatedAt: new Date().toISOString(),
      });
    } catch (e) {
      console.warn(`[task-actions] mark old AI job failed error: ${e.message}`);
    }
  }

  // 立即创建新 AI Job（解决 ai-pending 卡住无任务的问题）
  const jobResult = await createAiMetadataJob({
    parseTaskId: task.id,
    materialId: task.materialId,
    inputMarkdownObjectName: task.metadata?.markdownObjectName || null,
  });

  if (!jobResult.created && jobResult.reason !== 'duplicate') {
    const errorUpdate = {
      state: 'failed',
      stage: 'ai',
      errorMessage: `Re-AI 创建 AI 任务失败: ${jobResult.reason}`,
      aiJobId: null,
      updatedAt: new Date().toISOString(),
    };
    await dbPatch(`/tasks/${encodeURIComponent(task.id)}`, errorUpdate);
    throw new Error(`Re-AI 创建 AI 任务失败: ${jobResult.reason}`);
  }

  const update = {
    state: 'ai-pending',
    stage: 'ai',
    progress: 80,
    message: '用户发起 Re-AI，等待 AI Worker 拾取',
    errorMessage: null,
    aiJobId: jobResult.jobId || null,
    metadata: { ...(task.metadata || {}), aiJobId: jobResult.jobId || null },
    updatedAt: new Date().toISOString(),
  };
  await dbPatch(`/tasks/${encodeURIComponent(task.id)}`, update);
  await emitAndLog({
    taskId: task.id,
    event: 're-ai-requested',
    message: update.message,
    update,
  });
  return { ...task, ...update };
}

/**
 * cancel: 将活跃状态任务置为 canceled
 */
async function cancelTask(task) {
  // Check if task can be canceled
  const isCancellable = ['pending', 'running', 'ai-pending', 'ai-running', 'review-pending', 'result-store'].includes(task.state) ||
                        ['mineru-queued', 'mineru-processing', 'submit-failed-retryable', 'result-fetching'].includes(task.stage);

  if (!isCancellable) {
    if (!(task.state === 'failed' && task.stage === 'submit-failed-retryable')) {
      throw new Error(`Task state ${task.state} (stage: ${task.stage}) cannot be canceled directly`);
    }
  }

  const mineruTaskId = task.metadata?.mineruTaskId;
  let externalMineruStateAtCancel = undefined;
  let externalMineruStateUnknown = undefined;

  if (mineruTaskId) {
    const localEndpointRaw = task.optionsSnapshot?.localEndpoint;
    if (localEndpointRaw) {
      let localEndpoint = localEndpointRaw;
      if (localEndpoint.includes('localhost') || localEndpoint.includes('127.0.0.1')) {
        localEndpoint = localEndpoint.replace(/localhost|127\.0\.0\.1/g, 'host.docker.internal');
      }
      localEndpoint = localEndpoint.replace(/\/+$/, '');
      try {
        const tRes = await fetch(`${localEndpoint}/tasks/${mineruTaskId}`, { signal: AbortSignal.timeout(3000) });
        if (tRes.ok) {
          const mineruData = await tRes.json();
          externalMineruStateAtCancel = String(mineruData.status || mineruData.state || '').toLowerCase();
        } else {
          externalMineruStateUnknown = true;
        }
      } catch (e) {
        externalMineruStateUnknown = true;
      }
    } else {
      externalMineruStateUnknown = true;
    }
  }

  const update = {
    state: 'canceled',
    stage: 'canceled',
    message: '用户已取消 / 测试终止',
    updatedAt: new Date().toISOString(),
    completedAt: new Date().toISOString(),
    metadata: {
      ...(task.metadata || {}),
      canceledAt: new Date().toISOString(),
      canceledBy: 'user'
    }
  };

  const runningTocJob = task.metadata?.cleanServiceJobs?.['toc-rebuild'];
  if (['running', 'pending'].includes(String(runningTocJob?.status || runningTocJob?.cleanState || ''))) {
    const now = new Date().toISOString();
    update.metadata.cleanServiceJobs = {
      ...(task.metadata?.cleanServiceJobs || {}),
      'toc-rebuild': {
        ...runningTocJob,
        status: 'canceled',
        cleanState: 'skipped',
        productLabel: '目录重建已取消',
        taskIntent: 'skipped',
        finishedAt: now,
        updatedAt: now,
        error: {
          code: 'canceled',
          message: 'Task was canceled by operator before toc-rebuild completed',
          retriable: false,
        },
      },
    };
  }

  if (mineruTaskId) {
    update.metadata.externalMineruTaskId = mineruTaskId;
    if (externalMineruStateAtCancel !== undefined) {
      update.metadata.externalMineruStateAtCancel = externalMineruStateAtCancel;
    }
    if (externalMineruStateUnknown !== undefined) {
      update.metadata.externalMineruStateUnknown = externalMineruStateUnknown;
    }
    update.metadata.mineruStatus = 'canceled';
  }

  await dbPatch(`/tasks/${encodeURIComponent(task.id)}`, update);

  if (task.materialId) {
    try {
      const material = await dbGet(`/materials/${encodeURIComponent(task.materialId)}`);
      if (material) {
        const parsedFilesCount = material.metadata?.parsedFilesCount || task.metadata?.parsedFilesCount || 0;
        if (parsedFilesCount > 0) {
          const materialMetadata = { ...(material.metadata || {}) };
          if (runningTocJob) {
            materialMetadata.cleanMaterials = {
              ...(material.metadata?.cleanMaterials || {}),
              'toc-rebuild': {
                ...(material.metadata?.cleanMaterials?.['toc-rebuild'] || {}),
                serviceName: 'toc-rebuild',
                latestVersion: runningTocJob.assetVersion,
                status: 'canceled',
                cleanState: 'skipped',
                productLabel: '目录重建已取消',
                jobId: runningTocJob.jobId,
                prefix: runningTocJob.sink?.prefix,
                updatedAt: new Date().toISOString(),
                error: {
                  code: 'canceled',
                  message: 'Task was canceled by operator before toc-rebuild completed',
                  retriable: false,
                },
              },
            };
          }
          await dbPatch(`/materials/${encodeURIComponent(task.materialId)}`, {
            metadata: {
              ...materialMetadata,
              canceledTaskAt: new Date().toISOString(),
              canceledTaskId: task.id
            }
          });
        } else {
          await dbPatch(`/materials/${encodeURIComponent(task.materialId)}`, {
            status: 'canceled',
            mineruStatus: 'canceled',
            metadata: {
              ...(material.metadata || {}),
              mineruStatus: 'canceled',
              processingMsg: '用户已取消 / 测试终止',
              processingStage: 'canceled'
            }
          });
        }
      }
    } catch (e) {
      console.warn(`[task-actions] cancel backfill material failed: ${e.message}`);
    }
  }

  await emitAndLog({
    taskId: task.id,
    level: 'warn',
    event: 'task-canceled',
    message: update.message,
    update,
  });
  return { ...task, ...update };
}

/**
 * review: 人工审核通过，写回 Material.metadata 并将任务置为 completed
 * body: { metadata: Object, notes?: string }
 */
async function reviewTask(task, body) {
  const allowed = new Set(['review-pending', 'completed']);
  if (!allowed.has(task.state)) {
    throw new Error(`Task state ${task.state} cannot be reviewed`);
  }
  const metadata = body?.metadata || {};
  if (task.materialId) {
    try {
      await dbPatch(`/materials/${encodeURIComponent(task.materialId)}`, {
        status: 'completed',
        mineruStatus: 'completed',
        aiStatus: 'analyzed',
        updateTime: Date.now(),
        metadata: {
          ...metadata,
          aiJobId: task.aiJobId,
          reviewedAt: new Date().toISOString(),
          reviewer: body?.reviewer || 'operator',
          processingStage: 'done',
          processingMsg: '人工审核确认',
        },
      });
    } catch (e) {
      console.warn(`[task-actions] review backfill material failed: ${e.message}`);
    }
  }
  const update = {
    state: 'completed',
    stage: 'done',
    progress: 100,
    message: body?.notes || '审核通过',
    metadata: { ...(task.metadata || {}), ...metadata, reviewedAt: new Date().toISOString() },
    updatedAt: new Date().toISOString(),
    completedAt: new Date().toISOString(),
  };
  await dbPatch(`/tasks/${encodeURIComponent(task.id)}`, update);
  await emitAndLog({
    taskId: task.id,
    event: 'review-confirmed',
    message: update.message,
    update,
    payload: { reviewer: body?.reviewer || 'operator' },
  });
  return { ...task, ...update };
}

async function runManualTocRebuild(task, deps) {
  const allowed = new Set(['review-pending', 'completed']);
  if (!allowed.has(String(task.state))) {
    const err = new Error(`Only review-pending/completed tasks can run toc-rebuild manually (current: ${task.state})`);
    err.statusCode = 409;
    throw err;
  }

  const validation = await validateResources(task, deps, { needOriginal: false, needMarkdown: true });
  if (!validation.ok) {
    const err = new Error(validation.reason);
    err.statusCode = 409;
    err.resourceCheck = validation;
    throw err;
  }

  const material = await dbGet(`/materials/${encodeURIComponent(task.materialId)}`);
  if (!material) {
    const err = new Error(`关联的 Material (${task.materialId}) 已被删除，无法执行目录重建`);
    err.statusCode = 409;
    throw err;
  }

  const existingTaskJob = task.metadata?.cleanServiceJobs?.['toc-rebuild'];
  const existingMaterialJob = material.metadata?.cleanMaterials?.['toc-rebuild'];
  if (existingTaskJob || existingMaterialJob) {
    const err = new Error('当前任务或素材已存在 toc-rebuild Clean Material 元数据；为避免覆盖，请先审计现有版本');
    err.statusCode = 409;
    throw err;
  }

  if (deps.getStorageBackend() !== 'minio') {
    const err = new Error('目录重建当前仅支持 MinIO 存储后端');
    err.statusCode = 409;
    throw err;
  }

  const markdownObject = material.metadata?.markdownObjectName || task.metadata?.markdownObjectName;
  const parsedBucket = deps.getParsedBucket();
  const cleanBucket = process.env.MINIO_CLEAN_BUCKET || 'eduassets-clean';
  const minio = deps.getMinioClient();
  if (!minio) {
    const err = new Error('MinIO client is not available');
    err.statusCode = 503;
    throw err;
  }

  await emitAndLog({
    taskId: task.id,
    event: 'toc-rebuild-manual-started',
    message: '操作者手动触发目录重建',
    payload: { materialId: task.materialId, markdownObject, parsedBucket, cleanBucket },
  });

  const stream = await minio.getObject(parsedBucket, markdownObject);
  const markdownBuffer = await streamToBuffer(stream);
  const artifactPlan = buildManualTocArtifacts({
    task,
    material,
    markdown: markdownBuffer.toString('utf8'),
    sourceRef: { bucket: parsedBucket, object: markdownObject },
    sourceSha256: sha256Hex(markdownBuffer),
    sourceSizeBytes: markdownBuffer.length,
    cleanBucket,
  });

  for (const item of Object.values(artifactPlan.payloads)) {
    await minio.putObject(cleanBucket, item.object, item.buffer, item.buffer.length, { 'Content-Type': item.contentType });
  }

  const taskSummary = {
    serviceName: artifactPlan.serviceName,
    protocolVersion: 'v1',
    jobId: artifactPlan.jobId,
    status: 'completed',
    productLabel: '目录结构已完成',
    taskIntent: 'completed',
    cleanReview: null,
    materialId: String(task.materialId),
    parseTaskId: task.id,
    assetVersion: artifactPlan.assetVersion,
    submittedAt: artifactPlan.now,
    startedAt: artifactPlan.now,
    finishedAt: artifactPlan.now,
    artifacts: artifactPlan.artifacts,
    stats: {
      tokensPrompt: artifactPlan.stats.tokens.prompt,
      tokensCompletion: artifactPlan.stats.tokens.completion,
      tokensTotal: artifactPlan.stats.tokens.total,
      costCnyEstimated: 0,
      costCnyActual: 0,
      unresolvedAnchorCount: 0,
    },
    sourceInput: artifactPlan.sourceInput,
    error: null,
    warnings: ['manual-local-toc-rebuild-from-mineru-markdown'],
    updatedAt: artifactPlan.now,
  };

  const materialSummary = {
    serviceName: artifactPlan.serviceName,
    latestVersion: artifactPlan.assetVersion,
    status: 'completed',
    productLabel: '目录结构已完成',
    prefix: artifactPlan.prefix,
    provenanceObjectName: artifactPlan.artifacts.provenance.object,
    stats: {
      tokensPrompt: taskSummary.stats.tokensPrompt,
      tokensCompletion: taskSummary.stats.tokensCompletion,
      tokensTotal: taskSummary.stats.tokensTotal,
      costCnyActual: 0,
      unresolvedAnchorCount: 0,
    },
    sourceInput: artifactPlan.sourceInput,
    updatedAt: artifactPlan.now,
  };

  await dbPatch(`/tasks/${encodeURIComponent(task.id)}`, {
    metadata: {
      ...(task.metadata || {}),
      cleanServiceJobs: {
        ...(task.metadata?.cleanServiceJobs || {}),
        'toc-rebuild': taskSummary,
      },
    },
  });
  await dbPatch(`/materials/${encodeURIComponent(task.materialId)}`, {
    metadata: {
      ...(material.metadata || {}),
      cleanMaterials: {
        ...(material.metadata?.cleanMaterials || {}),
        'toc-rebuild': materialSummary,
      },
    },
  });

  await emitAndLog({
    taskId: task.id,
    event: 'toc-rebuild-manual-completed',
    message: `目录重建已完成: ${artifactPlan.prefix}`,
    update: { cleanServiceJobs: { 'toc-rebuild': taskSummary } },
    payload: {
      materialId: task.materialId,
      jobId: artifactPlan.jobId,
      assetVersion: artifactPlan.assetVersion,
      prefix: artifactPlan.prefix,
      artifactCount: Object.keys(artifactPlan.artifacts).length,
    },
  });

  return {
    ok: true,
    taskId: task.id,
    materialId: String(task.materialId),
    jobId: artifactPlan.jobId,
    assetVersion: artifactPlan.assetVersion,
    prefix: artifactPlan.prefix,
    artifacts: artifactPlan.artifacts,
  };
}

function parseAssetVersionNumber(value) {
  const match = String(value || '').match(/^v(\d+)$/i);
  return match ? Number(match[1]) : 0;
}

function nextTocRebuildAssetVersion(existingTaskJob, existingMaterialJob) {
  const current = Math.max(
    parseAssetVersionNumber(existingTaskJob?.assetVersion),
    parseAssetVersionNumber(existingMaterialJob?.latestVersion),
    1,
  );
  return `v${current + 1}`;
}

function withoutCleanServiceMetadata(record, serviceName) {
  const metadata = { ...(record?.metadata || {}) };
  if (metadata.cleanServiceJobs) {
    const cleanServiceJobs = { ...metadata.cleanServiceJobs };
    delete cleanServiceJobs[serviceName];
    metadata.cleanServiceJobs = cleanServiceJobs;
  }
  if (metadata.cleanMaterials) {
    const cleanMaterials = { ...metadata.cleanMaterials };
    delete cleanMaterials[serviceName];
    metadata.cleanMaterials = cleanMaterials;
  }
  return { ...(record || {}), metadata };
}

function getActiveTocRebuild(taskId) {
  const active = activeTocRebuildJobs.get(String(taskId));
  if (!active) return null;
  return {
    taskId: active.taskId,
    materialId: active.materialId,
    jobId: active.jobId,
    assetVersion: active.assetVersion,
    prefix: active.prefix,
    status: 'running',
    submittedAt: active.submittedAt,
  };
}

function classifyCleanServiceError(error) {
  const message = error?.message || String(error || 'CleanService job failed');
  const cleanState = error?.cleanState
    || (error?.code === 'canceled' ? 'skipped' : null)
    || (error?.name === 'AbortError' || /timeout|timed out|aborted/i.test(message) ? 'timeout' : 'protocol-failure');
  const status = cleanState === 'timeout'
    ? 'timeout'
    : (cleanState === 'skipped' ? 'canceled' : 'failed');
  return {
    cleanState,
    status,
    code: error?.code || (cleanState === 'timeout' ? 'timeout' : (cleanState === 'skipped' ? 'canceled' : 'cleanservice_async_failed')),
    message,
    retriable: cleanState === 'timeout' || error?.retriable === true,
  };
}

function buildRunningCleanServiceSummaries({ task, request, submittedAt }) {
  const serviceName = request.service_name || 'toc-rebuild';
  const source = request.inputs?.[0]?.source || {};
  const productLabel = failure.status === 'canceled' ? '目录重建已取消' : '目录重建失败';
  const stats = {
    tokensPrompt: 0,
    tokensCompletion: 0,
    tokensTotal: 0,
    costCnyEstimated: 0,
    costCnyActual: 0,
    unresolvedAnchorCount: 0,
  };
  const taskSummary = {
    serviceName,
    protocolVersion: 'v1',
    jobId: request.job_id,
    status: 'running',
    cleanState: 'running',
    productLabel: '目录重建中',
    taskIntent: 'running',
    cleanReview: null,
    materialId: String(task.materialId),
    parseTaskId: task.id,
    assetVersion: request.asset_version,
    submittedAt,
    startedAt: submittedAt,
    finishedAt: null,
    artifacts: null,
    stats,
    sourceInput: { bucket: source.bucket, object: source.object },
    sink: { bucket: request.sink?.bucket, prefix: request.sink?.prefix },
    error: null,
    warnings: ['async-cleanservice-job'],
    updatedAt: submittedAt,
  };
  const materialSummary = {
    serviceName,
    latestVersion: request.asset_version,
    status: 'running',
    cleanState: 'running',
    productLabel: '目录重建中',
    jobId: request.job_id,
    prefix: request.sink?.prefix,
    provenanceObjectName: null,
    stats,
    sourceInput: taskSummary.sourceInput,
    updatedAt: submittedAt,
  };
  return { taskSummary, materialSummary };
}

function buildFailedCleanServiceSummaries({ task, request, submittedAt, error }) {
  const failure = classifyCleanServiceError(error);
  const now = new Date().toISOString();
  const serviceName = request.service_name || 'toc-rebuild';
  const source = request.inputs?.[0]?.source || {};
  const stats = {
    tokensPrompt: 0,
    tokensCompletion: 0,
    tokensTotal: 0,
    costCnyEstimated: 0,
    costCnyActual: 0,
    unresolvedAnchorCount: 0,
  };
  const taskSummary = {
    serviceName,
    protocolVersion: 'v1',
    jobId: request.job_id,
    status: failure.status,
    cleanState: failure.cleanState,
    productLabel,
    taskIntent: 'failed',
    cleanReview: null,
    materialId: String(task.materialId),
    parseTaskId: task.id,
    assetVersion: request.asset_version,
    submittedAt,
    startedAt: submittedAt,
    finishedAt: now,
    artifacts: null,
    stats,
    sourceInput: { bucket: source.bucket, object: source.object },
    sink: { bucket: request.sink?.bucket, prefix: request.sink?.prefix },
    error: failure,
    warnings: ['async-cleanservice-job-failed'],
    updatedAt: now,
  };
  const materialSummary = {
    serviceName,
    latestVersion: request.asset_version,
    status: failure.status,
    cleanState: failure.cleanState,
    productLabel,
    jobId: request.job_id,
    prefix: request.sink?.prefix,
    provenanceObjectName: null,
    stats,
    sourceInput: taskSummary.sourceInput,
    error: failure,
    updatedAt: now,
  };
  return { taskSummary, materialSummary };
}

async function persistCleanServiceSummaries({ task, material, serviceName, taskSummary, materialSummary }) {
  await dbPatch(`/tasks/${encodeURIComponent(task.id)}`, {
    metadata: {
      ...(task.metadata || {}),
      cleanServiceJobs: {
        ...(task.metadata?.cleanServiceJobs || {}),
        [serviceName]: taskSummary,
      },
    },
  });
  await dbPatch(`/materials/${encodeURIComponent(task.materialId)}`, {
    metadata: {
      ...(material.metadata || {}),
      cleanMaterials: {
        ...(material.metadata?.cleanMaterials || {}),
        [serviceName]: materialSummary,
      },
    },
  });
}

async function prepareExternalCleanServiceTocRebuild(task, deps, options = {}) {
  const allowed = new Set(['review-pending', 'completed']);
  if (!allowed.has(String(task.state))) {
    const err = new Error(`Only review-pending/completed tasks can run toc-rebuild manually (current: ${task.state})`);
    err.statusCode = 409;
    throw err;
  }

  const validation = await validateResources(task, deps, { needOriginal: false, needMarkdown: true });
  if (!validation.ok) {
    const err = new Error(validation.reason);
    err.statusCode = 409;
    err.resourceCheck = validation;
    throw err;
  }

  const material = await dbGet(`/materials/${encodeURIComponent(task.materialId)}`);
  if (!material) {
    const err = new Error(`关联的 Material (${task.materialId}) 已被删除，无法执行目录重建`);
    err.statusCode = 409;
    throw err;
  }

  const serviceName = 'toc-rebuild';
  const existingTaskJob = task.metadata?.cleanServiceJobs?.[serviceName];
  const existingMaterialJob = material.metadata?.cleanMaterials?.[serviceName];
  const forceNewVersion = options.forceNewVersion === true;
  if ((existingTaskJob || existingMaterialJob) && !forceNewVersion) {
    const err = new Error('当前任务或素材已存在 toc-rebuild Clean Material 元数据；为避免覆盖，请先审计现有版本');
    err.statusCode = 409;
    throw err;
  }

  if (deps.getStorageBackend() !== 'minio') {
    const err = new Error('目录重建当前仅支持 MinIO 存储后端');
    err.statusCode = 409;
    throw err;
  }

  const minio = deps.getMinioClient();
  if (!minio) {
    const err = new Error('MinIO client is not available');
    err.statusCode = 503;
    throw err;
  }

  const config = loadCleanServiceConfig();
  if (!config.enabled || !config.endpoint) {
    const err = new Error('CleanService is not enabled or endpoint is missing');
    err.statusCode = 503;
    throw err;
  }

  const zipObjectName = material.metadata?.zipObjectName || task.metadata?.zipObjectName;
  if (!zipObjectName) {
    const err = new Error('MinerU result zip is required for MinerU-Popo toc-rebuild');
    err.statusCode = 409;
    throw err;
  }

  const parsedBucket = deps.getParsedBucket();
  const cleanBucket = process.env.MINIO_CLEAN_BUCKET || 'eduassets-clean';
  const submittedAt = new Date().toISOString();
  const assetVersion = forceNewVersion ? nextTocRebuildAssetVersion(existingTaskJob, existingMaterialJob) : 'v1';
  const jobId = forceNewVersion
    ? `luceon-${task.id}-${serviceName}-${assetVersion}-${Date.now()}`
    : `luceon-${task.id}-${serviceName}-${assetVersion}`;
  const request = {
    job_id: jobId,
    service_name: serviceName,
    material_id: String(task.materialId),
    parse_task_id: task.id,
    asset_version: assetVersion,
    submitted_at: submittedAt,
    submitted_by: config.submittedBy,
    inputs: [{
      role: 'mineru-result-zip',
      source: {
        type: 'minio',
        bucket: parsedBucket,
        object: zipObjectName,
        endpoint: config.storageEndpoint,
        use_ssl: config.storageUseSsl,
      },
    }],
    sink: {
      type: 'minio',
      bucket: cleanBucket,
      prefix: `${serviceName}/${task.materialId}/${assetVersion}/`,
      endpoint: config.storageEndpoint,
      use_ssl: config.storageUseSsl,
    },
    options: {
      max_cost_cny: config.costPolicy?.hardLimitCny ?? 8,
    },
  };

  return {
    task,
    material,
    deps,
    minio,
    config,
    serviceName,
    parsedBucket,
    cleanBucket,
    zipObjectName,
    existingTaskJob,
    existingMaterialJob,
    forceNewVersion,
    submittedAt,
    assetVersion,
    jobId,
    request,
  };
}

async function executeExternalCleanServiceTocRebuild(context) {
  const {
    task,
    material,
    minio,
    config,
    serviceName,
    parsedBucket,
    cleanBucket,
    zipObjectName,
    forceNewVersion,
    assetVersion,
    jobId,
    request,
  } = context;

  await emitAndLog({
    taskId: task.id,
    event: 'toc-rebuild-cleanservice-started',
    message: '操作者手动触发 MinerU-Popo CleanService 目录重建',
    payload: { materialId: task.materialId, jobId, endpoint: config.endpoint, zipObjectName, parsedBucket, cleanBucket },
  });

  const cleanClient = createCleanServiceClientWithTransport({ config });
  const submitResult = await cleanClient.submitJob(request);
  if (!submitResult?.ok || !submitResult.job) {
    const err = new Error(submitResult?.job?.error?.message || 'CleanService job failed');
    err.statusCode = 502;
    err.cleanState = submitResult?.job?.cleanState;
    err.code = submitResult?.job?.error?.code;
    err.retriable = submitResult?.job?.error?.retriable;
    throw err;
  }

  const artifactReader = {
    async readArtifact(_role, ref) {
      const stream = await minio.getObject(ref.bucket, ref.object);
      const buffer = await streamToBuffer(stream);
      return buffer.toString('utf8');
    },
  };

  const verification = await verifyCleanServiceOutputArtifacts(submitResult.job, {
    expected: {
      serviceName,
      protocolVersion: 'v1',
      materialId: String(task.materialId),
      assetVersion,
      jobId,
    },
    artifactReader,
  });

  if (!verification.ok) {
    const err = new Error(`CleanService output verification failed: ${(verification.errors || []).join(', ')}`);
    err.statusCode = 502;
    throw err;
  }

  const latestTaskBeforeApply = await dbGet(`/tasks/${encodeURIComponent(task.id)}`).catch(() => null);
  if (latestTaskBeforeApply?.state === 'canceled') {
    const err = new Error('Task was canceled before CleanService metadata apply');
    err.statusCode = 409;
    err.code = 'canceled';
    err.cleanState = 'skipped';
    err.retriable = false;
    throw err;
  }

  const candidate = buildVerifiedCleanOutputMetadataCandidate({
    job: submitResult.job,
    verification,
    now: () => new Date().toISOString(),
  });
  const existingTaskForApply = forceNewVersion ? withoutCleanServiceMetadata(task, serviceName) : task;
  const existingMaterialForApply = forceNewVersion ? withoutCleanServiceMetadata(material, serviceName) : material;
  const plan = buildCleanMetadataPersistencePlan({
    candidate,
    existingTask: existingTaskForApply,
    existingMaterial: existingMaterialForApply,
    now: () => new Date().toISOString(),
  });

  const applyResult = await applyCleanMetadataPersistencePlan({
    plan,
    taskId: task.id,
    materialId: String(task.materialId),
    existingTask: existingTaskForApply,
    existingMaterial: existingMaterialForApply,
    allowRealApply: true,
    dbClient: {
      async updateTask(taskId, patch) {
        await dbPatch(`/tasks/${encodeURIComponent(taskId)}`, patch);
        return true;
      },
      async updateMaterial(materialId, patch) {
        await dbPatch(`/materials/${encodeURIComponent(materialId)}`, patch);
        return true;
      },
    },
  });

  if (!applyResult.ok || !applyResult.applied) {
    const err = new Error(applyResult.reason || applyResult.classification || 'CleanService metadata apply failed');
    err.statusCode = 502;
    throw err;
  }

  await emitAndLog({
    taskId: task.id,
    event: 'toc-rebuild-cleanservice-completed',
    message: `MinerU-Popo 目录重建已完成: ${request.sink.prefix}`,
    update: { cleanServiceJobs: { [serviceName]: plan.taskPatch.metadata.cleanServiceJobs[serviceName] } },
    payload: {
      materialId: task.materialId,
      jobId,
      assetVersion,
      prefix: request.sink.prefix,
      engine: submitResult.job.stats?.engine || 'mineru-popo',
      artifactCount: Object.keys(submitResult.job.artifacts || {}).length,
    },
  });

  return {
    ok: true,
    taskId: task.id,
    materialId: String(task.materialId),
    jobId,
    assetVersion,
    prefix: request.sink.prefix,
    engine: submitResult.job.stats?.engine || 'mineru-popo',
    artifacts: plan.taskPatch.metadata.cleanServiceJobs[serviceName].artifacts,
  };
}

async function runExternalCleanServiceTocRebuild(task, deps, options = {}) {
  const context = await prepareExternalCleanServiceTocRebuild(task, deps, options);
  return await executeExternalCleanServiceTocRebuild(context);
}

async function markExternalCleanServiceTocRebuildFailed(context, error) {
  const { task, material, request, submittedAt, serviceName } = context;
  const latestTask = await dbGet(`/tasks/${encodeURIComponent(task.id)}`).catch(() => null) || task;
  const latestMaterial = await dbGet(`/materials/${encodeURIComponent(task.materialId)}`).catch(() => null) || material;
  const currentJob = latestTask.metadata?.cleanServiceJobs?.[serviceName];
  if (currentJob?.jobId && currentJob.jobId !== request.job_id && currentJob.status === 'completed') {
    return null;
  }

  const { taskSummary, materialSummary } = buildFailedCleanServiceSummaries({
    task: latestTask,
    request,
    submittedAt,
    error,
  });
  await persistCleanServiceSummaries({
    task: latestTask,
    material: latestMaterial,
    serviceName,
    taskSummary,
    materialSummary,
  });
  await emitAndLog({
    taskId: task.id,
    event: 'toc-rebuild-cleanservice-failed',
    message: `MinerU-Popo 目录重建失败: ${taskSummary.error?.message || 'unknown error'}`,
    update: { cleanServiceJobs: { [serviceName]: taskSummary } },
    payload: {
      materialId: task.materialId,
      jobId: request.job_id,
      assetVersion: request.asset_version,
      status: taskSummary.status,
      cleanState: taskSummary.cleanState,
      error: taskSummary.error,
    },
  });
  return taskSummary;
}

async function startExternalCleanServiceTocRebuildAsync(task, deps, options = {}) {
  const active = getActiveTocRebuild(task.id);
  if (active) {
    return { ok: true, accepted: true, ...active };
  }

  const context = await prepareExternalCleanServiceTocRebuild(task, deps, options);
  const { serviceName, request, material, submittedAt } = context;
  const { taskSummary, materialSummary } = buildRunningCleanServiceSummaries({ task, request, submittedAt });
  await persistCleanServiceSummaries({ task, material, serviceName, taskSummary, materialSummary });
  await emitAndLog({
    taskId: task.id,
    event: 'toc-rebuild-cleanservice-queued',
    message: `MinerU-Popo 目录重建已提交后台执行: ${request.job_id}`,
    update: { cleanServiceJobs: { [serviceName]: taskSummary } },
    payload: {
      materialId: task.materialId,
      jobId: request.job_id,
      assetVersion: request.asset_version,
      prefix: request.sink?.prefix,
    },
  });

  activeTocRebuildJobs.set(String(task.id), {
    taskId: task.id,
    materialId: String(task.materialId),
    jobId: request.job_id,
    assetVersion: request.asset_version,
    prefix: request.sink?.prefix,
    submittedAt,
  });

  void executeExternalCleanServiceTocRebuild(context)
    .catch((error) => markExternalCleanServiceTocRebuildFailed(context, error).catch((inner) => {
      console.error(`[task-actions] failed to persist async toc-rebuild failure for ${task.id}:`, inner);
    }))
    .finally(() => {
      const activeNow = activeTocRebuildJobs.get(String(task.id));
      if (activeNow?.jobId === request.job_id) activeTocRebuildJobs.delete(String(task.id));
    });

  return {
    ok: true,
    accepted: true,
    status: 'running',
    taskId: task.id,
    materialId: String(task.materialId),
    jobId: request.job_id,
    assetVersion: request.asset_version,
    prefix: request.sink?.prefix,
  };
}

// ─── 路由注册 ────────────────────────────────────────────────

/**
 * 注册任务动作路由
 * @param {Object} app - Express 应用实例
 * @param {Object} deps - 依赖注入对象
 * @param {Function} deps.getMinioClient - 获取 MinIO 客户端实例
 * @param {Function} deps.getMinioBucket - 获取原始资料桶名
 * @param {Function} deps.getStorageBackend - 获取存储后端类型 ('minio' | 'tmpfiles')
 * @param {Function} deps.getParsedBucket - 获取解析产物桶名
 */
export function registerTaskActionRoutes(app, deps = {}) {
  if (!app) throw new Error('registerTaskActionRoutes requires an express app');

  // 构建 deps 默认值（兼容无 MinIO 环境）
  const safeDeps = {
    getMinioClient: deps.getMinioClient || (() => null),
    getMinioBucket: deps.getMinioBucket || (() => 'eduassets'),
    getStorageBackend: deps.getStorageBackend || (() => 'tmpfiles'),
    getParsedBucket: deps.getParsedBucket || (() => 'eduassets-parsed'),
    checkDependencyHealth: deps.checkDependencyHealth,
  };

  async function loadTask(req, res) {
    const task = await dbGet(`/tasks/${encodeURIComponent(req.params.id)}`);
    if (!task) {
      res.status(404).json({ error: `task not found: ${req.params.id}` });
      return null;
    }
    return task;
  }

  /**
   * 统一错误响应：区分资源校验失败（409）和业务逻辑错误（400）
   */
  function handleActionError(res, err) {
    const status = err.statusCode || 400;
    const body = { error: err.message };
    if (err.resourceCheck) {
      body.resourceCheck = err.resourceCheck;
    }
    res.status(status).json(body);
  }

  // batch retry (MUST be before :id routes)
  app.post('/tasks/batch/retry', async (req, res) => {
    try {
      if (safeDeps.checkDependencyHealth) {
        const health = await safeDeps.checkDependencyHealth(undefined, { mineruSubmitProbe: true });
        if (health.blocking) {
          const blockingDep = Object.keys(health.dependencies).find(k =>
            health.dependencies[k].ok === false &&
            health.dependencies[k].requiredFor?.includes('parse') &&
            !health.dependencies[k].skipped
          );
          return res.status(503).json({
            ok: false,
            code: 'DEPENDENCY_UNHEALTHY',
            blockingDependency: blockingDep,
            message: '核心依赖不健康，无法执行批量重试',
            health
          });
        }
      }

      const ids = Array.isArray(req.body?.ids) ? req.body.ids : [];
      if (ids.length === 0) {
        res.status(400).json({ error: '缺少 ids 数组' });
        return;
      }
      const results = [];
      for (const id of ids) {
        try {
          const task = await dbGet(`/tasks/${encodeURIComponent(id)}`);
          if (!task) {
            results.push({ id, ok: false, error: 'not found' });
            continue;
          }
          const newTask = await retryTask(task, safeDeps);
          results.push({ id, ok: true, newTaskId: newTask.id });
        } catch (e) {
          results.push({ id, ok: false, error: e.message, resourceCheck: e.resourceCheck || undefined });
        }
      }
      res.json({ ok: true, results });
    } catch (err) {
      res.status(400).json({ error: err.message });
    }
  });

  // retry
  app.post('/tasks/:id/retry', async (req, res) => {
    try {
      if (safeDeps.checkDependencyHealth) {
        const health = await safeDeps.checkDependencyHealth(undefined, { mineruSubmitProbe: true });
        if (health.blocking) {
          const blockingDep = Object.keys(health.dependencies).find(k =>
            health.dependencies[k].ok === false &&
            health.dependencies[k].requiredFor?.includes('parse') &&
            !health.dependencies[k].skipped
          );
          return res.status(503).json({
            ok: false,
            code: 'DEPENDENCY_UNHEALTHY',
            blockingDependency: blockingDep,
            message: '核心依赖不健康，无法执行重试',
            health
          });
        }
      }

      const task = await loadTask(req, res);
      if (!task) return;
      const newTask = await retryTask(task, safeDeps);
      res.json({ ok: true, taskId: newTask.id, retryOf: task.id });
    } catch (err) {
      handleActionError(res, err);
    }
  });

  // reparse
  app.post('/tasks/:id/reparse', async (req, res) => {
    try {
      if (safeDeps.checkDependencyHealth) {
        const health = await safeDeps.checkDependencyHealth(undefined, { mineruSubmitProbe: true });
        if (health.blocking) {
          const blockingDep = Object.keys(health.dependencies).find(k =>
            health.dependencies[k].ok === false &&
            health.dependencies[k].requiredFor?.includes('parse') &&
            !health.dependencies[k].skipped
          );
          return res.status(503).json({
            ok: false,
            code: 'DEPENDENCY_UNHEALTHY',
            blockingDependency: blockingDep,
            message: '核心依赖不健康，无法重新解析',
            health
          });
        }
      }

      const task = await loadTask(req, res);
      if (!task) return;
      const updated = await reparseTask(task, safeDeps);
      res.json({ ok: true, taskId: updated.id, state: updated.state });
    } catch (err) {
      handleActionError(res, err);
    }
  });

  // re-ai
  app.post('/tasks/:id/re-ai', async (req, res) => {
    try {
      const task = await loadTask(req, res);
      if (!task) return;
      const updated = await reAiTask(task, safeDeps);
      res.json({ ok: true, taskId: updated.id, state: updated.state });
    } catch (err) {
      handleActionError(res, err);
    }
  });

  // cancel
  app.post('/tasks/:id/cancel', async (req, res) => {
    try {
      const task = await loadTask(req, res);
      if (!task) return;
      const { dryRun } = req.body || {};

      if (dryRun) {
        const isCancellable = ['pending', 'running', 'ai-pending', 'ai-running', 'review-pending', 'result-store'].includes(task.state) ||
                              ['mineru-queued', 'mineru-processing', 'submit-failed-retryable', 'result-fetching'].includes(task.stage) ||
                              (task.state === 'failed' && task.stage === 'submit-failed-retryable');

        let materialHasParsedFiles = false;
        if (task.materialId) {
          try {
            const material = await dbGet(`/materials/${encodeURIComponent(task.materialId)}`);
            if (material) {
              const parsedFilesCount = material.metadata?.parsedFilesCount || task.metadata?.parsedFilesCount || 0;
              if (parsedFilesCount > 0) materialHasParsedFiles = true;
            }
          } catch (e) { /* ignore */ }
        }

        return res.json({
          ok: true,
          dryRun: true,
          taskId: task.id,
          summary: {
            cancellable: isCancellable,
            state: task.state,
            stage: task.stage,
            hasMineruTaskId: !!task.metadata?.mineruTaskId,
            willUpdateMaterial: !!task.materialId,
            materialHasParsedFiles,
            externalMineruStateUnknown: true
          }
        });
      }

      const updated = await cancelTask(task);
      res.json({ ok: true, taskId: updated.id, state: updated.state });
    } catch (err) {
      handleActionError(res, err);
    }
  });

  // cancel-all-live
  app.post('/tasks/cancel-all-live', async (req, res) => {
    try {
      const { dryRun } = req.body || {};
      const allTasks = await dbGet('/tasks') || [];
      const liveTasks = allTasks.filter(t => {
        if (['review-pending', 'completed', 'canceled', 'done'].includes(t.state)) return false;
        if ((t.state === 'ai-pending' || t.state === 'review-pending') && (t.metadata?.parsedFilesCount > 0 || t.parsedFilesCount > 0)) return false;

        return ['pending', 'running', 'ai-running'].includes(t.state) ||
               ['mineru-queued', 'mineru-processing', 'result-fetching', 'submit-failed-retryable'].includes(t.stage) ||
               (t.state === 'failed' && t.stage === 'submit-failed-retryable');
      });

      let mineruApiUnreachableCount = 0;
      let mineruTaskIdCount = 0;
      let pendingCount = 0;
      let runningCount = 0;

      for (const t of liveTasks) {
        if (t.state === 'pending' || t.state === 'ai-pending' || t.state === 'review-pending') pendingCount++;
        else runningCount++;
        if (t.metadata?.mineruTaskId) mineruTaskIdCount++;
        if (t.stage === 'mineru-unreachable' || t.metadata?.mineruApiUnreachableCount > 0) mineruApiUnreachableCount++;
      }

      if (dryRun) {
        res.json({
          ok: true,
          summary: {
            totalToCancel: liveTasks.length,
            pendingCount,
            runningCount,
            mineruTaskIdCount,
            mineruApiUnreachableCount
          },
          affectedTaskIds: liveTasks.map(t => t.id)
        });
        return;
      }

      const results = [];
      for (const t of liveTasks) {
        try {
          await cancelTask(t);
          results.push({ id: t.id, ok: true });
        } catch (e) {
          results.push({ id: t.id, ok: false, error: e.message });
        }
      }

      res.json({
        ok: true,
        summary: { totalCanceled: results.filter(r => r.ok).length, totalFailed: results.filter(r => !r.ok).length },
        results
      });
    } catch (err) {
      handleActionError(res, err);
    }
  });

  // reset-test-env
  app.post('/ops/reset-test-env', async (req, res) => {
    try {
      const { dryRun, force } = req.body || {};

      function toCollectionArray(value) {
        if (Array.isArray(value)) return value;
        if (value && typeof value === 'object') return Object.values(value);
        return [];
      }

      const [materialsRaw, tasksRaw, taskEventsRaw, aiJobsRaw, assetDetailsRaw] = await Promise.all([
        dbGet('/materials').catch(() => []),
        dbGet('/tasks').catch(() => []),
        dbGet('/task-events').catch(() => []),
        dbGet('/ai-metadata-jobs').catch(() => []),
        dbGet('/asset-details').catch(() => [])
      ]);

      const materials = toCollectionArray(materialsRaw);
      const tasks = toCollectionArray(tasksRaw);
      const taskEvents = toCollectionArray(taskEventsRaw);
      const aiJobs = toCollectionArray(aiJobsRaw);
      const assetDetails = toCollectionArray(assetDetailsRaw);

      const runningTasks = tasks.filter(t => !t.metadata?.canceledAt && (['running', 'ai-running', 'result-store'].includes(t.state) || ['mineru-processing', 'mineru-queued'].includes(t.stage)));
      const stateDriftCanceledTasks = tasks.filter(t => t.metadata?.canceledAt && t.state !== 'canceled');
      const completedMaterials = materials.filter(m => m.status === 'completed');

      if (!force && runningTasks.length > 0 && !dryRun) {
        return res.status(400).json({ error: '存在运行中的任务，请先勾选 force 以强制清理。' });
      }

      const { scanOrphansInternal, cleanupOrphansInternal } = createOrphanHelpers(deps, dbGet);

      let minioOriginalsCountEstimate = 0;
      let minioParsedCountEstimate = 0;
      const minioOriginalObjects = [];
      const minioParsedObjects = [];

      materials.forEach(m => {
        if (m.metadata?.objectName) {
          minioOriginalsCountEstimate++;
          minioOriginalObjects.push(m.metadata.objectName);
        }
        if (m.metadata?.markdownObjectName || m.metadata?.zipObjectName) {
          minioParsedCountEstimate++;
          if (m.metadata?.markdownObjectName) minioParsedObjects.push(m.metadata.markdownObjectName);
          if (m.metadata?.zipObjectName) minioParsedObjects.push(m.metadata.zipObjectName);
        }
      });
      tasks.forEach(t => {
        if (t.metadata?.markdownObjectName || t.metadata?.zipObjectName) {
          minioParsedCountEstimate++;
          if (t.metadata?.markdownObjectName) minioParsedObjects.push(t.metadata.markdownObjectName);
          if (t.metadata?.zipObjectName) minioParsedObjects.push(t.metadata.zipObjectName);
        }
      });

      let orphanData;
      try {
        orphanData = await scanOrphansInternal();
      } catch (err) {
        return res.status(500).json({
          ok: false,
          error: err.message,
          details: {
            orphanObjects: { ok: false, error: err.message }
          }
        });
      }
      let deletedOrphanObjects = orphanData.totalCount;
      let deletedOrphanObjectBytes = orphanData.totalSize;
      let orphanBuckets = orphanData.orphanBuckets || [];

      if (dryRun) {
        return res.json({
          ok: true,
          dryRun: true,
          summary: {
            deletedMaterials: materials.length,
            deletedTasks: tasks.length,
            deletedTaskEvents: taskEvents.length,
            deletedAiJobs: aiJobs.length,
            deletedAssetDetails: assetDetails.length,
            deletedMinioOriginals: minioOriginalsCountEstimate,
            deletedMinioParsed: minioParsedCountEstimate,
            deletedOrphanObjects,
            deletedOrphanObjectBytes,
            orphanBuckets,
            stateDriftCanceledTasks: stateDriftCanceledTasks.length,
          }
        });
      }

      // EXECUTE
      if (force && runningTasks.length > 0) {
        for (const t of runningTasks) {
          try { await cancelTask(t); } catch (e) { /* ignore */ }
        }
      }

      const deleteCollection = async (collName, items) => {
        const ids = items.map(i => i.id).filter(Boolean);
        if (ids.length === 0) return { ok: true, deleted: 0 };
        try {
          const result = await fetch(`${DB_BASE_URL}/${collName}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids })
          });
          if (!result.ok) {
            return { ok: false, deleted: 0, error: `HTTP ${result.status}` };
          }
          return { ok: true, deleted: ids.length };
        } catch (e) {
          return { ok: false, deleted: 0, error: e.message };
        }
      };

      const [resMat, resTask, resEvent, resAi, resAsset] = await Promise.all([
        deleteCollection('materials', materials),
        deleteCollection('tasks', tasks),
        deleteCollection('task-events', taskEvents),
        deleteCollection('ai-metadata-jobs', aiJobs),
        deleteCollection('asset-details', assetDetails)
      ]);

      const details = {
        materials: resMat,
        tasks: resTask,
        taskEvents: resEvent,
        aiJobs: resAi,
        assetDetails: resAsset
      };

      let hasError = Object.values(details).some(r => !r.ok);

      // Delete MinIO objects
      let minioError = null;
      try {
        const minioClient = deps.getMinioClient ? deps.getMinioClient() : null;
        if (minioClient) {
          const rawBucket = deps.getMinioBucket ? deps.getMinioBucket() : 'eduassets';
          const parsedBucket = deps.getParsedBucket ? deps.getParsedBucket() : 'eduassets-parsed';

          if (minioOriginalObjects.length > 0) {
            await minioClient.removeObjects(rawBucket, minioOriginalObjects).catch(() => null);
          }
          if (minioParsedObjects.length > 0) {
            await minioClient.removeObjects(parsedBucket, minioParsedObjects).catch(() => null);
          }
        }
      } catch (e) {
        minioError = e.message;
        console.warn(`[task-actions] minio reset failed: ${e.message}`);
      }

      let orphanDetails = { ok: true, deleted: 0, bytes: 0 };
      try {
        const orphanRes = await cleanupOrphansInternal();
        orphanDetails = {
           ok: orphanRes.ok,
           deleted: orphanRes.removed,
           bytes: orphanRes.totalSize
        };
        if (!orphanRes.ok) {
           orphanDetails.error = orphanRes.errors?.[0]?.error || 'Orphan cleanup failed';
        }
      } catch (err) {
        orphanDetails = { ok: false, error: err.message };
      }
      details.orphanObjects = orphanDetails;
      if (!orphanDetails.ok) hasError = true;

      if (!orphanDetails.ok) {
        return res.status(500).json({
          ok: false,
          error: orphanDetails.error,
          details
        });
      }

      return res.json({
        ok: !hasError,
        dryRun: false,
        summary: {
          deletedMaterials: materials.length,
          deletedTasks: tasks.length,
          deletedTaskEvents: taskEvents.length,
          deletedAiJobs: aiJobs.length,
          deletedAssetDetails: assetDetails.length,
          deletedMinioOriginals: minioOriginalsCountEstimate,
          deletedMinioParsed: minioParsedCountEstimate,
          deletedOrphanObjects: orphanDetails.deleted,
          deletedOrphanObjectBytes: orphanDetails.bytes,
          orphanBuckets,
          stateDriftCanceledTasks: stateDriftCanceledTasks.length,
        },
        details
      });
    } catch (err) {
      handleActionError(res, err);
    }
  });

  // review
  app.post('/tasks/:id/review', async (req, res) => {
    try {
      const task = await loadTask(req, res);
      if (!task) return;
      const updated = await reviewTask(task, req.body || {});
      res.json({ ok: true, taskId: updated.id, state: updated.state });
    } catch (err) {
      handleActionError(res, err);
    }
  });

  app.get('/tasks/:id/toc-rebuild', async (req, res) => {
    try {
      const task = await loadTask(req, res);
      if (!task) return;
      const serviceName = 'toc-rebuild';
      const active = getActiveTocRebuild(task.id);
      res.json({
        ok: true,
        taskId: task.id,
        active,
        job: task.metadata?.cleanServiceJobs?.[serviceName] || null,
      });
    } catch (err) {
      handleActionError(res, err);
    }
  });

  app.post('/tasks/:id/toc-rebuild', async (req, res) => {
    try {
      const task = await loadTask(req, res);
      if (!task) return;
      const config = loadCleanServiceConfig();
      const forceCleanService = req.body?.mode === 'cleanservice-rerun' || req.body?.cleanservice === true;
      const forceNewVersion = req.body?.forceNewVersion === true || forceCleanService;
      if (forceCleanService && (!config.enabled || !config.endpoint)) {
        const err = new Error('MinerU-Popo CleanService 未启用，无法执行 Popo 重新目录重建');
        err.statusCode = 503;
        throw err;
      }
      const result = config.enabled
        ? await startExternalCleanServiceTocRebuildAsync(task, safeDeps, { forceNewVersion })
        : await runManualTocRebuild(task, safeDeps);
      res.status(config.enabled ? 202 : 200).json(result);
    } catch (err) {
      handleActionError(res, err);
    }
  });


  // SSE：/tasks/stream
  app.get('/tasks/stream', (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream; charset=utf-8');
    res.setHeader('Cache-Control', 'no-cache, no-transform');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Accel-Buffering', 'no'); // 禁用 Nginx 缓冲
    res.flushHeaders?.();

    const taskIdFilter = typeof req.query?.taskId === 'string' ? req.query.taskId : null;

    // 连接建立即发一条 hello，便于前端确认通道可用
    res.write(`event: hello\n`);
    res.write(`data: ${JSON.stringify({ at: new Date().toISOString(), filter: taskIdFilter || null })}\n\n`);

    const onUpdate = (payload) => {
      if (taskIdFilter && payload.taskId !== taskIdFilter) return;
      try {
        res.write(`event: task-update\n`);
        res.write(`data: ${JSON.stringify(payload)}\n\n`);
      } catch (e) {
        // 忽略写失败，close 会清理
      }
    };
    taskEventBus.on('task-update', onUpdate);

    // 保活心跳（每 25s），避免 Nginx/中间件断流
    const heartbeat = setInterval(() => {
      try {
        res.write(`: ping ${Date.now()}\n\n`);
      } catch (e) {
        /* noop */
      }
    }, 25_000);

    req.on('close', () => {
      clearInterval(heartbeat);
      taskEventBus.removeListener('task-update', onUpdate);
    });
  });

  console.log('[upload-server] task-actions & SSE routes registered');
}
