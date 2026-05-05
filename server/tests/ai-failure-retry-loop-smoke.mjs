import assert from 'assert';
import { ParseTaskWorker } from '../services/queue/task-worker.mjs';
import * as http from 'http';

/**
 * P1-lucode-ai-failure-retry-contract-guard Smoke Test
 * Verifies that AI Provider failures (stage: 'ai') do not get automatically recovered
 * by task-worker's recoverMisjudgedFailedTasks loop, breaking the infinite retry cycle.
 */

async function run() {
  console.log('--- Starting ai-failure-retry-loop-smoke ---');

  let localEndpointHitCount = 0;

  // Mock MinerU server to return completed
  const mockMineruServer = http.createServer((req, res) => {
    if (req.method === 'GET' && req.url === '/tasks/mock-mineru-task-1') {
      localEndpointHitCount++;
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'completed'
      }));
    } else {
      res.writeHead(404);
      res.end();
    }
  });

  await new Promise((resolve) => mockMineruServer.listen(0, '127.0.0.2', resolve));
  const port = mockMineruServer.address().port;
  const localEndpoint = `http://127.0.0.2:${port}`;

  console.log(`Mock MinerU API running on ${localEndpoint}`);

  let updatedTasks = [];

  // Create a worker with patched updateTaskWithRetry to intercept updates
  const worker = new ParseTaskWorker({});
  worker.updateTaskWithRetry = async (taskId, updateData) => {
    console.log(`[Mock UpdateTask] ${taskId}`, updateData);
    updatedTasks.push({ taskId, updateData });
    return true;
  };
  worker.updateMaterialWithRetry = async () => true;

  // 1. A task that failed in MinerU (stage: mineru-failed) but MinerU API says completed
  // This SHOULD be recovered (the original intended behavior)
  const task1 = {
    id: 'task-1',
    state: 'failed',
    stage: 'mineru-failed',
    engine: 'local-mineru',
    optionsSnapshot: { localEndpoint },
    metadata: {
      mineruTaskId: 'mock-mineru-task-1'
    }
  };

  // 2. A task that failed during AI provider processing (stage: ai) but MinerU API says completed
  // This SHOULD NOT be recovered (the fix we just made)
  const task2 = {
    id: 'task-2',
    state: 'failed',
    stage: 'ai',
    engine: 'local-mineru',
    optionsSnapshot: { localEndpoint },
    metadata: {
      mineruTaskId: 'mock-mineru-task-1', // Same mock MinerU task to ensure it says 'completed'
      aiJobId: 'ai-job-failed'
    }
  };

  // Execute recoverMisjudgedFailedTasks
  console.log('Running recoverMisjudgedFailedTasks...');
  await worker.recoverMisjudgedFailedTasks([task1, task2]);

  mockMineruServer.close();

  // Assertions
  console.log('\n--- Assertions ---');

  // task1 should be recovered
  const task1Update = updatedTasks.find(u => u.taskId === 'task-1');
  assert(task1Update, 'task1 (mineru-failed) should have been recovered');
  assert(task1Update.updateData.state === 'running', 'task1 should be running');
  assert(task1Update.updateData.stage === 'result-fetching', 'task1 should be fetching results');

  // task2 should NOT be recovered
  const task2Update = updatedTasks.find(u => u.taskId === 'task-2');
  assert(!task2Update, 'task2 (stage: ai) should NOT have been recovered to prevent infinite loop');

  // localEndpointHitCount should be 1 (only task1 queried MinerU)
  assert(localEndpointHitCount === 1, `MinerU API should be queried exactly 1 time, got ${localEndpointHitCount}`);

  console.log('SUCCESS: ai-failure-retry-loop-smoke passed! Infinite retry loop is blocked.');
}

run().catch(err => {
  console.error('Smoke test failed:', err);
  process.exit(1);
});
