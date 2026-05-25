import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const outDir = '/tmp/luceon-task276-raw2clean-algorithm-smoke';
const algorithmOutfile = join(outDir, 'app/utils/rawMaterial2CleanMaterialAlgorithm.js');
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
      readable_tree: objectRef(`${prefix}readable_tree.md`, { sha256: 'readable-sha' }),
      logic_tree: objectRef(`${prefix}logic_tree.json`, { sha256: 'logic-sha' }),
      skeleton: objectRef(`${prefix}skeleton.json`, { sha256: 'skeleton-sha' }),
      flooded_content: objectRef(`${prefix}flooded_content.json`, { sha256: 'flooded-sha' }),
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
    readable_tree: '# Unit 1\n\n## Lesson 1\n\nTraceable outline only.',
    logic_tree: JSON.stringify({
      sections: [
        { id: 'logic-sec-1', title: 'Unit 1' },
        { sourceRef: 'logic-sec-1-1', title: 'Lesson 1' },
      ],
    }),
    skeleton: JSON.stringify({
      nodes: [
        { nodeId: 'skel-node-1', title: 'Warm up' },
      ],
    }),
    flooded_content: JSON.stringify({
      blocks: [
        { block_id: 'blk-001', text: 'Read the short passage.' },
        { sourceRef: 'blk-002', text: 'Answer the comprehension question.' },
      ],
    }),
  };
}

function patchCompiledImports(file, replacements) {
  let compiled = readFileSync(file, 'utf8');
  for (const [from, to] of replacements) {
    compiled = compiled.replace(from, to);
  }
  writeFileSync(file, compiled);
}

