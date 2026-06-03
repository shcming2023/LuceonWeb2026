const DEFAULT_TIMEOUT_MS = 30_000;
const DEFAULT_POLL_INTERVAL_MS = 10_000;

function isTruthy(value) {
  return value === true || value === 'true' || value === '1' || value === 'yes' || value === 'on';
}

function finiteNumberOr(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export function loadRemoteGpuPipelineConfig(env = process.env) {
  const backend = String(env.MINERU_BACKEND || env.MINERU_MODE || '').trim().toLowerCase();
  const popoBackend = String(env.POPO_FULL_BACKGROUND_BACKEND || '').trim().toLowerCase();
  const enabled = isTruthy(env.REMOTE_GPU_PIPELINE_ENABLED)
    || backend === 'remote-gpu'
    || popoBackend === 'remote-gpu';

  const baseUrl = String(env.REMOTE_GPU_PIPELINE_BASE_URL || '').trim().replace(/\/+$/, '');
  const token = env.REMOTE_GPU_PIPELINE_TOKEN || '';

  return {
    version: 'remote-gpu-pipeline-config.v1',
    enabled,
    backend,
    popoBackend,
    baseUrl,
    hasToken: Boolean(token),
    token,
    timeoutMs: finiteNumberOr(env.REMOTE_GPU_PIPELINE_TIMEOUT_MS, DEFAULT_TIMEOUT_MS),
    pollIntervalMs: finiteNumberOr(env.REMOTE_GPU_PIPELINE_POLL_INTERVAL_MS, DEFAULT_POLL_INTERVAL_MS),
    pipeline: env.REMOTE_GPU_PIPELINE_NAME || 'mineru_popo',
    keepIntermediate: isTruthy(env.REMOTE_GPU_PIPELINE_KEEP_INTERMEDIATE),
  };
}

export function sanitizeRemoteGpuPipelineConfig(config = loadRemoteGpuPipelineConfig()) {
  return {
    ...config,
    token: undefined,
    hasToken: Boolean(config.hasToken),
  };
}
