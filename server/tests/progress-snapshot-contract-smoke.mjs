import assert from 'node:assert/strict';
import { buildProgressSnapshot } from '../lib/progress-snapshot.mjs';

async function main() {
  console.log('=== Progress Snapshot Contract Smoke ===');

  const directCompletedWhileDbRunning = buildProgressSnapshot(
    {
      id: 'task-db-running-direct-complete',
      state: 'running',
      stage: 'mineru-processing',
      metadata: { mineruTaskId: 'mineru-direct-complete', mineruStatus: 'processing' },
    },
    { directMineruStatus: 'completed', observedAt: '2026-05-16T06:30:00.000Z' },
  );
  assert.equal(directCompletedWhileDbRunning.phase, 'parse');
  assert.equal(directCompletedWhileDbRunning.sourcePriority, 'direct-mineru');
  assert.equal(directCompletedWhileDbRunning.lagKind, 'db-behind-direct-mineru');
  assert.match(directCompletedWhileDbRunning.operatorMessage, /正在同步解析结果/);

  const terminalStaleLog = buildProgressSnapshot(
    {
      id: 'task-terminal-stale-log',
      state: 'review-pending',
      stage: 'review',
      metadata: {
        mineruStatus: 'completed',
        mineruObservedProgress: { activityLevel: 'log-observation-stale' },
      },
    },
  );
  assert.equal(terminalStaleLog.phase, 'review');
  assert.equal(terminalStaleLog.freshness, 'terminal');
  assert.equal(terminalStaleLog.lagKind, 'log-stale-after-terminal');
  assert.doesNotMatch(terminalStaleLog.operatorMessage, /仍在处理/);

  const dependencyHealth = buildProgressSnapshot(
    {},
    { dependencyHealthReadinessOnly: true, observedAt: '2026-05-16T06:31:00.000Z' },
  );
  assert.equal(dependencyHealth.lagKind, 'dependency-health-readiness-only');
  assert.match(dependencyHealth.operatorMessage, /就绪性/);

  const aiFailedAfterParse = buildProgressSnapshot({
    id: 'task-ai-failed-after-parse',
    state: 'failed',
    stage: 'ai',
    metadata: {
      mineruStatus: 'completed',
      aiFailureKind: 'invalid-json',
      markdownObjectName: 'parsed/material/full.md',
    },
  });
  assert.equal(aiFailedAfterParse.phase, 'ai');
  assert.equal(aiFailedAfterParse.sourcePriority, 'ai');
  assert.equal(aiFailedAfterParse.lagKind, 'ai-after-parse');
  assert.equal(aiFailedAfterParse.aiState, 'failed');

  console.log('PASS progress snapshot contract smoke');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
