import assert from 'node:assert/strict';
import { verifyCleanServiceOutputArtifacts } from '../services/cleanservice/output-verifier.mjs';

// 构造通用的 ObjectRef 辅助函数
function objectRef(object, sizeBytes = 128) {
  return {
    bucket: 'eduassets-clean',
    object,
    size_bytes: sizeBytes,
    content_type: object.endsWith('.md') ? 'text/markdown' : 'application/json',
    sha256: 'abc123sha256',
  };
}

// 模拟的已完成 job 对象
function mockCompletedJob(overrides = {}) {
  const materialId = overrides.materialId || '1842780526581841';
  const assetVersion = overrides.assetVersion || 'v2';
  return {
    job_id: 'luceon-task-248-rebuild-v2',
    status: 'completed',
    service_name: 'toc-rebuild',
    service_version: '1.0.0',
    protocol_version: 'v1',
    material_id: materialId,
    parse_task_id: 'task-clean-248',
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
    ...overrides,
  };
}

// 内存 Mock Artifact Reader
class FakeArtifactReader {
  constructor(files = {}) {
    this.files = files;
  }

  async readArtifact(role, ref) {
    const key = `${ref.bucket}/${ref.object}`;
    if (this.files[key] !== undefined) {
      return this.files[key];
    }
    throw new Error(`File not found in fake reader: ${key}`);
  }
}

// 通用的 Fixture 数据生成
function generateFixtures(overrides = {}) {
  const flooded = overrides.flooded !== undefined ? overrides.flooded : JSON.stringify([{ id: 1, text: "block 1" }]);
  const logic = overrides.logic !== undefined ? overrides.logic : JSON.stringify({ root: {} });
  const readable = overrides.readable !== undefined ? overrides.readable : "## Title\n\nContent here.";
  const skeleton = overrides.skeleton !== undefined ? overrides.skeleton : JSON.stringify({ nodes: [] });
  const unresolved = overrides.unresolved !== undefined ? overrides.unresolved : JSON.stringify([]);
  const metrics = overrides.metrics !== undefined ? overrides.metrics : JSON.stringify({
    stats: {
      tokens: {
        prompt: 6212,
        completion: 54,
        total: 6266
      }
    },
    cost_cny_estimated: 0.00632,
    cost_cny_actual: 0.0,
  });
  const provenance = overrides.provenance !== undefined ? overrides.provenance : JSON.stringify({
    schema: 'luceon-provenance/v1',
    service: { name: 'toc-rebuild', version: '1.0.0', protocol_version: 'v1' },
    asset: { material_id: '1842780526581841', asset_version: 'v2' },
    job: { job_id: 'luceon-task-248-rebuild-v2', parse_task_id: 'task-clean-248' },
    inputs: [
      {
        bucket: 'eduassets-raw',
        object: 'mineru/1842780526581841/v1/content_list_v2.json',
        sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
        size_bytes: overrides.inputSizeBytes !== undefined ? overrides.inputSizeBytes : 31543,
      }
    ],
  });

  const materialId = overrides.materialId || '1842780526581841';
  const assetVersion = overrides.assetVersion || 'v2';

  return {
    [`eduassets-clean/toc-rebuild/${materialId}/${assetVersion}/flooded_content.json`]: flooded,
    [`eduassets-clean/toc-rebuild/${materialId}/${assetVersion}/logic_tree.json`]: logic,
    [`eduassets-clean/toc-rebuild/${materialId}/${assetVersion}/readable_tree.md`]: readable,
    [`eduassets-clean/toc-rebuild/${materialId}/${assetVersion}/skeleton.json`]: skeleton,
    [`eduassets-clean/toc-rebuild/${materialId}/${assetVersion}/unresolved_anchors.json`]: unresolved,
    [`eduassets-clean/toc-rebuild/${materialId}/${assetVersion}/metrics.json`]: metrics,
    [`eduassets-clean/toc-rebuild/${materialId}/${assetVersion}/provenance.json`]: provenance,
  };
}

