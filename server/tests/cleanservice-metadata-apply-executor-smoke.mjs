import assert from 'node:assert/strict';
import { buildVerifiedCleanOutputMetadataCandidate } from '../services/cleanservice/metadata-summary.mjs';
import { buildCleanMetadataPersistencePlan } from '../services/cleanservice/metadata-persistence.mjs';
import { applyCleanMetadataPersistencePlan, hasFullContentInMetadata } from '../services/cleanservice/metadata-apply-executor.mjs';

function objectRef(object, sizeBytes = 128) {
  return {
    bucket: 'eduassets-clean',
    object,
    size_bytes: sizeBytes,
    content_type: object.endsWith('.md') ? 'text/markdown' : 'application/json',
    sha256: 'abc123sha256',
  };
}

function mockJob(overrides = {}) {
  const materialId = overrides.materialId || '1842780526581841';
  const assetVersion = overrides.assetVersion || 'v2';
  return {
    job_id: overrides.jobId || 'luceon-task-251-rebuild-v2',
    status: 'completed',
    service_name: 'toc-rebuild',
    service_version: '1.0.0',
    protocol_version: 'v1',
    material_id: materialId,
    parse_task_id: overrides.parseTaskId || 'task-1779085089451',
    asset_version: assetVersion,
    submitted_at: '2026-05-22T00:00:00.000Z',
    started_at: '2026-05-22T00:00:01.000Z',
    finished_at: '2026-05-22T00:00:02.000Z',
    sink: { bucket: 'eduassets-clean', prefix: `toc-rebuild/${materialId}/${assetVersion}/` },
    artifacts: {
      flooded_content: objectRef(`toc-rebuild/${materialId}/${assetVersion}/flooded_content.json`),
      logic_tree: objectRef(`toc-rebuild/${materialId}/${assetVersion}/logic_tree.json`),
      readable_tree: objectRef(`toc-rebuild/${materialId}/${assetVersion}/readable_tree.md`),
      skeleton: objectRef(`toc-rebuild/${materialId}/${assetVersion}/skeleton.json`),
      unresolved_anchors: objectRef(`toc-rebuild/${materialId}/${assetVersion}/unresolved_anchors.json`),
      metrics: objectRef(`toc-rebuild/${materialId}/${assetVersion}/metrics.json`),
      provenance: objectRef(`toc-rebuild/${materialId}/${assetVersion}/provenance.json`),
    },
    stats: {
      tokens: { prompt: 6212, completion: 54, total: 6266 },
      tokensTotal: 6266,
      tokensPrompt: 6212,
      tokensCompletion: 54,
      cost_cny_estimated: 0.00632,
      costCnyEstimated: 0.00632,
      cost_cny_actual: 0.0,
      costCnyActual: 0.0,
      unresolved_anchor_count: 0,
    },
    provenance: {
      schema: 'luceon-provenance/v1',
      service: { name: 'toc-rebuild', version: '1.0.0', protocol_version: 'v1' },
      asset: { material_id: materialId, asset_version: assetVersion },
      job: { job_id: overrides.jobId || 'luceon-task-251-rebuild-v2', parse_task_id: overrides.parseTaskId || 'task-1779085089451' },
      inputs: [
        {
          bucket: 'eduassets-raw',
          object: `mineru/${materialId}/v1/content_list_v2.json`,
          sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
          size_bytes: 31543,
        }
      ],
    },
    ...overrides,
  };
}

function createMockDbClient({ taskOk = true, materialOk = true } = {}) {
  const calls = [];
  return {
    calls,
    async updateTask(id, data) {
      calls.push({ method: 'updateTask', id, data });
      return taskOk;
    },
    async updateMaterial(id, data) {
      calls.push({ method: 'updateMaterial', id, data });
      return materialOk;
    },
  };
}

