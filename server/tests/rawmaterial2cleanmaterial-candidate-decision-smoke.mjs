import assert from 'node:assert/strict';
import {
  RAW2CLEAN_ACCEPTED_DECISION_SHA,
  RAW2CLEAN_ACCEPTED_DECISION_SIZE,
  buildRaw2CleanAcceptedDecisionPlan,
} from '../services/rawmaterial2cleanmaterial/candidate-decision.mjs';

function candidateSummary(extra = {}) {
  return {
    serviceName: 'raw-material-2-clean-material',
    protocolVersion: 'v0.dry-run',
    jobId: 'luceon-task-1779085089451-raw2clean-v1',
    status: 'candidate',
    cleanState: 'candidate',
    materialId: '1842780526581841',
    parseTaskId: 'task-1779085089451',
    assetVersion: 'v1',
    artifact: {
      candidate: {
        bucket: 'eduassets-clean',
        object: 'raw-material-2-clean-material/1842780526581841/v1/candidate.json',
        sha256: RAW2CLEAN_ACCEPTED_DECISION_SHA,
        size_bytes: RAW2CLEAN_ACCEPTED_DECISION_SIZE,
        content_type: 'application/json',
      },
    },
    stats: {
      sectionCount: 73,
      blockCount: 71,
      sourceRefCount: 72,
      outputContractSizeBytes: 21706,
      candidateArtifactSizeBytes: RAW2CLEAN_ACCEPTED_DECISION_SIZE,
    },
    preview: {
      candidateArtifact: {
        size_bytes: RAW2CLEAN_ACCEPTED_DECISION_SIZE,
        sha256: RAW2CLEAN_ACCEPTED_DECISION_SHA,
      },
    },
    boundaries: {
      durableCandidateArtifactCreated: true,
      dbMetadataPatched: true,
      runtimePost: false,
      serviceExecution: false,
      finalQualityAccepted: false,
      readinessClaimed: false,
    },
    updatedAt: '2026-05-25T05:20:01.000Z',
    ...extra,
  };
}

function fixtures({ taskCandidate = candidateSummary(), materialCandidate = candidateSummary(), artifactReadback = null } = {}) {
  return {
    existingTask: {
      id: 'task-1779085089451',
      metadata: {
        rawMaterial2CleanMaterialJobs: {
          'raw-material-2-clean-material': taskCandidate,
        },
      },
    },
    existingMaterial: {
      id: '1842780526581841',
      metadata: {
        rawMaterial2CleanMaterial: {
          currentCandidate: materialCandidate,
          candidates: { v1: materialCandidate },
        },
      },
    },
    artifactReadback: artifactReadback || {
      status: 200,
      sha256: RAW2CLEAN_ACCEPTED_DECISION_SHA,
      size_bytes: RAW2CLEAN_ACCEPTED_DECISION_SIZE,
    },
  };
}

console.log('=== RawMaterial2CleanMaterial Candidate Decision Smoke ===');

{
  console.log('  [1] builds accepted decision patch for canonical sample...');
  const plan = buildRaw2CleanAcceptedDecisionPlan({
    ...fixtures(),
    now: '2026-05-25T05:54:05.000Z',
  });
  assert.equal(plan.ok, true, JSON.stringify(plan, null, 2));
  assert.equal(plan.operationLimit.dbPatch, 2);
  assert.equal(plan.operationLimit.minioPutObject, 0);
  assert.equal(plan.decision.state, 'accepted');
  assert.equal(plan.decision.boundaries.finalQualityAccepted, false);
  assert.equal(plan.taskPatch.metadata.rawMaterial2CleanMaterialJobs['raw-material-2-clean-material'].status, 'accepted');
  assert.equal(plan.materialPatch.metadata.rawMaterial2CleanMaterial.currentCandidate.status, 'accepted');
  assert.equal(plan.materialPatch.metadata.rawMaterial2CleanMaterial.currentDecision.state, 'accepted');
  assert.equal(JSON.stringify(plan.taskPatch).includes('"sections"'), false);
  assert.equal(JSON.stringify(plan.materialPatch).includes('"blocks"'), false);
}

{
  console.log('  [2] blocks mismatched artifact read-back...');
  const plan = buildRaw2CleanAcceptedDecisionPlan({
    ...fixtures({ artifactReadback: { status: 200, sha256: '0'.repeat(64), size_bytes: RAW2CLEAN_ACCEPTED_DECISION_SIZE } }),
    now: '2026-05-25T05:54:05.000Z',
  });
  assert.equal(plan.ok, false);
  assert.equal(plan.code, 'ARTIFACT_READBACK_MISMATCH');
}

{
  console.log('  [3] blocks candidate ObjectRef mismatch...');
  const plan = buildRaw2CleanAcceptedDecisionPlan({
    ...fixtures({
      taskCandidate: candidateSummary({
        artifact: {
          candidate: {
            bucket: 'eduassets-clean',
            object: 'raw-material-2-clean-material/1842780526581841/v1/other.json',
            sha256: RAW2CLEAN_ACCEPTED_DECISION_SHA,
            size_bytes: RAW2CLEAN_ACCEPTED_DECISION_SIZE,
          },
        },
      }),
    }),
    now: '2026-05-25T05:54:05.000Z',
  });
  assert.equal(plan.ok, false);
  assert.equal(plan.code, 'CANDIDATE_REF_MISMATCH');
}

{
  console.log('  [4] blocks full candidate content in metadata patch...');
  const plan = buildRaw2CleanAcceptedDecisionPlan({
    ...fixtures({ materialCandidate: candidateSummary({ candidateJson: '{"too":"large"}' }) }),
    now: '2026-05-25T05:54:05.000Z',
  });
  assert.equal(plan.ok, false);
  assert.equal(plan.code, 'FULL_CONTENT_IN_METADATA');
}

console.log('RawMaterial2CleanMaterial candidate decision smoke passed.');
