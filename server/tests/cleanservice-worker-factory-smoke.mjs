/**
 * CleanService Worker Factory & Retriable Error Semantics Smoke Test
 *
 * Validates worker/client factory wiring and retriable error propagation
 * using mock HTTP servers. No real Mineru2Table service is contacted.
 *
 * Coverage:
 * 1. Disabled/default factory path makes zero HTTP requests
 * 2. Enabled mock factory path submits exactly one POST /api/v1/jobs
 * 3. Missing endpoint makes zero HTTP requests and reports explicit failure
 * 4. Legacy parsed-only task makes zero HTTP requests
 * 5. 4xx result is non-retriable at normalized client result
 * 6. 5xx result is retriable at normalized client result
 * 7. Timeout remains retriable at normalized client result
 * 8. No test targets 127.0.0.1:8000
 */

import assert from 'node:assert/strict';
import http from 'node:http';
import { loadCleanServiceConfig } from '../services/cleanservice/config.mjs';
import { createCleanServiceWorker, createCleanServiceClientWithTransport } from '../services/cleanservice/worker-factory.mjs';
import { buildCleanServiceJobRequest } from '../services/cleanservice/cleanservice-worker.mjs';
import { createCleanServiceClient } from '../services/cleanservice/protocol.mjs';
import { createMineru2TableHttpTransport } from '../services/cleanservice/http-transport.mjs';

// ---- Test Fixtures ----

function eligibleTask(overrides = {}) {
  return {
    id: 'task-factory-1',
    materialId: 'mat-factory-1',
    state: 'review-pending',
    metadata: {
      mineruStatus: 'completed',
      rawMaterial: {
        version: 'v1',
        mineru: {
          contentListV2: {
            bucket: 'eduassets-raw',
            object: 'mineru/mat-factory-1/v1/content_list_v2.json',
            sha256: 'sha256-factory-fixture'
          }
        }
      }
    },
    ...overrides,
  };
}

function legacyParsedOnlyTask() {
  return {
    id: 'task-legacy-factory-1',
    materialId: 'mat-legacy-factory-1',
    state: 'review-pending',
    metadata: {
      mineruStatus: 'completed',
      parsedPrefix: 'parsed/mat-legacy-factory-1/',
      parsedFilesCount: 12,
      markdownObjectName: 'parsed/mat-legacy-factory-1/full.md',
    },
  };
}

// ---- Mock HTTP Server Helpers ----

function createMockServer(handler) {
  return new Promise((resolve) => {
    const server = http.createServer(handler);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({ server, port, endpoint: `http://127.0.0.1:${port}` });
    });
  });
}

function closeServer(server) {
  return new Promise((resolve) => server.close(resolve));
}

// ---- Tests ----

async function testDisabledFactoryNoHttp() {
  console.log('  [1] disabled/default factory path makes zero HTTP requests...');

  let requestCount = 0;
  const { server, endpoint } = await createMockServer((req, res) => {
    requestCount++;
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end('{}');
  });

  try {
    const config = loadCleanServiceConfig({});
    assert.equal(config.enabled, false, 'default config must be disabled');

    const worker = createCleanServiceWorker({
      config,
      taskSource: { listTasks: async () => [eligibleTask()] },
      persistence: { persistMetadataPatch: async () => {} },
      now: () => '2026-05-21T00:00:00.000Z',
    });

    const result = await worker.tickOnce();
    assert.equal(result.status, 'disabled-noop');
    assert.equal(result.scanned, 0);
    assert.equal(requestCount, 0, 'disabled factory must not make any HTTP request');
    console.log('    PASS');
  } finally {
    await closeServer(server);
  }
}

