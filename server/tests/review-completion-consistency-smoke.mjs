import assert from 'node:assert';
import express from 'express';
import http from 'node:http';
import { registerTaskActionRoutes } from '../lib/task-actions-routes.mjs';
import { registerConsistencyRoutes } from '../lib/consistency-routes.mjs';

const app = express();
app.use(express.json());

const dbStorage = {
  tasks: [],
  materials: [],
  'ai-metadata-jobs': [],
};

const deps = {
  getStorageBackend: () => 'minio',
  getMinioBucket: () => 'eduassets',
  getParsedBucket: () => 'eduassets-parsed',
  listAllObjects: async (bucket, prefix) => [],
  getMinioClient: () => ({
    statObject: async (bucket, obj) => { return true; },
  }),
  DB_BASE_URL: 'mock-db' // Handled by fetch override
};

registerTaskActionRoutes(app, deps);
registerConsistencyRoutes(app, deps);

const server = http.createServer(app);
await new Promise(r => server.listen(0, r));
const port = server.address().port;
deps.DB_BASE_URL = 'http://mock-db';

// Simple fetch wrapper
async function mockRequest(path, method = 'POST', body = {}) {
  const url = `http://127.0.0.1:${port}${path}`;
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: method !== 'GET' ? JSON.stringify(body) : undefined
  });
  const data = await res.json().catch(() => ({}));
  return { status: res.status, body: data };
}

const originalFetch = globalThis.fetch;
globalThis.fetch = async (url, opts) => {
  const urlStr = url.toString();

  if (urlStr.startsWith(`http://127.0.0.1:${port}`)) {
    return originalFetch(url, opts);
  }

  for (const coll of ['tasks', 'materials', 'ai-metadata-jobs']) {
    if (urlStr.endsWith(`/${coll}`)) {
      if (!opts || !opts.method || opts.method === 'GET') {
        return { ok: true, json: async () => dbStorage[coll] };
      }
    }
    if (urlStr.includes(`/${coll}/`)) {
      const idMatch = urlStr.match(new RegExp(`/${coll}/([^/]+)$`));
      if (idMatch) {
        const id = idMatch[1];
        if (!opts || !opts.method || opts.method === 'GET') {
          const item = dbStorage[coll].find(t => t.id === id);
          if (!item) return { ok: false, status: 404 };
          return { ok: true, json: async () => item };
        }
        if (opts.method === 'PATCH') {
          const body = JSON.parse(opts.body);
          const index = dbStorage[coll].findIndex(t => t.id === id);
          if (index !== -1) {
            // merge metadata if exists
            const existingMeta = dbStorage[coll][index].metadata || {};
            const incomingMeta = body.metadata || {};
            dbStorage[coll][index] = {
              ...dbStorage[coll][index],
              ...body,
              metadata: { ...existingMeta, ...incomingMeta }
            };
          }
          return { ok: true, json: async () => dbStorage[coll][index] };
        }
      }
    }
  }

  return { ok: true, json: async () => ({}) };
};

async function runTests() {
  console.log('=== P2 Review Completion & Consistency Smoke Test ===');

  // Test 1: Review pending -> Completed sync
  dbStorage.tasks = [{ id: 't1', state: 'review-pending', materialId: 'm1' }];
  dbStorage.materials = [{ id: 'm1', status: 'reviewing', metadata: { objectName: 'originals/m1/m1.pdf' } }];

  console.log('Test 1: Submit review for t1');
  let res = await mockRequest('/tasks/t1/review', 'POST', { metadata: { title: 'Approved' } });
  assert.equal(res.status, 200);
  assert.equal(res.body.ok, true);

  // Verify Task State
  const t1 = dbStorage.tasks.find(t => t.id === 't1');
  assert.equal(t1.state, 'completed');
  assert.equal(t1.stage, 'done');

  // Verify Material State (the fix!)
  const m1 = dbStorage.materials.find(m => m.id === 'm1');
  assert.equal(m1.status, 'completed');
  assert.equal(m1.mineruStatus, 'completed');
  assert.equal(m1.aiStatus, 'analyzed');
  assert.equal(m1.metadata.processingStage, 'done');
  assert.equal(m1.metadata.processingMsg, '人工审核确认');

  // Verify audit does not report completed-task-material-status-mismatch
  let auditRes = await mockRequest('/audit/consistency', 'GET');
  assert.equal(auditRes.body.ok, true);
  const mismatchFinding = auditRes.body.findings.find(f => f.kind === 'completed-task-material-status-mismatch' && f.targetId === 'm1');
  assert.equal(mismatchFinding, undefined, 'Audit should be clean for m1');
  console.log('Test 1 Pass ✅');

  // Test 2: Synthetic drift case -> Audit reports -> Apply fixes
  console.log('Test 2: Synthetic drift case');
  dbStorage.tasks.push({ id: 't2', state: 'completed', materialId: 'm2' });
  dbStorage.materials.push({ id: 'm2', status: 'reviewing', aiStatus: 'pending', mineruStatus: 'completed', metadata: { objectName: 'originals/m2/m2.pdf' } });

  auditRes = await mockRequest('/audit/consistency', 'GET');
  const t2Finding = auditRes.body.findings.find(f => f.kind === 'completed-task-material-status-mismatch' && f.targetId === 'm2');
  assert.ok(t2Finding, 'Audit should report drift for m2');
  assert.equal(t2Finding.severity, 'warn');

  console.log('Test 3: Apply audit repair');
  const applyRes = await mockRequest('/audit/consistency/apply', 'POST', { findings: [t2Finding] });
  assert.equal(applyRes.body.ok, true);

  const m2 = dbStorage.materials.find(m => m.id === 'm2');
  assert.equal(m2.status, 'completed');
  assert.equal(m2.mineruStatus, 'completed');
  assert.equal(m2.aiStatus, 'analyzed');
  assert.equal(m2.metadata.processingStage, 'done');
  assert.equal(m2.metadata.processingMsg, '人工审核确认 (通过一致性修复)');
  console.log('Test 2 & 3 Pass ✅');

  console.log('=== All Tests Passed ===');
  globalThis.fetch = originalFetch;
  server.close();
}

runTests().catch(e => {
  console.error(e);
  server.close();
  process.exit(1);
});
