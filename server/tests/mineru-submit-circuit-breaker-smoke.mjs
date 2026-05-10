/**
 * mineru-submit-circuit-breaker-smoke.mjs
 *
 * Covers the pressure-test failure mode where MinerU /health is healthy but
 * POST /tasks returns HTTP 500. The worker must pause further local-MinerU
 * submissions instead of cascading queued tasks into execution-failed.
 */

import { ParseTaskWorker } from '../services/queue/task-worker.mjs';
import { MineruSubmitUnreachableError } from '../services/mineru/local-adapter.mjs';

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    passed += 1;
    console.log(`PASS ${message}`);
  } else {
    failed += 1;
    console.error(`FAIL ${message}`);
  }
}

function makeTask(id, materialId, createdAt) {
  return {
    id,
    materialId,
    engine: 'local-mineru',
    state: 'pending',
    stage: 'upload',
    createdAt,
    updatedAt: createdAt,
    optionsSnapshot: {
      localTimeout: 3600,
      material: {
        fileName: `${materialId}.pdf`,
        mimeType: 'application/pdf',
        metadata: { objectName: `originals/${materialId}/source.pdf` },
      },
    },
    metadata: {},
  };
}

async function runSmoke() {
  console.log('--- mineru-submit-circuit-breaker-smoke ---');

  const task1 = makeTask('task-submit-500-1', 'mat-submit-500-1', '2026-05-10T00:00:00.000Z');
  const task2 = makeTask('task-submit-500-2', 'mat-submit-500-2', '2026-05-10T00:00:01.000Z');
  const tasks = [task1, task2];
  const taskUpdates = [];
  const materialUpdates = [];
  let mineruProcessorCalls = 0;

  const taskClient = {
    getAllTasks: async () => tasks,
    updateTask: async (id, patch) => {
      taskUpdates.push({ id, patch });
      const target = tasks.find((item) => item.id === id);
      if (target) {
        Object.assign(target, patch);
        if (patch.metadata) target.metadata = { ...(target.metadata || {}), ...patch.metadata };
      }
      return true;
    },
    updateMaterial: async (id, patch) => {
      materialUpdates.push({ id, patch });
      return true;
    },
  };

  const worker = new ParseTaskWorker({
    minioContext: {
      getFileStream: async () => ({}),
      saveMarkdown: async () => {},
      saveObject: async () => {},
    },
    taskClient,
    mineruProcessor: async () => {
      mineruProcessorCalls += 1;
      throw new MineruSubmitUnreachableError('MinerU 提交失败: 500 | Endpoint: http://mineru/tasks | Body: Internal Server Error', {
        status: 500,
        endpoint: 'http://mineru/tasks',
        dependencyBlocking: true,
        retryAfterMs: 60_000,
      });
    },
  });

  await worker.processTask(task1);

  assert(task1.state === 'pending', 'first task remains pending after submit-path 500');
  assert(task1.stage === 'dependency-blocked', 'first task is marked dependency-blocked');
  assert(task1.metadata.submitDependencyBlocked === true, 'first task records submit dependency block');
  assert(task1.metadata.nextSubmitRetryAt, 'first task records next submit retry time');
  assert(!taskUpdates.some(({ patch }) => patch.state === 'failed'), 'submit-path 500 does not mark task failed');
  assert(materialUpdates.some(({ id, patch }) => id === 'mat-submit-500-1' && patch.mineruStatus === 'blocked'), 'material is normalized to blocked, not failed');

  await worker.scanAndProcess();

  assert(mineruProcessorCalls === 1, 'circuit breaker prevents submitting another pending task');
  assert(task2.state === 'pending', 'second task remains pending');
  assert(task2.stage === 'upload', 'second task is not advanced to execution-failed');

  console.log(`\nResults: ${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

runSmoke().catch((error) => {
  console.error(error);
  process.exit(1);
});
