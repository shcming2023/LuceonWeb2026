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

  // Test canonical source wins over completed CleanService sourceInput fallback
  const canonicalWins = buildCanonicalRawMaterialRef({
    materialId: 'mat-1',
    metadata: {
      rawMaterial: {
        version: 'v1',
        mineru: {
          contentListV2: {
            bucket: 'eduassets-raw',
            object: 'mineru/mat-1/v1/content_list_v2.json',
            sha256: 'canonical-sha'
          }
        }
      },
      cleanServiceJobs: {
        'toc-rebuild': {
          status: 'completed',
          sourceInput: {
            bucket: 'eduassets-raw',
            object: 'mineru/mat-1/v2/content_list_v2.json',
            sha256: 'fallback-sha'
          }
        }
      }
    }
  });
  assert.equal(canonicalWins.source.object, 'mineru/mat-1/v1/content_list_v2.json');
  assert.equal(canonicalWins.hash, 'canonical-sha');

  // Test completed CleanService sourceInput fallback when rawMaterial is absent
  const fallbackRef = buildCanonicalRawMaterialRef({
    materialId: 'mat-1',
    metadata: {
      parsedPrefix: 'parsed/mat-1/',
      parsedFilesCount: 1,
      cleanServiceJobs: {
        'toc-rebuild': {
          status: 'completed',
          sourceInput: {
            bucket: 'eduassets-raw',
            object: 'mineru/mat-1/v7/content_list_v2.json',
            sha256: 'fallback-sha',
            size_bytes: 456
          }
        }
      }
    }
  });
  assert.equal(fallbackRef.source.bucket, 'eduassets-raw');
  assert.equal(fallbackRef.source.object, 'mineru/mat-1/v7/content_list_v2.json');
  assert.equal(fallbackRef.source.size_bytes, 456);
  assert.equal(fallbackRef.hash, 'fallback-sha');

  // Test fallback requires a completed CleanService job state
  assert.throws(() => buildCanonicalRawMaterialRef({
    materialId: 'mat-1',
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': {
          status: 'running',
          sourceInput: {
            bucket: 'eduassets-raw',
            object: 'mineru/mat-1/v7/content_list_v2.json',
            sha256: 'fallback-sha'
          }
        }
      }
    }
  }), /no-raw-material-evidence/);

  // Test fallback sourceInput must carry sha256 and stay under material versioned MinerU content path
  assert.throws(() => buildCanonicalRawMaterialRef({
    materialId: 'mat-1',
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': {
          status: 'completed',
          sourceInput: {
            bucket: 'eduassets-raw',
            object: 'mineru/mat-1/v7/content_list_v2.json'
          }
        }
      }
    }
  }), /invalid-raw-material: missing sha256/);

  assert.throws(() => buildCanonicalRawMaterialRef({
    materialId: 'mat-1',
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': {
          status: 'completed',
          sourceInput: {
            bucket: 'eduassets-raw',
            object: 'mineru/mat-2/v7/content_list_v2.json',
            sha256: 'fallback-sha'
          }
        }
      }
    }
  }), /invalid-raw-material: object path mismatch/);

  // Test materialId is matched literally and regex metacharacters cannot broaden the path
  const dottedMaterialRef = buildCanonicalRawMaterialRef({
    materialId: 'mat.260',
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': {
          status: 'completed',
          sourceInput: {
            bucket: 'eduassets-raw',
            object: 'mineru/mat.260/v1/content_list_v2.json',
            sha256: 'dotted-sha'
          }
        }
      }
    }
  });
  assert.equal(dottedMaterialRef.source.object, 'mineru/mat.260/v1/content_list_v2.json');
  assert.equal(dottedMaterialRef.hash, 'dotted-sha');

  assert.throws(() => buildCanonicalRawMaterialRef({
    materialId: 'mat.260',
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': {
          status: 'completed',
          sourceInput: {
            bucket: 'eduassets-raw',
            object: 'mineru/matX260/v1/content_list_v2.json',
            sha256: 'dotted-sha'
          }
        }
      }
    }
  }), /invalid-raw-material: object path mismatch/);

  // Test version segment is constrained to numeric vN shape
  assert.throws(() => buildCanonicalRawMaterialRef({
    materialId: 'mat-1',
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': {
          status: 'completed',
          sourceInput: {
            bucket: 'eduassets-raw',
            object: 'mineru/mat-1/vABC/content_list_v2.json',
            sha256: 'fallback-sha'
          }
        }
      }
    }
  }), /invalid-raw-material: object path mismatch/);

  console.log('PASS raw material adapter smoke');
}

run();