function compileAlgorithm() {
  rmSync(outDir, { recursive: true, force: true });
  execFileSync('npx', [
    'pnpm@10.4.1',
    'exec',
    'tsc',
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

compileAlgorithm();

const algorithmUrl = pathToFileURL(algorithmOutfile);
const runnerUrl = pathToFileURL(runnerOutfile);
const { buildRawMaterial2CleanMaterialDraftSkeleton } = await import(algorithmUrl.href);
const { buildRawMaterial2CleanMaterialRequest } = await import(runnerUrl.href);

function makeRequest() {
  const requestResult = buildRawMaterial2CleanMaterialRequest(makeBundle());
  assert.equal(requestResult.ok, true);
  return requestResult.request;
}

console.log('=== RawMaterial2CleanMaterial Algorithm Skeleton Smoke ===');

{
  console.log('  [1] mock request plus injected bodies produces traceable draft...');
  const request = makeRequest();
  const result = buildRawMaterial2CleanMaterialDraftSkeleton({
    request,
    artifactBodies: makeArtifactBodies(),
    options: { now: '2026-05-25T01:46:18.000Z' },
  });

  assert.equal(result.ok, true);
  assert.equal(result.draft.kind, 'raw-material-2-clean-material-draft');
  assert.equal(result.draft.protocolVersion, 'v0.mock');
  assert.equal(result.draft.status, 'MOCK_ALGORITHM_DRAFT_READY');
  assert.equal(result.draft.materialId, '1842780526581841');
  assert.equal(result.draft.taskId, 'task-1779085089451');
  assert.equal(result.draft.source.assetVersion, 'v4');
  assert.equal(result.draft.source.jobId, 'luceon-task-1779085089451-toc-rebuild-v4');
  assert.equal(result.draft.source.artifactRefs.flooded_content.sha256, 'flooded-sha');
  assert.equal(result.draft.source.artifactRefs.skeleton.sha256, 'skeleton-sha');
  assert.equal(result.draft.extracted.readableTree.headingCount, 2);
  assert.equal(result.draft.extracted.sections.map((item) => item.sourceRef).includes('logic-sec-1'), true);
  assert.equal(result.draft.extracted.sections.map((item) => item.sourceRef).includes('skel-node-1'), true);
  assert.deepEqual(result.draft.extracted.blocks.map((item) => item.sourceRef), ['blk-001', 'blk-002']);
  assert.equal(result.draft.persistencePlan.mode, 'none');
  assert.equal(result.draft.persistencePlan.writesPlanned, false);
  assert.equal(result.draft.boundaries.dbAccess, false);
  assert.equal(result.draft.boundaries.minioAccess, false);
  assert.equal(result.draft.boundaries.runtimePost, false);
  assert.equal(result.draft.boundaries.dockerOperation, false);
  assert.equal(result.draft.boundaries.generatedFinalArtifact, false);
}

{
  console.log('  [2] numeric stable ids are preserved as source refs...');
  const bodies = makeArtifactBodies();
  bodies.logic_tree = JSON.stringify({
    sections: [
      { id: 101, title: 'Numeric section id' },
    ],
  });
  bodies.skeleton = JSON.stringify({
    nodes: [
      { node_id: 201, title: 'Numeric node id' },
    ],
  });
  bodies.flooded_content = JSON.stringify({
    blocks: [
      { id: 301, text: 'Numeric block id' },
      { block_id: 302, text: 'Numeric snake block id' },
    ],
  });

  const result = buildRawMaterial2CleanMaterialDraftSkeleton({
    request: makeRequest(),
    artifactBodies: bodies,
    options: { now: '2026-05-25T02:04:53.000Z' },
  });

  assert.equal(result.ok, true);
  assert.equal(result.draft.extracted.sections.map((item) => item.sourceRef).includes('101'), true);
  assert.equal(result.draft.extracted.sections.map((item) => item.sourceRef).includes('201'), true);
  assert.deepEqual(result.draft.extracted.blocks.map((item) => item.sourceRef), ['301', '302']);
}

{
  console.log('  [3] real-shaped canonical artifact bodies are traversed safely...');
  const bodies = makeArtifactBodies();
  bodies.logic_tree = JSON.stringify({
    node_id: 'root',
    title: '文档根节点',
    level: 0,
    status: 'pending_anchor',
    evidence: [],
    children: [
      {
        node_id: 'p0_80_77_359_96_title',
        title: '向树叶学习：人工光合作用',
        level: 1,
        status: 'anchored',
        start_block_uid: 'p0_80_77_359_96_title',
        children: [],
      },
    ],
  });
  bodies.skeleton = JSON.stringify({
    blocks: [
      {
        block_uid: 'p0_80_77_359_96_title',
        block_seq_id: 0,
        page_idx: 0,
        type: 'title',
        text: '向树叶学习：人工光合作用',
      },
      {
        block_uid: 'p0_78_120_443_135_paragraph',
        block_seq_id: 1,
        page_idx: 0,
        type: 'paragraph',
        text: 'What if we could take carbon dioxide,',
      },
    ],
  });
  bodies.flooded_content = JSON.stringify([
    [
      {
        type: 'title',
        content: {
          title_content: ['向树叶学习：人工光合作用'],
          level: 1,
        },
        __meta_flooding__: {
          L1_id: 'p0_80_77_359_96_title',
          L1_title: '向树叶学习：人工光合作用',
        },
      },
      {
        type: 'paragraph',
        content: {
          paragraph_content: ['What if we could take carbon dioxide,'],
        },
        __meta_flooding__: {
          L1_id: 'p0_80_77_359_96_title',
          L1_title: '向树叶学习：人工光合作用',
        },
      },
    ],
    [
      {
        type: 'paragraph',
        content: {
          paragraph_content: ['Unreferenced fragment must not become source truth.'],
        },
      },
    ],
  ]);

  const result = buildRawMaterial2CleanMaterialDraftSkeleton({
    request: makeRequest(),
    artifactBodies: bodies,
    options: { now: '2026-05-25T04:36:33.000Z' },
  });

  assert.equal(result.ok, true);
  assert.equal(result.draft.status, 'MOCK_ALGORITHM_DRAFT_READY');
  assert.equal(result.draft.extracted.sections.map((item) => item.sourceRef).includes('root'), true);
  assert.equal(result.draft.extracted.sections.map((item) => item.sourceRef).includes('p0_80_77_359_96_title'), true);
  assert.equal(result.draft.extracted.sections.map((item) => item.sourceRef).includes('p0_78_120_443_135_paragraph'), true);
  assert.deepEqual(result.draft.extracted.blocks.map((item) => item.sourceRef), [
    'p0_80_77_359_96_title',
    'p0_80_77_359_96_title',
  ]);
  assert.equal(result.draft.extracted.blocks.some((item) => item.text === 'Unreferenced fragment must not become source truth.'), false);
  assert.equal(result.draft.quality.warnings.includes('flooded_content:skipped-unreferenced-text-fragments=1'), true);
}

{
  console.log('  [4] missing request and wrong kind/mode block...');
  assertBlocked(buildRawMaterial2CleanMaterialDraftSkeleton({
    request: null,
    artifactBodies: makeArtifactBodies(),
  }), 'MISSING_REQUEST');

  assertBlocked(buildRawMaterial2CleanMaterialDraftSkeleton({
    request: { kind: 'not-the-request-kind', mode: 'mock-dry-run' },
    artifactBodies: makeArtifactBodies(),
  }), 'UNSUPPORTED_REQUEST_KIND');

  const request = makeRequest();
  request.mode = 'real-run';
  assertBlocked(buildRawMaterial2CleanMaterialDraftSkeleton({
    request,
    artifactBodies: makeArtifactBodies(),
  }), 'UNSUPPORTED_MODE');
}

{
  console.log('  [5] missing or invalid artifact body blocks...');
  const bodies = makeArtifactBodies();
  delete bodies.flooded_content;
  assertBlocked(buildRawMaterial2CleanMaterialDraftSkeleton({
    request: makeRequest(),
    artifactBodies: bodies,
  }), 'MISSING_ARTIFACT_BODY');

  const invalidBodies = makeArtifactBodies();
  invalidBodies.logic_tree = '{not-json';
  assertBlocked(buildRawMaterial2CleanMaterialDraftSkeleton({
    request: makeRequest(),
    artifactBodies: invalidBodies,
  }), 'INVALID_ARTIFACT_BODY');
}

{
  console.log('  [6] source-derived items without references block...');
  const bodies = makeArtifactBodies();
  bodies.flooded_content = JSON.stringify({
    blocks: [
      { text: 'This text has no block id.' },
    ],
  });
  assertBlocked(buildRawMaterial2CleanMaterialDraftSkeleton({
    request: makeRequest(),
    artifactBodies: bodies,
  }), 'MISSING_SOURCE_REFERENCE');
}

{
  console.log('  [7] live dependency markers block...');
  const bodies = makeArtifactBodies();
  bodies.liveDependencies = { minioClient: {}, dbClient: {} };
  assertBlocked(buildRawMaterial2CleanMaterialDraftSkeleton({
    request: makeRequest(),
    artifactBodies: bodies,
  }), 'LIVE_DEPENDENCY_NOT_ALLOWED');
}

console.log('RawMaterial2CleanMaterial algorithm skeleton smoke passed.');
