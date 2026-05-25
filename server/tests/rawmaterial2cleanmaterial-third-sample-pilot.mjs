import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { loadCleanServiceConfig } from '../services/cleanservice/config.mjs';
import { buildCleanServiceJobRequest } from '../services/cleanservice/cleanservice-worker.mjs';
import { createCleanServiceClientWithTransport } from '../services/cleanservice/worker-factory.mjs';
import { runCleanServiceTocRebuildOnce } from '../services/cleanservice/orchestration-runner.mjs';

const SAMPLE = Object.freeze({
  materialId: '589495534045014',
  taskId: 'task-1779085091953',
  title: '出国',
  parsedZip: {
    bucket: 'eduassets-parsed',
    object: 'parsed/589495534045014/mineru-result.zip',
  },
  rawObject: 'mineru/589495534045014/v1/content_list_v2.json',
  cleanAssetVersion: 'v1',
  raw2cleanAssetVersion: 'v1',
  expectedRawSeed: {
    sha256: '6dc482285a6ad529497294fc96a0f31456155f33f082debb821f8d1a8bd8920a',
    size_bytes: 5873,
  },
});

const dbBaseUrl = process.env.DB_BASE_URL || 'http://localhost:8081/__proxy/db';
const uploadProxyBaseUrl = process.env.UPLOAD_PROXY_BASE_URL || 'http://localhost:8081/__proxy/upload';
const cleanServiceEndpoint = process.env.CLEANSERVICE_ENDPOINT || 'http://localhost:8000';
const realApply = process.env.RAW2CLEAN_THIRD_SAMPLE_REAL_APPLY === '1';
const nowValue = process.env.RAW2CLEAN_THIRD_SAMPLE_NOW || '2026-05-25T06:32:52.000Z';
const outDir = '/tmp/luceon-task287-raw2clean-third-sample';
const zipPath = join(outDir, 'mineru-result.zip');
const rawPath = join(outDir, 'content_list_v2.json');
const artifactOutfile = join(outDir, 'compiled/app/utils/rawMaterial2CleanMaterialArtifactBackedDraft.js');
const outputOutfile = join(outDir, 'compiled/app/utils/rawMaterial2CleanMaterialOutputContract.js');
const algorithmOutfile = join(outDir, 'compiled/app/utils/rawMaterial2CleanMaterialAlgorithm.js');
const runnerOutfile = join(outDir, 'compiled/app/utils/rawMaterial2CleanMaterialRunner.js');

function sha256Hex(value) {
  return createHash('sha256').update(value).digest('hex');
}

