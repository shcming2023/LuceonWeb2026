/**
 * Remote GPU Pipeline client/adapter smoke test.
 *
 * This test never contacts a real GPU host. It validates the server-side
 * contract boundary that Luceon will use once the A800 service exposes the API:
 * auth header, multipart submit shape, status polling, and result storage.
 */

import assert from 'node:assert/strict';
import { Readable } from 'node:stream';
import JSZip from 'jszip';

import { loadRemoteGpuPipelineConfig } from '../services/gpu-pipeline/config.mjs';
import {
  createRemoteGpuPipelineClient,
  RemoteGpuPipelineError,
} from '../services/gpu-pipeline/client.mjs';
import { processWithRemoteGpuPipeline } from '../services/gpu-pipeline/remote-adapter.mjs';

async function readBodyText(body) {
  const chunks = [];
  for await (const chunk of body) {
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString('utf-8');
}

function jsonResponse(payload, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(payload),
    arrayBuffer: async () => Buffer.from(JSON.stringify(payload)).buffer,
  };
}

async function testConfigAndSubmitContract() {
  console.log('  [1] client sends Bearer auth and multipart submit contract...');

  const captured = [];
  const fetchImpl = async (url, init) => {
    const bodyText = init.body ? await readBodyText(init.body) : '';
    captured.push({ url, init, bodyText });
    assert.equal(init.headers.Authorization, 'Bearer gpu-test-token');
    assert.equal(init.headers.Accept, 'application/json');
    if (url.endsWith('/api/v1/tasks')) {
      assert.equal(init.method, 'POST');
      assert.match(init.headers['content-type'], /^multipart\/form-data; boundary=/);
      assert.match(bodyText, /name="pipeline"\r\n\r\nmineru_popo/);
      assert.match(bodyText, /name="luceon_task_id"\r\n\r\ntask-remote-1/);
      assert.match(bodyText, /name="material_id"\r\n\r\nmat-remote-1/);
      assert.match(bodyText, /name="file"; filename="sample\.pdf"/);
      assert.match(bodyText, /%PDF-smoke/);
      return jsonResponse({ task_id: 'gpu-job-1', status: 'queued' });
    }
    if (url.endsWith('/api/v1/tasks/gpu-job-1')) {
      return jsonResponse({ task_id: 'gpu-job-1', status: 'running_inference' });
    }
    if (url.endsWith('/api/v1/tasks/gpu-job-1/outputs')) {
      return jsonResponse({ markdown: '# Remote result' });
    }
    throw new Error(`unexpected URL ${url}`);
  };

  const config = loadRemoteGpuPipelineConfig({
    REMOTE_GPU_PIPELINE_ENABLED: 'true',
    REMOTE_GPU_PIPELINE_BASE_URL: 'https://gpu.example.test/',
    REMOTE_GPU_PIPELINE_TOKEN: 'gpu-test-token',
    REMOTE_GPU_PIPELINE_TIMEOUT_MS: '5000',
  });
  const client = createRemoteGpuPipelineClient({ config, fetchImpl });

  const submitted = await client.submitTask({
    luceonTaskId: 'task-remote-1',
    materialId: 'mat-remote-1',
    fileName: 'sample.pdf',
    mimeType: 'application/pdf',
    fileStream: Readable.from([Buffer.from('%PDF-smoke')]),
    options: { enableFormula: true, enableTable: true, ocrLanguage: 'ch' },
  });
  assert.equal(submitted.task_id, 'gpu-job-1');
  assert.equal(submitted.status, 'queued');

  const queried = await client.queryTask('gpu-job-1');
  assert.equal(queried.status, 'running_inference');

  const outputs = await client.getOutputs('gpu-job-1');
  assert.equal(outputs.markdown, '# Remote result');
  assert.equal(captured.length, 3);
  console.log('    PASS');
}

async function testMissingSecretFailsClosed() {
  console.log('  [2] missing endpoint/token fails closed without network...');

  assert.throws(
    () => createRemoteGpuPipelineClient({
      config: loadRemoteGpuPipelineConfig({
        REMOTE_GPU_PIPELINE_ENABLED: 'true',
        REMOTE_GPU_PIPELINE_TOKEN: 'gpu-test-token',
      }),
      fetchImpl: async () => jsonResponse({}),
    }),
    RemoteGpuPipelineError,
  );

  assert.throws(
    () => createRemoteGpuPipelineClient({
      config: loadRemoteGpuPipelineConfig({
        REMOTE_GPU_PIPELINE_ENABLED: 'true',
        REMOTE_GPU_PIPELINE_BASE_URL: 'https://gpu.example.test',
      }),
      fetchImpl: async () => jsonResponse({}),
    }),
    RemoteGpuPipelineError,
  );
  console.log('    PASS');
}

