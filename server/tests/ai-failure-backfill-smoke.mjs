import assert from 'node:assert/strict';
import {
  buildAiFailureBackfillMetadata,
  buildAiFailureTaskMessage,
  extractAiFailureClassification
} from '../lib/ai-failure-backfill.mjs';

const classification = {
  kind: 'timeout',
  aiPhase: 'provider-call',
  timeoutKind: 'transport-timeout',
  durationMs: 120_500,
  timeoutMs: 120_000,
  providerId: 'ollama',
  model: 'qwen3.5:9b',
  baseUrl: 'http://ollama:11434',
  manualRetryEligible: true,
  manualRetryEligibilityStatus: 'eligible-manual-only',
  manualRetryEligibilityReason: 'Provider timeout after MinerU parse succeeded'
};

const update = {
  state: 'failed',
  metadata: {
    aiFailureClassification: classification
  }
};

const backfill = buildAiFailureBackfillMetadata({
  update,
  job: { id: 'ai-job-1' },
  analyzedAt: '2026-05-15T00:00:00.000Z'
});

assert.equal(extractAiFailureClassification(update), classification);
assert.equal(backfill.aiFailureClassification, classification);
assert.equal(backfill.aiFailureKind, 'timeout');
assert.equal(backfill.aiFailurePhase, 'provider-call');
assert.equal(backfill.aiFailureTimeoutKind, 'transport-timeout');
assert.equal(backfill.aiFailureProviderId, 'ollama');
assert.equal(backfill.aiFailureModel, 'qwen3.5:9b');
assert.equal(backfill.aiAutoRetryAllowed, false);
assert.equal(backfill.aiManualRetryEligible, true);
assert.equal(backfill.aiManualRetryEligibilityStatus, 'eligible-manual-only');
assert.equal(backfill.aiFailureRecordedAt, '2026-05-15T00:00:00.000Z');
assert.equal(backfill.aiJobId, 'ai-job-1');
assert.match(buildAiFailureTaskMessage(update), /手动重试/);

console.log('[ai-failure-backfill-smoke] ok');