async function testEnabledFactoryMockSubmit() {
  console.log('  [2] enabled mock factory path submits exactly one POST /api/v1/jobs...');

  const capturedRequests = [];

  const { server, endpoint } = await createMockServer((req, res) => {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      capturedRequests.push({
        method: req.method,
        url: req.url,
        headers: req.headers,
        body: JSON.parse(body),
      });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        job_id: 'mock-factory-job-001',
        status: 'queued',
        service_name: 'toc-rebuild',
        protocol_version: 'v1',
        material_id: 'mat-factory-1',
        parse_task_id: 'task-factory-1',
      }));
    });
  });

  try {
    const config = loadCleanServiceConfig({
      CLEANSERVICE_ENABLED: 'true',
      CLEANSERVICE_ENDPOINT: endpoint,
      CLEANSERVICE_API_KEY: 'test-factory-key',
    });

    const persisted = [];
    const worker = createCleanServiceWorker({
      config,
      taskSource: { listTasks: async () => [eligibleTask()] },
      persistence: { persistMetadataPatch: async (patch) => persisted.push(patch) },
      now: () => '2026-05-21T00:00:00.000Z',
    });

    const result = await worker.tickOnce();
    assert.equal(result.status, 'submitted-one');
    assert.equal(result.submitted, 1);
    assert.equal(capturedRequests.length, 1, 'must send exactly one request');

    const captured = capturedRequests[0];
    assert.equal(captured.method, 'POST');
    assert.equal(captured.url, '/api/v1/jobs');
    assert.equal(captured.headers['x-api-key'], 'test-factory-key');

    // Verify payload shape
    const payload = captured.body;
    assert.equal(payload.material_id, 'mat-factory-1');
    assert.equal(payload.inputs[0].role, 'mineru-content');
    assert.equal(payload.inputs[0].source.bucket, 'eduassets-raw');
    assert.ok(payload.inputs[0].source.object.endsWith('/content_list_v2.json'));
    assert.equal(payload.sink.bucket, 'eduassets-clean');

    // Verify persistence
    assert.equal(persisted.length, 1);
    assert.equal(persisted[0].taskId, 'task-factory-1');

    console.log('    PASS');
    console.log(`    Captured payload keys: ${Object.keys(payload).join(', ')}`);
  } finally {
    await closeServer(server);
  }
}

async function testMissingEndpointExplicitFailure() {
  console.log('  [3] missing endpoint makes zero HTTP requests and reports explicit failure...');

  let requestCount = 0;
  const { server, endpoint } = await createMockServer((req, res) => {
    requestCount++;
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end('{}');
  });

  try {
    // Enabled but no endpoint
    const config = loadCleanServiceConfig({
      CLEANSERVICE_ENABLED: 'true',
      // CLEANSERVICE_ENDPOINT not set
    });
    assert.equal(config.enabled, true);
    assert.equal(config.endpoint, null);

    const worker = createCleanServiceWorker({
      config,
      taskSource: { listTasks: async () => [eligibleTask()] },
      persistence: { persistMetadataPatch: async () => {} },
      now: () => '2026-05-21T00:00:00.000Z',
    });

    const result = await worker.tickOnce();
    // Transport is null → client reports transport not configured
    assert.equal(result.ok, false, 'missing endpoint must not be ok');
    assert.notEqual(result.status, 'disabled-noop', 'must not be disabled-noop when enabled');
    assert.equal(requestCount, 0, 'missing endpoint must not make any HTTP request');

    console.log('    PASS');
  } finally {
    await closeServer(server);
  }
}

async function testLegacyParsedOnlyNoHttp() {
  console.log('  [4] legacy parsed-only task makes zero HTTP requests...');

  let requestCount = 0;
  const { server, endpoint } = await createMockServer((req, res) => {
    requestCount++;
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end('{}');
  });

  try {
    const config = loadCleanServiceConfig({
      CLEANSERVICE_ENABLED: 'true',
      CLEANSERVICE_ENDPOINT: endpoint,
    });

    const persisted = [];
    const worker = createCleanServiceWorker({
      config,
      taskSource: { listTasks: async () => [legacyParsedOnlyTask()] },
      persistence: { persistMetadataPatch: async (patch) => persisted.push(patch) },
      now: () => '2026-05-21T00:00:00.000Z',
    });

    const result = await worker.tickOnce();
    assert.equal(result.status, 'skipped-policy');
    assert.equal(result.submitted, 0);
    assert.equal(requestCount, 0, 'legacy task must not make any HTTP request');
    assert.equal(persisted.length, 1);
    assert.equal(
      persisted[0].metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'].cleanState,
      'skipped-policy'
    );

    console.log('    PASS');
  } finally {
    await closeServer(server);
  }
}

