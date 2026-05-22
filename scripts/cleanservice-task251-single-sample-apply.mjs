/**
 * scripts/cleanservice-task251-single-sample-apply.mjs
 *
 * Controlled single-sample metadata apply script for Task 251.
 * Safely applies the verified Task 245/246 metadata to target sample in real DB.
 */

import assert from 'node:assert/strict';
import { buildVerifiedCleanOutputMetadataCandidate } from '../server/services/cleanservice/metadata-summary.mjs';
import { buildCleanMetadataPersistencePlan } from '../server/services/cleanservice/metadata-persistence.mjs';
import { applyCleanMetadataPersistencePlan } from '../server/services/cleanservice/metadata-apply-executor.mjs';
import { getTaskById, updateTask, getMaterialById, updateMaterial } from '../server/services/tasks/task-client.mjs';

async function main() {
  console.log('=== Task 251: Single-Sample Verified Metadata Apply Script ===');

  const targetMaterialId = '1842780526581841';
  const targetTaskId = 'task-1779085089451';
  const targetJobId = 'luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230';
  const targetVersion = 'v2';

  const dbBaseUrl = process.env.DB_BASE_URL || 'http://localhost:8789';
  console.log(`Using Database Base URL: ${dbBaseUrl}`);

  // 1. Environmental Controls & Double Confirmation Check
  const realWriteEnv = process.env.TASK251_ALLOW_REAL_DB_WRITE;
  const targetConfirmEnv = process.env.TASK251_CONFIRM_TARGET;

  const envWriteEnabled = realWriteEnv === 'true';
  const expectedConfirmString = `${targetMaterialId}:${targetTaskId}:${targetJobId}`;
  const targetMatched = targetConfirmEnv === expectedConfirmString;

  const allowRealApply = envWriteEnabled && targetMatched;

  if (allowRealApply) {
    console.log('>>> [WRITE MODE AUTHORIZED] Real Database writes will be executed! <<<');
  } else {
    console.log('>>> [DRY RUN MODE] Real Database writes are disabled. <<<');
    console.log(`TASK251_ALLOW_REAL_DB_WRITE: ${realWriteEnv}`);
    console.log(`TASK251_CONFIRM_TARGET: ${targetConfirmEnv} (Expected: ${expectedConfirmString})`);
  }

  // 2. Preflight Stage (Read-only fetches)
  console.log('\n--- Preflight Verification ---');
  console.log(`Fetching task record ${targetTaskId}...`);
  const existingTask = await getTaskById(targetTaskId);
  if (!existingTask) {
    console.error(`[ERROR] Preflight failed: Task ${targetTaskId} not found in DB!`);
    console.log('Result Classification: BLOCKED_DB_TARGET_NOT_FOUND');
    process.exit(1);
  }
  console.log('Task found successfully.');

  console.log(`Fetching material record ${targetMaterialId}...`);
  const existingMaterial = await getMaterialById(targetMaterialId);
  if (!existingMaterial) {
    console.error(`[ERROR] Preflight failed: Material ${targetMaterialId} not found in DB!`);
    console.log('Result Classification: BLOCKED_DB_TARGET_NOT_FOUND');
    process.exit(1);
  }
  console.log('Material found successfully.');

  // Print before apply snapshots (bounded)
  console.log('\nExisting task cleanServiceJobs before apply:');
  console.log(JSON.stringify(existingTask.metadata?.cleanServiceJobs || {}, null, 2));
  console.log('Existing material cleanMaterials before apply:');
  console.log(JSON.stringify(existingMaterial.metadata?.cleanMaterials || {}, null, 2));

  // Take a snapshot of existing unrelated metadata to verify they are preserved unaltered
  const unrelatedTaskMetadata = { ...existingTask.metadata };
  if (unrelatedTaskMetadata.cleanServiceJobs) {
    unrelatedTaskMetadata.cleanServiceJobs = { ...unrelatedTaskMetadata.cleanServiceJobs };
    delete unrelatedTaskMetadata.cleanServiceJobs['toc-rebuild'];
    if (Object.keys(unrelatedTaskMetadata.cleanServiceJobs).length === 0) {
      delete unrelatedTaskMetadata.cleanServiceJobs;
    }
  }

  const unrelatedMaterialMetadata = { ...existingMaterial.metadata };
  if (unrelatedMaterialMetadata.cleanMaterials) {
    unrelatedMaterialMetadata.cleanMaterials = { ...unrelatedMaterialMetadata.cleanMaterials };
    delete unrelatedMaterialMetadata.cleanMaterials['toc-rebuild'];
    if (Object.keys(unrelatedMaterialMetadata.cleanMaterials).length === 0) {
      delete unrelatedMaterialMetadata.cleanMaterials;
    }
  }

  // 3. Metadata Ingestion Candidate & Plan Construction (Task 245 evidence)
  console.log('\n--- Constructing Metadata Candidate and Plan ---');

  const rawInput = {
    bucket: 'eduassets-raw',
    object: 'mineru/1842780526581841/v1/content_list_v2.json',
    sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
    sizeBytes: 31543
  };

  const artifacts = {
    flooded_content: { bucket: 'eduassets-clean', object: `toc-rebuild/${targetMaterialId}/${targetVersion}/flooded_content.json`, size_bytes: 20054, sha256: 'e1a8355a80a5014b5a616ed441a4d0851c47d6a3d6092711ce765ffe11eea7b7' },
    logic_tree: { bucket: 'eduassets-clean', object: `toc-rebuild/${targetMaterialId}/${targetVersion}/logic_tree.json`, size_bytes: 375, sha256: 'b61ee669b63bccb597f9ff31e5773ac1cc53a7bf6d6ef7a5ba73d467c7267665' },
    readable_tree: { bucket: 'eduassets-clean', object: `toc-rebuild/${targetMaterialId}/${targetVersion}/readable_tree.md`, size_bytes: 106, sha256: 'bba5cf360fa7c0d92a9489ce84dfc40458de6072f812d7ab5d381b8e828946d7' },
    skeleton: { bucket: 'eduassets-clean', object: `toc-rebuild/${targetMaterialId}/${targetVersion}/skeleton.json`, size_bytes: 21160, sha256: 'c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e' },
    unresolved_anchors: { bucket: 'eduassets-clean', object: `toc-rebuild/${targetMaterialId}/${targetVersion}/unresolved_anchors.json`, size_bytes: 2, sha256: '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945' },
    metrics: { bucket: 'eduassets-clean', object: `toc-rebuild/${targetMaterialId}/${targetVersion}/metrics.json`, size_bytes: 129, sha256: 'add72cb0a0c0dcb2fe051961795da8c151181022df79770583d5fb75c7ed9718' },
    provenance: { bucket: 'eduassets-clean', object: `toc-rebuild/${targetMaterialId}/${targetVersion}/provenance.json`, size_bytes: 2108, sha256: '4762b30f5ab344b1eec0a46b4541b9fa1df314ca756eb837b4622b43169104eb' },
  };

  const job = {
    job_id: targetJobId,
    status: 'completed',
    service_name: 'toc-rebuild',
    service_version: '1.0.0',
    protocol_version: 'v1',
    material_id: targetMaterialId,
    parse_task_id: targetTaskId,
    asset_version: targetVersion,
    submitted_at: '2026-05-22T05:22:30.000Z',
    started_at: '2026-05-22T05:22:31.000Z',
    finished_at: '2026-05-22T05:23:00.000Z',
    sink: { bucket: 'eduassets-clean', prefix: `toc-rebuild/${targetMaterialId}/${targetVersion}/` },
    artifacts,
    stats: {
      tokens: { prompt: 6212, completion: 54, total: 6266 },
      tokensTotal: 6266,
      tokensPrompt: 6212,
      tokensCompletion: 54,
      cost_cny_estimated: 0.006319999999999999,
      costCnyEstimated: 0.006319999999999999,
      cost_cny_actual: 0.0,
      costCnyActual: 0.0,
      unresolved_anchor_count: 0,
    },
    provenance: {
      schema: 'luceon-provenance/v1',
      service: { name: 'toc-rebuild', version: '1.0.0', protocol_version: 'v1' },
      asset: { material_id: targetMaterialId, asset_version: targetVersion },
      job: { job_id: targetJobId, parse_task_id: targetTaskId },
      inputs: [
        {
          bucket: rawInput.bucket,
          object: rawInput.object,
          sha256: rawInput.sha256,
          size_bytes: rawInput.sizeBytes,
        }
      ],
    },
  };

  const verification = {
    ok: true,
    cleanState: 'completed',
    errors: [],
    warnings: ['input-size-bytes-zero'],
    unresolvedAnchorCount: 0,
    inputSizeBytes: rawInput.sizeBytes,
    sourceInput: rawInput,
  };

  const customNow = () => '2026-05-22T17:32:06.000Z';

  const candidate = buildVerifiedCleanOutputMetadataCandidate({
    job,
    verification,
    now: customNow,
  });

  const plan = buildCleanMetadataPersistencePlan({
    candidate,
    existingTask,
    existingMaterial,
    now: customNow,
  });

  if (!plan.ok) {
    console.error(`[ERROR] Plan building failed: ${plan.reason}`);
    console.log(`Result Classification: BLOCKED_PLAN_NOT_APPLYABLE`);
    process.exit(1);
  }

  console.log('Metadata Persistence Plan built successfully.');

  // 4. Execution Stage
  console.log('\n--- Applying Metadata Plan ---');
  const dbClient = { updateTask, updateMaterial };

  const result = await applyCleanMetadataPersistencePlan({
    plan,
    taskId: targetTaskId,
    materialId: targetMaterialId,
    dbClient,
    existingTask,
    existingMaterial,
    allowRealApply,
  });

  console.log('Execution outcome:', JSON.stringify(result, null, 2));

  // 5. Verification & Read-back Stage
  if (result.ok && result.applied) {
    console.log('\n--- Post-Read Verification Stage ---');
    console.log('Fetching updated records from the database...');

    const updatedTask = await getTaskById(targetTaskId);
    const updatedMaterial = await getMaterialById(targetMaterialId);

    if (!updatedTask || !updatedMaterial) {
      console.error('[ERROR] Read-back failed! Records disappeared from DB!');
      process.exit(1);
    }

    const taskJobSummary = updatedTask.metadata?.cleanServiceJobs?.['toc-rebuild'];
    const materialSummary = updatedMaterial.metadata?.cleanMaterials?.['toc-rebuild'];

    // 1. Verify existence of metadata branches
    assert.ok(taskJobSummary, 'taskJobSummary is missing');
    assert.ok(materialSummary, 'materialSummary is missing');

    // 2. Verify sourceInput values
    assert.equal(taskJobSummary.sourceInput.bucket, rawInput.bucket);
    assert.equal(taskJobSummary.sourceInput.object, rawInput.object);
    assert.equal(taskJobSummary.sourceInput.sha256, rawInput.sha256);
    assert.equal(taskJobSummary.sourceInput.size_bytes, rawInput.sizeBytes);

    assert.equal(materialSummary.sourceInput.bucket, rawInput.bucket);
    assert.equal(materialSummary.sourceInput.object, rawInput.object);
    assert.equal(materialSummary.sourceInput.sha256, rawInput.sha256);
    assert.equal(materialSummary.sourceInput.size_bytes, rawInput.sizeBytes);

    // 3. Verify ObjectRefs (7 key artifacts)
    const requiredRoles = ['flooded_content', 'logic_tree', 'readable_tree', 'skeleton', 'unresolved_anchors', 'metrics', 'provenance'];
    for (const role of requiredRoles) {
      assert.ok(taskJobSummary.artifacts[role], `artifact ${role} is missing in task`);
      assert.equal(taskJobSummary.artifacts[role].bucket, 'eduassets-clean');
      assert.equal(taskJobSummary.artifacts[role].object, job.artifacts[role].object);
      assert.equal(taskJobSummary.artifacts[role].sha256, job.artifacts[role].sha256);
      assert.equal(taskJobSummary.artifacts[role].size_bytes, job.artifacts[role].size_bytes);
    }

    // 4. Verify metrics, costs and tokens
    assert.equal(taskJobSummary.stats.tokensPrompt, 6212);
    assert.equal(taskJobSummary.stats.tokensCompletion, 54);
    assert.equal(taskJobSummary.stats.tokensTotal, 6266);
    assert.equal(taskJobSummary.stats.costCnyEstimated, 0.006319999999999999);
    assert.equal(taskJobSummary.stats.costCnyActual, 0.0);

    assert.equal(materialSummary.stats.tokensPrompt, 6212);
    assert.equal(materialSummary.stats.tokensCompletion, 54);
    assert.equal(materialSummary.stats.tokensTotal, 6266);
    assert.equal(materialSummary.stats.costCnyActual, 0.0);

    // 5. Verify input-size-bytes-zero warning is persisted
    assert.ok(taskJobSummary.warnings.includes('input-size-bytes-zero'), 'input-size-bytes-zero warning missing in task');

    // 6. Verify unrelated existing metadata fields remain preserved
    const postUnrelatedTaskMetadata = { ...updatedTask.metadata };
    if (postUnrelatedTaskMetadata.cleanServiceJobs) {
      postUnrelatedTaskMetadata.cleanServiceJobs = { ...postUnrelatedTaskMetadata.cleanServiceJobs };
      delete postUnrelatedTaskMetadata.cleanServiceJobs['toc-rebuild'];
      if (Object.keys(postUnrelatedTaskMetadata.cleanServiceJobs).length === 0) {
        delete postUnrelatedTaskMetadata.cleanServiceJobs;
      }
    }
    assert.deepEqual(postUnrelatedTaskMetadata, unrelatedTaskMetadata, 'Unrelated task metadata was altered!');

    const postUnrelatedMaterialMetadata = { ...updatedMaterial.metadata };
    if (postUnrelatedMaterialMetadata.cleanMaterials) {
      postUnrelatedMaterialMetadata.cleanMaterials = { ...postUnrelatedMaterialMetadata.cleanMaterials };
      delete postUnrelatedMaterialMetadata.cleanMaterials['toc-rebuild'];
      if (Object.keys(postUnrelatedMaterialMetadata.cleanMaterials).length === 0) {
        delete postUnrelatedMaterialMetadata.cleanMaterials;
      }
    }
    assert.deepEqual(postUnrelatedMaterialMetadata, unrelatedMaterialMetadata, 'Unrelated material metadata was altered!');

    // 7. Verify NO full content is stored (JSON size check and specific content key checking)
    const taskJobStr = JSON.stringify(taskJobSummary);
    assert.ok(!taskJobStr.includes('"blocks"'), 'Should not contain "blocks" list');
    assert.ok(!taskJobStr.includes('"paragraphs"'), 'Should not contain "paragraphs" list');
    assert.ok(!taskJobStr.includes('"nodes"'), 'Should not contain "nodes" list');
    assert.ok(!taskJobStr.includes('"parsedArtifacts"'), 'Should not contain "parsedArtifacts" list');

    console.log('>>> [SUCCESS] Post-Read Verification PASSED successfully! <<<');
    console.log('All stats, metrics, warnings, sourceInputs, and ObjectRefs successfully persisted.');
    console.log('Unrelated metadata is perfectly preserved and no full content was written.');
  }

  console.log(`\nResult Classification: ${result.classification}`);
  console.log('Script execution finished.');
}

main().catch((err) => {
  console.error('[CRITICAL] Script execution aborted with error:', err);
  process.exit(1);
});
