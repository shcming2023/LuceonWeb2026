import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { rmSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const outDir = '/tmp/luceon-task273-raw2clean-bundle-smoke';

function objectRef(object, extra = {}) {
  return {
    bucket: 'eduassets-clean',
    object,
    sha256: 'abc123sha256',
    size_bytes: 128,
    content_type: object.endsWith('.md') ? 'text/markdown' : 'application/json',
    ...extra,
  };
}

function makeFixture() {
  const materialId = '1842780526581841';
  const taskId = 'task-1779085089451';
  const serviceName = 'toc-rebuild';
  const assetVersion = 'v4';
  const jobId = 'luceon-task-1779085089451-toc-rebuild-v4';
  const prefix = `${serviceName}/${materialId}/${assetVersion}/`;
  const sourceInput = {
    bucket: 'eduassets-raw',
    object: `mineru/${materialId}/v1/content_list_v2.json`,
    sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
    size_bytes: 31543,
  };
  const artifactRefs = {
    readable_tree: objectRef(`${prefix}readable_tree.md`),
    logic_tree: objectRef(`${prefix}logic_tree.json`),
    skeleton: objectRef(`${prefix}skeleton.json`),
    flooded_content: objectRef(`${prefix}flooded_content.json`),
    metrics: objectRef(`${prefix}metrics.json`),
    provenance: objectRef(`${prefix}provenance.json`),
    unresolved_anchors: objectRef(`${prefix}unresolved_anchors.json`),
  };

  return {
    material: {
      id: materialId,
      metadata: {
        cleanMaterials: {
          [serviceName]: {
            serviceName,
            latestVersion: assetVersion,
            status: 'completed',
            prefix,
            provenanceObjectName: `${prefix}provenance.json`,
            sourceInput,
            stats: {
              tokensTotal: 6266,
              unresolvedAnchorCount: 0,
            },
            operatorDecision: {
              state: 'accepted',
              decidedAt: '2026-05-24T13:41:26.000Z',
              decidedBy: 'local-operator',
              artifactSnapshot: {
                assetVersion,
                jobId,
                provenanceObjectName: `${prefix}provenance.json`,
                sourceInput,
                artifactRefs,
              },
            },
          },
        },
      },
    },
    task: {
      id: taskId,
      materialId,
      metadata: {
        cleanServiceJobs: {
          [serviceName]: {
            serviceName,
            status: 'completed',
            materialId,
            parseTaskId: taskId,
            assetVersion,
            jobId,
            sourceInput,
            artifacts: artifactRefs,
          },
        },
      },
    },
  };
}

function compileHelper() {
  rmSync(outDir, { recursive: true, force: true });
  execFileSync('npx', [
    'pnpm@10.4.1',
    'exec',
    'tsc',
    'src/app/utils/rawMaterial2CleanMaterialInputBundle.ts',
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
}

function assertBlocked(result, code) {
  assert.equal(result.ok, false);
  assert.equal(result.code, code);
}

compileHelper();

const helperUrl = pathToFileURL(join(outDir, 'app/utils/rawMaterial2CleanMaterialInputBundle.js'));
const {
  REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES,
  buildRawMaterial2CleanMaterialInputBundle,
} = await import(helperUrl.href);

console.log('=== RawMaterial2CleanMaterial Input Bundle Smoke ===');

{
  console.log('  [1] accepted canonical-shape metadata builds a traceable bundle...');
  const fixture = makeFixture();
  const result = buildRawMaterial2CleanMaterialInputBundle({
    material: fixture.material,
    task: fixture.task,
    currentAssetVersion: 'v4',
  });

  assert.equal(result.ok, true);
  assert.equal(result.bundle.kind, 'raw-material-2-clean-material-input');
  assert.equal(result.bundle.serviceName, 'toc-rebuild');
  assert.equal(result.bundle.materialId, '1842780526581841');
  assert.equal(result.bundle.taskId, 'task-1779085089451');
  assert.equal(result.bundle.assetVersion, 'v4');
  assert.equal(result.bundle.jobId, 'luceon-task-1779085089451-toc-rebuild-v4');
  assert.equal(result.bundle.sourceInput.object, 'mineru/1842780526581841/v1/content_list_v2.json');
  assert.equal(result.bundle.sourceInput.sha256, 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db');
  assert.deepEqual(Object.keys(result.bundle.artifactRefs).sort(), [
    'flooded_content',
    'logic_tree',
    'metrics',
    'provenance',
    'readable_tree',
    'skeleton',
    'unresolved_anchors',
  ]);
  assert.equal(result.bundle.artifactRefs.readable_tree.content, undefined);
}

{
  console.log('  [2] non-accepted decision blocks...');
  const fixture = makeFixture();
  fixture.material.metadata.cleanMaterials['toc-rebuild'].operatorDecision.state = 'needs-repair';
  assertBlocked(buildRawMaterial2CleanMaterialInputBundle(fixture), 'CLEAN_MATERIAL_NOT_ACCEPTED');
}

{
  console.log('  [3] missing sourceInput blocks...');
  const fixture = makeFixture();
  delete fixture.material.metadata.cleanMaterials['toc-rebuild'].sourceInput;
  delete fixture.task.metadata.cleanServiceJobs['toc-rebuild'].sourceInput;
  delete fixture.material.metadata.cleanMaterials['toc-rebuild'].operatorDecision.artifactSnapshot.sourceInput;
  assertBlocked(buildRawMaterial2CleanMaterialInputBundle(fixture), 'MISSING_SOURCE_INPUT');
}

{
  console.log('  [4] missing each required artifact role blocks...');
  for (const role of REQUIRED_RAW_MATERIAL_2_CLEAN_MATERIAL_ARTIFACT_ROLES) {
    const fixture = makeFixture();
    delete fixture.task.metadata.cleanServiceJobs['toc-rebuild'].artifacts[role];
    delete fixture.material.metadata.cleanMaterials['toc-rebuild'].operatorDecision.artifactSnapshot.artifactRefs[role];
    assertBlocked(buildRawMaterial2CleanMaterialInputBundle(fixture), 'MISSING_REQUIRED_ARTIFACT');
  }
}

{
  console.log('  [5] assetVersion mismatch blocks...');
  const fixture = makeFixture();
  assertBlocked(buildRawMaterial2CleanMaterialInputBundle({
    ...fixture,
    currentAssetVersion: 'v5',
  }), 'ASSET_VERSION_MISMATCH');
}

{
  console.log('  [6] material/task/snapshot/current assetVersion signals must align...');
  {
    const fixture = makeFixture();
    fixture.task.metadata.cleanServiceJobs['toc-rebuild'].assetVersion = 'v5';
    assertBlocked(buildRawMaterial2CleanMaterialInputBundle({
      ...fixture,
      currentAssetVersion: 'v4',
    }), 'ASSET_VERSION_MISMATCH');
  }

  {
    const fixture = makeFixture();
    fixture.material.metadata.cleanMaterials['toc-rebuild'].operatorDecision.artifactSnapshot.assetVersion = 'v5';
    assertBlocked(buildRawMaterial2CleanMaterialInputBundle({
      ...fixture,
      currentAssetVersion: 'v4',
    }), 'ASSET_VERSION_MISMATCH');
  }

  {
    const fixture = makeFixture();
    assertBlocked(buildRawMaterial2CleanMaterialInputBundle({
      ...fixture,
      currentAssetVersion: 'v5',
    }), 'ASSET_VERSION_MISMATCH');
  }
}

{
  console.log('  [7] missing jobId blocks...');
  const fixture = makeFixture();
  delete fixture.task.metadata.cleanServiceJobs['toc-rebuild'].jobId;
  delete fixture.material.metadata.cleanMaterials['toc-rebuild'].operatorDecision.artifactSnapshot.jobId;
  assertBlocked(buildRawMaterial2CleanMaterialInputBundle(fixture), 'MISSING_JOB_ID');
}

{
  console.log('  [8] artifact prefix mismatch blocks...');
  const fixture = makeFixture();
  fixture.task.metadata.cleanServiceJobs['toc-rebuild'].artifacts.readable_tree.object = 'toc-rebuild/wrong/v4/readable_tree.md';
  assertBlocked(buildRawMaterial2CleanMaterialInputBundle(fixture), 'ARTIFACT_PREFIX_MISMATCH');
}

{
  console.log('  [9] missing material/task and body-shaped refs block without live reads...');
  assertBlocked(buildRawMaterial2CleanMaterialInputBundle({ material: null, task: makeFixture().task }), 'MATERIAL_MISSING');
  assertBlocked(buildRawMaterial2CleanMaterialInputBundle({ material: makeFixture().material, task: null }), 'TASK_MISSING');

  const fixture = makeFixture();
  fixture.task.metadata.cleanServiceJobs['toc-rebuild'].artifacts.skeleton.content = '{"body":"not allowed"}';
  assertBlocked(buildRawMaterial2CleanMaterialInputBundle(fixture), 'ARTIFACT_BODY_READ_REQUIRED');
}

console.log('RawMaterial2CleanMaterial input bundle smoke passed.');
