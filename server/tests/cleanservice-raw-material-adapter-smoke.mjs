import assert from 'node:assert/strict';
import { buildCanonicalRawMaterialRef } from '../services/cleanservice/raw-material-adapter.mjs';

function run() {
  console.log('=== Raw Material Adapter Smoke ===');

  // Test missing raw material
  assert.throws(() => buildCanonicalRawMaterialRef({}), /no-raw-material-evidence/);

  // Test legacy -> skipped-policy
  assert.throws(() => buildCanonicalRawMaterialRef({
    metadata: { parsedPrefix: 'parsed/mat-1/', parsedFilesCount: 1 }
  }), /legacy-parsed-evidence-skipped/);

  // Test invalid bucket
  assert.throws(() => buildCanonicalRawMaterialRef({
    metadata: { rawMaterial: { mineru: { contentListV2: { bucket: 'wrong', object: 'mineru/mat/v1/content_list_v2.json' } } } }
  }), /invalid-raw-material: bucket must be eduassets-raw/);

  // Test invalid object missing
  assert.throws(() => buildCanonicalRawMaterialRef({
    metadata: { rawMaterial: { mineru: { contentListV2: { bucket: 'eduassets-raw' } } } }
  }), /invalid-raw-material: missing object/);

  // Test invalid object path mismatch
  assert.throws(() => buildCanonicalRawMaterialRef({
    materialId: 'mat-1',
    metadata: { rawMaterial: { version: 'v1', mineru: { contentListV2: { bucket: 'eduassets-raw', object: 'mineru/mat-2/v1/content_list_v2.json' } } } }
  }), /invalid-raw-material: object path mismatch/);

  // Test success
  const ref = buildCanonicalRawMaterialRef({
    materialId: 'mat-1',
    metadata: {
      rawMaterial: {
        version: 'v1',
        mineru: {
          contentListV2: {
            bucket: 'eduassets-raw',
            object: 'mineru/mat-1/v1/content_list_v2.json',
            sha256: 'xyz123'
          }
        }
      }
    }
  });

  assert.equal(ref.role, 'mineru-content');
  assert.equal(ref.source.bucket, 'eduassets-raw');
  assert.equal(ref.source.object, 'mineru/mat-1/v1/content_list_v2.json');
  assert.equal(ref.hash, 'xyz123');

  console.log('PASS raw material adapter smoke');
}

run();
