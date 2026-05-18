import assert from 'assert';
import { reAiTask } from '../lib/task-actions-routes.mjs';

/**
 * P0 Re-AI Task Job Creation Contract Smoke Test
 * Verifies that POST /tasks/:id/re-ai explicitly creates a new AI job
 * and transitions to failed state if job creation fails.
 */

async function run() {
  console.log('--- Starting re-ai-task-smoke ---');

  let dbGetHitCount = 0;
  let dbPatchCalls = [];
  let createJobCalls = [];
  let createJobResult = null;

  const originalFetch = global.fetch;
  global.fetch = async (url, options) => {
    const urlStr = url.toString();
    const method = options?.method || 'GET';
    
    // Intercept GET tasks or materials
    if (method === 'GET' && (urlStr.includes('/tasks/') || urlStr.includes('/materials/'))) {
      dbGetHitCount++;
      return {
        ok: true,
        status: 200,
        json: async () => ({
          id: urlStr.includes('task-1') ? 'task-1' : 'mat-1',
          state: 'review-pending',
          stage: 'review',
          metadata: { aiJobId: 'old-job-id' }
        })
      };
    }
    
    // Intercept PATCH tasks or ai-metadata-jobs
    if (method === 'PATCH') {
      const body = JSON.parse(options.body);
      dbPatchCalls.push({ url: urlStr, updates: body });
      return { ok: true, status: 200, json: async () => ({}) };
    }
    
    // Intercept POST /ai-metadata-jobs
    if (method === 'POST' && urlStr.includes('/ai-metadata-jobs')) {
      const body = JSON.parse(options.body);
      createJobCalls.push(body);
      
      if (!createJobResult.created) {
        // To trigger failure, the db route actually returns 409 or similar, but the client code 
        // metadata-job-client.mjs checks for duplicate or handles it.
        // Wait, metadataJobClient checks DB first. Let's mock the GET /ai-metadata-jobs
        return { ok: false, status: 500 };
      }
      return { 
        ok: true, 
        status: 200, 
        json: async () => ({ id: 'new-job-123', parseTaskId: body.parseTaskId }) 
      };
    }
    
    // Intercept GET /ai-metadata-jobs (for duplication check)
    if (method === 'GET' && urlStr.includes('/ai-metadata-jobs')) {
      return { ok: true, status: 200, json: async () => ([]) };
    }

    return originalFetch(url, options);
  };

  const mockDeps = {
    getMinioClient: () => ({
      statObject: async () => ({}) // simulate object exists
    }),
    getParsedBucket: () => 'parsed-assets',
    getMaterialBucket: () => 'materials',
    getStorageBackend: () => 'local-minio'
  };

  const reqTask = {
    id: 'task-1',
    state: 'review-pending',
    materialId: 'mat-1',
    aiJobId: 'old-job',
    metadata: { markdownObjectName: 'doc.md', aiJobId: 'old-job' }
  };

  // 1. Success case: Job created successfully
  createJobResult = { created: true };
  
  await reAiTask(reqTask, mockDeps);

  assert(createJobCalls.length === 1, 'Expected createAiMetadataJob to be called once');
  assert(createJobCalls[0].parseTaskId === 'task-1', 'Expected createAiMetadataJob called with correct task id');
  assert(dbPatchCalls.length === 2, 'Expected dbPatch to be called twice (invalidate old job + set ai-pending)');
  assert(dbPatchCalls[0].url.includes('/ai-metadata-jobs/old-job'), 'Expected old job to be invalidated');
  assert(dbPatchCalls[1].url.includes('/tasks/task-1'), 'Expected task state to be updated');
  assert(dbPatchCalls[1].updates.state === 'ai-pending', 'Expected state ai-pending');
  assert(typeof dbPatchCalls[1].updates.metadata.aiJobId === 'string', 'Expected new aiJobId to be a string');
  assert(dbPatchCalls[1].updates.metadata.aiJobId.startsWith('ai-job-'), 'Expected new aiJobId to start with ai-job-');
  
  // Reset
  dbPatchCalls = [];
  createJobCalls = [];

  // 2. Failure case: Job creation fails
  createJobResult = { created: false, reason: 'Simulated failure' };

  try {
    await reAiTask(reqTask, mockDeps);
    assert.fail('Expected reAiTask to throw an error');
  } catch (err) {
    assert(err.message.includes('创建 AI 任务失败'), 'Expected error message');
  }

  // The task state transitions to failed
  assert(createJobCalls.length === 1, 'Expected createAiMetadataJob to be called once');
  assert(dbPatchCalls.length === 2, 'Expected dbPatch to be called twice (invalidate old + set failed)');
  assert(dbPatchCalls[1].updates.state === 'failed', 'Expected state to transition to failed');
  assert(dbPatchCalls[1].updates.stage === 'ai', 'Expected stage ai');
  assert(dbPatchCalls[1].updates.errorMessage.includes('创建 AI 任务失败'), 'Expected failure message');

  global.fetch = originalFetch;

  console.log('SUCCESS: re-ai-task-smoke passed! Re-AI job creation contract is verified.');
}

run().catch(err => {
  console.error('Smoke test failed:', err);
  process.exit(1);
});
