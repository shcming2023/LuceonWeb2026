export const CLEAN_SERVICE_PROTOCOL_VERSION = 'v1';
export const DEFAULT_CLEAN_SERVICE_NAME = 'toc-rebuild';
export const CLEAN_SERVICE_SOFT_COST_CNY = 5;
export const CLEAN_SERVICE_HARD_COST_CNY = 8;
export const CLEAN_SERVICE_DEFAULT_TIMEOUT_MS = 30_000;

function isTruthy(value) {
  return value === true || value === 'true' || value === '1' || value === 'yes' || value === 'on';
}

function finiteNumberOr(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function loadCleanServiceConfig(env = process.env) {
  const enabled = isTruthy(env.CLEANSERVICE_ENABLED);
  const serviceName = env.CLEANSERVICE_SERVICE_NAME || DEFAULT_CLEAN_SERVICE_NAME;
  const endpoint = env.CLEANSERVICE_ENDPOINT || null;
  const apiKey = env.CLEANSERVICE_API_KEY || null;
  const callbackSecretRef = env.CLEANSERVICE_CALLBACK_SECRET_REF || 'TOC_REBUILD_CALLBACK_SECRET';
  const softCostLimitCny = finiteNumberOr(env.CLEANSERVICE_SOFT_COST_LIMIT_CNY, CLEAN_SERVICE_SOFT_COST_CNY);
  const hardCostLimitCny = finiteNumberOr(env.CLEANSERVICE_HARD_COST_LIMIT_CNY, CLEAN_SERVICE_HARD_COST_CNY);
  const timeoutMs = finiteNumberOr(env.CLEANSERVICE_TIMEOUT_MS, CLEAN_SERVICE_DEFAULT_TIMEOUT_MS);

  return {
    version: 'cleanservice-config.v0.1',
    enabled,
    status: enabled ? 'enabled' : 'not-enabled',
    serviceName,
    protocolVersion: CLEAN_SERVICE_PROTOCOL_VERSION,
    endpoint,
    hasApiKey: Boolean(apiKey),
    apiKey,
    callbackSecretRef,
    timeoutMs,
    costPolicy: {
      currency: 'CNY',
      softLimitCny: softCostLimitCny,
      hardLimitCny: hardCostLimitCny,
    },
  };
}

export function summarizeCleanServiceAvailability(config = loadCleanServiceConfig()) {
  if (!config.enabled) {
    return {
      enabled: false,
      cleanState: 'not-enabled',
      productLabel: '未启用',
      reason: 'cleanservice-disabled-by-default',
      blockingCurrentPhase1: false,
    };
  }

  const missing = [];
  if (!config.endpoint) missing.push('endpoint');
  if (!config.hasApiKey) missing.push('apiKey');

  return {
    enabled: true,
    cleanState: missing.length > 0 ? 'protocol-failure' : 'pending',
    productLabel: missing.length > 0 ? '目录重建失败' : '等待目录重建',
    reason: missing.length > 0 ? `missing-${missing.join('-')}` : null,
    blockingCurrentPhase1: false,
  };
}
