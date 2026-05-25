import assert from 'node:assert/strict';
import {
  RAW2CLEAN_DURABLE_ASSET_VERSION,
  RAW2CLEAN_DURABLE_JOB_ID,
  RAW2CLEAN_DURABLE_OBJECT,
  RAW2CLEAN_DURABLE_SERVICE_NAME,
  buildRaw2CleanDurableCandidatePlan,
  hasFullRaw2CleanCandidateContent,
} from '../services/rawmaterial2cleanmaterial/durable-candidate.mjs';

function makeOutput(extra = {}) {
  return {
    kind: 'raw-material-2-clean-material-output-candidate',
    contractVersion: 'v0.dry-run',
    createdAt: '2026-05-25T05:20:01.000Z',
    materialId: '1842780526581841',
    taskId: 'task-1779085089451',
    sourceCleanMaterial: {
      serviceName: 'toc-rebuild',
      assetVersion: 'v4',
      jobId: 'luceon-task-1779085089451-toc-rebuild-v4',
      provenanceObjectName: 'toc-rebuild/1842780526581841/v4/provenance.json',
    },
    sourceInput: {
      bucket: 'eduassets-raw',
      object: 'mineru/1842780526581841/v1/content_list_v2.json',
      sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
      size_bytes: 31543,
    },
    sourceArtifacts: {
      readable_tree: { bucket: 'eduassets-clean', object: 'toc-rebuild/1842780526581841/v4/readable_tree.md', sha256: 'readable-sha', size_bytes: 106 },
      logic_tree: { bucket: 'eduassets-clean', object: 'toc-rebuild/1842780526581841/v4/logic_tree.json', sha256: 'logic-sha', size_bytes: 375 },
      skeleton: { bucket: 'eduassets-clean', object: 'toc-rebuild/1842780526581841/v4/skeleton.json', sha256: 'skeleton-sha', size_bytes: 21160 },
      flooded_content: { bucket: 'eduassets-clean', object: 'toc-rebuild/1842780526581841/v4/flooded_content.json', sha256: 'flooded-sha', size_bytes: 20054 },
    },
    sections: [{ sourceRef: 'root', sourceRole: 'logic_tree', title: 'Document root' }],
    blocks: [{ sourceRef: 'block-1', sourceRole: 'flooded_content', text: 'Read the short passage.' }],
    provenance: {
      draftKind: 'raw-material-2-clean-material-draft',
      draftStatus: 'MOCK_ALGORITHM_DRAFT_READY',
      draftCreatedAt: '2026-05-25T05:20:01.000Z',
      sourceRefCount: 2,
      readableTree: { titleCount: 1, charCount: 20 },
    },
    warnings: [],
    preview: {
      contentType: 'application/json',
      size_bytes: 21706,
      sha256: 'd641c3dbfda693049e740341c86ad7a37e9970d13af8e530591f6af25316f3b3',
    },
    ...extra,
  };
}

function assertBlocked(result, code) {
  assert.equal(result.ok, false);
  assert.equal(result.code, code);
}

console.log('=== RawMaterial2CleanMaterial Durable Candidate Smoke ===');

{
  console.log('  [1] builds narrow task/material metadata patches...');
  const result = buildRaw2CleanDurableCandidatePlan({
    output: makeOutput(),
    existingTask: { metadata: { keepTask: true } },
    existingMaterial: { metadata: { keepMaterial: true } },
    candidateArtifactPreview: {
      contentType: 'application/json',
      size_bytes: 21888,
      sha256: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    },
    now: '2026-05-25T05:20:01.000Z',
  });
  assert.equal(result.ok, true);
  assert.equal(result.operationLimit.minioPutObject, 1);
  assert.equal(result.operationLimit.dbPatch, 2);
  assert.equal(result.candidateRef.object, RAW2CLEAN_DURABLE_OBJECT);
  assert.equal(result.candidateRef.sha256, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');

  const taskSummary = result.taskPatch.metadata.rawMaterial2CleanMaterialJobs[RAW2CLEAN_DURABLE_SERVICE_NAME];
  assert.equal(taskSummary.jobId, RAW2CLEAN_DURABLE_JOB_ID);
  assert.equal(taskSummary.assetVersion, RAW2CLEAN_DURABLE_ASSET_VERSION);
  assert.equal(taskSummary.status, 'candidate');
  assert.equal(taskSummary.artifact.candidate.object, RAW2CLEAN_DURABLE_OBJECT);
  assert.equal(taskSummary.preview.candidateArtifact.sha256, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
  assert.equal(taskSummary.preview.outputContract.sha256, 'd641c3dbfda693049e740341c86ad7a37e9970d13af8e530591f6af25316f3b3');
  assert.equal(taskSummary.stats.sectionCount, 1);
  assert.equal(taskSummary.stats.blockCount, 1);
  assert.equal(result.taskPatch.metadata.keepTask, true);
  assert.equal(result.materialPatch.metadata.keepMaterial, true);
  assert.equal(result.materialPatch.metadata.rawMaterial2CleanMaterial.currentCandidate.artifact.candidate.object, RAW2CLEAN_DURABLE_OBJECT);
  assert.equal(hasFullRaw2CleanCandidateContent(result.taskPatch), false);
  assert.equal(hasFullRaw2CleanCandidateContent(result.materialPatch), false);
}

{
  console.log('  [2] blocks wrong output and missing refs...');
  assertBlocked(buildRaw2CleanDurableCandidatePlan({ output: null }), 'MISSING_OUTPUT');
  assertBlocked(buildRaw2CleanDurableCandidatePlan({ output: makeOutput({ kind: 'wrong' }) }), 'UNSUPPORTED_OUTPUT_KIND');
  assertBlocked(buildRaw2CleanDurableCandidatePlan({ output: makeOutput({ materialId: 'other' }) }), 'SCOPE_MISMATCH');
  assertBlocked(buildRaw2CleanDurableCandidatePlan({
    output: makeOutput({ sourceCleanMaterial: { serviceName: 'toc-rebuild', assetVersion: 'v3' } }),
  }), 'SOURCE_CLEAN_MATERIAL_MISMATCH');

  const missingRef = makeOutput();
  missingRef.blocks[0].sourceRef = '';
  assertBlocked(buildRaw2CleanDurableCandidatePlan({ output: missingRef }), 'MISSING_SOURCE_REFERENCE');
}

{
  console.log('  [3] blocks incompatible existing metadata and detects full content...');
  const incompatible = {
    metadata: {
      rawMaterial2CleanMaterialJobs: {
        [RAW2CLEAN_DURABLE_SERVICE_NAME]: {
          jobId: RAW2CLEAN_DURABLE_JOB_ID,
          assetVersion: RAW2CLEAN_DURABLE_ASSET_VERSION,
          artifact: { candidate: { bucket: 'eduassets-clean', object: 'different.json', sha256: 'bad', size_bytes: 1 } },
        },
      },
    },
  };
  assertBlocked(buildRaw2CleanDurableCandidatePlan({
    output: makeOutput(),
    existingTask: incompatible,
    existingMaterial: { metadata: {} },
  }), 'INCOMPATIBLE_EXISTING_METADATA');

  assert.equal(hasFullRaw2CleanCandidateContent({ sections: [{ sourceRef: 'root' }] }), true);
  assert.equal(hasFullRaw2CleanCandidateContent({ artifact: { candidate: { object: RAW2CLEAN_DURABLE_OBJECT } } }), false);
}

console.log('RawMaterial2CleanMaterial durable candidate smoke passed.');
