import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const outDir = '/tmp/luceon-task283-raw2clean-candidate-view-smoke';
const helperOutfile = join(outDir, 'app/utils/rawMaterial2CleanMaterialCandidateView.js');

function objectRef(object, extra = {}) {
  return {
    bucket: 'eduassets-clean',
    object,
    sha256: '49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27',
    size_bytes: 21767,
    content_type: 'application/json',
    ...extra,
  };
}

function summary(extra = {}) {
  return {
    serviceName: 'raw-material-2-clean-material',
    jobId: 'luceon-task-1779085089451-raw2clean-v1',
    status: 'candidate',
    assetVersion: 'v1',
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
    artifact: {
      candidate: objectRef('raw-material-2-clean-material/1842780526581841/v1/candidate.json'),
    },
    stats: {
      sectionCount: 73,
      blockCount: 71,
      sourceRefCount: 72,
      candidateArtifactSizeBytes: 21767,
      outputContractSizeBytes: 21706,
    },
    preview: {
      candidateArtifact: {
        size_bytes: 21767,
        sha256: '49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27',
      },
      outputContract: {
        size_bytes: 21706,
        sha256: 'c87cbf75bf91b43700239ea890f9c6fda7ef2e3c61db18a4533397235e872c16',
      },
    },
    warnings: ['mock-algorithm-skeleton-only'],
    boundaries: { runtimePost: false, finalQualityAccepted: false },
    updatedAt: '2026-05-25T05:20:01.000Z',
    ...extra,
  };
}

function acceptedDecision() {
  return {
    state: 'accepted',
    decision: 'accepted',
    decidedAt: '2026-05-25T05:54:05.000Z',
    decidedBy: 'Luceon',
    reason: 'Director-approved single-sample durable accepted decision apply',
    boundaries: {
      finalQualityAccepted: false,
      runtimePost: false,
      serviceExecution: false,
      minioMutation: false,
      batch: false,
      readinessClaimed: false,
    },
  };
}

function compileHelper() {
  rmSync(outDir, { recursive: true, force: true });
  execFileSync('npx', [
    'pnpm@10.4.1',
    'exec',
    'tsc',
    'src/app/utils/rawMaterial2CleanMaterialCandidateView.ts',
    '--target',
    'ES2020',
    '--module',
    'ES2020',
    '--moduleResolution',
    'bundler',
    '--skipLibCheck',
    '--noEmit',
    'false',
    '--outDir',
    outDir,
  ], { stdio: 'inherit' });
  let compiled = readFileSync(helperOutfile, 'utf8');
  compiled = compiled.replace("export {};\n", '');
  writeFileSync(helperOutfile, compiled);
}

compileHelper();
const { buildRawMaterial2CleanMaterialCandidateView } = await import(pathToFileURL(helperOutfile).href);

console.log('=== RawMaterial2CleanMaterial Candidate View Smoke ===');

{
  console.log('  [1] discovers candidate from task plus material metadata...');
  const material = {
    metadata: {
      rawMaterial2CleanMaterial: {
        currentCandidate: summary(),
        candidates: { v1: summary() },
      },
    },
  };
  const task = {
    metadata: {
      rawMaterial2CleanMaterialJobs: {
        'raw-material-2-clean-material': summary(),
      },
    },
  };
  const view = buildRawMaterial2CleanMaterialCandidateView({ material, task });
  assert.equal(view.present, true);
  assert.equal(view.status, 'candidate');
  assert.equal(view.assetVersion, 'v1');
  assert.equal(view.jobId, 'luceon-task-1779085089451-raw2clean-v1');
  assert.equal(view.artifact.object, 'raw-material-2-clean-material/1842780526581841/v1/candidate.json');
  assert.equal(view.artifactUrl, '/__proxy/upload/proxy-file?objectName=raw-material-2-clean-material%2F1842780526581841%2Fv1%2Fcandidate.json&bucket=eduassets-clean');
  assert.equal(view.sourceCleanMaterial.assetVersion, 'v4');
  assert.equal(view.sourceInput.sha256, 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db');
  assert.equal(view.stats.sectionCount, 73);
  assert.equal(view.stats.blockCount, 71);
  assert.equal(view.preview.candidateArtifactSha256, '49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27');
  assert.equal(view.preview.outputContractSha256, 'c87cbf75bf91b43700239ea890f9c6fda7ef2e3c61db18a4533397235e872c16');
  assert.equal(view.decision, null);
  assert.deepEqual(view.warnings, ['mock-algorithm-skeleton-only']);
  assert.equal(view.conflict, null);
}

{
  console.log('  [2] supports material-only and task-only discovery...');
  const materialOnly = buildRawMaterial2CleanMaterialCandidateView({
    material: { metadata: { rawMaterial2CleanMaterial: { currentCandidate: summary() } } },
    task: null,
  });
  assert.equal(materialOnly.present, true);
  assert.equal(materialOnly.artifact.object, 'raw-material-2-clean-material/1842780526581841/v1/candidate.json');

  const taskOnly = buildRawMaterial2CleanMaterialCandidateView({
    material: null,
    task: { metadata: { rawMaterial2CleanMaterialJobs: { 'raw-material-2-clean-material': summary() } } },
  });
  assert.equal(taskOnly.present, true);
  assert.equal(taskOnly.stats.sourceRefCount, 72);
}

{
  console.log('  [3] detects missing and conflicting metadata...');
  const empty = buildRawMaterial2CleanMaterialCandidateView({ material: { metadata: {} }, task: { metadata: {} } });
  assert.equal(empty.present, false);
  assert.equal(empty.artifactUrl, null);

  const conflict = buildRawMaterial2CleanMaterialCandidateView({
    material: { metadata: { rawMaterial2CleanMaterial: { currentCandidate: summary() } } },
    task: {
      metadata: {
        rawMaterial2CleanMaterialJobs: {
          'raw-material-2-clean-material': summary({
            artifact: { candidate: objectRef('raw-material-2-clean-material/1842780526581841/v1/other.json') },
          }),
        },
      },
    },
  });
  assert.equal(conflict.present, true);
  assert.equal(conflict.conflict, 'task/material candidate ObjectRef mismatch');
}

{
  console.log('  [4] surfaces accepted decision metadata...');
  const view = buildRawMaterial2CleanMaterialCandidateView({
    material: {
      metadata: {
        rawMaterial2CleanMaterial: {
          currentCandidate: summary({ status: 'accepted', cleanState: 'accepted-candidate', decision: acceptedDecision() }),
          candidates: { v1: summary({ status: 'accepted', cleanState: 'accepted-candidate', decision: acceptedDecision() }) },
        },
      },
    },
    task: {
      metadata: {
        rawMaterial2CleanMaterialJobs: {
          'raw-material-2-clean-material': summary({ status: 'accepted', cleanState: 'accepted-candidate', decision: acceptedDecision() }),
        },
      },
    },
  });
  assert.equal(view.present, true);
  assert.equal(view.status, 'accepted');
  assert.equal(view.decision.state, 'accepted');
  assert.equal(view.decision.decidedBy, 'Luceon');
  assert.equal(view.decision.finalQualityAccepted, false);
}

console.log('RawMaterial2CleanMaterial candidate view smoke passed.');
