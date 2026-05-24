import assert from 'node:assert/strict';
import { allocateAssetVersion, resolveAssetVersion } from '../services/cleanservice/asset-version.mjs';

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

  // targetAssetVersion is explicit and preserves default allocation evidence
  const targetTask = {
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': { cleanState: 'completed', assetVersion: 'v2' }
      }
    }
  };
  const targetResult = resolveAssetVersion(targetTask, 'toc-rebuild', {
    targetAssetVersion: 'v4',
    previousAssetVersion: 'v2',
  });
  assert.equal(targetResult.assetVersion, 'v4');
  assert.equal(targetResult.defaultAllocatedAssetVersion, 'v3');
  assert.equal(targetResult.targetAssetVersion, 'v4');
  assert.equal(targetResult.resolvedBy, 'targetAssetVersion');

  assert.throws(() => resolveAssetVersion(targetTask, 'toc-rebuild', {
    targetAssetVersion: 'vABC',
    previousAssetVersion: 'v2',
  }), /invalid-target-asset-version/);

  assert.throws(() => resolveAssetVersion(targetTask, 'toc-rebuild', {
    targetAssetVersion: 'v4',
  }), /target-asset-version-requires-previous-version/);

  assert.throws(() => resolveAssetVersion(targetTask, 'toc-rebuild', {
    targetAssetVersion: 'v2',
    previousAssetVersion: 'v2',
  }), /target-asset-version-below-default|target-asset-version-not-greater-than-previous/);

  const activeDuplicateTask = {
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': { cleanState: 'running', assetVersion: 'v2' }
      }
    }
  };
  assert.throws(() => resolveAssetVersion(activeDuplicateTask, 'toc-rebuild', {
    targetAssetVersion: 'v4',
    previousAssetVersion: 'v2',
  }), /target-asset-version-blocked-by-active-duplicate/);

  console.log('PASS asset version allocator smoke');
}

run();
