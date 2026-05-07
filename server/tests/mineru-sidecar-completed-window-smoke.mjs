import assert from 'node:assert';

process.env.UPLOAD_PORT = '0';
process.env.DISABLE_WORKERS = 'true';

const { selectMineruObservationAttribution } = await import('../upload-server.mjs');

const startedAt = '2026-05-07T02:00:00.000Z';
const completedAt = '2026-05-07T02:00:30.000Z';
const nowInsideGrace = Date.parse('2026-05-07T02:02:00.000Z');

function makeTask(overrides = {}) {
  const metadataOverrides = overrides.metadata || {};
  const { metadata: _metadata, ...rest } = overrides;
  return {
    id: overrides.id || 'task-a',
    engine: 'local-mineru',
    state: 'completed',
    stage: 'review',
    metadata: {
      mineruTaskId: overrides.mineruTaskId || 'mineru-a',
      mineruStartedAt: overrides.mineruStartedAt || startedAt,
      mineruLastStatusAt: overrides.mineruLastStatusAt || completedAt,
      ...metadataOverrides,
    },
    parsedAt: overrides.parsedAt || completedAt,
    ...rest,
  };
}

function makeSnapshot(observedAt = '2026-05-07T02:00:15.000Z') {
  return {
    contextTime: observedAt,
    progress: 100,
    line: 'mineru completed',
  };
}

function assertNoTask(result, reasonPattern) {
  assert.equal(result.task, null);
  assert.equal(result.mode, 'unattributed');
  assert.match(result.reason, reasonPattern);
}

async function main() {
  console.log('--- MinerU Sidecar Completed-Window Attribution Smoke Test Start ---');

  const live = makeTask({
    id: 'live-task',
    state: 'running',
    stage: 'mineru-processing',
    parsedAt: null,
    metadata: {
      mineruTaskId: 'mineru-live',
      mineruStartedAt: startedAt,
    },
  });
  const liveResult = selectMineruObservationAttribution([live], makeSnapshot(), nowInsideGrace);
  assert.equal(liveResult.task.id, 'live-task');
  assert.equal(liveResult.mode, 'live-active');
  console.log('Case 1 Pass: exactly one live active task remains preferred');

  const completedResult = selectMineruObservationAttribution([makeTask()], makeSnapshot(), nowInsideGrace);
  assert.equal(completedResult.task.id, 'task-a');
  assert.equal(completedResult.mode, 'completed-window-backfill');
  console.log('Case 2 Pass: exactly one recently completed task can receive backfill');

  const multipleResult = selectMineruObservationAttribution([
    makeTask({ id: 'task-a' }),
    makeTask({ id: 'task-b', mineruTaskId: 'mineru-b' }),
  ], makeSnapshot(), nowInsideGrace);
  assertNoTask(multipleResult, /multiple completed-window/);
  console.log('Case 3 Pass: multiple completed candidates remain unattributed');

  const beforeStartResult = selectMineruObservationAttribution(
    [makeTask()],
    makeSnapshot('2026-05-07T01:59:59.000Z'),
    nowInsideGrace
  );
  assertNoTask(beforeStartResult, /no matching completed-window/);
  console.log('Case 4 Pass: observations before task start remain unattributed');

  const afterGraceResult = selectMineruObservationAttribution(
    [makeTask()],
    makeSnapshot('2026-05-07T02:06:00.001Z'),
    nowInsideGrace
  );
  assertNoTask(afterGraceResult, /no matching completed-window/);
  console.log('Case 5 Pass: observations after grace window remain unattributed');

  const oldCompletedResult = selectMineruObservationAttribution(
    [makeTask()],
    makeSnapshot(),
    Date.parse('2026-05-07T02:06:00.001Z')
  );
  assertNoTask(oldCompletedResult, /no matching completed-window/);
  console.log('Case 6 Pass: old completed tasks are not considered indefinitely');

  const canceledResult = selectMineruObservationAttribution(
    [makeTask({ state: 'canceled', metadata: { canceledAt: '2026-05-07T02:00:20.000Z' } })],
    makeSnapshot(),
    nowInsideGrace
  );
  assertNoTask(canceledResult, /no matching completed-window/);
  console.log('Case 7 Pass: canceled tasks are excluded');

  console.log('--- MinerU Sidecar Completed-Window Attribution Smoke Test Passed ---');
  process.exit(0);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