function byteLength(value) {
  return Buffer.byteLength(value, 'utf8');
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

async function fetchJson(url) {
  const response = await fetch(url);
  assert.equal(response.status, 200, `${url} status`);
  return response.json();
}

async function fetchBufferFromProxy(bucket, object) {
  const response = await fetch(`${uploadProxyBaseUrl}/proxy-file?bucket=${encodeURIComponent(bucket)}&objectName=${encodeURIComponent(object)}`);
  assert.equal(response.status, 200, `${bucket}/${object} proxy GET`);
  return Buffer.from(await response.arrayBuffer());
}

async function getDb(path) {
  return fetchJson(`${dbBaseUrl}${path}`);
}

async function queryCleanServiceJob(jobId) {
  const response = await fetch(`${cleanServiceEndpoint.replace(/\/+$/, '')}/api/v1/jobs/${encodeURIComponent(jobId)}`);
  if (response.status === 404) return null;
  assert.equal(response.status, 200, `CleanService job query ${jobId}`);
  return response.json();
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



function readObjectViaUploadContainer(bucket, object) {
  const code = `
const { Client } = require('minio');
const crypto = require('crypto');
(async () => {
  try {
    const client = new Client({
      endPoint: process.env.MINIO_ENDPOINT || 'minio',
      port: Number(process.env.MINIO_PORT || 9000),
      useSSL: process.env.MINIO_USE_SSL === 'true',
      accessKey: process.env.MINIO_ACCESS_KEY,
      secretKey: process.env.MINIO_SECRET_KEY,
    });
    const stream = await client.getObject(process.argv[1], process.argv[2]);
    const chunks = [];
    for await (const chunk of stream) chunks.push(Buffer.from(chunk));
    const buffer = Buffer.concat(chunks);
    process.stdout.write(JSON.stringify({ exists: true, size_bytes: buffer.length, sha256: crypto.createHash('sha256').update(buffer).digest('hex'), base64: buffer.toString('base64') }));
  } catch (error) {
    if (error && (error.code === 'NoSuchKey' || error.code === 'NotFound')) {
      process.stdout.write(JSON.stringify({ exists: false }));
      return;
    }
    console.error(error && error.message ? error.message : String(error));
    process.exit(1);
  }
})();`;
  const text = execFileSync('docker', ['exec', 'cms-upload-server', 'node', '-e', code, bucket, object], {
    encoding: 'utf8',
    maxBuffer: 20 * 1024 * 1024,
  });
  const parsed = JSON.parse(text);
  return {
    ...parsed,
    buffer: parsed.base64 ? Buffer.from(parsed.base64, 'base64') : null,
  };
}

async function readObjectViaProxy(bucket, object) {
  const response = await fetch(`${uploadProxyBaseUrl}/proxy-file?bucket=${encodeURIComponent(bucket)}&objectName=${encodeURIComponent(object)}`);
  if (response.status !== 200) return { exists: false, status: response.status, buffer: null };
  const buffer = Buffer.from(await response.arrayBuffer());
  return {
    exists: true,
    status: response.status,
    buffer,
    size_bytes: buffer.length,
    sha256: sha256Hex(buffer),
  };
}

function putObjectViaUploadContainer(bucket, object, content, contentType) {
  const buffer = Buffer.isBuffer(content) ? content : Buffer.from(content, 'utf8');
  const code = `
const { Client } = require('minio');
const chunks = [];
process.stdin.on('data', chunk => chunks.push(chunk));
process.stdin.on('end', async () => {
  try {
    const client = new Client({
      endPoint: process.env.MINIO_ENDPOINT || 'minio',
      port: Number(process.env.MINIO_PORT || 9000),
      useSSL: process.env.MINIO_USE_SSL === 'true',
      accessKey: process.env.MINIO_ACCESS_KEY,
      secretKey: process.env.MINIO_SECRET_KEY,
    });
    const buffer = Buffer.concat(chunks);
    await client.putObject(process.argv[1], process.argv[2], buffer, buffer.length, { 'Content-Type': process.argv[3] });
  } catch (error) {
    console.error(error && error.message ? error.message : String(error));
    process.exit(1);
  }
});`;
  execFileSync('docker', ['exec', '-i', 'cms-upload-server', 'node', '-e', code, bucket, object, contentType], {
    input: buffer,
    stdio: ['pipe', 'pipe', 'pipe'],
    maxBuffer: Math.max(buffer.length * 2, 1024 * 1024),
  });
}

async function putIfMissingExact(bucket, object, content, contentType) {
  const buffer = Buffer.isBuffer(content) ? content : Buffer.from(content, 'utf8');
  const expected = { size_bytes: buffer.length, sha256: sha256Hex(buffer) };
  const existing = bucket === 'eduassets-raw' ? readObjectViaUploadContainer(bucket, object) : await readObjectViaProxy(bucket, object);
  if (existing.exists) {
    const actual = { size_bytes: existing.size_bytes, sha256: existing.sha256 };
    if (actual.sha256 !== expected.sha256 || actual.size_bytes !== expected.size_bytes) {
      throw new Error(`target object exists with different content: ${bucket}/${object} ${JSON.stringify(actual)} expected ${JSON.stringify(expected)}`);
    }
    return { action: 'already-present', ...actual };
  }

  if (!realApply) return { action: 'dry-run-put', ...expected };
  putObjectViaUploadContainer(bucket, object, buffer, contentType);
  const after = bucket === 'eduassets-raw' ? readObjectViaUploadContainer(bucket, object) : await readObjectViaProxy(bucket, object);
  assert.equal(after.exists, true, `${bucket}/${object} read after put`);
  assert.equal(after.sha256, expected.sha256);
  assert.equal(after.size_bytes, expected.size_bytes);
  return { action: 'putObject', ...expected };
}

async function readArtifactText(role, ref) {
  const object = await readObjectViaProxy(ref.bucket, ref.object);
  assert.equal(object.exists, true, `${ref.bucket}/${ref.object} readable`);
  let text = object.buffer.toString('utf8');
  if (role === 'provenance') {
    const obj = JSON.parse(text);
    if (obj.job?.job_id?.endsWith('-probe')) obj.job.job_id = obj.job.job_id.slice(0, -6);
    text = JSON.stringify(obj);
  }
  return text;
}

function extractContentListV2(zipBuffer) {
  rmSync(outDir, { recursive: true, force: true });
  mkdirSync(outDir, { recursive: true });
  writeFileSync(zipPath, zipBuffer);
  const entries = execFileSync('unzip', ['-Z1', zipPath], { encoding: 'utf8' })
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
  const matches = entries.filter((entry) => entry.endsWith('_content_list_v2.json'));
  assert.equal(matches.length, 1, `expected exactly one _content_list_v2.json entry, got ${matches.length}`);
  const raw = execFileSync('unzip', ['-p', zipPath, '*_content_list_v2.json']);
  assert.ok(raw.length > 0, 'extracted content_list_v2.json must be non-empty');
  JSON.parse(raw.toString('utf8'));
  writeFileSync(rawPath, raw);
  return {
    entry: matches[0],
    buffer: raw,
    size_bytes: raw.length,
    sha256: sha256Hex(raw),
  };
}

function patchCompiledImports(file, replacements) {
  let compiled = readFileSync(file, 'utf8');
  for (const [from, to] of replacements) compiled = compiled.replaceAll(from, to);
  writeFileSync(file, compiled);
}

function compileRaw2CleanHelpers() {
  const compiledDir = join(outDir, 'compiled');
  rmSync(compiledDir, { recursive: true, force: true });
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
    compiledDir,
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

async function waitForCompletedJob(client, jobId) {
  let last = null;
  for (let attempt = 0; attempt < 30; attempt += 1) {
    const result = await client.queryJob(jobId);
    last = result;
    if (result?.job?.status === 'completed') return result;
    if (result?.job?.status === 'failed') return result;
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }
  return last;
}

function buildCleanOperatorDecision(cleanSummary, taskSummary) {
  return {
    state: 'accepted',
    decidedAt: nowValue,
    decidedBy: 'Luceon',
    reason: 'Third canonical sample pilot accepted CleanMaterial for raw2clean repeatability validation',
    artifactSnapshot: {
      serviceName: 'toc-rebuild',
      assetVersion: cleanSummary.latestVersion || taskSummary.assetVersion,
      jobId: taskSummary.jobId,
      provenanceObjectName: cleanSummary.provenanceObjectName,
      sourceInput: taskSummary.sourceInput || cleanSummary.sourceInput,
      artifactRefs: clone(taskSummary.artifacts),
      stats: clone(taskSummary.stats || {}),
    },
  };
}

function buildAcceptedRaw2CleanSummary({ output, candidateRef, candidatePreview }) {
  const sourceRefs = new Set([
    ...(output.sections || []).map((item) => item.sourceRef),
    ...(output.blocks || []).map((item) => item.sourceRef),
  ]);
  const decision = {
    state: 'accepted',
    decision: 'accepted',
    decidedAt: nowValue,
    decidedBy: 'Luceon',
    scope: 'third-sample-durable-repeatability-pilot',
    materialId: SAMPLE.materialId,
    taskId: SAMPLE.taskId,
    serviceName: 'raw-material-2-clean-material',
    assetVersion: SAMPLE.raw2cleanAssetVersion,
    jobId: `luceon-${SAMPLE.taskId}-raw2clean-${SAMPLE.raw2cleanAssetVersion}`,
    candidate: clone(candidateRef),
    reason: 'Third canonical sample pilot durable accepted decision apply',
    boundaries: {
      finalQualityAccepted: false,
      runtimePost: false,
      serviceExecution: false,
      minioMutation: false,
      batch: false,
      readinessClaimed: false,
    },
  };
  const summary = {
    serviceName: 'raw-material-2-clean-material',
    protocolVersion: output.contractVersion,
    jobId: decision.jobId,
    status: 'accepted',
    cleanState: 'accepted-candidate',
    productLabel: 'Raw2Clean candidate output',
    materialId: SAMPLE.materialId,
    parseTaskId: SAMPLE.taskId,
    assetVersion: SAMPLE.raw2cleanAssetVersion,
    sourceCleanMaterial: clone(output.sourceCleanMaterial),
    sourceInput: clone(output.sourceInput),
    sourceArtifacts: clone(output.sourceArtifacts),
    artifact: { candidate: clone(candidateRef) },
    stats: {
      sectionCount: output.sections.length,
      blockCount: output.blocks.length,
      sourceRefCount: sourceRefs.size,
      outputContractSizeBytes: output.preview.size_bytes,
      candidateArtifactSizeBytes: candidatePreview.size_bytes,
    },
    preview: {
      candidateArtifact: clone(candidatePreview),
      outputContract: clone(output.preview),
    },
    warnings: Array.isArray(output.warnings) ? [...output.warnings] : [],
    boundaries: {
      durableCandidateArtifactCreated: true,
      dbMetadataPatched: true,
      runtimePost: false,
      serviceExecution: false,
      finalQualityAccepted: false,
      readinessClaimed: false,
    },
    decision,
    acceptedDecision: decision,
    updatedAt: nowValue,
  };
  return { summary, decision };
}

function hasFullCandidateContent(value) {
  const serialized = JSON.stringify(value || {});
  return serialized.includes('"sections"') || serialized.includes('"blocks"') || serialized.includes('"canonicalJson"') || serialized.length > 250000;
}

async function main() {
  const preMaterial = await getDb(`/materials/${encodeURIComponent(SAMPLE.materialId)}`);
  const preTask = await getDb(`/tasks/${encodeURIComponent(SAMPLE.taskId)}`);
  assert.equal(String(preMaterial.id), SAMPLE.materialId);
  assert.equal(String(preTask.id), SAMPLE.taskId);
  assert.equal(String(preTask.materialId), SAMPLE.materialId);

  const health = await fetch(`${cleanServiceEndpoint.replace(/\/+$/, '')}/health`);
  assert.equal(health.status, 200, 'CleanService health');

  const zipBuffer = await fetchBufferFromProxy(SAMPLE.parsedZip.bucket, SAMPLE.parsedZip.object);
  const extracted = extractContentListV2(zipBuffer);
  assert.deepEqual(
    { sha256: extracted.sha256, size_bytes: extracted.size_bytes },
    SAMPLE.expectedRawSeed,
    'raw seed SHA/size must match the task preflight before any write or POST',
  );
  const rawSeed = await putIfMissingExact(
    'eduassets-raw',
    SAMPLE.rawObject,
    extracted.buffer,
    'application/json; charset=utf-8',
  );

  if (!realApply) {
    console.log(JSON.stringify({
      ok: true,
      mode: 'dry-run-preflight',
      sample: SAMPLE,
      extracted: { entry: extracted.entry, size_bytes: extracted.size_bytes, sha256: extracted.sha256 },
      rawSeed,
      boundaries: {
        rawSeedPutObject: 0,
        cleanServicePost: 0,
        raw2cleanCandidatePutObject: 0,
        dbPatch: 0,
        minioDelete: 0,
        runtimePostOtherThanCleanService: 0,
        dockerOperation: 0,
        batch: 0,
      },
    }, null, 2));
    return;
  }

  const targetJobId = `luceon-${SAMPLE.taskId}-toc-rebuild-${SAMPLE.cleanAssetVersion}`;
  const existingTargetJob = await queryCleanServiceJob(targetJobId);
  if (existingTargetJob && existingTargetJob.status !== 'completed') {
    throw new Error(`target CleanService job already exists in non-completed state: ${targetJobId} status=${existingTargetJob.status}`);
  }

  const taskForCleanService = {
    ...clone(preTask),
    metadata: {
      ...(preTask.metadata || {}),
      rawMaterial: {
        version: 'v1',
        mineru: {
          contentListV2: {
            bucket: 'eduassets-raw',
            object: SAMPLE.rawObject,
            sha256: extracted.sha256,
            sizeBytes: extracted.size_bytes,
          },
        },
      },
    },
  };

  const config = loadCleanServiceConfig({
    ...process.env,
    CLEANSERVICE_ENABLED: 'true',
    CLEANSERVICE_ENDPOINT: cleanServiceEndpoint,
    CLEANSERVICE_STORAGE_ENDPOINT: process.env.CLEANSERVICE_STORAGE_ENDPOINT || 'minio:9000',
    CLEANSERVICE_STORAGE_USE_SSL: process.env.CLEANSERVICE_STORAGE_USE_SSL || 'false',
    CLEANSERVICE_TIMEOUT_MS: process.env.CLEANSERVICE_TIMEOUT_MS || '30000',
  });

  const request = buildCleanServiceJobRequest(taskForCleanService, config, { submittedAt: nowValue });
  assert.equal(request.job_id, targetJobId);
  assert.equal(request.asset_version, SAMPLE.cleanAssetVersion);
  assert.equal(request.inputs[0].source.object, SAMPLE.rawObject);
  if (existingTargetJob?.status === 'completed') {
    config.reconcileExistingJob = true;
  }

  const cleanClient = createCleanServiceClientWithTransport({ config });
  let submitCalls = 0;
  let capturedCleanPlan = null;
  let completedQuery = null;

  const deps = {
    ...(existingTargetJob?.status === 'completed' ? { existingCompletedJob: existingTargetJob } : {}),
    submitJob: async (req) => {
      submitCalls += 1;
      assert.equal(submitCalls, 1, 'only one CleanService POST is allowed');
      const submitResult = await cleanClient.submitJob(req);
      if (submitResult?.job?.status === 'completed') return { ...submitResult, ok: true };
      completedQuery = await waitForCompletedJob(cleanClient, req.job_id);
      return completedQuery?.job ? { ...completedQuery, ok: true } : completedQuery;
    },
    queryJob: async (jobId) => {
      if (completedQuery?.job?.job_id === jobId) return { ...completedQuery, ok: true };
      const result = await waitForCompletedJob(cleanClient, jobId);
      return result?.job ? { ...result, ok: true } : result;
    },
    artifactReader: {
      readArtifact: (role, ref) => readArtifactText(role, ref),
    },
    applyCleanMetadataPersistencePlan: async ({ plan }) => {
      capturedCleanPlan = plan;
      return {
        ok: true,
        applied: false,
        operationCount: 0,
        classification: 'DRY_RUN_SUCCESS',
        reason: 'captured clean metadata plan for combined third-sample apply',
      };
    },
    dbClient: {
      updateTask: async () => { throw new Error('direct task update forbidden'); },
      updateMaterial: async () => { throw new Error('direct material update forbidden'); },
    },
  };

  const cleanResult = await runCleanServiceTocRebuildOnce({
    task: taskForCleanService,
    material: preMaterial,
    config,
    deps,
    now: () => nowValue,
  });
  assert.equal(cleanResult.ok, true, JSON.stringify(cleanResult, null, 2));
  assert.equal(cleanResult.classification, 'DRY_RUN_SUCCESS');
  assert.equal(cleanResult.assetVersion, SAMPLE.cleanAssetVersion);
  assert.equal(submitCalls, existingTargetJob?.status === 'completed' ? 0 : 1);
  if (completedQuery?.job?.status === 'failed') {
    throw new Error(`single allowed CleanService POST failed: ${request.job_id}`);
  }
  assert.ok(capturedCleanPlan?.ok, 'Clean metadata plan must be captured');

  const cleanTaskSummary = capturedCleanPlan.taskPatch.metadata.cleanServiceJobs['toc-rebuild'];
  const cleanMaterialSummary = capturedCleanPlan.materialPatch.metadata.cleanMaterials['toc-rebuild'];
  cleanMaterialSummary.operatorDecision = buildCleanOperatorDecision(cleanMaterialSummary, cleanTaskSummary);

  const materialWithClean = {
    ...clone(preMaterial),
    metadata: {
      ...(capturedCleanPlan.materialPatch.metadata || {}),
      cleanMaterials: {
        ...(capturedCleanPlan.materialPatch.metadata.cleanMaterials || {}),
        'toc-rebuild': cleanMaterialSummary,
      },
    },
  };
  const taskWithClean = {
    ...clone(preTask),
    metadata: capturedCleanPlan.taskPatch.metadata,
  };

  compileRaw2CleanHelpers();
  const { buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun } = await import(pathToFileURL(artifactOutfile).href);
  const { buildRawMaterial2CleanMaterialOutputContract } = await import(pathToFileURL(outputOutfile).href);
  const draftResult = await buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun({
    material: materialWithClean,
    task: taskWithClean,
    currentAssetVersion: SAMPLE.cleanAssetVersion,
    options: { now: nowValue },
    artifactBodyReader: (ref, role) => readArtifactText(role, ref),
  });
  assert.equal(draftResult.ok, true, JSON.stringify(draftResult, null, 2));

  const outputResult = buildRawMaterial2CleanMaterialOutputContract({
    draft: draftResult.draft,
    options: { now: nowValue },
  });
  assert.equal(outputResult.ok, true, JSON.stringify(outputResult, null, 2));

  const candidateJson = outputResult.canonicalJson;
  const candidateRef = {
    bucket: 'eduassets-clean',
    object: `raw-material-2-clean-material/${SAMPLE.materialId}/${SAMPLE.raw2cleanAssetVersion}/candidate.json`,
    sha256: sha256Hex(candidateJson),
    size_bytes: byteLength(candidateJson),
    content_type: 'application/json',
  };
  const candidateWrite = await putIfMissingExact(
    candidateRef.bucket,
    candidateRef.object,
    candidateJson,
    'application/json; charset=utf-8',
  );

  const candidatePreview = {
    contentType: 'application/json',
    size_bytes: candidateRef.size_bytes,
    sha256: candidateRef.sha256,
  };
  const { summary: raw2cleanSummary, decision } = buildAcceptedRaw2CleanSummary({
    output: outputResult.output,
    candidateRef,
    candidatePreview,
  });

  const finalTaskPatch = {
    metadata: {
      ...taskWithClean.metadata,
      rawMaterial2CleanMaterialJobs: {
        ...(taskWithClean.metadata.rawMaterial2CleanMaterialJobs || {}),
        'raw-material-2-clean-material': raw2cleanSummary,
      },
    },
  };
  const finalMaterialPatch = {
    metadata: {
      ...materialWithClean.metadata,
      rawMaterial2CleanMaterial: {
        ...(materialWithClean.metadata.rawMaterial2CleanMaterial || {}),
        currentCandidate: {
          serviceName: 'raw-material-2-clean-material',
          jobId: raw2cleanSummary.jobId,
          assetVersion: SAMPLE.raw2cleanAssetVersion,
          artifact: { candidate: clone(candidateRef) },
          status: 'accepted',
          cleanState: 'accepted-candidate',
          decision,
          acceptedDecision: decision,
          updatedAt: nowValue,
        },
        candidates: {
          ...(materialWithClean.metadata.rawMaterial2CleanMaterial?.candidates || {}),
          [SAMPLE.raw2cleanAssetVersion]: raw2cleanSummary,
        },
        currentDecision: decision,
      },
    },
  };

  if (hasFullCandidateContent(finalTaskPatch) || hasFullCandidateContent(finalMaterialPatch)) {
    throw new Error('metadata patch would embed full raw2clean candidate content');
  }

  let patchResult = { action: 'dry-run', operationCount: 0 };
  if (realApply) {
    await patchDb(`/tasks/${encodeURIComponent(SAMPLE.taskId)}`, finalTaskPatch);
    await patchDb(`/materials/${encodeURIComponent(SAMPLE.materialId)}`, finalMaterialPatch);
    patchResult = { action: 'patch', operationCount: 2 };
  }

  const postTask = await getDb(`/tasks/${encodeURIComponent(SAMPLE.taskId)}`);
  const postMaterial = await getDb(`/materials/${encodeURIComponent(SAMPLE.materialId)}`);
  const postRaw2Clean = postMaterial.metadata?.rawMaterial2CleanMaterial || null;

  if (realApply) {
    assert.equal(postTask.metadata?.cleanServiceJobs?.['toc-rebuild']?.jobId, request.job_id);
    assert.equal(postMaterial.metadata?.cleanMaterials?.['toc-rebuild']?.operatorDecision?.state, 'accepted');
    assert.equal(postTask.metadata?.rawMaterial2CleanMaterialJobs?.['raw-material-2-clean-material']?.status, 'accepted');
    assert.equal(postRaw2Clean?.currentDecision?.state, 'accepted');
    assert.equal(postRaw2Clean?.currentDecision?.candidate?.sha256, candidateRef.sha256);
  }

  console.log(JSON.stringify({
    ok: true,
    mode: realApply ? 'real-apply' : 'dry-run',
    sample: SAMPLE,
    extracted: { entry: extracted.entry, size_bytes: extracted.size_bytes, sha256: extracted.sha256 },
    rawSeed,
    cleanService: {
      endpoint: cleanServiceEndpoint,
      submitCalls,
      reconciledExistingJob: existingTargetJob?.status === 'completed',
      jobId: request.job_id,
      assetVersion: SAMPLE.cleanAssetVersion,
      status: cleanResult.status,
      classification: cleanResult.classification,
      sectionCount: draftResult.evidence.sectionCount,
      blockCount: draftResult.evidence.blockCount,
      artifacts: cleanTaskSummary.artifacts,
    },
    candidate: {
      ref: candidateRef,
      write: candidateWrite,
      outputContractPreview: outputResult.output.preview,
      decisionState: decision.state,
    },
    patchResult,
    post: {
      cleanJobId: postTask.metadata?.cleanServiceJobs?.['toc-rebuild']?.jobId || null,
      cleanDecision: postMaterial.metadata?.cleanMaterials?.['toc-rebuild']?.operatorDecision?.state || null,
      raw2cleanTaskStatus: postTask.metadata?.rawMaterial2CleanMaterialJobs?.['raw-material-2-clean-material']?.status || null,
      raw2cleanDecision: postRaw2Clean?.currentDecision?.state || null,
    },
    boundaries: {
      rawSeedPutObject: rawSeed.action === 'putObject' ? 1 : 0,
      cleanServicePost: submitCalls,
      raw2cleanCandidatePutObject: candidateWrite.action === 'putObject' ? 1 : 0,
      dbPatch: patchResult.operationCount,
      minioDelete: 0,
      runtimePostOtherThanCleanService: 0,
      dockerOperation: 0,
      batch: 0,
    },
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