async function runTests() {
  console.log('=== CleanService Seven-Artifact Output Verifier Smoke ===');

  const expectedOpts = {
    serviceName: 'toc-rebuild',
    protocolVersion: 'v1',
    materialId: '1842780526581841',
    assetVersion: 'v2',
    jobId: 'luceon-task-248-rebuild-v2',
    rawInput: {
      bucket: 'eduassets-raw',
      object: 'mineru/1842780526581841/v1/content_list_v2.json',
      sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
      sizeBytes: 31543,
    },
  };

  // Case 1: 标准成功样本（Task 245 成功特征：tokens > 0，cost_cny_actual = 0.0，unresolved_anchors = 0）
  {
    console.log('  [1] standard success v2 path verification...');
    const files = generateFixtures();
    const reader = new FakeArtifactReader(files);
    const job = mockCompletedJob();

    const result = await verifyCleanServiceOutputArtifacts(job, {
      artifactReader: reader,
      expected: expectedOpts,
    });

    assert.equal(result.ok, true);
    assert.equal(result.cleanState, 'completed');
    assert.equal(result.errors.length, 0);
    assert.equal(result.unresolvedAnchorCount, 0);
    assert.equal(result.inputSizeBytes, 31543);

    // 强断言：打通真实 verifier -> candidate 链路所需的 metrics / sourceInput 细节
    assert.ok(result.sourceInput);
    assert.equal(result.sourceInput.bucket, 'eduassets-raw');
    assert.equal(result.sourceInput.object, 'mineru/1842780526581841/v1/content_list_v2.json');
    assert.equal(result.sourceInput.sha256, 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db');
    assert.equal(result.sourceInput.sizeBytes, 31543);

    assert.equal(result.tokensTotal, 6266);
    assert.equal(result.tokensPrompt, 6212);
    assert.equal(result.tokensCompletion, 54);
  }

  // Case 2: 部分未解析（unresolved_anchors > 0 -> review-pending-partial）
  {
    console.log('  [2] review-pending-partial path verification...');
    const files = generateFixtures({
      unresolved: JSON.stringify([{ anchor_id: 'anc-1', reason: 'dangling' }]),
    });
    const reader = new FakeArtifactReader(files);
    const job = mockCompletedJob();

    const result = await verifyCleanServiceOutputArtifacts(job, {
      artifactReader: reader,
      expected: expectedOpts,
    });

    assert.equal(result.ok, true);
    assert.equal(result.cleanState, 'review-pending-partial');
    assert.equal(result.errors.length, 0);
    assert.equal(result.unresolvedAnchorCount, 1);
  }

  // Case 3: input size_bytes = 0 债务补偿校验
  {
    console.log('  [3] provenance size_bytes=0 debt compensation...');
    const files = generateFixtures({
      inputSizeBytes: 0,
    });
    const reader = new FakeArtifactReader(files);
    const job = mockCompletedJob();

    const result = await verifyCleanServiceOutputArtifacts(job, {
      artifactReader: reader,
      expected: expectedOpts,
    });

    assert.equal(result.ok, true);
    assert.equal(result.cleanState, 'completed');
    assert.equal(result.warnings.includes('input-size-bytes-zero'), true);
    // 确保返回的 summary 中，inputSizeBytes 已经被 expected.rawInput.sizeBytes 补偿
    assert.equal(result.inputSizeBytes, 31543);
  }

  // Case 4: 零 tokens 拦截验证（Task 242 漏洞防御）
  {
    console.log('  [4] zero tokens protocol-failure blocking...');
    const files = generateFixtures({
      metrics: JSON.stringify({
        stats: { tokens: { total: 0 } },
        cost_cny_estimated: 0.0,
        cost_cny_actual: 0.0,
      }),
    });
    const reader = new FakeArtifactReader(files);
    const job = mockCompletedJob();

    const result = await verifyCleanServiceOutputArtifacts(job, {
      artifactReader: reader,
      expected: expectedOpts,
    });

    assert.equal(result.ok, false);
    assert.equal(result.cleanState, 'protocol-failure');
    assert.equal(result.errors.includes('zero-or-missing-tokens'), true);
  }

  // Case 5: 缺失 tokens 拦截验证
  {
    console.log('  [5] missing tokens in metrics protocol-failure...');
    const files = generateFixtures({
      metrics: JSON.stringify({
        stats: {},
      }),
    });
    const reader = new FakeArtifactReader(files);
    const job = mockCompletedJob();

    const result = await verifyCleanServiceOutputArtifacts(job, {
      artifactReader: reader,
      expected: expectedOpts,
    });

    assert.equal(result.ok, false);
    assert.equal(result.cleanState, 'protocol-failure');
    assert.equal(result.errors.includes('zero-or-missing-tokens'), true);
  }

  // Case 6: 路径 mismatch 拒绝（预期 v2 却返回了 v1 的路径）
  {
    console.log('  [6] asset version path prefix mismatch...');
    const files = generateFixtures({
      materialId: '1842780526581841',
      assetVersion: 'v1', // 构造 v1 的产物
    });
    const reader = new FakeArtifactReader(files);
    // 但 job 宣告的是 v1 的 artifacts
    const job = mockCompletedJob({
      artifacts: {
        flooded_content: objectRef('toc-rebuild/1842780526581841/v1/flooded_content.json'),
        logic_tree: objectRef('toc-rebuild/1842780526581841/v1/logic_tree.json'),
        readable_tree: objectRef('toc-rebuild/1842780526581841/v1/readable_tree.md'),
        skeleton: objectRef('toc-rebuild/1842780526581841/v1/skeleton.json'),
        unresolved_anchors: objectRef('toc-rebuild/1842780526581841/v1/unresolved_anchors.json'),
        metrics: objectRef('toc-rebuild/1842780526581841/v1/metrics.json'),
        provenance: objectRef('toc-rebuild/1842780526581841/v1/provenance.json'),
      },
    });

    // 预期却指定了 v2
    const result = await verifyCleanServiceOutputArtifacts(job, {
      artifactReader: reader,
      expected: expectedOpts, // expected 指定了 assetVersion: 'v2'
    });

    assert.equal(result.ok, false);
    assert.equal(result.cleanState, 'protocol-failure');
    // 应该识别到 path-prefix-mismatch
    assert.equal(result.errors.some(e => e.startsWith('path-prefix-mismatch:')), true);
  }

  // Case 7: 各种格式错误（空 MD、空 flooded 数组、无效 JSON 等）
  {
    console.log('  [7] negative formats (empty markdown, invalid arrays)...');

    // 1. 空 MD 拒绝
    const filesMD = generateFixtures({ readable: '   \n  ' });
    const readerMD = new FakeArtifactReader(filesMD);
    const resultMD = await verifyCleanServiceOutputArtifacts(mockCompletedJob(), {
      artifactReader: readerMD,
      expected: expectedOpts,
    });
    assert.equal(resultMD.ok, false);
    assert.equal(resultMD.errors.includes('empty-readable_tree'), true);

    // 2. 空 flooded 数组拒绝
    const filesFlooded = generateFixtures({ flooded: '[]' });
    const readerFlooded = new FakeArtifactReader(filesFlooded);
    const resultFlooded = await verifyCleanServiceOutputArtifacts(mockCompletedJob(), {
      artifactReader: readerFlooded,
      expected: expectedOpts,
    });
    assert.equal(resultFlooded.ok, false);
    assert.equal(resultFlooded.errors.includes('invalid-flooded_content-array'), true);

    // 3. 非 JSON flooded 拒绝
    const filesJSON = generateFixtures({ flooded: 'this-is-not-json' });
    const readerJSON = new FakeArtifactReader(filesJSON);
    const resultJSON = await verifyCleanServiceOutputArtifacts(mockCompletedJob(), {
      artifactReader: readerJSON,
      expected: expectedOpts,
    });
    assert.equal(resultJSON.ok, false);
    assert.equal(resultJSON.errors.includes('invalid-flooded_content-json'), true);
  }

  // Case 8: 缺失 Object 拒绝
  {
    console.log('  [8] missing physical object in bucket...');
    const files = generateFixtures();
    // 故意删掉 metrics.json
    delete files['eduassets-clean/toc-rebuild/1842780526581841/v2/metrics.json'];
    const reader = new FakeArtifactReader(files);
    const job = mockCompletedJob();

    const result = await verifyCleanServiceOutputArtifacts(job, {
      artifactReader: reader,
      expected: expectedOpts,
    });

    assert.equal(result.ok, false);
    assert.equal(result.cleanState, 'protocol-failure');
    assert.equal(result.errors.includes('missing-object:metrics'), true);
  }

  // Case 9: bounded provenance job_id -probe compatibility
  {
    console.log('  [9] bounded provenance job_id -probe suffix policy...');
    const probeProvenance = JSON.stringify({
      schema: 'luceon-provenance/v1',
      service: { name: 'toc-rebuild', version: '1.0.0', protocol_version: 'v1' },
      asset: { material_id: '1842780526581841', asset_version: 'v2' },
      job: { job_id: 'luceon-task-248-rebuild-v2-probe', parse_task_id: 'task-clean-248' },
      inputs: [
        {
          bucket: 'eduassets-raw',
          object: 'mineru/1842780526581841/v1/content_list_v2.json',
          sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
          size_bytes: 31543,
        }
      ],
    });

    const files = generateFixtures({ provenance: probeProvenance });
    const reader = new FakeArtifactReader(files);
    const result = await verifyCleanServiceOutputArtifacts(mockCompletedJob(), {
      artifactReader: reader,
      expected: expectedOpts,
    });

    assert.equal(result.ok, true);
    assert.equal(result.canonicalJobId, 'luceon-task-248-rebuild-v2');
    assert.equal(result.provenanceJobId, 'luceon-task-248-rebuild-v2-probe');
    assert.equal(result.provenanceJobIdPolicy, 'accepted-probe-suffix');
    assert.equal(result.warnings.includes('provenance-job-id-probe-suffix-accepted'), true);

    const unrelatedProvenance = JSON.stringify({
      ...JSON.parse(probeProvenance),
      job: { job_id: 'different-job-id-probe', parse_task_id: 'task-clean-248' },
    });
    const badResult = await verifyCleanServiceOutputArtifacts(mockCompletedJob(), {
      artifactReader: new FakeArtifactReader(generateFixtures({ provenance: unrelatedProvenance })),
      expected: expectedOpts,
    });
    assert.equal(badResult.ok, false);
    assert.equal(badResult.errors.includes('job-id-mismatch'), true);
  }

  console.log('PASS cleanservice seven-artifact output verifier smoke tests (9/9)');
}

runTests().catch(err => {
  console.error(err);
  process.exit(1);
});
