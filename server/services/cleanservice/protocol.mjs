import { loadCleanServiceConfig } from './config.mjs';
import { evaluateCleanCostPolicy, CLEAN_STAGE_STATES } from './states.mjs';
import { verifyCleanServiceOutput } from './output-verifier.mjs';
import { buildCleanMetadataPatch } from './metadata-summary.mjs';

function normalizeError(error, fallbackCode = 'protocol_error') {
  if (!error) return null;
  if (typeof error === 'string') {
    return { code: fallbackCode, message: error, retriable: false };
  }
  return {
    code: error.code || fallbackCode,
    message: error.message || JSON.stringify(error),
    retriable: error.retriable === true,
  };
}

function mapProtocolStatus(status) {
  if (status === 'queued') return CLEAN_STAGE_STATES.PENDING;
  if (status === 'processing') return CLEAN_STAGE_STATES.RUNNING;
  if (status === 'canceled') return CLEAN_STAGE_STATES.SKIPPED;
  if (status === 'failed') return CLEAN_STAGE_STATES.PROTOCOL_FAILURE;
  return null;
}

export function normalizeCleanServiceJob(response = {}, options = {}) {
  const serviceName = response.service_name || response.serviceName || options.serviceName || 'toc-rebuild';
  const protocolVersion = response.protocol_version || response.protocolVersion || options.protocolVersion || 'v1';
  const costDecision = evaluateCleanCostPolicy(response.stats || {}, options.costPolicy || {});
  const protocolMappedState = mapProtocolStatus(response.status);

  let verification = null;
  let cleanState = costDecision.cleanState || protocolMappedState || CLEAN_STAGE_STATES.PROTOCOL_FAILURE;
  if (!costDecision.cleanState && response.status === 'completed') {
    verification = verifyCleanServiceOutput(response, { serviceName, protocolVersion });
    cleanState = verification.cleanState;
  }

  const job = {
    ...response,
    service_name: serviceName,
    protocol_version: protocolVersion,
    cleanState,
    error: normalizeError(response.error, cleanState === CLEAN_STAGE_STATES.TIMEOUT ? 'timeout' : 'protocol_error'),
  };

  return {
    ok: cleanState === CLEAN_STAGE_STATES.COMPLETED || cleanState === CLEAN_STAGE_STATES.REVIEW_PENDING_PARTIAL,
    job,
    verification,
    metadataPatch: buildCleanMetadataPatch(job, verification || {}),
    costDecision,
  };
}

export function normalizeCleanServiceTransportError(error) {
  const message = error?.message || String(error || 'CleanService transport failed');
  const timeout = error?.name === 'AbortError' || /timeout/i.test(message);
  const cleanState = timeout ? CLEAN_STAGE_STATES.TIMEOUT : CLEAN_STAGE_STATES.PROTOCOL_FAILURE;
  const job = {
    service_name: 'toc-rebuild',
    protocol_version: 'v1',
    status: 'failed',
    cleanState,
    error: {
      code: timeout ? 'timeout' : 'transport_error',
      message,
      retriable: timeout || error?.retriable === true,
    },
  };
  return {
    ok: false,
    job,
    verification: null,
    metadataPatch: buildCleanMetadataPatch(job),
    costDecision: null,
  };
}

export function createCleanServiceClient({ config = loadCleanServiceConfig(), transport = null } = {}) {
  async function call(action, payload) {
    if (!config.enabled) {
      const job = {
        service_name: config.serviceName,
        protocol_version: config.protocolVersion,
        status: 'not-enabled',
        cleanState: CLEAN_STAGE_STATES.NOT_ENABLED,
        error: null,
      };
      return {
        ok: false,
        job,
        verification: null,
        metadataPatch: buildCleanMetadataPatch(job),
        costDecision: null,
      };
    }

    if (typeof transport !== 'function') {
      return normalizeCleanServiceTransportError(new Error('CleanService transport is not configured'));
    }

    try {
      const response = await transport({ action, payload, config });
      return normalizeCleanServiceJob(response, {
        serviceName: config.serviceName,
        protocolVersion: config.protocolVersion,
        costPolicy: config.costPolicy,
      });
    } catch (error) {
      return normalizeCleanServiceTransportError(error);
    }
  }

  return {
    config,
    submitJob: (request) => call('submitJob', request),
    queryJob: (jobId) => call('queryJob', { jobId }),
  };
}
