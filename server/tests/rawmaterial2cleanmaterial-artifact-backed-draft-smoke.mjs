import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const outDir = '/tmp/luceon-task277-raw2clean-artifact-backed-smoke';
const helperOutfile = join(outDir, 'app/utils/rawMaterial2CleanMaterialArtifactBackedDraft.js');
const algorithmOutfile = join(outDir, 'app/utils/rawMaterial2CleanMaterialAlgorithm.js');
const runnerOutfile = join(outDir, 'app/utils/rawMaterial2CleanMaterialRunner.js');

function objectRef(object, extra = {}) {
  return {
    bucket: 'eduassets-clean',
    object,
    sha256: `${object.split('/').pop()}-sha`,
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

function bodyForRole(role) {
  if (role === 'readable_tree') return '# Unit 1\n\n## Lesson 1\n\nArtifact-backed fake body.';
  if (role === 'logic_tree') {
    return JSON.stringify({
      sections: [
        { id: 101, title: 'Numeric section id' },
        { sourceRef: 'logic-sec-2', title: 'String section id' },
      ],
    });
  }
  if (role === 'skeleton') {
    return JSON.stringify({
      nodes: [
        { node_id: 201, title: 'Numeric node id' },
      ],
    });
  }
  if (role === 'flooded_content') {
    return JSON.stringify({
      blocks: [
        { id: 301, text: 'Numeric block id text.' },
        { block_id: 'blk-302', text: 'String block id text.' },
      ],
    });
  }
  throw new Error(`unexpected optional artifact read: ${role}`);
}

function patchCompiledImports(file, replacements) {
  let compiled = readFileSync(file, 'utf8');
  for (const [from, to] of replacements) {
    compiled = compiled.replace(from, to);
  }
  writeFileSync(file, compiled);
}

function compileHelper() {
  rmSync(outDir, { recursive: true, force: true });
  execFileSync('npx', [
    'pnpm@10.4.1',
    'exec',
    'tsc',
    'src/app/utils/rawMaterial2CleanMaterialArtifactBackedDraft.ts',
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

  patchCompiledImports(helperOutfile, [
    ["from './rawMaterial2CleanMaterialAlgorithm';", "from './rawMaterial2CleanMaterialAlgorithm.js';"],
    ["from './rawMaterial2CleanMaterialInputBundle';", "from './rawMaterial2CleanMaterialInputBundle.js';"],
    ["from './rawMaterial2CleanMaterialRunner';", "from './rawMaterial2CleanMaterialRunner.js';"],
  ]);
  patchCompiledImports(algorithmOutfile, [
    ["from './rawMaterial2CleanMaterialRunner';", "from './rawMaterial2CleanMaterialRunner.js';"],
    ["from './rawMaterial2CleanMaterialInputBundle';", "from './rawMaterial2CleanMaterialInputBundle.js';"],
  ]);
  patchCompiledImports(runnerOutfile, [
    ["from './rawMaterial2CleanMaterialInputBundle';", "from './rawMaterial2CleanMaterialInputBundle.js';"],
  ]);
}

function assertBlocked(result, code) {
  assert.equal(result.ok, false);
  assert.equal(result.code, code);
}

compileHelper();

const helperUrl = pathToFileURL(helperOutfile);
const {
  buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun,
} = await import(helperUrl.href);

console.log('=== RawMaterial2CleanMaterial Artifact-Backed Draft Smoke ===');

{
  console.log('  [1] accepted bundle plus fake read-only reader produces draft...');
  const reads = [];
  const result = await buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun({
    bundle: makeBundle(),
    options: { now: '2026-05-25T02:26:04.000Z' },
    artifactBodyReader: (ref, role) => {
      reads.push({ role, object: ref.object });
      return bodyForRole(role);
    },
  });

  assert.equal(result.ok, true);
  assert.equal(result.draft.status, 'MOCK_ALGORITHM_DRAFT_READY');
  assert.deepEqual(result.evidence.rolesRead, [
    'readable_tree',
    'logic_tree',
    'skeleton',
    'flooded_content',
  ]);
  assert.deepEqual(reads.map((read) => read.role), [
    'readable_tree',
    'logic_tree',
    'skeleton',
    'flooded_content',
  ]);
  assert.equal(reads.some((read) => read.role === 'metrics'), false);
  assert.equal(result.evidence.boundaries.optionalArtifactsRead, false);
  assert.equal(result.evidence.boundaries.dbWrites, false);
  assert.equal(result.evidence.boundaries.minioWrites, false);
  assert.equal(result.evidence.boundaries.runtimePost, false);
  assert.equal(result.evidence.sectionCount, 3);
  assert.equal(result.evidence.blockCount, 2);
  assert.deepEqual(result.evidence.sampleSourceRefs, ['101', 'logic-sec-2', '201', '301', 'blk-302']);
  assert.equal(result.evidence.sourceInput.sha256, 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db');
}

{
  console.log('  [2] request input is accepted directly...');
  const runnerUrl = pathToFileURL(runnerOutfile);
  const { buildRawMaterial2CleanMaterialRequest } = await import(runnerUrl.href);
  const requestResult = buildRawMaterial2CleanMaterialRequest(makeBundle());
  assert.equal(requestResult.ok, true);

  const result = await buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun({
    request: requestResult.request,
    artifactBodyReader: (_ref, role) => bodyForRole(role),
  });

  assert.equal(result.ok, true);
  assert.equal(result.draft.status, 'MOCK_ALGORITHM_DRAFT_READY');
}

{
  console.log('  [3] missing input or reader blocks...');
  assertBlocked(await buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun({
    artifactBodyReader: (_ref, role) => bodyForRole(role),
  }), 'MISSING_INPUT');

  assertBlocked(await buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun({
    bundle: makeBundle(),
  }), 'MISSING_ARTIFACT_READER');
}

{
  console.log('  [4] read failure and draft failure block structurally...');
  assertBlocked(await buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun({
    bundle: makeBundle(),
    artifactBodyReader: (_ref, role) => {
      if (role === 'skeleton') throw new Error('fake read failure');
      return bodyForRole(role);
    },
  }), 'ARTIFACT_READ_FAILED');

  assertBlocked(await buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun({
    bundle: makeBundle(),
    artifactBodyReader: (_ref, role) => {
      if (role === 'flooded_content') return JSON.stringify({ blocks: [{ text: 'missing source ref' }] });
      return bodyForRole(role);
    },
  }), 'DRAFT_BUILD_BLOCKED');
}

{
  console.log('  [5] live dependency markers block...');
  const bundle = makeBundle();
  bundle.liveDependencies = { dbClient: {}, minioClient: {} };
  assertBlocked(await buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun({
    bundle,
    artifactBodyReader: (_ref, role) => bodyForRole(role),
  }), 'LIVE_DEPENDENCY_NOT_ALLOWED');
}

console.log('RawMaterial2CleanMaterial artifact-backed draft smoke passed.');
