import assert from 'node:assert/strict';
import { classifyMineruActiveTasks } from '../lib/ops-mineru-diagnostics.mjs';

function ids(tasks) {
  return tasks.map(t => t.id).sort();
}

function includesTask(tasks, id) {
  return ids(tasks).includes(id);
}

async function main() {
  console.log('=== Ops MinerU Active Task Classification Smoke ===');

  const tasks = [
    {
      id: 'task-active-processing',
      engine: 'local-mineru',
      state: 'running',
      stage: 'mineru-processing',
      metadata: { mineruTaskId: 'mineru-active-processing', mineruStatus: 'processing' },
    },
    {
      id: 'task-active-queued',
      engine: 'local-mineru',
      state: 'running',
      stage: 'mineru-queued',
      metadata: { mineruTaskId: 'mineru-active-queued', mineruStatus: 'queued' },
    },
    {
      id: 'task-drift-upload',
      engine: 'local-mineru',
      state: 'running',
      stage: 'upload',
      metadata: { mineruTaskId: 'mineru-drift-upload' },
    },
    {
      id: 'task-failed-completed-not-ingested',
      engine: 'local-mineru',
      state: 'failed',
      stage: 'mineru-processing',
      metadata: { mineruTaskId: 'mineru-not-ingested', mineruStatus: 'completed', parsedFilesCount: 0 },
    },
    {
      id: 'task-running-completed-needs-takeover',
      engine: 'local-mineru',
      state: 'running',
      stage: 'mineru-processing',
      metadata: { mineruTaskId: 'mineru-running-completed', mineruStatus: 'completed', parsedFilesCount: 0 },
    },
    {
      id: 'task-historical-ai-failed-with-artifacts',
      engine: 'local-mineru',
      state: 'failed',
      stage: 'ai',
      message: 'AI 识别完成: failed',
      aiJobId: 'ai-job-historical',
      metadata: {
        mineruTaskId: 'mineru-historical-ai',
        mineruStatus: 'completed',
        parsedFilesCount: 99,
        markdownObjectName: 'parsed/mat-historical/full.md',
        zipObjectName: 'parsed/mat-historical/mineru-result.zip',
        aiJobId: 'ai-job-historical',
      },
    },
    {
      id: 'task-completed-ok',
      engine: 'local-mineru',
      state: 'review-pending',
      stage: 'review',
      metadata: { mineruTaskId: 'mineru-completed-ok', mineruStatus: 'completed', parsedFilesCount: 12 },
    },
    {
      id: 'task-canceled-ignored',
      engine: 'local-mineru',
      state: 'canceled',
      stage: 'mineru-processing',
      metadata: { mineruTaskId: 'mineru-canceled', mineruStatus: 'completed', parsedFilesCount: 0 },
    },
  ];

  const classified = classifyMineruActiveTasks(tasks);

  assert.deepEqual(
    ids(classified.runningWithMineru),
    ['task-active-processing', 'task-active-queued', 'task-running-completed-needs-takeover'].sort(),
    'active/current/queued parse work classification should remain based on running MinerU stages',
  );
  assert.deepEqual(ids(classified.driftTasks), ['task-drift-upload'], 'drift upload task should remain visible');

  assert(includesTask(classified.completedButNotIngestedTasks, 'task-failed-completed-not-ingested'), 'failed completed without artifacts should be completed-but-not-ingested');
  assert(includesTask(classified.completedButNotIngestedTasks, 'task-running-completed-needs-takeover'), 'running completed without artifacts should be completed-but-not-ingested');

  assert(includesTask(classified.takeoverRequiredTasks, 'task-failed-completed-not-ingested'), 'failed completed without artifacts should require takeover');
  assert(includesTask(classified.takeoverRequiredTasks, 'task-running-completed-needs-takeover'), 'running completed MinerU task should require takeover');
  assert(!includesTask(classified.takeoverRequiredTasks, 'task-historical-ai-failed-with-artifacts'), 'historical AI failure with parsed artifacts must not require MinerU takeover');

  assert.deepEqual(ids(classified.historicalAiFailureTasks), ['task-historical-ai-failed-with-artifacts'], 'historical terminal AI failure should be separately classified');

  console.log('PASS ops mineru active-task classification smoke');
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});