async function testRemoteAdapterStoresOutputs() {
  console.log('  [3] adapter polls remote task and stores markdown/zip artifacts...');

  process.env.REMOTE_GPU_PIPELINE_POLL_INTERVAL_MS = '1';

  const zip = new JSZip();
  zip.file('full.md', '# Rebuilt from GPU\n');
  zip.file('content_list.json', JSON.stringify([{ id: 'block-1' }]));
  zip.file('images/hash-name.png', Buffer.from('png-bytes'));
  const zipBase64 = (await zip.generateAsync({ type: 'nodebuffer' })).toString('base64');

  const statusSequence = [
    { task_id: 'gpu-job-2', status: 'running_mineru', progress: { percent: 33, stage: 'mineru' } },
    { task_id: 'gpu-job-2', status: 'running_inference', progress: { percent: 66, stage: 'popo-inference' } },
    {
      task_id: 'gpu-job-2',
      status: 'succeeded',
      metrics: { mineru_seconds: 204, popo_seconds: 1055 },
      outputs: {
        markdown: '# Rebuilt from GPU\n',
        mineru_result_zip_base64: zipBase64,
      },
    },
  ];

  const fakeClient = {
    submitTask: async () => ({ task_id: 'gpu-job-2', status: 'queued' }),
    queryTask: async () => statusSequence.shift(),
    getOutputs: async () => {
      throw new Error('outputs should already be attached to completed payload');
    },
    download: async () => Buffer.from('unused'),
  };

  const saved = [];
  const minioContext = {
    saveMarkdown: async (objectName, content) => saved.push({ kind: 'markdown', objectName, content }),
    saveObject: async (objectName, buffer, mimeType) => saved.push({ kind: 'object', objectName, size: buffer.length, mimeType }),
  };
  const progress = [];
  const task = {
    id: 'task-remote-2',
    materialId: 'mat-remote-2',
    engine: 'local-mineru',
    metadata: {},
    optionsSnapshot: {
      material: {
        fileName: 'large.pdf',
        mimeType: 'application/pdf',
        fileSize: 123456,
      },
    },
  };

  const result = await processWithRemoteGpuPipeline({
    task,
    material: task.optionsSnapshot.material,
    fileStream: Readable.from([Buffer.from('%PDF-large')]),
    fileName: 'large.pdf',
    mimeType: 'application/pdf',
    timeoutMs: 10_000,
    minioContext,
    updateProgress: async (update) => progress.push(update),
    client: fakeClient,
  });

  assert.equal(result.mineruTaskId, 'gpu-job-2');
  assert.equal(result.objectName, 'parsed/mat-remote-2/full.md');
  assert.equal(result.zipObjectName, 'parsed/mat-remote-2/mineru-result.zip');
  assert.equal(result.artifactStorageMode, 'zip-source');
  assert.ok(result.parsedArtifacts.some((item) =>
    item.source === 'zip-entry' &&
    item.zipObjectName === 'parsed/mat-remote-2/mineru-result.zip' &&
    item.zipEntryPath === 'images/hash-name.png' &&
    item.relativePath === 'images/hash-name.png'
  ));
  assert.ok(saved.some((item) => item.kind === 'markdown' && item.objectName === 'parsed/mat-remote-2/full.md'));
  assert.ok(saved.some((item) => item.kind === 'object' && item.objectName === 'parsed/mat-remote-2/mineru-result.zip'));
  assert.ok(progress.some((item) => item.stage === 'remote-gpu-inference'));
  assert.equal(progress[0].metadata.mineruExecutionProfile.backendEffective, 'remote-gpu-pipeline');
  console.log('    PASS');
}

async function main() {
  console.log('=== Remote GPU Pipeline Client Smoke ===');
  await testConfigAndSubmitContract();
  await testMissingSecretFailsClosed();
  await testRemoteAdapterStoresOutputs();
  console.log('All remote GPU pipeline client smoke cases passed successfully!');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
