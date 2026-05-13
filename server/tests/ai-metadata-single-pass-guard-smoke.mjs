import assert from 'node:assert/strict';
import express from 'express';

const DB_BASE_URL = 'http://localhost:8798';
process.env.DB_BASE_URL = DB_BASE_URL;

const { AiMetadataWorker } = await import('../services/ai/metadata-worker.mjs');

const dbState = {
  calls: {
    listJobs: 0,
    getJobById: 0,
    patchJob: 0
  },
  jobs: [
    {
      id: 'ai-job-duplicate-guard',
      parseTaskId: 'task-duplicate-guard',
      materialId: 'mat-duplicate-guard',
      state: 'pending',
      createdAt: '2026-05-13T07:00:00.000Z',
      updatedAt: '2026-05-13T07:00:00.000Z'
    }
  ]
};

const app = express();
app.use(express.json());

app.get('/ai-metadata-jobs', (_req, res) => {
  dbState.calls.listJobs += 1;
  res.json(dbState.jobs.map(job => ({ ...job })));
});

app.get('/ai-metadata-jobs/:id', (req, res) => {
  dbState.calls.getJobById += 1;
  const job = dbState.jobs.find(item => item.id === req.params.id);
  if (!job) {
    res.status(404).json({ error: 'not_found' });
    return;
  }
  res.json({ ...job });
});

app.patch('/ai-metadata-jobs/:id', (req, res) => {
  dbState.calls.patchJob += 1;
  const job = dbState.jobs.find(item => item.id === req.params.id);
  if (!job) {
    res.status(404).json({ error: 'not_found' });
    return;
  }
  Object.assign(job, req.body, { updatedAt: req.body.updatedAt || new Date().toISOString() });
  res.json({ ...job });
});

const server = await new Promise(resolve => {
  const instance = app.listen(8798, () => resolve(instance));
});

try {
  class TestWorker extends AiMetadataWorker {
    constructor() {
      super({});
      this.processedJobIds = [];
    }

    async processJob(job) {
      this.processedJobIds.push(job.id);
      dbState.jobs[0] = {
        ...dbState.jobs[0],
        state: 'review-pending',
        message: 'test terminal state',
        completedAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
    }
  }

  const worker = new TestWorker();
  await worker.scanAndProcess();

  assert.deepEqual(worker.processedJobIds, ['ai-job-duplicate-guard']);
  assert.equal(dbState.jobs[0].state, 'review-pending');
  assert.ok(dbState.calls.listJobs >= 2, 'scan should read pre and post recovery snapshots');
  assert.equal(dbState.calls.patchJob, 0, 'focused test should not mutate through updateJob');

  const baseWorker = new AiMetadataWorker({});
  await baseWorker.processJob({ ...dbState.jobs[0], state: 'pending' });
  assert.deepEqual(
    worker.processedJobIds,
    ['ai-job-duplicate-guard'],
    'processJob must re-read latest terminal state and skip stale pending input'
  );

  console.log('AI metadata single-pass guard smoke passed');
} finally {
  await new Promise(resolve => server.close(resolve));
}
