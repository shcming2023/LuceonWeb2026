import assert from 'node:assert';

process.env.UPLOAD_PORT = '0';
process.env.DISABLE_WORKERS = 'true';

const {
  isTerminalMineruObservationTask,
  shouldMutateMineruObservation,
  normalizeTerminalMineruObservationSnapshot,
} = await import('../upload-server.mjs');

function makeTask(overrides = {}) {
  return {
    id: 'task-terminal',
    state: 'review-pending',
    stage: 'review',
    engine: 'local-mineru',
    metadata: {
      mineruObservedProgress: {
        activityLevel: 'active-progress',
        attribution: 'task-terminal',
        attributionMode: 'live-active',
      },
    },
    ...overrides,
  };
}

async function main() {
  console.log('--- MinerU Completed Observation Semantics Smoke Test Start ---');

  const terminalTask = makeTask();
  assert.equal(isTerminalMineruObservationTask(terminalTask), true);
  assert.deepEqual(
    shouldMutateMineruObservation(terminalTask, 'completed-window-backfill'),
    {
      mutate: false,
      reason: 'terminal task already has mineru observation; completed-window observation kept global-only',
    }
  );
  console.log('Case 1 Pass: terminal task with existing observation rejects completed-window mutation');

  const terminalWithoutObservation = makeTask({ metadata: {} });
  assert.equal(shouldMutateMineruObservation(terminalWithoutObservation, 'completed-window-backfill').mutate, true);
  console.log('Case 2 Pass: terminal task without existing observation can receive first diagnostic backfill');

  const runningTask = makeTask({ state: 'running', stage: 'mineru-processing' });
  assert.equal(isTerminalMineruObservationTask(runningTask), false);
  assert.equal(shouldMutateMineruObservation(runningTask, 'live-active').mutate, true);
  console.log('Case 3 Pass: live task observation remains mutable');

  const normalized = normalizeTerminalMineruObservationSnapshot(terminalTask, {
    activityLevel: 'log-observation-stale',
    observationStaleReason: 'host-filesystem MinerU log file is stale while MinerU API is still processing',
    logFreshnessDiagnostic: {
      logSourceContext: 'host-filesystem',
      suggestion: 'old suggestion',
    },
    mountDiagnostic: {
      logSourceContext: 'host-filesystem',
      suggestion: 'old suggestion',
    },
  });
  assert.equal(
    normalized.observationStaleReason,
    'completed local-MinerU task has no newer host log activity; final task observation is diagnostic only'
  );
  assert.equal(normalized.terminalTaskState, 'review-pending');
  assert.match(normalized.logFreshnessDiagnostic.suggestion, /terminal task/);
  assert.match(normalized.mountDiagnostic.suggestion, /terminal task/);
  console.log('Case 4 Pass: completed-task stale wording does not imply active MinerU processing');

  console.log('--- MinerU Completed Observation Semantics Smoke Test Passed ---');
  process.exit(0);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
