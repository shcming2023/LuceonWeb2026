import assert from 'node:assert/strict';
import { buildVerifiedCleanOutputMetadataCandidate } from '../services/cleanservice/metadata-summary.mjs';
import { buildCleanMetadataPersistencePlan } from '../services/cleanservice/metadata-persistence.mjs';

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
    job_id: 'luceon-task-250-rebuild-v2',
    status: 'completed',
    service_name: 'toc-rebuild',
    service_version: '1.0.0',
    protocol_version: 'v1',
    material_id: materialId,
    parse_task_id: 'task-clean-250',
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
      asset: { material_id: '1842780526581841', asset_version: 'v2' },
      job: { job_id: 'luceon-task-250-rebuild-v2', parse_task_id: 'task-clean-250' },
      inputs: [
        {
          bucket: 'eduassets-raw',
          object: 'mineru/1842780526581841/v1/content_list_v2.json',
          sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
          size_bytes: 31543,
        }
      ],
    },
    ...overrides,
  };
}

async function runTests() {
  console.log('=== CleanService Metadata Persistence Smoke ===');

  const customNow = () => '2026-05-22T16:48:20.000Z';

  // Case 1: Standard Success Persistence Plan
  {
    console.log('  [1] standard success persistence planning...');
    const job = mockJob();
    const verification = {
      ok: true,
      cleanState: 'completed',
      errors: [],
      warnings: [],
      unresolvedAnchorCount: 0,
      inputSizeBytes: 31543,
    };

    const candidate = buildVerifiedCleanOutputMetadataCandidate({
      job,
      verification,
      now: customNow,
    });

    const existingTask = {
      id: 'task-clean-250',
      metadata: {
        existingUnrelatedTaskField: 'preserve-me',
        cleanServiceJobs: {
          'another-service': { serviceName: 'another-service', status: 'completed' },
        },
      },
    };

    const existingMaterial = {
      id: '1842780526581841',
      metadata: {
        existingUnrelatedMaterialField: 'preserve-me',
        cleanMaterials: {
          'another-service': { serviceName: 'another-service', latestVersion: 'v1' },
        },
      },
    };

    const plan = buildCleanMetadataPersistencePlan({
      candidate,
      existingTask,
      existingMaterial,
      now: customNow,
    });

    // 基础校验
    assert.equal(plan.ok, true);
    assert.equal(plan.shouldApply, true);
    assert.equal(plan.dryRun, true);
    assert.equal(plan.serviceName, 'toc-rebuild');
    assert.equal(plan.materialId, '1842780526581841');
    assert.equal(plan.parseTaskId, 'task-clean-250');

    // 校验 pre-merge 机制 (不应该破坏原有字段)
    const taskPatch = plan.taskPatch;
    assert.ok(taskPatch);
    assert.equal(taskPatch.metadata.existingUnrelatedTaskField, 'preserve-me');
    assert.ok(taskPatch.metadata.cleanServiceJobs['another-service']);
    assert.equal(taskPatch.metadata.cleanServiceJobs['another-service'].status, 'completed');
    assert.ok(taskPatch.metadata.cleanServiceJobs['toc-rebuild']);
    assert.equal(taskPatch.metadata.cleanServiceJobs['toc-rebuild'].status, 'completed');

    const materialPatch = plan.materialPatch;
    assert.ok(materialPatch);
    assert.equal(materialPatch.metadata.existingUnrelatedMaterialField, 'preserve-me');
    assert.ok(materialPatch.metadata.cleanMaterials['another-service']);
    assert.equal(materialPatch.metadata.cleanMaterials['toc-rebuild'].latestVersion, 'v2');

    // 校验入参未被污染
    assert.equal(existingTask.metadata.cleanServiceJobs['toc-rebuild'], undefined);
    assert.equal(existingMaterial.metadata.cleanMaterials['toc-rebuild'], undefined);

    // 校验 audit
    assert.ok(plan.audit);
    assert.equal(plan.audit.costSource, 'job-stats');
    assert.equal(plan.audit.tokensTotal, 6266);
    assert.equal(plan.audit.cleanState, 'completed');
    assert.equal(plan.audit.timestamp, '2026-05-22T16:48:20.000Z');
  }

  // Case 2: Verification/Candidate Cost Path
  {
    console.log('  [2] verification/candidate cost preservation path...');
    const job = mockJob();
    delete job.stats; // 清空 stats

    const verification = {
      ok: true,
      cleanState: 'completed',
      errors: [],
      warnings: [],
      unresolvedAnchorCount: 0,
      inputSizeBytes: 31543,
      tokensPrompt: 4500,
      tokensCompletion: 50,
      tokensTotal: 4550,
      costCnyEstimated: 0.004,
      costCnyActual: 0.003, // 手工传入 cost 字段
      sourceInput: {
        bucket: 'eduassets-raw',
        object: 'mineru/1842780526581841/v1/content_list_v2.json',
        sha256: 'abc123sha256',
        sizeBytes: 31543,
      },
    };

    const candidate = buildVerifiedCleanOutputMetadataCandidate({
      job,
      verification,
      now: customNow,
    });

    const plan = buildCleanMetadataPersistencePlan({
      candidate,
      now: customNow,
    });

    assert.equal(plan.ok, true);
    assert.equal(plan.shouldApply, true);
    assert.equal(plan.audit.costSource, 'verification/candidate');
    
    const taskSummary = plan.taskPatch.metadata.cleanServiceJobs['toc-rebuild'];
    assert.equal(taskSummary.stats.costCnyActual, 0.003);
    assert.equal(taskSummary.stats.costCnyEstimated, 0.004);
  }

  // Case 3: Cost Unavailable Path
  {
    console.log('  [3] cost unavailable path...');
    const job = mockJob();
    delete job.stats;

    const verification = {
      ok: true,
      cleanState: 'completed',
      errors: [],
      warnings: [],
      unresolvedAnchorCount: 0,
      inputSizeBytes: 31543,
      tokensPrompt: 4500,
      tokensCompletion: 50,
      tokensTotal: 4550,
      sourceInput: {
        bucket: 'eduassets-raw',
        object: 'mineru/1842780526581841/v1/content_list_v2.json',
        sha256: 'abc123sha256',
        sizeBytes: 31543,
      },
    };

    const candidate = buildVerifiedCleanOutputMetadataCandidate({
      job,
      verification,
      now: customNow,
    });

    const plan = buildCleanMetadataPersistencePlan({
      candidate,
      now: customNow,
    });

    assert.equal(plan.ok, true);
    assert.equal(plan.shouldApply, true);
    assert.equal(plan.audit.costSource, 'unavailable');
    
    const taskSummary = plan.taskPatch.metadata.cleanServiceJobs['toc-rebuild'];
    assert.equal(taskSummary.stats.costCnyActual, null);
    assert.equal(taskSummary.stats.costCnyEstimated, null);
  }

  // Case 4: Non-persistable Candidate Gate
  {
    console.log('  [4] non-persistable candidate gate...');
    const candidate = {
      ok: false,
      shouldPersist: false,
      verificationSummary: { errors: ['zero-or-missing-tokens'] },
    };

    const plan = buildCleanMetadataPersistencePlan({
      candidate,
      now: customNow,
    });

    assert.equal(plan.ok, false);
    assert.equal(plan.shouldApply, false);
    assert.equal(plan.taskPatch, null);
    assert.equal(plan.materialPatch, null);
    assert.equal(plan.reason, 'candidate-not-persistable');
    assert.deepEqual(plan.errors, ['zero-or-missing-tokens']);
  }

  // Case 5: Traceability Gate Violations
  {
    console.log('  [5] traceability gate violations (missing fields)...');

    // 5.1 缺失 sourceInput
    {
      const job = mockJob();
      const verification = {
        ok: true,
        cleanState: 'completed',
        errors: [],
        warnings: [],
        unresolvedAnchorCount: 0,
        inputSizeBytes: 31543,
      };

      const candidate = buildVerifiedCleanOutputMetadataCandidate({
        job,
        verification,
        now: customNow,
      });

      // 故意破坏 sourceInput
      delete candidate.verificationSummary.sourceInput;

      const plan = buildCleanMetadataPersistencePlan({
        candidate,
        now: customNow,
      });

      assert.equal(plan.shouldApply, false);
      assert.equal(plan.reason, 'missing-source-input');
    }

    // 5.2 缺失 7 个 artifacts 之一
    const roles = ['flooded_content', 'logic_tree', 'readable_tree', 'skeleton', 'unresolved_anchors', 'metrics', 'provenance'];
    for (const missingRole of roles) {
      const job = mockJob();
      const verification = {
        ok: true,
        cleanState: 'completed',
        errors: [],
        warnings: [],
        unresolvedAnchorCount: 0,
        inputSizeBytes: 31543,
      };

      const candidate = buildVerifiedCleanOutputMetadataCandidate({
        job,
        verification,
        now: customNow,
      });

      // 故意破坏特定 artifact
      delete candidate.metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'].artifacts[missingRole];

      const plan = buildCleanMetadataPersistencePlan({
        candidate,
        now: customNow,
      });

      assert.equal(plan.shouldApply, false);
      assert.equal(plan.reason, `missing-artifact-ref:${missingRole}`);
    }

    // 5.3 缺失 token 总数
    {
      const job = mockJob();
      const verification = {
        ok: true,
        cleanState: 'completed',
        errors: [],
        warnings: [],
        unresolvedAnchorCount: 0,
        inputSizeBytes: 31543,
      };

      const candidate = buildVerifiedCleanOutputMetadataCandidate({
        job,
        verification,
        now: customNow,
      });

      // 故意将 tokensTotal 设为 0
      candidate.metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'].stats.tokensTotal = 0;

      const plan = buildCleanMetadataPersistencePlan({
        candidate,
        now: customNow,
      });

      assert.equal(plan.shouldApply, false);
      assert.equal(plan.reason, 'missing-token-total');
    }

    // 5.4 缺失 taskSummary
    {
      const job = mockJob();
      const verification = {
        ok: true,
        cleanState: 'completed',
        errors: [],
        warnings: [],
        unresolvedAnchorCount: 0,
        inputSizeBytes: 31543,
      };

      const candidate = buildVerifiedCleanOutputMetadataCandidate({
        job,
        verification,
        now: customNow,
      });

      // 故意删除 task summary
      delete candidate.metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'];

      const plan = buildCleanMetadataPersistencePlan({
        candidate,
        now: customNow,
      });

      assert.equal(plan.shouldApply, false);
      assert.equal(plan.reason, 'missing-task-summary');
    }

    // 5.5 缺失 materialSummary
    {
      const job = mockJob();
      const verification = {
        ok: true,
        cleanState: 'completed',
        errors: [],
        warnings: [],
        unresolvedAnchorCount: 0,
        inputSizeBytes: 31543,
      };

      const candidate = buildVerifiedCleanOutputMetadataCandidate({
        job,
        verification,
        now: customNow,
      });

      // 故意删除 material summary
      delete candidate.metadataPatch.materialMetadata.cleanMaterials['toc-rebuild'];

      const plan = buildCleanMetadataPersistencePlan({
        candidate,
        now: customNow,
      });

      assert.equal(plan.shouldApply, false);
      assert.equal(plan.reason, 'missing-material-summary');
    }
  }

  // Case 6: ID-Only Integrity
  {
    console.log('  [6] ID-only integrity check (no full contents in patches)...');
    const job = mockJob();
    const verification = {
      ok: true,
      cleanState: 'completed',
      errors: [],
      warnings: [],
      unresolvedAnchorCount: 0,
      inputSizeBytes: 31543,
    };

    const candidate = buildVerifiedCleanOutputMetadataCandidate({
      job,
      verification,
      now: customNow,
    });

    const plan = buildCleanMetadataPersistencePlan({
      candidate,
      now: customNow,
    });

    const art = plan.taskPatch.metadata.cleanServiceJobs['toc-rebuild'].artifacts.readable_tree;
    const keys = Object.keys(art);
    const allowedKeys = new Set(['bucket', 'object', 'size_bytes', 'content_type', 'sha256']);
    for (const key of keys) {
      assert.ok(allowedKeys.has(key));
    }
  }

  console.log('PASS cleanservice metadata persistence smoke tests (6/6)');
}

runTests().catch(err => {
  console.error(err);
  process.exit(1);
});
