import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { Client } from 'minio';
import {
  RAW2CLEAN_DURABLE_BUCKET,
  buildRaw2CleanDurableCandidatePlan,
} from '../services/rawmaterial2cleanmaterial/durable-candidate.mjs';

const materialId = '1842780526581841';
const taskId = 'task-1779085089451';
const dbBaseUrl = process.env.DB_BASE_URL || 'http://localhost:8081/__proxy/db';
const uploadProxyBaseUrl = process.env.UPLOAD_PROXY_BASE_URL || 'http://localhost:8081/__proxy/upload';
const realApply = process.env.RAW2CLEAN_REAL_APPLY === '1';
const candidateJsonPath = process.env.RAW2CLEAN_CANDIDATE_JSON_PATH || '';
const planJsonPath = process.env.RAW2CLEAN_PLAN_JSON_PATH || '';
const outDir = '/tmp/luceon-task282-raw2clean-durable-candidate-apply';
const artifactOutfile = join(outDir, 'app/utils/rawMaterial2CleanMaterialArtifactBackedDraft.js');
const outputOutfile = join(outDir, 'app/utils/rawMaterial2CleanMaterialOutputContract.js');
const algorithmOutfile = join(outDir, 'app/utils/rawMaterial2CleanMaterialAlgorithm.js');
const runnerOutfile = join(outDir, 'app/utils/rawMaterial2CleanMaterialRunner.js');

function sha256Hex(value) {
  return createHash('sha256').update(value).digest('hex');
}

function byteLength(value) {
  return Buffer.byteLength(value, 'utf8');
}

function patchCompiledImports(file, replacements) {
  let compiled = readFileSync(file, 'utf8');
  for (const [from, to] of replacements) compiled = compiled.replaceAll(from, to);
  writeFileSync(file, compiled);
}

