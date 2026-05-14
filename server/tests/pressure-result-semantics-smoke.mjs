import assert from 'node:assert/strict';
import { classifyPressureRunOutcome } from '../lib/pressure-result-semantics.mjs';

const successful = Array.from({ length: 20 }, (_, index) => ({
  id: `task-ok-${index + 1}`,
  state: index % 2 === 0 ? 'review-pending' : 'completed',
  stage: index % 2 === 0 ? 'review' : 'done'
}));

const retryableAiResiduals = Array.from({ length: 3 }, (_, index) => ({
  id: `task-ai-failed-${index + 1}`,
  state: 'failed',
  stage: 'ai',
  metadata: {
    aiStatus: 'failed',
    aiFailureClassification: {
      kind: 'timeout',
      manualRetryEligible: true
    }
  }
}));

const activeMineru = {
  id: 'task-mineru-active',
  state: 'running',
  stage: 'mineru-processing',
  metadata: {
    mineruRuntimeProgressTruth: {
      directMineruStatus: 'processing',
      rawLogAdvancing: true,
      terminalFailure: false
    }
  }
};

const result = classifyPressureRunOutcome([
  ...successful,
  ...retryableAiResiduals,
  activeMineru
]);

assert.equal(result.systemicFailure, false);
assert.equal(result.partialSuccess, true);
assert.equal(result.outcome, 'partial-success-with-retryable-ai-residuals');
assert.equal(result.counts.successLike, 20);
assert.equal(result.counts.retryableAiResidual, 3);
assert.equal(result.counts.systemicFailureSignal, 0);

const systemic = classifyPressureRunOutcome([
  { id: 'task-bad-1', state: 'failed', stage: 'mineru-processing', metadata: { mineruRuntimeProgressTruth: { terminalFailure: true } } },
  { id: 'task-bad-2', state: 'failed', stage: 'submit-failed' }
]);

assert.equal(systemic.systemicFailure, true);
assert.equal(systemic.outcome, 'systemic-failure');

console.log('[pressure-result-semantics-smoke] ok');
