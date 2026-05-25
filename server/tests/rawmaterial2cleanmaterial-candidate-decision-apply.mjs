import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import {
  RAW2CLEAN_ACCEPTED_DECISION_SHA,
  RAW2CLEAN_ACCEPTED_DECISION_SIZE,
  RAW2CLEAN_DECISION_MATERIAL_ID,
  RAW2CLEAN_DECISION_TASK_ID,
  buildRaw2CleanAcceptedDecisionPlan,
} from '../services/rawmaterial2cleanmaterial/candidate-decision.mjs';
import { RAW2CLEAN_DURABLE_BUCKET, RAW2CLEAN_DURABLE_OBJECT } from '../services/rawmaterial2cleanmaterial/durable-candidate.mjs';

const dbBaseUrl = process.env.DB_BASE_URL || 'http://localhost:8081/__proxy/db';
const uploadProxyBaseUrl = process.env.UPLOAD_PROXY_BASE_URL || 'http://localhost:8081/__proxy/upload';
const realApply = process.env.RAW2CLEAN_DECISION_REAL_APPLY === '1';

function sha256Hex(value) {
  return createHash('sha256').update(value).digest('hex');
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

async function readCandidateArtifact() {
  const response = await fetch(
    `${uploadProxyBaseUrl}/proxy-file?bucket=${encodeURIComponent(RAW2CLEAN_DURABLE_BUCKET)}&objectName=${encodeURIComponent(RAW2CLEAN_DURABLE_OBJECT)}`,
  );
  assert.equal(response.status, 200, `${RAW2CLEAN_DURABLE_OBJECT} GET status`);
  const body = await response.text();
  const sha256 = sha256Hex(body);
  const size_bytes = Buffer.byteLength(body, 'utf8');
  assert.equal(sha256, RAW2CLEAN_ACCEPTED_DECISION_SHA, 'candidate artifact sha256');
  assert.equal(size_bytes, RAW2CLEAN_ACCEPTED_DECISION_SIZE, 'candidate artifact size');
  return { status: response.status, sha256, size_bytes };
}

function extractDecision(task, material) {
  const taskSummary = task.metadata?.rawMaterial2CleanMaterialJobs?.['raw-material-2-clean-material'] || null;
  const currentCandidate = material.metadata?.rawMaterial2CleanMaterial?.currentCandidate || null;
  const versionCandidate = material.metadata?.rawMaterial2CleanMaterial?.candidates?.v1 || null;
  const currentDecision = material.metadata?.rawMaterial2CleanMaterial?.currentDecision || null;
  return {
    taskStatus: taskSummary?.status || null,
    taskCleanState: taskSummary?.cleanState || null,
    taskDecision: taskSummary?.decision || null,
    materialStatus: currentCandidate?.status || null,
    materialCleanState: currentCandidate?.cleanState || null,
    materialDecision: currentCandidate?.decision || null,
    versionDecision: versionCandidate?.decision || null,
    currentDecision,
  };
}

const preTask = await getDb(`/tasks/${encodeURIComponent(RAW2CLEAN_DECISION_TASK_ID)}`);
const preMaterial = await getDb(`/materials/${encodeURIComponent(RAW2CLEAN_DECISION_MATERIAL_ID)}`);
const artifactReadback = await readCandidateArtifact();
const plan = buildRaw2CleanAcceptedDecisionPlan({
  existingTask: preTask,
  existingMaterial: preMaterial,
  artifactReadback,
  now: '2026-05-25T05:54:05.000Z',
});
assert.equal(plan.ok, true, JSON.stringify(plan, null, 2));

let patchResult = { action: 'dry-run', operationCount: 0 };
if (realApply) {
  await patchDb(`/tasks/${encodeURIComponent(RAW2CLEAN_DECISION_TASK_ID)}`, plan.taskPatch);
  await patchDb(`/materials/${encodeURIComponent(RAW2CLEAN_DECISION_MATERIAL_ID)}`, plan.materialPatch);
  patchResult = { action: 'patch', operationCount: 2 };
}

const postTask = await getDb(`/tasks/${encodeURIComponent(RAW2CLEAN_DECISION_TASK_ID)}`);
const postMaterial = await getDb(`/materials/${encodeURIComponent(RAW2CLEAN_DECISION_MATERIAL_ID)}`);
const postDecision = extractDecision(postTask, postMaterial);

if (realApply) {
  assert.equal(postDecision.taskStatus, 'accepted');
  assert.equal(postDecision.taskCleanState, 'accepted-candidate');
  assert.equal(postDecision.taskDecision?.state, 'accepted');
  assert.equal(postDecision.materialStatus, 'accepted');
  assert.equal(postDecision.materialCleanState, 'accepted-candidate');
  assert.equal(postDecision.materialDecision?.state, 'accepted');
  assert.equal(postDecision.versionDecision?.state, 'accepted');
  assert.equal(postDecision.currentDecision?.state, 'accepted');
  assert.equal(postDecision.currentDecision?.candidate?.sha256, RAW2CLEAN_ACCEPTED_DECISION_SHA);
}

console.log(JSON.stringify({
  ok: true,
  mode: realApply ? 'real-apply' : 'dry-run',
  artifactReadback,
  decision: plan.decision,
  patchResult,
  postDecision,
  boundaries: {
    dbPatch: patchResult.operationCount,
    minioPutObject: 0,
    minioDelete: 0,
    minioList: 0,
    runtimePost: 0,
    dockerOperation: 0,
  },
}, null, 2));
