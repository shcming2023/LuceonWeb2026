import assert from 'node:assert/strict';
import { buildVerifiedCleanOutputMetadataCandidate } from '../services/cleanservice/metadata-summary.mjs';

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
    job_id: 'luceon-task-249-rebuild-v2',
    status: 'completed',
    service_name: 'toc-rebuild',
    service_version: '1.0.0',
    protocol_version: 'v1',
    material_id: materialId,
    parse_task_id: 'task-clean-249',
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
      job: { job_id: 'luceon-task-249-rebuild-v2', parse_task_id: 'task-clean-249' },
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
  console.log('=== CleanService Output Ingestion Candidate Smoke ===');

  const customNow = () => '2026-05-22T15:09:02.000Z';

  // Case 1: 标准成功元数据候选构建器 (Task 245-shaped verified result)
  {
    console.log('  [1] standard success path candidate builder...');
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

    assert.equal(candidate.ok, true);
    assert.equal(candidate.shouldPersist, true);
    assert.equal(candidate.serviceName, 'toc-rebuild');
    assert.equal(candidate.materialId, '1842780526581841');
    assert.equal(candidate.assetVersion, 'v2');
    assert.equal(candidate.cleanState, 'completed');

    // 检查 metadataPatch 存在
    assert.ok(candidate.metadataPatch);
    const taskSummary = candidate.metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'];
    const materialSummary = candidate.metadataPatch.materialMetadata.cleanMaterials['toc-rebuild'];

    assert.ok(taskSummary);
    assert.ok(materialSummary);

    // 确保 values 准确
    assert.equal(taskSummary.serviceName, 'toc-rebuild');
    assert.equal(taskSummary.status, 'completed');
    assert.equal(taskSummary.stats.tokensTotal, 6266);
    assert.equal(taskSummary.stats.tokensPrompt, 6212);
    assert.equal(taskSummary.stats.tokensCompletion, 54);
    assert.equal(taskSummary.stats.costCnyActual, 0.0);
    assert.equal(taskSummary.updatedAt, '2026-05-22T15:09:02.000Z');

    // 确保 material 拥有 output prefix 和 provenance object name 以及 tokensPrompt/Completion
    assert.equal(materialSummary.prefix, 'toc-rebuild/1842780526581841/v2/');
    assert.equal(materialSummary.provenanceObjectName, 'toc-rebuild/1842780526581841/v2/provenance.json');
    assert.equal(materialSummary.stats.tokensPrompt, 6212);
    assert.equal(materialSummary.stats.tokensCompletion, 54);
    assert.equal(materialSummary.updatedAt, '2026-05-22T15:09:02.000Z');

    // 确保 verificationSummary 与 sourceInput 存在
    const verif = candidate.verificationSummary;
    assert.equal(verif.ok, true);
    assert.equal(verif.cleanState, 'completed');
    assert.equal(verif.inputSizeBytes, 31543);
    assert.ok(verif.sourceInput);
    assert.equal(verif.sourceInput.bucket, 'eduassets-raw');
    assert.equal(verif.sourceInput.object, 'mineru/1842780526581841/v1/content_list_v2.json');
    assert.equal(verif.sourceInput.sha256, 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db');
    assert.equal(verif.sourceInput.sizeBytes, 31543);
  }

  // Case 2: 部分未解析锚点 (unresolved anchors > 0)
  {
    console.log('  [2] review-pending-partial path candidate...');
    const job = mockJob({
      stats: {
        tokensTotal: 6266,
        costCnyActual: 0.0,
        unresolved_anchor_count: 3,
      }
    });
    const verification = {
      ok: true,
      cleanState: 'review-pending-partial',
      errors: [],
      warnings: [],
      unresolvedAnchorCount: 3,
      inputSizeBytes: 31543,
    };

    const candidate = buildVerifiedCleanOutputMetadataCandidate({
      job,
      verification,
      now: customNow,
    });

    assert.equal(candidate.ok, true);
    assert.equal(candidate.shouldPersist, true);
    assert.equal(candidate.cleanState, 'review-pending-partial');

    const taskSummary = candidate.metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'];
    assert.equal(taskSummary.status, 'review-pending-partial');
    assert.equal(taskSummary.stats.unresolvedAnchorCount, 3);
  }

  // Case 3: 包含警告与 size_bytes=0 补偿
  {
    console.log('  [3] warning support and input size_bytes=0 compensation...');
    const job = mockJob();
    const verification = {
      ok: true,
      cleanState: 'completed',
      errors: [],
      warnings: ['input-size-bytes-zero'],
      unresolvedAnchorCount: 0,
      inputSizeBytes: 31543, // 补偿后的 sizeBytes
    };

    const candidate = buildVerifiedCleanOutputMetadataCandidate({
      job,
      verification,
      now: customNow,
    });

    assert.equal(candidate.ok, true);
    assert.equal(candidate.shouldPersist, true);
    assert.deepEqual(candidate.verificationSummary.warnings, ['input-size-bytes-zero']);

    const taskSummary = candidate.metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'];
    assert.deepEqual(taskSummary.warnings, ['input-size-bytes-zero']);
    assert.equal(candidate.verificationSummary.sourceInput.sizeBytes, 31543);
  }

  // Case 4: 校验失败 (zero/missing tokens) 返回 non-persistable candidate
  {
    console.log('  [4] verification failure candidate blocking...');
    const job = mockJob();
    const verification = {
      ok: false,
      cleanState: 'protocol-failure',
      errors: ['zero-or-missing-tokens'],
      warnings: [],
      unresolvedAnchorCount: 0,
      inputSizeBytes: 31543,
    };

    const candidate = buildVerifiedCleanOutputMetadataCandidate({
      job,
      verification,
      now: customNow,
    });

    assert.equal(candidate.ok, false);
    assert.equal(candidate.shouldPersist, false);
    assert.equal(candidate.cleanState, 'protocol-failure');
    assert.equal(candidate.metadataPatch, null);

    assert.ok(candidate.verificationSummary);
    assert.deepEqual(candidate.verificationSummary.errors, ['zero-or-missing-tokens']);
  }

  // Case 5: 真实形状测试（无 inline job.provenance，完全从 verification.sourceInput 中读取）
  {
    console.log('  [5] real-shape job with no inline provenance, using verification.sourceInput...');
    const rawJob = mockJob();
    delete rawJob.provenance; // 完全清除 inline 属性

    const verification = {
      ok: true,
      cleanState: 'completed',
      errors: [],
      warnings: [],
      unresolvedAnchorCount: 0,
      inputSizeBytes: 31543,
      tokensPrompt: 6212,
      tokensCompletion: 54,
      tokensTotal: 6266,
      sourceInput: {
        bucket: 'eduassets-raw',
        object: 'mineru/1842780526581841/v1/content_list_v2.json',
        sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
        sizeBytes: 31543,
      },
    };

    const candidate = buildVerifiedCleanOutputMetadataCandidate({
      job: rawJob,
      verification,
      now: customNow,
    });

    assert.equal(candidate.ok, true);
    assert.equal(candidate.shouldPersist, true);
    assert.equal(candidate.cleanState, 'completed');

    const verif = candidate.verificationSummary;
    assert.equal(verif.ok, true);
    assert.ok(verif.sourceInput);
    assert.equal(verif.sourceInput.bucket, 'eduassets-raw');
    assert.equal(verif.sourceInput.object, 'mineru/1842780526581841/v1/content_list_v2.json');
    assert.equal(verif.sourceInput.sha256, 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db');
    assert.equal(verif.sourceInput.sizeBytes, 31543);

    const taskSummary = candidate.metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'];
    assert.equal(taskSummary.stats.tokensPrompt, 6212);
    assert.equal(taskSummary.stats.tokensCompletion, 54);
    assert.equal(taskSummary.stats.tokensTotal, 6266);
  }

  // Case 6: 缺口阻断测试（ok=true，但是由于无 job.provenance 且 verification 无 sourceInput，导致 Traceability 缺失而触发阻断）
  {
    console.log('  [6] verifier contract gap detection (missing traceability elements triggers BLOCKED_VERIFIER_CONTRACT_GAP)...');
    const rawJob = mockJob();
    delete rawJob.provenance; // 完全清除 inline 属性

    const verification = {
      ok: true,
      cleanState: 'completed',
      errors: [],
      warnings: [],
      unresolvedAnchorCount: 0,
      inputSizeBytes: 31543,
    };

    const candidate = buildVerifiedCleanOutputMetadataCandidate({
      job: rawJob,
      verification,
      now: customNow,
    });

    assert.equal(candidate.ok, false);
    assert.equal(candidate.shouldPersist, false);
    assert.equal(candidate.cleanState, 'protocol-failure');
    assert.equal(candidate.metadataPatch, null);

    const verif = candidate.verificationSummary;
    assert.equal(verif.ok, false);
    assert.equal(verif.cleanState, 'protocol-failure');
    assert.ok(verif.errors.includes('BLOCKED_VERIFIER_CONTRACT_GAP'));
  }

  console.log('PASS cleanservice output ingestion candidate smoke tests (6/6)');
}

runTests().catch(err => {
  console.error(err);
  process.exit(1);
});
