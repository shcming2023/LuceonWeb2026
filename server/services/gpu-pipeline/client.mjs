/**
 * Remote GPU MinerU/MinerU-Popo Pipeline Client.
 *
 * Contract:
 *   POST /api/v1/tasks              multipart file submit
 *   GET  /api/v1/tasks/<task_id>    status
 *   GET  /api/v1/tasks/<task_id>/outputs
 *   GET  /api/v1/tasks/<task_id>/logs
 *
 * This client is server-side only. Tokens must come from environment or a
 * secret manager, never from frontend settings or Git-tracked files.
 */

import { loadRemoteGpuPipelineConfig } from './config.mjs';

export class RemoteGpuPipelineError extends Error {
  constructor(message, options = {}) {
    super(message);
    this.name = 'RemoteGpuPipelineError';
    this.code = options.code || 'remote_gpu_pipeline_error';
    this.status = options.status ?? null;
    this.endpoint = options.endpoint || '';
    this.retriable = options.retriable === true;
    this.dependencyBlocking = options.dependencyBlocking === true;
  }
}

export function createRemoteGpuPipelineClient({
  config = loadRemoteGpuPipelineConfig(),
  fetchImpl = globalThis.fetch,
} = {}) {
  if (!config?.baseUrl) {
    throw new RemoteGpuPipelineError('REMOTE_GPU_PIPELINE_BASE_URL is required', {
      code: 'remote_gpu_missing_base_url',
      dependencyBlocking: true,
    });
  }
  if (!config?.token) {
    throw new RemoteGpuPipelineError('REMOTE_GPU_PIPELINE_TOKEN is required', {
      code: 'remote_gpu_missing_token',
      dependencyBlocking: true,
    });
  }
  if (typeof fetchImpl !== 'function') {
    throw new RemoteGpuPipelineError('fetch implementation is required', {
      code: 'remote_gpu_missing_fetch',
      dependencyBlocking: true,
    });
  }

  const baseUrl = config.baseUrl.replace(/\/+$/, '');

  async function submitTask({
    luceonTaskId,
    materialId,
    fileName,
    mimeType,
    fileStream,
    options = {},
  }) {
    const boundary = `----luceon-remote-gpu-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const fields = [
      ['pipeline', options.pipeline || config.pipeline || 'mineru_popo'],
      ['luceon_task_id', luceonTaskId || ''],
      ['material_id', materialId || ''],
      ['keep_intermediate', String(options.keepIntermediate ?? config.keepIntermediate ?? false)],
      ['backend', options.backend || 'pipeline'],
      ['parse_method', options.parseMethod || options.parse_method || 'auto'],
      ['formula_enable', enabledFlag(options.enableFormula) ? '1' : '0'],
      ['table_enable', enabledFlag(options.enableTable) ? '1' : '0'],
      ['lang_list', options.ocrLanguage || options.language || 'ch'],
      ['return_md', 'true'],
      ['return_middle_json', 'true'],
      ['return_content_list', 'true'],
      ['return_images', 'true'],
      ['return_original_file', 'true'],
    ];
    if (Number.isFinite(Number(options.maxPages)) && Number(options.maxPages) > 0) {
      fields.push(['max_pages', String(Math.floor(Number(options.maxPages)))]);
    }

    const multipart = createMultipartStream({
      boundary,
      fields,
      fileFieldName: 'file',
      fileName,
      mimeType: mimeType || 'application/octet-stream',
      fileStream,
    });

    const payload = await requestJson(`${baseUrl}/api/v1/tasks`, {
      method: 'POST',
      headers: { 'content-type': multipart.contentType },
      body: multipart.body,
      timeoutMs: Math.max(config.timeoutMs, 120_000),
      fetchImpl,
      token: config.token,
    });
    return normalizeTask(payload);
  }

  async function queryTask(taskId) {
    const payload = await requestJson(`${baseUrl}/api/v1/tasks/${encodeURIComponent(taskId)}`, {
      method: 'GET',
      timeoutMs: config.timeoutMs,
      fetchImpl,
      token: config.token,
    });
    return normalizeTask(payload);
  }

  async function getOutputs(taskId) {
    return await requestJson(`${baseUrl}/api/v1/tasks/${encodeURIComponent(taskId)}/outputs`, {
      method: 'GET',
      timeoutMs: config.timeoutMs,
      fetchImpl,
      token: config.token,
    });
  }

  async function getLogs(taskId) {
    return await requestJson(`${baseUrl}/api/v1/tasks/${encodeURIComponent(taskId)}/logs`, {
      method: 'GET',
      timeoutMs: config.timeoutMs,
      fetchImpl,
      token: config.token,
    });
  }

  async function download(url, timeoutMs = config.timeoutMs) {
    return await requestBuffer(url, { timeoutMs, fetchImpl, token: config.token });
  }

  return {
    config,
    submitTask,
    queryTask,
    getOutputs,
    getLogs,
    download,
  };
}

export function normalizeTask(payload = {}) {
  const task = payload.task || payload.data || payload;
  const status = String(task.status || task.state || '').toLowerCase();
  const taskId = task.task_id || task.taskId || task.id;
  return {
    ...task,
    task_id: taskId,
    status,
    outputs: task.outputs || payload.outputs || null,
    metrics: task.metrics || payload.metrics || null,
    error: task.error || payload.error || null,
  };
}

export function isRemoteGpuTerminalStatus(status) {
  const value = String(status || '').toLowerCase();
  return ['succeeded', 'success', 'completed', 'done', 'failed', 'error', 'cancelled', 'canceled'].includes(value);
}

export function isRemoteGpuSuccessStatus(status) {
  return ['succeeded', 'success', 'completed', 'done'].includes(String(status || '').toLowerCase());
}

export function isRemoteGpuFailureStatus(status) {
  return ['failed', 'error', 'cancelled', 'canceled'].includes(String(status || '').toLowerCase());
}

async function requestJson(url, { method, headers = {}, body, timeoutMs, fetchImpl, token }) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(url, {
      method,
      headers: authHeaders(headers, token),
      body,
      duplex: body ? 'half' : undefined,
      signal: controller.signal,
    }).catch((error) => {
      throw new RemoteGpuPipelineError(`remote GPU pipeline request failed: ${error.message}`, {
        code: 'remote_gpu_transport_error',
        endpoint: url,
        dependencyBlocking: true,
        retriable: true,
      });
    });
    const text = await response.text();
    if (!response.ok) {
      throw new RemoteGpuPipelineError(`remote GPU pipeline HTTP ${response.status}: ${text.slice(0, 500)}`, {
        code: 'remote_gpu_http_error',
        status: response.status,
        endpoint: url,
        dependencyBlocking: response.status >= 500,
        retriable: response.status >= 500,
      });
    }
    try {
      return text ? JSON.parse(text) : {};
    } catch {
      throw new RemoteGpuPipelineError(`remote GPU pipeline returned non-JSON: ${text.slice(0, 200)}`, {
        code: 'remote_gpu_parse_error',
        endpoint: url,
      });
    }
  } finally {
    clearTimeout(timer);
  }
}

async function requestBuffer(url, { timeoutMs, fetchImpl, token }) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(url, {
      method: 'GET',
      headers: authHeaders({}, token),
      signal: controller.signal,
    });
    if (!response.ok) {
      const text = await response.text().catch(() => '');
      throw new RemoteGpuPipelineError(`remote GPU pipeline download HTTP ${response.status}: ${text.slice(0, 300)}`, {
        code: 'remote_gpu_download_error',
        status: response.status,
        endpoint: url,
        retriable: response.status >= 500,
      });
    }
    return Buffer.from(await response.arrayBuffer());
  } finally {
    clearTimeout(timer);
  }
}

function authHeaders(headers, token) {
  return {
    ...headers,
    Accept: headers.Accept || headers.accept || 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

function enabledFlag(value) {
  return value === true || value === 'true' || value === '1' || value === 1 || value === 'yes' || value === 'on';
}

function createMultipartStream({ boundary, fields, fileFieldName, fileName, mimeType, fileStream }) {
  const enc = new TextEncoder();
  const safeName = String(fileName || 'upload.bin').replace(/"/g, '_');
  const fileHeader = `--${boundary}\r\nContent-Disposition: form-data; name="${fileFieldName}"; filename="${safeName}"\r\nContent-Type: ${mimeType}\r\n\r\n`;
  const fileFooter = `\r\n--${boundary}--\r\n`;
  const fieldChunk = (name, value) => enc.encode(`--${boundary}\r\nContent-Disposition: form-data; name="${name}"\r\n\r\n${String(value ?? '')}\r\n`);

  async function* gen() {
    for (const [key, value] of fields || []) yield fieldChunk(key, value);
    yield enc.encode(fileHeader);
    for await (const chunk of fileStream) yield chunk;
    yield enc.encode(fileFooter);
  }
  return { contentType: `multipart/form-data; boundary=${boundary}`, body: gen() };
}
