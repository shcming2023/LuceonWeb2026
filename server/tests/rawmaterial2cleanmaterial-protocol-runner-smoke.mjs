import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const outDir = '/tmp/luceon-task275-raw2clean-runner-smoke';
const runnerOutfile = join(outDir, 'app/utils/rawMaterial2CleanMaterialRunner.js');

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

function makeBundle() {
  const materialId = '1842780526581841';
  const taskId = 'task-1779085089451';
  const serviceName = 'toc-rebuild';
  const assetVersion = 'v4';
  const jobId = 'luceon-task-1779085089451-toc-rebuild-v4';
  const prefix = `${serviceName}/${materialId}/${assetVersion}/`;

  return {
    kind: 'raw-material-2-clean-material-input',
    serviceName,
    materialId,
    taskId,
    assetVersion,
    jobId,
    provenanceObjectName: `${prefix}provenance.json`,
    sourceInput: {
      bucket: 'eduassets-raw',
      object: `mineru/${materialId}/v1/content_list_v2.json`,
      sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
      size_bytes: 31543,
    },
    artifactRefs: {
      readable_tree: objectRef(`${prefix}readable_tree.md`),
      logic_tree: objectRef(`${prefix}logic_tree.json`),
      skeleton: objectRef(`${prefix}skeleton.json`),
      flooded_content: objectRef(`${prefix}flooded_content.json`),
      metrics: objectRef(`${prefix}metrics.json`),
      provenance: objectRef(`${prefix}provenance.json`),
      unresolved_anchors: objectRef(`${prefix}unresolved_anchors.json`),
    },
    operatorDecision: {
      state: 'accepted',
      decidedAt: '2026-05-24T13:41:26.000Z',
      decidedBy: 'local-operator',
    },
  };
}

function compileRunner() {
  rmSync(outDir, { recursive: true, force: true });
  execFileSync('npx', [
    'pnpm@10.4.1',
    'exec',
    'tsc',
    'src/app/utils/rawMaterial2CleanMaterialRunner.ts',
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

  const compiled = readFileSync(runnerOutfile, 'utf8');
  writeFileSync(
    runnerOutfile,
    compiled.replace(
      "from './rawMaterial2CleanMaterialInputBundle';",
      "from './rawMaterial2CleanMaterialInputBundle.js';",
    ),
  );
}

function assertBlocked(result, code) {
  assert.equal(result.ok, false);
  assert.equal(result.code, code);
}

compileRunner();

const runnerUrl = pathToFileURL(runnerOutfile);
const {
  RAW_MATERIAL_2_CLEAN_MATERIAL_DRY_RUN_STATUS,
  buildRawMaterial2CleanMaterialRequest,
  runRawMaterial2CleanMaterialMockDryRun,
} = await import(runnerUrl.href);

console.log('=== RawMaterial2CleanMaterial Protocol Runner Smoke ===');

{
  console.log('  [1] accepted bundle builds request and mock dry-run succeeds...');
  const bundle = makeBundle();
  const requestResult = buildRawMaterial2CleanMaterialRequest(bundle);

  assert.equal(requestResult.ok, true);
  assert.equal(requestResult.request.kind, 'raw-material-2-clean-material-request');
  assert.equal(requestResult.request.protocolVersion, 'v0.mock');
  assert.equal(requestResult.request.mode, 'mock-dry-run');
  assert.equal(requestResult.request.materialId, '1842780526581841');
  assert.equal(requestResult.request.taskId, 'task-1779085089451');
  assert.equal(requestResult.request.source.cleanServiceName, 'toc-rebuild');
  assert.equal(requestResult.request.source.assetVersion, 'v4');
  assert.equal(requestResult.request.source.jobId, 'luceon-task-1779085089451-toc-rebuild-v4');
  assert.equal(requestResult.request.source.operatorDecision.state, 'accepted');
  assert.equal(requestResult.request.source.artifactRefs.readable_tree.content, undefined);

  const dryRun = runRawMaterial2CleanMaterialMockDryRun(requestResult.request);
  assert.equal(dryRun.ok, true);
  assert.equal(dryRun.status, RAW_MATERIAL_2_CLEAN_MATERIAL_DRY_RUN_STATUS);
  assert.equal(dryRun.classification, 'MOCK_DRY_RUN_SUCCESS');
  assert.equal(dryRun.summary.sourceCleanMaterial.assetVersion, 'v4');
  assert.equal(dryRun.summary.output.category, 'raw-material-2-clean-material-draft');
  assert.equal(dryRun.summary.output.writePlanned, false);
  assert.equal(dryRun.summary.boundaries.dbAccess, false);
  assert.equal(dryRun.summary.boundaries.minioAccess, false);
  assert.equal(dryRun.summary.boundaries.runtimePost, false);
  assert.equal(dryRun.summary.boundaries.dockerOperation, false);
  assert.deepEqual(dryRun.summary.artifactRolesToReadLater.sort(), [
    'flooded_content',
    'logic_tree',
    'metrics',
    'provenance',
    'readable_tree',
    'skeleton',
    'unresolved_anchors',
  ]);
}

{
  console.log('  [2] runner accepts bundle directly...');
  const result = runRawMaterial2CleanMaterialMockDryRun(makeBundle());
  assert.equal(result.ok, true);
  assert.equal(result.status, 'MOCK_DRY_RUN_SUCCESS');
}

{
  console.log('  [3] missing input and unsupported kind block...');
  assertBlocked(runRawMaterial2CleanMaterialMockDryRun(null), 'MISSING_INPUT_BUNDLE');
  assertBlocked(runRawMaterial2CleanMaterialMockDryRun({ kind: 'not-a-raw2clean-request' }), 'UNSUPPORTED_INPUT_KIND');
}

{
  console.log('  [4] unsupported mode blocks...');
  const requestResult = buildRawMaterial2CleanMaterialRequest(makeBundle());
  assert.equal(requestResult.ok, true);
  requestResult.request.mode = 'real-run';
  assertBlocked(runRawMaterial2CleanMaterialMockDryRun(requestResult.request), 'UNSUPPORTED_MODE');
}

{
  console.log('  [5] non-accepted operator decision blocks...');
  const bundle = makeBundle();
  bundle.operatorDecision.state = 'needs-repair';
  assertBlocked(buildRawMaterial2CleanMaterialRequest(bundle), 'CLEAN_MATERIAL_NOT_ACCEPTED');
}

{
  console.log('  [6] missing required artifact blocks...');
  const bundle = makeBundle();
  delete bundle.artifactRefs.skeleton;
  assertBlocked(buildRawMaterial2CleanMaterialRequest(bundle), 'MISSING_REQUIRED_ARTIFACT');
}

{
  console.log('  [7] body-shaped artifact refs block...');
  const bundle = makeBundle();
  bundle.artifactRefs.logic_tree.content = '{"body":"not allowed"}';
  assertBlocked(buildRawMaterial2CleanMaterialRequest(bundle), 'ARTIFACT_BODY_READ_REQUIRED');
}

{
  console.log('  [8] live dependency markers block...');
  const bundle = makeBundle();
  bundle.liveDependencies = { dbClient: {}, minioClient: {} };
  assertBlocked(runRawMaterial2CleanMaterialMockDryRun(bundle), 'LIVE_DEPENDENCY_NOT_ALLOWED');
}

console.log('RawMaterial2CleanMaterial protocol runner smoke passed.');
