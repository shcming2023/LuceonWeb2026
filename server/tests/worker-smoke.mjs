/**
 * AI Worker Smoke Test
 * 验证 AI Worker 是否能正确加载 MinIO 上下文并读取 Markdown 文件
 */
process.env.DISABLE_AI_SKELETON_FALLBACK = 'true';
process.env.ALLOW_AI_SKELETON_FALLBACK = 'false';
process.env.OLLAMA_TIER2_MODEL = process.env.OLLAMA_TIER2_MODEL || 'qwen3.5:9b';

const { AiMetadataWorker } = await import('../services/ai/metadata-worker.mjs');
const { ParseTaskWorker } = await import('../services/queue/task-worker.mjs');

async function runTest() {
  console.log('--- AI Worker Smoke Test Start ---');

  // 1. 测试用 MinIO 上下文
  const mockAiMinio = {
    getFileStream: async (name) => {
      console.log(`[test-minio] getFileStream called for: ${name}`);
      return {
        [Symbol.asyncIterator]: async function* () {
          yield Buffer.from('# Test Document\nThis is a test markdown file.');
        }
      };
    }
  };

  // 2. 测试 Job
  const mockJob = {
    id: 'smoke-job-1',
    parseTaskId: 'task-1',
    inputMarkdownObjectName: 'test/doc.md',
    state: 'pending'
  };

  const aiUpdates = [];

  // 3. 初始化 Worker (使用 Spread 模式，模拟 upload-server.mjs 的调用方式)
  const worker = new AiMetadataWorker({
    ...mockAiMinio,
    onComplete: async (job, update) => {
      aiUpdates.push({ jobId: job.id, ...update });
    }
  });
  worker.transition = async (_job, update) => {
    aiUpdates.push(update);
  };
  worker.createProvider = () => ({
    id: 'ollama',
    model: process.env.OLLAMA_TIER2_MODEL,
    baseUrl: 'http://127.0.0.1:1',
    timeoutMs: 1,
    extractMetadata: async () => {
      throw new Error('provider unavailable for strict smoke');
    }
  });

  // 验证 Context 注入诊断
  if (typeof worker.minioContext?.getFileStream !== 'function') {
    console.error('FAILED: minioContext was not correctly injected.');
    process.exit(1);
  } else {
    console.log('PASSED: minioContext injected correctly.');
  }

  // 4. 手动触发一个 Tick 处理
  // 我们不需要启动循环，直接调用 tickOnce 处理特定 job
  try {
    // 模拟从 DB 扫描到一个任务
    // 这里我们绕过 start()，直接测试内部逻辑
    console.log('--- Testing Job Processing ---');
    await worker.processJob(mockJob);
  } catch (err) {
    console.error('FAILED: Job processing error:', err.message);
    process.exit(1);
  }

  const failedAiUpdate = aiUpdates.find((u) => u.state === 'failed');
  if (!failedAiUpdate) {
    console.error('FAILED: strict AI mode should mark provider failure as failed.');
    process.exit(1);
  }
  if (!String(failedAiUpdate.errorMessage || '').includes('[AI 严格模式拦截]')) {
    console.error('FAILED: strict AI failure did not include the no-skeleton guard message.');
    process.exit(1);
  }
  const usedSkeleton = aiUpdates.some((u) =>
    u.providerId === 'skeleton' ||
    u.result?.aiClassificationProvider === 'skeleton' ||
    u.result?.aiClassificationModel === 'skeleton'
  );
  if (usedSkeleton) {
    console.error('FAILED: strict AI mode produced a skeleton result.');
    process.exit(1);
  }
  console.log('PASSED: strict AI mode fails fast without skeleton fallback.');

  console.log('--- AI Worker Smoke Test Success ---');

  console.log('--- ParseTask Worker Reliability Test Start ---');

  const calls = {
    updateTask: [],
    updateMaterial: [],
  };

  let failOnce = true;
  const mockTaskClient = {
    getAllTasks: async () => [],
    updateTask: async (_id, update) => {
      calls.updateTask.push(update);
      if (failOnce) {
        failOnce = false;
        return false;
      }
      return true;
    },
    updateMaterial: async (_id, update) => {
      calls.updateMaterial.push(update);
      return true;
    },
  };

  const mockParseMinio = {
    getFileStream: async () => ({}),
    saveMarkdown: async () => {},
    saveObject: async () => {},
  };

  const parseWorker = new ParseTaskWorker({
    minioContext: mockParseMinio,
    taskClient: mockTaskClient,
    mineruProcessor: async () => {
      throw new Error('fetch failed');
    }
  });

  const mockTask = {
    id: 'smoke-parse-task-1',
    engine: 'local-mineru',
    state: 'pending',
    stage: 'upload',
    progress: 0,
    materialId: 'smoke-material-1',
    optionsSnapshot: {
      localTimeout: 1,
      material: {
        fileName: 'smoke.pdf',
        mimeType: 'application/pdf',
        metadata: { objectName: 'originals/smoke-material-1/source.pdf' }
      }
    },
    metadata: {},
  };

  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    if (url.toString().includes('/ai-metadata-jobs')) {
      return { ok: false, status: 500, json: async () => ({ error: 'mock error' }) };
    }
    if (originalFetch) return originalFetch(url, options);
    return { ok: true, status: 200, json: async () => ({}) };
  };

  try {
    await parseWorker.processTask(mockTask);
  } catch (err) {
    globalThis.fetch = originalFetch;
    console.error('FAILED: ParseTaskWorker processTask threw:', err.message);
    process.exit(1);
  }
  globalThis.fetch = originalFetch;

  const hasFailedUpdate = calls.updateTask.some((u) => u && u.state === 'failed');
  if (!hasFailedUpdate) {
    console.error('FAILED: expected a failed task patch to be written');
    process.exit(1);
  }

  if (calls.updateTask.length < 2) {
    console.error('FAILED: expected updateTask retry when first call fails');
    process.exit(1);
  }

  const hasMaterialFailed = calls.updateMaterial.some((u) => u && u.status === 'failed');
  if (!hasMaterialFailed) {
    console.error('FAILED: expected material to be marked failed');
    process.exit(1);
  }

  console.log('PASSED: ParseTask worker failure is reliably written even if first updateTask fails.');
  console.log('--- ParseTask Worker Reliability Test Success ---');
}

runTest();
