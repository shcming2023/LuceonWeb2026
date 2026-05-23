import assert from 'node:assert/strict';
import { runCleanServiceTocRebuildOnce } from '../services/cleanservice/orchestration-runner.mjs';
import { buildCleanMetadataPersistencePlan } from '../services/cleanservice/metadata-persistence.mjs';

// Helper to construct ObjectRef
function objectRef(object, sizeBytes = 128) {
  return {
    bucket: 'eduassets-clean',
    object,
    size_bytes: sizeBytes,
    content_type: object.endsWith('.md') ? 'text/markdown' : 'application/json',
    sha256: 'abc123sha256',
  };
}

// Mock completed job
function mockCompletedJob(overrides = {}) {
  const materialId = overrides.materialId || '1842780526581841';
  const assetVersion = overrides.assetVersion || 'v2';
  return {
    job_id: overrides.jobId || `luceon-task-clean-123-toc-rebuild-${assetVersion}`,
    status: 'completed',
    service_name: 'toc-rebuild',
    service_version: '1.0.0',
    protocol_version: 'v1',
    material_id: materialId,
    parse_task_id: 'task-clean-123',
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

// Memory Mock Artifact Reader
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

// Generate test fixtures
function generateFixtures(overrides = {}) {
  const materialId = overrides.materialId || '1842780526581841';
  const assetVersion = overrides.assetVersion || 'v2';
  const jobId = overrides.jobId || `luceon-task-clean-123-toc-rebuild-${assetVersion}`;

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
    asset: { material_id: materialId, asset_version: assetVersion },
    job: { job_id: jobId, parse_task_id: 'task-clean-123' },
    inputs: [
      {
        bucket: 'eduassets-raw',
        object: `mineru/${materialId}/v1/content_list_v2.json`,
        sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
        size_bytes: overrides.inputSizeBytes !== undefined ? overrides.inputSizeBytes : 31543,
      }
    ],
  });

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

// Generate base task/material records
function makeBaseTask(overrides = {}) {
  return {
    id: 'task-clean-123',
    materialId: '1842780526581841',
    state: 'completed',
    metadata: {
      mineruStatus: 'completed',
      rawMaterial: {
        version: 'v1',
        mineru: {
          contentListV2: {
            bucket: 'eduassets-raw',
            object: 'mineru/1842780526581841/v1/content_list_v2.json',
            sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
          }
        }
      },
      ...overrides.metadata,
    },
    ...overrides,
  };
}

function makeBaseMaterial(overrides = {}) {
  return {
    id: '1842780526581841',
    status: 'reviewing',
    metadata: {
      ...overrides.metadata,
    },
    ...overrides,
  };
}

function makeBaseConfig(overrides = {}) {
  return {
    enabled: true,
    serviceName: 'toc-rebuild',
    storageEndpoint: 'minio:9000',
    storageUseSsl: false,
    submittedBy: 'luceon2026/cleanservice-worker',
    costPolicy: {
      hardLimitCny: 8,
    },
    ...overrides,
  };
}

async function runTests() {
  console.log('=== CleanService Minimal Orchestration Runner Smoke Tests ===');

  // Test 1: disabled config returns `disabled-noop` and performs zero calls
  {
    console.log('  [1] Testing disabled config...');
    const task = makeBaseTask();
    const material = makeBaseMaterial();
    const config = makeBaseConfig({ enabled: false });

    // Mock dependencies that throw error if called
    const failFn = () => { throw new Error('Should not be called'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
      artifactReader: { readArtifact: failFn },
      dbClient: { updateTask: failFn, updateMaterial: failFn },
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, true);
    assert.equal(result.status, 'disabled-noop');
    assert.equal(result.classification, 'disabled-noop');
  }

  // Test 2: already-applied task/material metadata returns `ALREADY_APPLIED_NOOP` and performs zero submit/query/verify/apply calls
  {
    console.log('  [2] Testing already-applied metadata...');
    const jobId = 'luceon-task-clean-123-toc-rebuild-v2';
    const assetVersion = 'v2';

    const task = makeBaseTask({
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { jobId, assetVersion, cleanState: 'review-pending-partial' },
        },
      },
    });
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: assetVersion },
        },
      },
    });
    const config = makeBaseConfig();

    const failFn = () => { throw new Error('Should not be called'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
      artifactReader: { readArtifact: failFn },
      dbClient: { updateTask: failFn, updateMaterial: failFn },
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, true);
    assert.equal(result.status, 'ALREADY_APPLIED_NOOP');
    assert.equal(result.classification, 'ALREADY_APPLIED_NOOP');
    assert.equal(result.jobId, jobId);
    assert.equal(result.assetVersion, assetVersion);
  }

  // Test 3: happy-path mock completed job runs through verify -> candidate -> plan -> dry-run apply and returns a completed dry-run result
  {
    console.log('  [3] Testing happy-path dry-run orchestration...');
    const task = makeBaseTask();
    const material = makeBaseMaterial();
    const config = makeBaseConfig();

    const files = generateFixtures({ assetVersion: 'v1' });
    const reader = new FakeArtifactReader(files);

    const deps = {
      submitJob: async (req) => {
        return { ok: true, job: { job_id: req.job_id, status: 'submitted' } };
      },
      queryJob: async (jobId) => {
        return { ok: true, job: mockCompletedJob({ jobId, assetVersion: 'v1' }) };
      },
      artifactReader: reader,
      dbClient: {
        updateTask: async () => { throw new Error('DB writes forbidden during dry-run'); },
        updateMaterial: async () => { throw new Error('DB writes forbidden during dry-run'); },
      },
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });

    console.log('Test 3 result:', result);
    assert.equal(result.ok, true);
    assert.equal(result.status, 'DRY_RUN_SUCCESS');
    assert.equal(result.classification, 'DRY_RUN_SUCCESS');
    assert.equal(result.jobId, 'luceon-task-clean-123-toc-rebuild-v1');
    assert.equal(result.materialId, '1842780526581841');
    assert.equal(result.taskId, 'task-clean-123');
    assert.equal(result.assetVersion, 'v1');
    assert.equal(result.dryRun, true);
    assert.ok(result.audit);
    assert.equal(result.audit.cleanState, 'completed');
    assert.equal(result.audit.tokensTotal, 6266);
    assert.ok(result.verificationSummary);
    assert.equal(result.verificationSummary.ok, true);
    assert.equal(result.verificationSummary.cleanState, 'completed');
  }

  // Test 4: completed job with verifier failure returns `PROTOCOL_FAILURE` and performs no apply
  {
    console.log('  [4] Testing verifier failure blocking...');
    const task = makeBaseTask();
    const material = makeBaseMaterial();
    const config = makeBaseConfig();

    // Setup zero token metrics in metrics.json to trigger verifier failure
    const files = generateFixtures({
      assetVersion: 'v1',
      metrics: JSON.stringify({ stats: { tokens: { total: 0 } } })
    });
    const reader = new FakeArtifactReader(files);

    let applyCalled = false;
    const deps = {
      submitJob: async (req) => {
        return { ok: true, job: { job_id: req.job_id, status: 'submitted' } };
      },
      queryJob: async (jobId) => {
        return { ok: true, job: mockCompletedJob({ jobId, assetVersion: 'v1' }) };
      },
      artifactReader: reader,
      applyCleanMetadataPersistencePlan: async () => {
        applyCalled = true;
        return { ok: false };
      },
      dbClient: {},
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });

    assert.equal(result.ok, false);
    // Verifier zero token error will fall back to protocol-failure
    assert.equal(result.status, 'protocol-failure');
    assert.equal(result.classification, 'protocol-failure');
    assert.equal(applyCalled, false, 'Persistence apply executor should not be called');
  }

  // Test 5: dispatch failure returns a bounded dispatch failure and performs no verify or apply
  {
    console.log('  [5] Testing dispatch failure blocking...');
    const task = makeBaseTask();
    const material = makeBaseMaterial();
    const config = makeBaseConfig();

    let queryCalled = false;
    let applyCalled = false;
    const deps = {
      submitJob: async (req) => {
        return { ok: false, job: { error: 'Mineru2Table service down' } };
      },
      queryJob: async () => {
        queryCalled = true;
        return { ok: false };
      },
      artifactReader: { readArtifact: async () => { throw new Error('Not called'); } },
      applyCleanMetadataPersistencePlan: async () => {
        applyCalled = true;
        return { ok: false };
      },
      dbClient: {},
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });

    assert.equal(result.ok, false);
    assert.equal(result.status, 'DISPATCH_FAILURE');
    assert.equal(result.classification, 'DISPATCH_FAILURE');
    assert.equal(result.error, 'Mineru2Table service down');
    assert.equal(queryCalled, false, 'Query should not be called on dispatch failure');
    assert.equal(applyCalled, false, 'Persistence apply should not be called on dispatch failure');
  }

  // Test 6: incompatible existing `toc-rebuild` metadata blocks before submit
  {
    console.log('  [6] Testing incompatible existing metadata blocking...');
    // Existing task has different jobId
    const task = makeBaseTask({
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { jobId: 'luceon-old-job-id', assetVersion: 'v1' },
        },
      },
    });
    const material = makeBaseMaterial();
    const config = makeBaseConfig();

    const failFn = () => { throw new Error('Should not be called'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
      artifactReader: { readArtifact: failFn },
      dbClient: { updateTask: failFn, updateMaterial: failFn },
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });

    assert.equal(result.ok, false);
    assert.equal(result.status, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
    assert.equal(result.classification, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
  }

  // Test 7: no dependency receives or emits reset/cleanup/null metadata behavior
  {
    console.log('  [7] Testing zero reset/cleanup behavior in happy-path persistence plan...');
    const task = makeBaseTask();
    const material = makeBaseMaterial();
    const config = makeBaseConfig();

    const files = generateFixtures({ assetVersion: 'v1' });
    const reader = new FakeArtifactReader(files);

    let planObject = null;
    const deps = {
      submitJob: async (req) => {
        return { ok: true, job: { job_id: req.job_id, status: 'submitted' } };
      },
      queryJob: async (jobId) => {
        return { ok: true, job: mockCompletedJob({ jobId, assetVersion: 'v1' }) };
      },
      artifactReader: reader,
      buildCleanMetadataPersistencePlan: (opts) => {
        const { buildCleanMetadataPersistencePlan: realPlanner } = opts.deps || {};
        // Use standard planner or import it
        // We will capture the actual planner output
        const plan = realPlanner ? realPlanner(opts) : buildCleanMetadataPersistencePlan(opts);
        planObject = plan;
        return plan;
      },
      dbClient: {},
    };

    // We can directly require/import the module's real planner if not injected.
    // Let's run the happy path to grab the persistence plan object.
    await runCleanServiceTocRebuildOnce({ task, material, config, deps });

    assert.ok(planObject);
    assert.equal(planObject.ok, true);

    const planStr = JSON.stringify(planObject);
    // Enforce that NO reset/cleanup/rollback keys or null metadata assignments exist
    assert.equal(planStr.includes('"reset"'), false, 'Plan must not contain reset');
    assert.equal(planStr.includes('"cleanup"'), false, 'Plan must not contain cleanup');
    assert.equal(planStr.includes('"rollback"'), false, 'Plan must not contain rollback');
    assert.equal(planStr.includes('"clear"'), false, 'Plan must not contain clear');
    assert.equal(planStr.includes('"nullify"'), false, 'Plan must not contain nullify');
    assert.equal(planStr.includes('"truncate"'), false, 'Plan must not contain truncate');
    assert.equal(planStr.includes('"delete"'), false, 'Plan must not contain delete');

    // Ensure we do not assign null to key metadata branches
    assert.notEqual(planObject.taskPatch?.metadata?.cleanServiceJobs?.['toc-rebuild'], null);
    assert.notEqual(planObject.materialPatch?.metadata?.cleanMaterials?.['toc-rebuild'], null);
  }

  // Test 8: no result contains full artifact content keys such as `blocks`, `paragraphs`, `nodes`, `children`, or large markdown/json bodies
  {
    console.log('  [8] Testing output filtering of heavy parsed textual content...');
    const task = makeBaseTask();
    const material = makeBaseMaterial();
    const config = makeBaseConfig();

    const files = generateFixtures({ assetVersion: 'v1' });
    const reader = new FakeArtifactReader(files);

    const deps = {
      submitJob: async (req) => {
        return { ok: true, job: { job_id: req.job_id, status: 'submitted' } };
      },
      queryJob: async (jobId) => {
        // Mock a job that includes raw large data in some custom properties, just in case
        return {
          ok: true,
          job: mockCompletedJob({
            jobId,
            assetVersion: 'v1',
            rawTextContent: 'x'.repeat(2000),
            parsedBlocks: [{ id: 1, text: 'some text' }]
          })
        };
      },
      artifactReader: reader,
      dbClient: {},
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    const resultStr = JSON.stringify(result);

    // Enforce strict bounded result shape check
    assert.equal(resultStr.includes('"blocks"'), false, 'Result must filter out blocks key');
    assert.equal(resultStr.includes('"paragraphs"'), false, 'Result must filter out paragraphs key');
    assert.equal(resultStr.includes('"nodes"'), false, 'Result must filter out nodes key');
    assert.equal(resultStr.includes('"children"'), false, 'Result must filter out children key');
    assert.equal(resultStr.includes('parsedBlocks'), false, 'Result must filter out parsedBlocks');
    assert.equal(resultStr.includes('rawTextContent'), false, 'Result must filter out heavy textual strings');
    assert.ok(resultStr.length < 2000, 'Result size should be bounded and lightweight');
  }

  // Test 9: in-progress job status (e.g. processing) returns `ORCHESTRATION_IN_PROGRESS` and performs zero verify/apply
  {
    console.log('  [9] Testing in-progress job status early return...');
    const task = makeBaseTask();
    const material = makeBaseMaterial();
    const config = makeBaseConfig();

    let verifyCalled = false;
    let applyCalled = false;

    const deps = {
      submitJob: async (req) => {
        return { ok: true, job: { job_id: req.job_id, status: 'submitted' } };
      },
      queryJob: async (jobId) => {
        return { ok: true, job: { job_id: jobId, status: 'processing' } };
      },
      verifyCleanServiceOutputArtifacts: async () => {
        verifyCalled = true;
        return { ok: true };
      },
      applyCleanMetadataPersistencePlan: async () => {
        applyCalled = true;
        return { ok: true };
      },
      dbClient: {},
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, true);
    assert.equal(result.status, 'ORCHESTRATION_IN_PROGRESS');
    assert.equal(result.classification, 'ORCHESTRATION_IN_PROGRESS');
    assert.equal(verifyCalled, false, 'Verifier must not be called for in-progress status');
    assert.equal(applyCalled, false, 'Apply must not be called for in-progress status');
  }

  // Test 10: unknown job status returns `UNSUPPORTED_STATUS` and performs zero verify/apply
  {
    console.log('  [10] Testing unknown/unsupported job status early return...');
    const task = makeBaseTask();
    const material = makeBaseMaterial();
    const config = makeBaseConfig();

    let verifyCalled = false;

    const deps = {
      submitJob: async (req) => {
        return { ok: true, job: { job_id: req.job_id, status: 'submitted' } };
      },
      queryJob: async (jobId) => {
        return { ok: true, job: { job_id: jobId, status: 'unknown_xyz_status' } };
      },
      verifyCleanServiceOutputArtifacts: async () => {
        verifyCalled = true;
        return { ok: true };
      },
      dbClient: {},
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, false);
    assert.equal(result.status, 'UNSUPPORTED_STATUS');
    assert.equal(result.classification, 'UNSUPPORTED_STATUS');
    assert.equal(verifyCalled, false, 'Verifier must not be called for unsupported status');
  }

  // Test 11: expected raw input hash and size are dynamically propagated without sample hardcoding
  {
    console.log('  [11] Testing dynamic raw input propagation without hardcoding...');
    const customHash = 'my-custom-test-hash-sha256';
    const customSize = 987654;

    const task = makeBaseTask({
      metadata: {
        rawMaterial: {
          version: 'v1',
          mineru: {
            contentListV2: {
              bucket: 'eduassets-raw',
              object: 'mineru/1842780526581841/v1/content_list_v2.json',
              sha256: customHash,
              size_bytes: customSize,
            }
          }
        }
      }
    });

    const material = makeBaseMaterial();
    const config = makeBaseConfig();

    let capturedExpected = null;

    const deps = {
      submitJob: async (req) => {
        return { ok: true, job: { job_id: req.job_id, status: 'submitted' } };
      },
      queryJob: async (jobId) => {
        return { ok: true, job: mockCompletedJob({ jobId, assetVersion: 'v1' }) };
      },
      verifyCleanServiceOutputArtifacts: async (job, opts) => {
        capturedExpected = opts.expected;
        // Return protocol-failure to abort further candidate/apply steps cleanly
        return { ok: false, cleanState: 'protocol-failure', errors: ['aborted-for-assertion'] };
      },
      artifactReader: new FakeArtifactReader(generateFixtures({ assetVersion: 'v1' })),
      dbClient: {},
    };

    await runCleanServiceTocRebuildOnce({ task, material, config, deps });

    assert.ok(capturedExpected);
    assert.ok(capturedExpected.rawInput);
    assert.equal(capturedExpected.rawInput.bucket, 'eduassets-raw');
    assert.equal(capturedExpected.rawInput.object, 'mineru/1842780526581841/v1/content_list_v2.json');
    assert.equal(capturedExpected.rawInput.sha256, customHash);
    assert.equal(capturedExpected.rawInput.sizeBytes, customSize, 'sizeBytes must propagate customSize instead of hardcoded 31543');
  }

  // Test 12: aligned completed task and material metadata returns `CURRENT_CLEAN_MATERIAL_NOOP` and performs zero dependency calls
  {
    console.log('  [12] Testing CURRENT_CLEAN_MATERIAL_NOOP positive aligned path...');
    const jobId = 'luceon-task-clean-123-toc-rebuild-v2';
    const assetVersion = 'v2';

    const task = makeBaseTask({
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { jobId, assetVersion, status: 'completed' },
        },
      },
    });
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: assetVersion, status: 'completed' },
        },
      },
    });
    const config = makeBaseConfig();

    const failFn = () => { throw new Error('Dependency should not be called during current-state noop preflight'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
      verifyCleanServiceOutputArtifacts: failFn,
      buildVerifiedCleanOutputMetadataCandidate: failFn,
      buildCleanMetadataPersistencePlan: failFn,
      applyCleanMetadataPersistencePlan: failFn,
      dbClient: { updateTask: failFn, updateMaterial: failFn },
      artifactReader: { readArtifact: failFn },
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, true);
    assert.equal(result.status, 'CURRENT_CLEAN_MATERIAL_NOOP');
    assert.equal(result.classification, 'CURRENT_CLEAN_MATERIAL_NOOP');
    assert.equal(result.materialId, material.id);
    assert.equal(result.taskId, task.id);
    assert.equal(result.assetVersion, assetVersion);
    assert.equal(result.jobId, jobId);
    assert.equal(result.cleanState, 'completed');
  }

  // Test 13: misaligned metadata (different assetVersion) does not return noop and stays blocked
  {
    console.log('  [13] Testing mismatched assetVersion blocking...');
    const task = makeBaseTask({
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { jobId: 'luceon-task-clean-123-toc-rebuild-v2', assetVersion: 'v2', status: 'completed' },
        },
      },
    });
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: 'v1', status: 'completed' }, // mismatched: v1 !== v2
        },
      },
    });
    const config = makeBaseConfig();

    const failFn = () => { throw new Error('Should not be called'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, false);
    assert.equal(result.status, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
  }

  // Test 14: non-completed existing task status does not return noop and stays blocked
  {
    console.log('  [14] Testing non-completed task status blocking...');
    const task = makeBaseTask({
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { jobId: 'luceon-task-clean-123-toc-rebuild-v2', assetVersion: 'v2', status: 'failed' }, // failed
        },
      },
    });
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: 'v2', status: 'completed' },
        },
      },
    });
    const config = makeBaseConfig();

    const failFn = () => { throw new Error('Should not be called'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, false);
    assert.equal(result.status, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
  }

  // Test 15: missing jobId in task metadata does not return noop and stays blocked
  {
    console.log('  [15] Testing missing jobId blocking...');
    const task = makeBaseTask({
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { assetVersion: 'v2', status: 'completed' }, // missing jobId
        },
      },
    });
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: 'v2', status: 'completed' },
        },
      },
    });
    const config = makeBaseConfig();

    const failFn = () => { throw new Error('Should not be called'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, false);
    assert.equal(result.status, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
  }

  // Test 16: missing task metadata (single-sided material-only exists) does not return noop and stays blocked
  {
    console.log('  [16] Testing one-sided metadata blocking...');
    const task = makeBaseTask(); // missing cleanServiceJobs
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: 'v2', status: 'completed' },
        },
      },
    });
    const config = makeBaseConfig();

    const failFn = () => { throw new Error('Should not be called'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, false);
    assert.equal(result.status, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
  }

  // Test 17: positive rerun intent + reason bypasses noop and proceeds to mock dry-run with v3
  {
    console.log('  [17] Testing CURRENT_CLEAN_MATERIAL_NOOP bypass on create-new-version rerun...');
    const prevJobId = 'luceon-task-clean-123-toc-rebuild-v2';
    const prevAssetVersion = 'v2';

    const task = makeBaseTask({
      metadata: {
        ...makeBaseTask().metadata,
        cleanServiceJobs: {
          'toc-rebuild': { jobId: prevJobId, assetVersion: prevAssetVersion, status: 'completed' },
        },
      },
    });
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: prevAssetVersion, status: 'completed' },
        },
      },
    });

    const config = makeBaseConfig({
      intent: 'create-new-version',
      newVersionReason: 'operator-requested-rerun',
    });

    const files = generateFixtures({ assetVersion: 'v3' });
    const reader = new FakeArtifactReader(files);

    const deps = {
      submitJob: async (req) => {
        return { ok: true, job: { job_id: req.job_id, status: 'submitted' } };
      },
      queryJob: async (jobId) => {
        return { ok: true, job: mockCompletedJob({ jobId, assetVersion: 'v3' }) };
      },
      artifactReader: reader,
      buildCleanMetadataPersistencePlan: (opts) => {
        return {
          ok: true,
          shouldApply: true,
          audit: {
            costSource: 'unavailable',
            tokensTotal: 6266,
            cleanState: 'completed',
            timestamp: '2026-05-23T00:00:00.000Z',
          },
          warnings: [],
        };
      },
      applyCleanMetadataPersistencePlan: async () => {
        return { ok: true, classification: 'DRY_RUN_SUCCESS' };
      },
      dbClient: {
        updateTask: async () => { throw new Error('DB writes forbidden during dry-run'); },
        updateMaterial: async () => { throw new Error('DB writes forbidden during dry-run'); },
      },
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, true);
    assert.equal(result.status, 'DRY_RUN_SUCCESS');
    assert.equal(result.classification, 'DRY_RUN_SUCCESS');
    assert.equal(result.assetVersion, 'v3');
    assert.equal(result.jobId, 'luceon-task-clean-123-toc-rebuild-v3');

    assert.ok(result.audit);
    assert.ok(result.audit.newVersionIntent);
    assert.equal(result.audit.newVersionIntent.intent, 'create-new-version');
    assert.equal(result.audit.newVersionIntent.triggerReason, 'operator-requested-rerun');
    assert.equal(result.audit.newVersionIntent.previousAssetVersion, prevAssetVersion);
    assert.equal(result.audit.newVersionIntent.previousJobId, prevJobId);
    assert.equal(result.audit.newVersionIntent.newAssetVersion, 'v3');
  }

  // Test 18: create-new-version without reason returns BLOCKED_NEW_VERSION_REASON_REQUIRED
  {
    console.log('  [18] Testing create-new-version without reason blocking...');
    const task = makeBaseTask({
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { jobId: 'luceon-task-clean-123-toc-rebuild-v2', assetVersion: 'v2', status: 'completed' },
        },
      },
    });
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: 'v2', status: 'completed' },
        },
      },
    });

    const config = makeBaseConfig({
      intent: 'create-new-version',
      // missing newVersionReason
    });

    const failFn = () => { throw new Error('Dependency should not be called during validation failure'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
      verifyCleanServiceOutputArtifacts: failFn,
      applyCleanMetadataPersistencePlan: failFn,
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, false);
    assert.equal(result.status, 'BLOCKED_NEW_VERSION_REASON_REQUIRED');
    assert.equal(result.classification, 'BLOCKED_NEW_VERSION_REASON_REQUIRED');
  }

  // Test 19: unsupported intent returns BLOCKED_UNSUPPORTED_CLEANSERVICE_INTENT
  {
    console.log('  [19] Testing unsupported intent blocking...');
    const task = makeBaseTask({
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { jobId: 'luceon-task-clean-123-toc-rebuild-v2', assetVersion: 'v2', status: 'completed' },
        },
      },
    });
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: 'v2', status: 'completed' },
        },
      },
    });

    const config = makeBaseConfig({
      intent: 'some-unsupported-garbage-intent',
      newVersionReason: 'operator-requested-rerun',
    });

    const failFn = () => { throw new Error('Dependency should not be called during validation failure'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
      verifyCleanServiceOutputArtifacts: failFn,
      applyCleanMetadataPersistencePlan: failFn,
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, false);
    assert.equal(result.status, 'BLOCKED_UNSUPPORTED_CLEANSERVICE_INTENT');
    assert.equal(result.classification, 'BLOCKED_UNSUPPORTED_CLEANSERVICE_INTENT');
  }

  // Test 20: create-new-version rerun intent + failed existing task job is blocked and throws zero tripwire leaks
  {
    console.log('  [20] Testing rerun intent + failed existing task job blocking...');
    const task = makeBaseTask({
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { jobId: 'luceon-task-clean-123-toc-rebuild-v2', assetVersion: 'v2', status: 'failed' },
        },
      },
    });
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: 'v2', status: 'completed' },
        },
      },
    });

    const config = makeBaseConfig({
      intent: 'create-new-version',
      newVersionReason: 'operator-requested-rerun',
    });

    const failFn = () => { throw new Error('Dependency should not be called during validation failure'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
      verifyCleanServiceOutputArtifacts: failFn,
      applyCleanMetadataPersistencePlan: failFn,
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, false);
    assert.equal(result.status, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
    assert.equal(result.classification, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
  }

  // Test 21: create-new-version rerun intent + version mismatch history is blocked and throws zero tripwire leaks
  {
    console.log('  [21] Testing rerun intent + version mismatch blocking...');
    const task = makeBaseTask({
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { jobId: 'luceon-task-clean-123-toc-rebuild-v2', assetVersion: 'v2', status: 'completed' },
        },
      },
    });
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: 'v1', status: 'completed' }, // mismatched
        },
      },
    });

    const config = makeBaseConfig({
      intent: 'create-new-version',
      newVersionReason: 'operator-requested-rerun',
    });

    const failFn = () => { throw new Error('Dependency should not be called during validation failure'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
      verifyCleanServiceOutputArtifacts: failFn,
      applyCleanMetadataPersistencePlan: failFn,
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, false);
    assert.equal(result.status, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
    assert.equal(result.classification, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
  }

  // Test 22: create-new-version rerun intent + one-sided metadata history is blocked and throws zero tripwire leaks
  {
    console.log('  [22] Testing rerun intent + one-sided metadata blocking...');
    const task = makeBaseTask(); // missing cleanServiceJobs
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: 'v2', status: 'completed' },
        },
      },
    });

    const config = makeBaseConfig({
      intent: 'create-new-version',
      newVersionReason: 'operator-requested-rerun',
    });

    const failFn = () => { throw new Error('Dependency should not be called during validation failure'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
      verifyCleanServiceOutputArtifacts: failFn,
      applyCleanMetadataPersistencePlan: failFn,
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, false);
    assert.equal(result.status, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
    assert.equal(result.classification, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
  }

  // Test 23: create-new-version rerun intent + missing task jobId history is blocked and throws zero tripwire leaks
  {
    console.log('  [23] Testing rerun intent + missing task jobId blocking...');
    const task = makeBaseTask({
      metadata: {
        cleanServiceJobs: {
          'toc-rebuild': { assetVersion: 'v2', status: 'completed' }, // missing jobId
        },
      },
    });
    const material = makeBaseMaterial({
      metadata: {
        cleanMaterials: {
          'toc-rebuild': { latestVersion: 'v2', status: 'completed' },
        },
      },
    });

    const config = makeBaseConfig({
      intent: 'create-new-version',
      newVersionReason: 'operator-requested-rerun',
    });

    const failFn = () => { throw new Error('Dependency should not be called during validation failure'); };
    const deps = {
      submitJob: failFn,
      queryJob: failFn,
      verifyCleanServiceOutputArtifacts: failFn,
      applyCleanMetadataPersistencePlan: failFn,
    };

    const result = await runCleanServiceTocRebuildOnce({ task, material, config, deps });
    assert.equal(result.ok, false);
    assert.equal(result.status, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
    assert.equal(result.classification, 'BLOCKED_EXISTING_TOC_REBUILD_METADATA');
  }

  console.log('ALL cleanservice orchestration runner smoke tests PASSED! (23/23)');
}

runTests().catch(err => {
  console.error('Smoke test failed:', err);
  process.exit(1);
});
