import assert from 'node:assert/strict';
import { allocateAssetVersion } from '../services/cleanservice/asset-version.mjs';

function run() {
  console.log('=== Asset Version Allocator Smoke ===');

  // Empty -> v1
  assert.equal(allocateAssetVersion({}).assetVersion, 'v1');

  // Active job duplicate test
  const activeTask = {
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': { cleanState: 'running', assetVersion: 'v2', jobId: 'job-123' }
      }
    }
  };
  const activeResult = allocateAssetVersion(activeTask);
  assert.equal(activeResult.isActiveDuplicate, true);
  assert.equal(activeResult.assetVersion, 'v2');
  assert.equal(activeResult.jobId, 'job-123');

  // Terminal jobs -> increment
  const terminalTask = {
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': { cleanState: 'completed', assetVersion: 'v3' }
      }
    }
  };
  const terminalResult = allocateAssetVersion(terminalTask);
  assert.equal(terminalResult.isActiveDuplicate, false);
  assert.equal(terminalResult.assetVersion, 'v4');

  // Terminal jobs in materials -> increment
  const materialTask = {
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': { cleanState: 'completed', assetVersion: 'v2' }
      }
    },
    materialMetadata: {
      cleanMaterials: {
        'toc-rebuild': { assetVersion: 'v10' }
      }
    }
  };
  assert.equal(allocateAssetVersion(materialTask).assetVersion, 'v11');

  // Ignore invalid versions
  const invalidTask = {
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': { cleanState: 'completed', assetVersion: 'invalid' },
        'other': { cleanState: 'completed', assetVersion: 'v2' }
      }
    }
  };
  assert.equal(allocateAssetVersion(invalidTask).assetVersion, 'v3');

  console.log('PASS asset version allocator smoke');
}

run();