function compileHelpers() {
  rmSync(outDir, { recursive: true, force: true });
  execFileSync('npx', [
    'pnpm@10.4.1',
    'exec',
    'tsc',
    'src/app/utils/rawMaterial2CleanMaterialArtifactBackedDraft.ts',
    'src/app/utils/rawMaterial2CleanMaterialOutputContract.ts',
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

  patchCompiledImports(artifactOutfile, [
    ["from './rawMaterial2CleanMaterialAlgorithm';", "from './rawMaterial2CleanMaterialAlgorithm.js';"],
    ["from './rawMaterial2CleanMaterialInputBundle';", "from './rawMaterial2CleanMaterialInputBundle.js';"],
    ["from './rawMaterial2CleanMaterialRunner';", "from './rawMaterial2CleanMaterialRunner.js';"],
  ]);
  patchCompiledImports(outputOutfile, [
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

async function fetchJson(url) {
  const response = await fetch(url);
  assert.equal(response.status, 200, `${url} status`);
  return response.json();
}

async function getDb(path) {
  return fetchJson(`${dbBaseUrl}${path}`);
}

async function patchDb(path, body) {
  const response = await fetch(`${dbBaseUrl}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  assert.equal(response.ok, true, `${path} PATCH status ${response.status}`);
  return response.json().catch(() => ({}));
}

async function getArtifact(ref) {
  const response = await fetch(
    `${uploadProxyBaseUrl}/proxy-file?bucket=${encodeURIComponent(ref.bucket || RAW2CLEAN_DURABLE_BUCKET)}&objectName=${encodeURIComponent(ref.object)}`,
  );
  assert.equal(response.status, 200, `${ref.object} GET status`);
  const body = await response.text();
  assert.equal(sha256Hex(body), ref.sha256, `${ref.object} sha256`);
  return body;
}

function createMinioClient() {
  return new Client({
    endPoint: process.env.RAW2CLEAN_MINIO_ENDPOINT || process.env.MINIO_ENDPOINT || '127.0.0.1',
    port: Number(process.env.RAW2CLEAN_MINIO_PORT || process.env.MINIO_PORT || 9000),
    useSSL: (process.env.RAW2CLEAN_MINIO_USE_SSL || process.env.MINIO_USE_SSL) === 'true',
    accessKey: process.env.MINIO_ACCESS_KEY || 'minioadmin',
    secretKey: process.env.MINIO_SECRET_KEY || 'minioadmin',
  });
}

async function streamToBuffer(stream) {
  const chunks = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  return Buffer.concat(chunks);
}

async function readCandidateObject(client, ref) {
  try {
    const stream = await client.getObject(ref.bucket, ref.object);
    const buffer = await streamToBuffer(stream);
    return {
      exists: true,
      size_bytes: buffer.length,
      sha256: sha256Hex(buffer),
    };
  } catch (error) {
    if (error?.code === 'NoSuchKey' || error?.code === 'NotFound') {
      return { exists: false };
    }
    throw error;
  }
}

async function putCandidateObject(client, ref, content) {
  const existing = await readCandidateObject(client, ref);
  if (existing.exists) {
    if (existing.sha256 !== ref.sha256 || existing.size_bytes !== ref.size_bytes) {
      throw new Error(`target object exists with different content: ${JSON.stringify(existing)}`);
    }
    return { action: 'already-present', existing };
  }

  const buffer = Buffer.from(content, 'utf8');
  await client.putObject(ref.bucket, ref.object, buffer, buffer.length, {
    'Content-Type': 'application/json; charset=utf-8',
  });
  const after = await readCandidateObject(client, ref);
  assert.equal(after.exists, true);
  assert.equal(after.sha256, ref.sha256);
  assert.equal(after.size_bytes, ref.size_bytes);
  return { action: 'putObject', after };
}

function extractAppliedRefs(task, material) {
  const taskSummary = task.metadata?.rawMaterial2CleanMaterialJobs?.['raw-material-2-clean-material'] || null;
  const materialCandidate = material.metadata?.rawMaterial2CleanMaterial?.currentCandidate || null;
  return {
    taskRef: taskSummary?.artifact?.candidate || null,
    materialRef: materialCandidate?.artifact?.candidate || null,
    taskSummary,
    materialCandidate,
  };
}

compileHelpers();
const { buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun } = await import(pathToFileURL(artifactOutfile).href);
const { buildRawMaterial2CleanMaterialOutputContract } = await import(pathToFileURL(outputOutfile).href);

const preMaterial = await getDb(`/materials/${encodeURIComponent(materialId)}`);
const preTask = await getDb(`/tasks/${encodeURIComponent(taskId)}`);

const draftResult = await buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun({
  material: preMaterial,
  task: preTask,
  currentAssetVersion: 'v4',
  options: { now: '2026-05-25T05:20:01.000Z' },
  artifactBodyReader: (ref) => getArtifact(ref),
});
assert.equal(draftResult.ok, true, JSON.stringify(draftResult, null, 2));

const outputResult = buildRawMaterial2CleanMaterialOutputContract({
  draft: draftResult.draft,
  options: { now: '2026-05-25T05:20:01.000Z' },
});
assert.equal(outputResult.ok, true, JSON.stringify(outputResult, null, 2));

const candidateJson = outputResult.canonicalJson;
const candidateArtifactPreview = {
  contentType: 'application/json',
  size_bytes: byteLength(candidateJson),
  sha256: sha256Hex(candidateJson),
};

const plan = buildRaw2CleanDurableCandidatePlan({
  output: outputResult.output,
  existingTask: preTask,
  existingMaterial: preMaterial,
  candidateArtifactPreview,
  now: '2026-05-25T05:20:01.000Z',
});
assert.equal(plan.ok, true, JSON.stringify(plan, null, 2));

if (candidateJsonPath) writeFileSync(candidateJsonPath, candidateJson);
if (planJsonPath) writeFileSync(planJsonPath, JSON.stringify(plan, null, 2));

let writeResult = { action: 'dry-run', existing: null };
let patchResult = { action: 'dry-run', operationCount: 0 };

if (realApply) {
  const client = createMinioClient();
  writeResult = await putCandidateObject(client, plan.candidateRef, candidateJson);
  await patchDb(`/tasks/${encodeURIComponent(taskId)}`, plan.taskPatch);
  await patchDb(`/materials/${encodeURIComponent(materialId)}`, plan.materialPatch);
  patchResult = { action: 'patch', operationCount: 2 };
}

const postTask = await getDb(`/tasks/${encodeURIComponent(taskId)}`);
const postMaterial = await getDb(`/materials/${encodeURIComponent(materialId)}`);
const appliedRefs = extractAppliedRefs(postTask, postMaterial);

if (realApply) {
  assert.deepEqual(appliedRefs.taskRef, plan.candidateRef);
  assert.deepEqual(appliedRefs.materialRef, plan.candidateRef);
}

console.log(JSON.stringify({
  ok: true,
  mode: realApply ? 'real-apply' : 'dry-run',
  candidateRef: plan.candidateRef,
  candidateArtifactPreview,
  outputContractPreview: outputResult.output.preview,
  draftEvidence: draftResult.evidence,
  writeResult,
  patchResult,
  appliedRefs,
  boundaries: {
    minioPutObject: realApply ? (writeResult.action === 'putObject' ? 1 : 0) : 0,
    dbPatch: patchResult.operationCount,
    minioDelete: 0,
    minioList: 0,
    runtimePost: 0,
    dockerOperation: 0,
  },
}, null, 2));
