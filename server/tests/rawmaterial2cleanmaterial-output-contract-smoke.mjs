import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const outDir = '/tmp/luceon-task281-raw2clean-output-contract-smoke';
const contractOutfile = join(outDir, 'app/utils/rawMaterial2CleanMaterialOutputContract.js');
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

function makeArtifactBodies() {
  return {
    readable_tree: '# Unit 1\n\n## Lesson 1\n\nArtifact-backed fake body.',
    logic_tree: JSON.stringify({
      node_id: 'root',
      title: 'Document root',
      children: [
        { node_id: 'logic-sec-1', title: 'Unit 1', children: [] },
      ],
    }),
    skeleton: JSON.stringify({
      blocks: [
        { block_uid: 'skel-node-1', title: 'Warm up' },
      ],
    }),
    flooded_content: JSON.stringify([
      [
        {
          type: 'paragraph',
          content: { paragraph_content: [{ type: 'text', content: 'Read the short passage.' }] },
          __meta_flooding__: { L1_id: 'logic-sec-1', L1_title: 'Unit 1' },
        },
        {
          type: 'paragraph',
          content: { paragraph_content: [{ type: 'text', content: 'Answer the question.' }] },
          __meta_flooding__: { L1_id: 'logic-sec-1', L1_title: 'Unit 1' },
        },
      ],
    ]),
  };
}

function patchCompiledImports(file, replacements) {
  let compiled = readFileSync(file, 'utf8');
  for (const [from, to] of replacements) {
    compiled = compiled.replace(from, to);
  }
  writeFileSync(file, compiled);
}

function compileContract() {
  rmSync(outDir, { recursive: true, force: true });
  execFileSync('npx', [
    'pnpm@10.4.1',
    'exec',
    'tsc',
    'src/app/utils/rawMaterial2CleanMaterialOutputContract.ts',
    'src/app/utils/rawMaterial2CleanMaterialAlgorithm.ts',
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

  patchCompiledImports(contractOutfile, [
    ["from './rawMaterial2CleanMaterialAlgorithm';", "from './rawMaterial2CleanMaterialAlgorithm.js';"],
    ["from './rawMaterial2CleanMaterialInputBundle';", "from './rawMaterial2CleanMaterialInputBundle.js';"],
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

function asRecord(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : null;
}

function sortStable(value) {
  if (Array.isArray(value)) return value.map(sortStable);
  const record = asRecord(value);
  if (!record) return value;

  return Object.keys(record)
    .sort()
    .reduce((sorted, key) => {
      sorted[key] = sortStable(record[key]);
      return sorted;
    }, {});
}

function stableJson(value) {
  return JSON.stringify(sortStable(value));
}

compileContract();

const contractUrl = pathToFileURL(contractOutfile);
const algorithmUrl = pathToFileURL(algorithmOutfile);
const runnerUrl = pathToFileURL(runnerOutfile);
const { buildRawMaterial2CleanMaterialOutputContract } = await import(contractUrl.href);
const { buildRawMaterial2CleanMaterialDraftSkeleton } = await import(algorithmUrl.href);
const { buildRawMaterial2CleanMaterialRequest } = await import(runnerUrl.href);

function makeDraft() {
  const requestResult = buildRawMaterial2CleanMaterialRequest(makeBundle());
  assert.equal(requestResult.ok, true);
  const draftResult = buildRawMaterial2CleanMaterialDraftSkeleton({
    request: requestResult.request,
    artifactBodies: makeArtifactBodies(),
    options: { now: '2026-05-25T05:06:54.000Z' },
  });
  assert.equal(draftResult.ok, true);
  return draftResult.draft;
}

console.log('=== RawMaterial2CleanMaterial Output Contract Smoke ===');

{
  console.log('  [1] ready draft becomes deterministic output preview...');
  const draft = makeDraft();
  const result = buildRawMaterial2CleanMaterialOutputContract({
    draft,
    options: { now: '2026-05-25T05:06:54.000Z' },
  });
  assert.equal(result.ok, true);
  assert.equal(result.output.kind, 'raw-material-2-clean-material-output-candidate');
  assert.equal(result.output.contractVersion, 'v0.dry-run');
  assert.equal(result.output.materialId, '1842780526581841');
  assert.equal(result.output.taskId, 'task-1779085089451');
  assert.equal(result.output.sourceCleanMaterial.assetVersion, 'v4');
  assert.equal(result.output.sourceInput.sha256, 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db');
  assert.equal(result.output.sourceArtifacts.flooded_content.object, 'toc-rebuild/1842780526581841/v4/flooded_content.json');
  assert.equal(result.output.sections.every((item) => item.sourceRef), true);
  assert.equal(result.output.blocks.every((item) => item.sourceRef), true);
  assert.equal(result.output.blocks[0].text, 'Read the short passage.');
  assert.equal(result.output.provenance.draftStatus, 'MOCK_ALGORITHM_DRAFT_READY');
  assert.equal(result.output.persistencePlan.writesPlanned, false);
  assert.equal(result.output.boundaries.dbWrites, false);
  assert.equal(result.output.boundaries.minioWrites, false);
  assert.equal(result.output.boundaries.runtimePost, false);
  assert.equal(result.output.boundaries.durableArtifactCreated, false);
  assert.equal(result.output.preview.contentType, 'application/json');
  assert.match(result.output.preview.sha256, /^[a-f0-9]{64}$/);
  assert.equal(result.output.preview.size_bytes > 0, true);

  const resultAgain = buildRawMaterial2CleanMaterialOutputContract({
    draft,
    options: { now: '2026-05-25T05:06:54.000Z' },
  });
  assert.equal(resultAgain.ok, true);
  assert.equal(resultAgain.canonicalJson, result.canonicalJson);
  assert.equal(resultAgain.output.preview.sha256, result.output.preview.sha256);

  const canonicalHash = createHash('sha256').update(stableJson({
    ...result.output,
    preview: {
      contentType: 'application/json',
      size_bytes: 0,
      sha256: 'pending',
    },
  })).digest('hex');
  assert.equal(result.output.preview.sha256, canonicalHash);
}

{
  console.log('  [2] missing or unsupported draft blocks...');
  assertBlocked(buildRawMaterial2CleanMaterialOutputContract({ draft: null }), 'MISSING_DRAFT');

  const draft = makeDraft();
  draft.kind = 'wrong-kind';
  assertBlocked(buildRawMaterial2CleanMaterialOutputContract({ draft }), 'UNSUPPORTED_DRAFT_KIND');

  const notReadyDraft = makeDraft();
  notReadyDraft.status = 'NOT_READY';
  assertBlocked(buildRawMaterial2CleanMaterialOutputContract({ draft: notReadyDraft }), 'DRAFT_NOT_READY');
}

{
  console.log('  [3] missing source refs and live dependency markers block...');
  const draft = makeDraft();
  draft.extracted.blocks[0].sourceRef = '';
  assertBlocked(buildRawMaterial2CleanMaterialOutputContract({ draft }), 'MISSING_SOURCE_REFERENCE');

  const liveDraft = makeDraft();
  liveDraft.liveDependencies = { dbClient: {}, minioClient: {} };
  assertBlocked(buildRawMaterial2CleanMaterialOutputContract({ draft: liveDraft }), 'LIVE_DEPENDENCY_NOT_ALLOWED');
}

console.log('RawMaterial2CleanMaterial output contract smoke passed.');
