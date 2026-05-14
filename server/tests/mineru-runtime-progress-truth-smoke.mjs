import assert from 'node:assert/strict';
import { deriveMineruRuntimeProgressTruth } from '../lib/ops-mineru-log-parser.mjs';

const previousObservation = {
  activityLevel: 'log-observation-stale',
  stage: {
    rawPhase: 'Table-ocr det',
    current: 65,
    total: 66
  },
  observationStale: true
};

const currentObservation = {
  activityLevel: 'active-progress',
  stage: {
    rawPhase: 'Table-ocr det',
    current: 66,
    total: 66
  },
  observationStale: false
};

const truth = deriveMineruRuntimeProgressTruth({
  task: {
    state: 'failed',
    stage: 'mineru-processing',
    metadata: {
      mineruStatus: 'processing',
      localTimeoutOccurred: true
    }
  },
  observation: currentObservation,
  previousObservation
});

assert.equal(truth.directMineruStatus, 'processing');
assert.equal(truth.rawLogAdvancing, true);
assert.equal(truth.localTimeoutOccurred, true);
assert.equal(truth.terminalFailure, false);
assert.equal(truth.operatorState, 'local-timeout-remote-processing-raw-log-advancing');
assert.match(truth.message, /仍在推进/);

const staleTruth = deriveMineruRuntimeProgressTruth({
  task: {
    state: 'failed',
    metadata: {
      mineruStatus: 'processing',
      localTimeoutOccurred: true
    }
  },
  observation: previousObservation
});

assert.equal(staleTruth.terminalFailure, false);
assert.equal(staleTruth.operatorState, 'local-timeout-remote-processing-observation-stale');
assert.match(staleTruth.message, /不能按终态失败处理/);

console.log('[mineru-runtime-progress-truth-smoke] ok');