async function runTests() {
  console.log('=== CleanService Metadata Apply Executor Smoke ===');

  const customNow = () => '2026-05-22T17:32:06.000Z';
  const targetMaterialId = '1842780526581841';
  const targetTaskId = 'task-1779085089451';
  const targetJobId = 'luceon-task-251-rebuild-v2';
  const targetVersion = 'v2';

  const validVerification = {
    ok: true,
    cleanState: 'completed',
    errors: [],
    warnings: [],
    unresolvedAnchorCount: 0,
    inputSizeBytes: 31543,
  };

  const defaultJob = mockJob({
    materialId: targetMaterialId,
    parseTaskId: targetTaskId,
    jobId: targetJobId,
    assetVersion: targetVersion,
  });

  const defaultCandidate = buildVerifiedCleanOutputMetadataCandidate({
    job: defaultJob,
    verification: validVerification,
    now: customNow,
  });

  const defaultExistingTask = {
    id: targetTaskId,
    metadata: {
      existingUnrelatedField: 'preserve-task',
      cleanServiceJobs: {
        'another-service': { jobId: 'some-other-job', status: 'completed' },
      },
    },
  };

  const defaultExistingMaterial = {
    id: targetMaterialId,
    metadata: {
      existingUnrelatedField: 'preserve-material',
      cleanMaterials: {
        'another-service': { latestVersion: 'v1', status: 'completed' },
      },
    },
  };

  // Case 1: Standard Success Apply
  {
    console.log('  [1] standard success apply under allowRealApply=true...');
    const plan = buildCleanMetadataPersistencePlan({
      candidate: defaultCandidate,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      now: customNow,
    });

    const mockDb = createMockDbClient({ taskOk: true, materialOk: true });

    const res = await applyCleanMetadataPersistencePlan({
      plan,
      taskId: targetTaskId,
      materialId: targetMaterialId,
      dbClient: mockDb,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      allowRealApply: true,
    });

    assert.equal(res.ok, true);
    assert.equal(res.applied, true);
    assert.equal(res.operationCount, 2);
    assert.equal(res.classification, 'APPLIED_SINGLE_SAMPLE_METADATA');

    assert.equal(mockDb.calls.length, 2);
    assert.equal(mockDb.calls[0].method, 'updateTask');
    assert.equal(mockDb.calls[0].id, targetTaskId);
    assert.ok(mockDb.calls[0].data.metadata.cleanServiceJobs['toc-rebuild']);
    assert.equal(mockDb.calls[0].data.metadata.existingUnrelatedField, 'preserve-task');

    assert.equal(mockDb.calls[1].method, 'updateMaterial');
    assert.equal(mockDb.calls[1].id, targetMaterialId);
    assert.ok(mockDb.calls[1].data.metadata.cleanMaterials['toc-rebuild']);
    assert.equal(mockDb.calls[1].data.metadata.existingUnrelatedField, 'preserve-material');
  }

  // Case 2: Dry Run Mode (allowRealApply=false)
  {
    console.log('  [2] dry-run success when allowRealApply=false...');
    const plan = buildCleanMetadataPersistencePlan({
      candidate: defaultCandidate,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      now: customNow,
    });

    const mockDb = createMockDbClient();

    const res = await applyCleanMetadataPersistencePlan({
      plan,
      taskId: targetTaskId,
      materialId: targetMaterialId,
      dbClient: mockDb,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      allowRealApply: false,
    });

    assert.equal(res.ok, true);
    assert.equal(res.applied, false);
    assert.equal(res.operationCount, 0);
    assert.equal(res.classification, 'DRY_RUN_SUCCESS');
    assert.equal(mockDb.calls.length, 0);
  }

  // Case 3: Invalid Plan Gate (shouldApply=false)
  {
    console.log('  [3] plan validity check should fail on invalid candidate...');
    const badCandidate = { ok: false, shouldPersist: false };
    const plan = buildCleanMetadataPersistencePlan({
      candidate: badCandidate,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      now: customNow,
    });

    const mockDb = createMockDbClient();

    const res = await applyCleanMetadataPersistencePlan({
      plan,
      taskId: targetTaskId,
      materialId: targetMaterialId,
      dbClient: mockDb,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      allowRealApply: true,
    });

    assert.equal(res.ok, false);
    assert.equal(res.applied, false);
    assert.equal(res.classification, 'BLOCKED_PLAN_NOT_APPLYABLE');
    assert.equal(mockDb.calls.length, 0);
  }

  // Case 4: Scope Expansion Check (Identity Mismatch)
  {
    console.log('  [4] scope expansion check blocks mismatched materialId or taskId...');
    const plan = buildCleanMetadataPersistencePlan({
      candidate: defaultCandidate,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      now: customNow,
    });

    const mockDb = createMockDbClient();

    // Mismatched taskId
    const res1 = await applyCleanMetadataPersistencePlan({
      plan,
      taskId: 'mismatched-task-id',
      materialId: targetMaterialId,
      dbClient: mockDb,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      allowRealApply: true,
    });
    assert.equal(res1.ok, false);
    assert.equal(res1.classification, 'BLOCKED_SCOPE_WOULD_EXPAND');

    // Mismatched materialId
    const res2 = await applyCleanMetadataPersistencePlan({
      plan,
      taskId: targetTaskId,
      materialId: 'mismatched-material-id',
      dbClient: mockDb,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      allowRealApply: true,
    });
    assert.equal(res2.ok, false);
    assert.equal(res2.classification, 'BLOCKED_SCOPE_WOULD_EXPAND');
    assert.equal(mockDb.calls.length, 0);
  }

  // Case 5: DB Target Not Found Check
  {
    console.log('  [5] db target not found blocks missing task or material...');
    const plan = buildCleanMetadataPersistencePlan({
      candidate: defaultCandidate,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      now: customNow,
    });

    const mockDb = createMockDbClient();

    const res = await applyCleanMetadataPersistencePlan({
      plan,
      taskId: targetTaskId,
      materialId: targetMaterialId,
      dbClient: mockDb,
      existingTask: null,
      existingMaterial: defaultExistingMaterial,
      allowRealApply: true,
    });

    assert.equal(res.ok, false);
    assert.equal(res.classification, 'BLOCKED_DB_TARGET_NOT_FOUND');
    assert.equal(mockDb.calls.length, 0);
  }

  // Case 6: Already Applied Noop Check
  {
    console.log('  [6] already applied check stops with ALREADY_APPLIED_NOOP...');
    const plan = buildCleanMetadataPersistencePlan({
      candidate: defaultCandidate,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      now: customNow,
    });

    const existingTaskApplied = {
      id: targetTaskId,
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { jobId: targetJobId, assetVersion: targetVersion },
        },
      },
    };

    const existingMaterialApplied = {
      id: targetMaterialId,
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: targetVersion },
        },
      },
    };

    const mockDb = createMockDbClient();

    const res = await applyCleanMetadataPersistencePlan({
      plan,
      taskId: targetTaskId,
      materialId: targetMaterialId,
      dbClient: mockDb,
      existingTask: existingTaskApplied,
      existingMaterial: existingMaterialApplied,
      allowRealApply: true,
    });

    assert.equal(res.ok, true);
    assert.equal(res.applied, false);
    assert.equal(res.classification, 'ALREADY_APPLIED_NOOP');
    assert.equal(mockDb.calls.length, 0);
  }

  // Case 7: Incompatible Existing Metadata Check
  {
    console.log('  [7] incompatible metadata stops with BLOCKED_EXISTING_TOC_REBUILD_METADATA...');
    const plan = buildCleanMetadataPersistencePlan({
      candidate: defaultCandidate,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      now: customNow,
    });

    const existingTaskDifferent = {
      id: targetTaskId,
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { jobId: 'different-job-id', assetVersion: targetVersion },
        },
      },
    };

    const mockDb = createMockDbClient();

    const res = await applyCleanMetadataPersistencePlan({
      plan,
      taskId: targetTaskId,
      materialId: targetMaterialId,
      dbClient: mockDb,
      existingTask: existingTaskDifferent,
      existingMaterial: defaultExistingMaterial,
      allowRealApply: true,
    });

    assert.equal(res.ok, false);
    assert.equal(res.classification, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
    assert.equal(mockDb.calls.length, 0);
  }

  // Case 8: Patch Scope Violation Check
  {
    console.log('  [8] scope violation check blocks updates outside metadata root...');
    const plan = buildCleanMetadataPersistencePlan({
      candidate: defaultCandidate,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      now: customNow,
    });

    // Artificially pollute the patches with non-metadata keys
    plan.taskPatch.status = 'polluted';

    const mockDb = createMockDbClient();

    const res = await applyCleanMetadataPersistencePlan({
      plan,
      taskId: targetTaskId,
      materialId: targetMaterialId,
      dbClient: mockDb,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      allowRealApply: true,
    });

    assert.equal(res.ok, false);
    assert.equal(res.classification, 'BLOCKED_PATCH_SCOPE_VIOLATION');
    assert.equal(mockDb.calls.length, 0);
  }

  // Case 9: Full Content Prevention Check
  {
    console.log('  [9] full content verification blocks large body arrays or long markdown strings...');

    // Test helper directly first
    assert.equal(hasFullContentInMetadata({ status: 'completed' }), false);
    assert.equal(hasFullContentInMetadata({ metadata: { blocks: [] } }), true);
    assert.equal(hasFullContentInMetadata({ metadata: { cleanServiceJobs: { 'toc-rebuild': { readable_tree: 'a'.repeat(600) } } } }), true);

    const plan = buildCleanMetadataPersistencePlan({
      candidate: defaultCandidate,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      now: customNow,
    });

    // Artificially inject full paragraphs array under metadata clean jobs
    plan.taskPatch.metadata.cleanServiceJobs['toc-rebuild'].flooded_content = {
      bucket: 'eduassets-clean',
      object: 'flooded_content.json',
      blocks: Array(50).fill({ text: 'full content text blocks' }), // Violating extra fields/blocks
    };

    const mockDb = createMockDbClient();

    const res = await applyCleanMetadataPersistencePlan({
      plan,
      taskId: targetTaskId,
      materialId: targetMaterialId,
      dbClient: mockDb,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      allowRealApply: true,
    });

    assert.equal(res.ok, false);
    assert.equal(res.classification, 'BLOCKED_FULL_CONTENT_IN_METADATA');
    assert.equal(mockDb.calls.length, 0);
  }

  // Case 10: Partial Apply Failure (Rollback Forbidden) Check
  {
    console.log('  [10] partial apply failure blocks rollback and reports PARTIAL_DB_APPLY_REQUIRES_LUCEON_REVIEW...');
    const plan = buildCleanMetadataPersistencePlan({
      candidate: defaultCandidate,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      now: customNow,
    });

    const mockDb = createMockDbClient({ taskOk: true, materialOk: false });

    const res = await applyCleanMetadataPersistencePlan({
      plan,
      taskId: targetTaskId,
      materialId: targetMaterialId,
      dbClient: mockDb,
      existingTask: defaultExistingTask,
      existingMaterial: defaultExistingMaterial,
      allowRealApply: true,
    });

    assert.equal(res.ok, false);
    assert.equal(res.applied, true); // Succeeded on task but failed on material -> marked as applied!
    assert.equal(res.operationCount, 2);
    assert.equal(res.classification, 'PARTIAL_DB_APPLY_REQUIRES_LUCEON_REVIEW');

    // Confirm both were called (no rollback was executed)
    assert.equal(mockDb.calls.length, 2);
    assert.equal(mockDb.calls[0].method, 'updateTask');
    assert.equal(mockDb.calls[1].method, 'updateMaterial');
  }

  console.log('All apply-executor smoke cases passed successfully!');
}

runTests().catch((err) => {
  console.error('Smoke tests failed:', err);
  process.exit(1);
});
