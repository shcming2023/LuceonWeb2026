import assert from 'node:assert/strict';
import { loadCleanServiceConfig } from '../services/cleanservice/config.mjs';
import { buildCleanServiceJobRequest } from '../services/cleanservice/cleanservice-worker.mjs';
import { buildCanonicalRawMaterialRef } from '../services/cleanservice/raw-material-adapter.mjs';

function eligibleTask(overrides = {}) {
  return {
    id: 'task-clean-1',
    materialId: 'mat-clean-1',
    state: 'review-pending',
    metadata: {
      mineruStatus: 'completed',
      rawMaterial: {
        version: 'v1',
        mineru: {
          contentListV2: {
            bucket: 'eduassets-raw',
            object: 'mineru/mat-clean-1/v1/content_list_v2.json',
            sha256: 'abc12345'
          }
        }
      }
    },
    ...overrides,
  };
}

function legacyTask() {
  return {
    id: 'task-clean-2',
    materialId: 'mat-clean-2',
    state: 'review-pending',
    metadata: {
      mineruStatus: 'completed',
      artifactManifestObjectName: 'mineru/mat-clean-2/v1/manifest.json',
    }
  };
}

async function main() {
  console.log('=== CleanService ProtocolV1 Payload Alignment Smoke ===');

  const config = loadCleanServiceConfig({
    CLEANSERVICE_ENABLED: 'true',
    CLEANSERVICE_ENDPOINT: 'http://cleanservice.invalid',
    CLEANSERVICE_API_KEY: 'test-only',
    CLEANSERVICE_STORAGE_ENDPOINT: 'custom-minio:9000',
    CLEANSERVICE_STORAGE_USE_SSL: 'false',
    CLEANSERVICE_SUBMITTED_BY: 'custom-worker',
  });

  const fixtureTime = '2026-05-21T14:00:00.000Z';
  const task = eligibleTask();
  const request = buildCleanServiceJobRequest(task, config, { submittedAt: fixtureTime });

  // 1. Builds a canonical Raw Material task request.
  assert.ok(request);

  // 2. Asserts all six Task 231 missing fields are present.
  assert.ok(request.submitted_at, 'submitted_at missing');
  assert.ok(request.submitted_by, 'submitted_by missing');
  assert.ok(request.inputs[0].source.endpoint, 'source.endpoint missing');
  assert.ok(request.inputs[0].source.use_ssl !== undefined, 'source.use_ssl missing');
  assert.ok(request.sink.endpoint, 'sink.endpoint missing');
  assert.ok(request.sink.use_ssl !== undefined, 'sink.use_ssl missing');

  // 3. Asserts source.endpoint === sink.endpoint.
  assert.equal(request.inputs[0].source.endpoint, request.sink.endpoint);
  assert.equal(request.inputs[0].source.endpoint, 'custom-minio:9000');

  // 4. Asserts source.use_ssl === false and sink.use_ssl === false by default.
  assert.equal(request.inputs[0].source.use_ssl, false);
  assert.equal(request.sink.use_ssl, false);

  // 5. Asserts submitted_by is deterministic from config.
  assert.equal(request.submitted_by, 'custom-worker');

  // 6. Asserts submitted_at is present and valid, or equals an injected fixture timestamp.
  assert.equal(request.submitted_at, fixtureTime);

  // Default configuration check
  const defaultConfig = loadCleanServiceConfig({
    CLEANSERVICE_ENABLED: 'true',
  });
  const defaultRequest = buildCleanServiceJobRequest(task, defaultConfig);
  assert.equal(defaultRequest.inputs[0].source.endpoint, 'minio:9000');
  assert.equal(defaultRequest.inputs[0].source.use_ssl, false);
  assert.equal(defaultRequest.sink.endpoint, 'minio:9000');
  assert.equal(defaultRequest.sink.use_ssl, false);
  assert.equal(defaultRequest.submitted_by, 'luceon2026/cleanservice-worker');
  // submitted_at must be a valid ISO string
  assert.ok(Date.parse(defaultRequest.submitted_at) > 0);

  // 7. Asserts legacy parsed-only evidence still throws or results in skipped-policy and sends no submit.
  assert.throws(() => buildCanonicalRawMaterialRef(legacyTask()), (err) => {
    return err.code === 'skipped-policy';
  });

  console.log('PASS cleanservice payload alignment smoke');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