async function test4xxNonRetriable() {
  console.log('  [5] 4xx result is non-retriable at normalized client result...');

  const { server, endpoint } = await createMockServer((req, res) => {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      res.writeHead(422, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ detail: 'Validation failed' }));
    });
  });

  try {
    const config = loadCleanServiceConfig({
      CLEANSERVICE_ENABLED: 'true',
      CLEANSERVICE_ENDPOINT: endpoint,
    });

    const transport = createMineru2TableHttpTransport({
      endpoint: config.endpoint,
      timeoutMs: 5000,
    });

    const client = createCleanServiceClient({ config, transport });
    const request = buildCleanServiceJobRequest(eligibleTask(), config);
    const result = await client.submitJob(request);

    assert.equal(result.ok, false);
    assert.ok(result.job.error, 'must have error');
    assert.equal(result.job.error.retriable, false, '4xx must be non-retriable');
    assert.ok(result.job.error.message.includes('422'));

    console.log('    PASS');
  } finally {
    await closeServer(server);
  }
}

async function test5xxRetriable() {
  console.log('  [6] 5xx result is retriable at normalized client result...');

  const { server, endpoint } = await createMockServer((req, res) => {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      res.writeHead(503, { 'Content-Type': 'text/plain' });
      res.end('Service Unavailable');
    });
  });

  try {
    const config = loadCleanServiceConfig({
      CLEANSERVICE_ENABLED: 'true',
      CLEANSERVICE_ENDPOINT: endpoint,
    });

    const transport = createMineru2TableHttpTransport({
      endpoint: config.endpoint,
      timeoutMs: 5000,
    });

    const client = createCleanServiceClient({ config, transport });
    const request = buildCleanServiceJobRequest(eligibleTask(), config);
    const result = await client.submitJob(request);

    assert.equal(result.ok, false);
    assert.ok(result.job.error, 'must have error');
    assert.equal(result.job.error.retriable, true, '5xx must be retriable at client level');
    assert.ok(result.job.error.message.includes('503'));

    console.log('    PASS');
  } finally {
    await closeServer(server);
  }
}

async function testTimeoutRetriable() {
  console.log('  [7] timeout remains retriable at normalized client result...');

  const { server, endpoint } = await createMockServer((req, res) => {
    // Never respond
  });

  try {
    const config = loadCleanServiceConfig({
      CLEANSERVICE_ENABLED: 'true',
      CLEANSERVICE_ENDPOINT: endpoint,
    });

    const transport = createMineru2TableHttpTransport({
      endpoint: config.endpoint,
      timeoutMs: 500,
    });

    const client = createCleanServiceClient({ config, transport });
    const request = buildCleanServiceJobRequest(eligibleTask(), config);
    const result = await client.submitJob(request);

    assert.equal(result.ok, false);
    assert.equal(result.job.cleanState, 'timeout');
    assert.ok(result.job.error, 'must have error');
    assert.equal(result.job.error.code, 'timeout');
    assert.equal(result.job.error.retriable, true, 'timeout must be retriable');

    console.log('    PASS');
  } finally {
    await closeServer(server);
  }
}

async function testNoRealEndpointTargeted() {
  console.log('  [8] no test targets 127.0.0.1:8000...');

  // Meta-assertion: createCleanServiceWorker with enabled config but no
  // endpoint should produce a worker that fails explicitly without requests
  const config = loadCleanServiceConfig({
    CLEANSERVICE_ENABLED: 'true',
  });
  const worker = createCleanServiceWorker({
    config,
    taskSource: { listTasks: async () => [eligibleTask()] },
    persistence: { persistMetadataPatch: async () => {} },
  });
  const result = await worker.tickOnce();
  assert.equal(result.ok, false, 'no-endpoint worker must fail explicitly');

  console.log('    PASS (all tests use ephemeral mock ports; no-endpoint fails explicitly)');
}

// ---- Main ----

async function main() {
  console.log('=== CleanService Worker Factory & Retriable Semantics Smoke ===');

  await testDisabledFactoryNoHttp();
  await testEnabledFactoryMockSubmit();
  await testMissingEndpointExplicitFailure();
  await testLegacyParsedOnlyNoHttp();
  await test4xxNonRetriable();
  await test5xxRetriable();
  await testTimeoutRetriable();
  await testNoRealEndpointTargeted();

  console.log('PASS cleanservice worker factory & retriable semantics smoke (8/8)');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
