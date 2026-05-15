import assert from 'assert';
import express from 'express';
import multer from 'multer';
import { spawn } from 'child_process';

if (!globalThis.fetch) {
  globalThis.fetch = fetch;
}

let failedCount = 0;
let passedCount = 0;

function assertEqual(actual, expected, msg) {
  try {
    assert.deepStrictEqual(actual, expected);
    passedCount++;
    console.log(`[PASS] ${msg}`);
  } catch (err) {
    failedCount++;
    console.error(`[FAIL] ${msg}`);
    console.error(`  Expected:`, expected);
    console.error(`  Actual:  `, actual);
  }
}

async function runTest() {
  console.log('--- dependency-health-smoke ---');

  // We will run the real upload-server as a child process
  // But first, we create dummy db-server, mineru-server, and ollama-server
  
  const dummyApp = express();
  dummyApp.use(express.json());
  let mineruOk = false;
  let mineruSubmitOk = false;
  let mineruSubmitCalls = 0;
  let ollamaOk = false;
  let ollamaChatOk = true;
  let ollamaModels = [{ name: 'qwen3.5:9b' }];
  let ollamaResidentModels = [{ name: 'qwen3.5:9b' }];
  let ollamaChatHangs = false;
  let lastOllamaChatBody = null;
  const settingsStore = {
    mineruConfig: { localEndpoint: null },
    aiConfig: { enabled: true, providers: [] },
    mineruAdmissionCircuit: undefined,
  };

  // DB Server settings mock
  dummyApp.get('/settings', (req, res) => {
    res.json({
      mineruConfig: { localEndpoint: 'http://127.0.0.1:18083' },
      aiConfig: { enabled: true, providers: [{ providerId: 'ollama', enabled: true, priority: 1, apiEndpoint: 'http://127.0.0.1:11434' }] }
    });
  });

  // DB Server other mocks needed by POST /tasks
  dummyApp.get('/tasks', (req, res) => res.json([]));
  dummyApp.post('/materials', (req, res) => res.json({ id: 'test-mat' }));
  dummyApp.get('/materials/:id', (req, res) => res.status(404).json({}));
  dummyApp.post('/tasks', (req, res) => res.json({ id: 'test-task' }));

  // MinerU Mock
  dummyApp.get('/mineru/health', (req, res) => {
    if (mineruOk) res.sendStatus(200);
    else res.sendStatus(503);
  });
  dummyApp.post('/mineru/tasks', multer().any(), (req, res) => {
    mineruSubmitCalls++;
    if (mineruSubmitOk) res.json({ task_id: `probe-task-${mineruSubmitCalls}` });
    else res.status(503).json({ error: 'submit path unavailable' });
  });

  // Ollama Mock
  dummyApp.get('/ollama/api/tags', (req, res) => {
    if (ollamaOk) res.json({ models: ollamaModels });
    else res.sendStatus(503);
  });
  dummyApp.get('/ollama/api/ps', (req, res) => {
    if (ollamaOk) res.json({ models: ollamaResidentModels });
    else res.sendStatus(503);
  });
  dummyApp.post('/ollama/api/chat', (req, res) => {
    lastOllamaChatBody = req.body;
    if (ollamaChatHangs) return;
    if (ollamaOk && ollamaChatOk) res.json({ message: { content: 'mock' } });
    else res.sendStatus(503);
  });

  // MinIO Mock
  dummyApp.use((req, res, next) => {
    console.log(`[dummyApp] ${req.method} ${req.url}`);
    if (req.method === 'PUT' || req.method === 'HEAD' || req.method === 'GET') {
      res.set('ETag', '"dummy-etag"');
      res.sendStatus(200);
    } else {
      next();
    }
  });

  const dummyServer = await new Promise((resolve) => {
    const s = dummyApp.listen(0, '127.0.0.1', () => resolve(s));
  });
  const dummyPort = dummyServer.address().port;

  // Rewrite endpoints to hit the dummy server
  // mineru -> http://127.0.0.1:dummyPort/mineru
  // ollama -> http://127.0.0.1:dummyPort/ollama
  const dbApp = express();
  dbApp.use(express.json());
  dbApp.get('/settings', (req, res) => {
    settingsStore.mineruConfig.localEndpoint = `http://127.0.0.1:${dummyPort}/mineru`;
    settingsStore.aiConfig.providers = [{ providerId: 'ollama', enabled: true, priority: 1, apiEndpoint: `http://127.0.0.1:${dummyPort}/ollama` }];
    res.json(settingsStore);
  });
  dbApp.put('/settings/:key', (req, res) => {
    settingsStore[req.params.key] = req.body;
    res.json({ ok: true, key: req.params.key });
  });
  dbApp.get('/tasks', (req, res) => res.json([]));
  dbApp.get('/ai-metadata-jobs', (req, res) => res.json([]));
  dbApp.post('/materials', (req, res) => res.json({ id: 'test-mat' }));
  dbApp.get('/materials/:id', (req, res) => res.status(404).json({}));
  dbApp.post('/tasks', (req, res) => res.json({ id: 'test-task' }));
  dbApp.post('/task-events', (req, res) => res.json({}));

  const dbServer = await new Promise((resolve) => {
    const s = dbApp.listen(0, '127.0.0.1', () => resolve(s));
  });
  const dbPort = dbServer.address().port;

  const uploadServerBind = await new Promise((resolve) => {
    const s = express().listen(0, '127.0.0.1', () => resolve(s));
  });
  const uploadPort = uploadServerBind.address().port;
  uploadServerBind.close();

  const child = spawn('node', ['server/upload-server.mjs'], {
    env: {
      ...process.env,
      UPLOAD_PORT: String(uploadPort),
      DB_BASE_URL: `http://127.0.0.1:${dbPort}`,
      STORAGE_BACKEND: 'tmpfiles', // bypass MinIO actual bucket check for this test since we focus on mineru/ollama logic blocking
      DISABLE_AI_SKELETON_FALLBACK: 'true',
      OLLAMA_API_URL: `http://127.0.0.1:${dummyPort}/ollama`,
      OLLAMA_TIER2_MODEL: 'qwen3.5:9b',
      OLLAMA_KEEP_ALIVE: '24h',
      ALLOW_LOCAL_AI_ENDPOINT: 'true',
      MINIO_ENDPOINT: '127.0.0.1',
      MINIO_PORT: String(dummyPort),
      DEPENDENCY_HEALTH_REWRITE_LOCAL_ENDPOINTS: 'false',
      DEPENDENCY_HEALTH_OLLAMA_CHAT_TIMEOUT_MS: '200',
      MINERU_ADMISSION_CIRCUIT_COOLDOWN_MS: '0'
    }
  });
  
  child.stdout.on('data', d => console.log('[upload-server]', d.toString().trim()));
  child.stderr.on('data', d => console.error('[upload-server err]', d.toString().trim()));
  child.on('exit', code => console.log('[upload-server] EXITED with code', code));

  const uploadBase = `http://127.0.0.1:${uploadPort}`;
  // Wait for upload-server to start by polling /health
  let serverReady = false;
  for (let i = 0; i < 20; i++) {
    try {
      const hRes = await fetch(`${uploadBase}/health`);
      if (hRes.ok) {
        serverReady = true;
        break;
      }
    } catch (e) {
      // ignore
    }
    await new Promise(r => setTimeout(r, 500));
  }
  if (!serverReady) {
    console.error('upload-server failed to start in time');
    process.exit(1);
  }

  try {
    // Test 1: dependency-health reports mineru down
    mineruOk = false;
    ollamaOk = true;
    ollamaModels = [{ name: 'qwen3.5:9b' }];
    ollamaResidentModels = [{ name: 'qwen3.5:9b' }];
    ollamaChatHangs = false;
    let res = await fetch(`${uploadBase}/ops/dependency-health`);
    let data = await res.json();
    assertEqual(data.ok, false, 'health.ok should be false when mineru is down');
    assertEqual(data.blocking, true, 'health.blocking should be true');
    assertEqual(data.dependencies.mineru.ok, false, 'mineru.ok should be false');
    assertEqual(data.dependencies.mineru.healthOk, false, 'mineru.healthOk should be false when /health is down');

    // Test 1b: /health OK with submit probe disabled keeps default dependency-health cheap
    mineruOk = true;
    mineruSubmitOk = false;
    ollamaOk = true;
    ollamaModels = [{ name: 'qwen3.5:9b' }];
    ollamaResidentModels = [{ name: 'qwen3.5:9b' }];
    ollamaChatHangs = false;
    lastOllamaChatBody = null;
    mineruSubmitCalls = 0;
    res = await fetch(`${uploadBase}/ops/dependency-health`);
    data = await res.json();
    assertEqual(data.dependencies.mineru.healthOk, true, 'mineru.healthOk should be true when /health is OK');
    assertEqual(data.dependencies.mineru.submitProbe.enabled, false, 'mineru submit probe should be disabled by default');
    assertEqual(data.dependencies.mineru.ok, true, 'mineru.ok should use cheap /health result by default');
    assertEqual(mineruSubmitCalls, 0, 'default dependency-health should not call MinerU /tasks');
    assertEqual(lastOllamaChatBody?.model, 'qwen3.5:9b', 'ollama smoke should use required model');
    assertEqual(lastOllamaChatBody?.stream, false, 'ollama smoke should disable streaming');
    assertEqual(lastOllamaChatBody?.think, false, 'ollama smoke should disable top-level thinking');
    assertEqual(lastOllamaChatBody?.keep_alive, '24h', 'ollama smoke should keep qwen3.5:9b warm');
    assertEqual(lastOllamaChatBody?.options?.think, false, 'ollama smoke should disable options thinking');
    assertEqual(lastOllamaChatBody?.options?.num_predict, 1, 'ollama smoke should use a minimal token budget');
    assertEqual(data.dependencies.ollama.serviceReachable, true, 'ollama serviceReachable should be true when /api/tags responds');
    assertEqual(data.dependencies.ollama.tagsOk, true, 'ollama tagsOk should be true when /api/tags succeeds');
    assertEqual(data.dependencies.ollama.modelPresent, true, 'ollama modelPresent should be true when required model is listed');
    assertEqual(data.dependencies.ollama.residency.beforeChat.modelResident, true, 'ollama residency should report resident model before warm chat');
    assertEqual(data.dependencies.ollama.warmState, 'resident-before-chat', 'ollama warmState should report resident-before-chat');
    assertEqual(data.dependencies.ollama.readinessState, 'resident-chat-succeeded', 'resident chat success should have explicit readinessState');
    assertEqual(data.dependencies.ollama.readinessBlocking, false, 'resident chat success should not be readinessBlocking');
    assertEqual(data.dependencies.ollama.blockingAi, false, 'resident chat success should not block AI readiness');
    assertEqual(data.dependencies.ollama.recommendedClientTimeoutMs, 20000, 'recommended client timeout should exceed configured chat timeout');

    // Test 1b.1: cold-before-chat can be slow-but-successful without becoming a hard failure
    ollamaResidentModels = [];
    lastOllamaChatBody = null;
    res = await fetch(`${uploadBase}/ops/dependency-health`);
    data = await res.json();
    assertEqual(data.dependencies.ollama.ok, true, 'cold-before-chat success should keep ollama.ok true');
    assertEqual(data.dependencies.ollama.chatOk, true, 'cold-before-chat success should keep chatOk true');
    assertEqual(data.dependencies.ollama.warmState, 'cold-before-chat', 'cold-before-chat success should preserve warmState');
    assertEqual(data.dependencies.ollama.readinessState, 'cold-start-chat-succeeded', 'cold-before-chat success should be explicit');
    assertEqual(data.dependencies.ollama.coldStartChatSucceeded, true, 'cold-before-chat success should set coldStartChatSucceeded');
    assertEqual(data.dependencies.ollama.readinessBlocking, false, 'cold-before-chat success should not be readinessBlocking');
    assertEqual(data.dependencies.ollama.blockingParse, false, 'cold-before-chat success should not block parse/upload');
    assertEqual(data.dependencies.ollama.probeTimeoutMs, 200, 'ollama probe timeout should be reported');
    assertEqual(data.dependencies.ollama.recommendedClientTimeoutMs, 20000, 'cold-before-chat success should report client timeout expectation');
    assertEqual(data.blocking, false, 'cold-before-chat success should not block parse/upload health');
    ollamaResidentModels = [{ name: 'qwen3.5:9b' }];

    // Test 1c: /health OK but /tasks submit fails with submit probe enabled
    res = await fetch(`${uploadBase}/ops/dependency-health?mineruSubmitProbe=true`);
    data = await res.json();
    assertEqual(data.dependencies.mineru.healthOk, true, 'submit probe failure case keeps /health true');
    assertEqual(data.dependencies.mineru.submitProbe.enabled, true, 'mineru submit probe should be enabled by query');
    assertEqual(data.dependencies.mineru.submitProbe.ok, false, 'mineru submit probe should fail when /tasks fails');
    assertEqual(data.dependencies.mineru.submitProbe.status, 503, 'mineru submit probe should report HTTP status');
    assertEqual(data.dependencies.mineru.ok, false, 'mineru.ok should be false when submit probe fails');
    assertEqual(data.blocking, true, 'blocking should be true when submit probe fails');
    assertEqual(data.dependencies.mineru.admissionCircuit.state, 'open', 'submit probe failure should open durable admission circuit');

    // Test 1c.1: /health 200 alone must not close an open circuit
    res = await fetch(`${uploadBase}/ops/dependency-health`);
    data = await res.json();
    assertEqual(data.dependencies.mineru.healthOk, true, '/health-only check still sees MinerU health OK');
    assertEqual(data.dependencies.mineru.submitProbe.enabled, false, '/health-only check does not run submit probe');
    assertEqual(data.dependencies.mineru.admissionCircuit.state, 'open', '/health 200 alone must not close admission circuit');

    // Test 1d: /health OK and /tasks submit returns task_id with submit probe enabled
    mineruSubmitOk = true;
    res = await fetch(`${uploadBase}/ops/dependency-health?mineruSubmitProbe=true`);
    data = await res.json();
    assertEqual(data.dependencies.mineru.healthOk, true, 'submit probe success case keeps /health true');
    assertEqual(data.dependencies.mineru.submitProbe.ok, true, 'mineru submit probe should pass when /tasks returns task_id');
    assertEqual(Boolean(data.dependencies.mineru.submitProbe.taskId), true, 'mineru submit probe should include taskId');
    assertEqual(data.dependencies.mineru.ok, true, 'mineru.ok should be true when /health and submit probe pass');
    assertEqual(data.blocking, false, 'blocking should be false when minio and mineru submit probe pass');
    assertEqual(data.dependencies.mineru.admissionCircuit.state, 'closed', 'successful submit probe should close circuit after cooldown and clean active diagnostics');

    // Test 2: POST /tasks blocked when mineru down
    const form1 = new FormData();
    const blob1 = new Blob(['dummy pdf content'], { type: 'application/pdf' });
    form1.append('file', blob1, 'test.pdf');
    
    mineruOk = false;
    let taskRes = await fetch(`${uploadBase}/tasks`, { method: 'POST', body: form1 });
    assertEqual(taskRes.status, 503, 'POST /tasks should return 503 when mineru down');
    let taskData = await taskRes.json();
    assertEqual(taskData.code, 'DEPENDENCY_UNHEALTHY', 'Should return DEPENDENCY_UNHEALTHY code');
    assertEqual(taskData.blockingDependency, 'mineru', 'blocking dependency should be mineru');

    // Test 3: POST /tasks blocks PDF intake when /health is OK but submit path fails
    mineruOk = true;
    mineruSubmitOk = false;
    // (minio ok is implicit via tmpfiles backend mock)
    const form2 = new FormData();
    form2.append('file', blob1, 'test.pdf');
    taskRes = await fetch(`${uploadBase}/tasks`, { method: 'POST', body: form2 });
    if (taskRes.status !== 503) {
      console.error('Test 3 failed payload:', await taskRes.text());
    }
    assertEqual(taskRes.status, 503, 'POST /tasks should return 503 when MinerU submit circuit opens');
    taskData = await taskRes.json();
    assertEqual(taskData.code, 'MINERU_ADMISSION_CIRCUIT_OPEN', 'POST /tasks should return admission circuit code');
    assertEqual(taskData.message, 'MinerU 当前不可接收新任务，文件未收取，请稍后重试。', 'POST /tasks should tell operator the file was not accepted');

    // Test 3b: POST /tasks allowed when submit probe succeeds
    mineruSubmitOk = true;
    const form2b = new FormData();
    form2b.append('file', blob1, 'test.pdf');
    taskRes = await fetch(`${uploadBase}/tasks`, { method: 'POST', body: form2b });
    if (taskRes.status !== 200) {
      console.error('Test 3b failed payload:', await taskRes.text());
    }
    assertEqual(taskRes.status, 200, 'POST /tasks should succeed (200) when /health and submit probe are ok');

    // Test 4: ollama down does not block parse but is reported
    mineruOk = true;
    ollamaOk = false;
    ollamaModels = [{ name: 'qwen3.5:9b' }];
    ollamaResidentModels = [];
    ollamaChatHangs = false;
    let resOllamaDown = await fetch(`${uploadBase}/ops/dependency-health`);
    let dataOllamaDown = await resOllamaDown.json();
    assertEqual(dataOllamaDown.dependencies.mineru.ok, true, 'mineru.ok should be true');
    assertEqual(dataOllamaDown.dependencies.ollama.ok, false, 'ollama.ok should be false');
    assertEqual(dataOllamaDown.dependencies.ollama.blockingParse, false, 'ollama.blockingParse should be false');
    assertEqual(dataOllamaDown.dependencies.ollama.blockingAi, true, 'ollama down should block AI readiness');
    assertEqual(dataOllamaDown.dependencies.ollama.readinessState, 'tags-http-error', 'ollama down should classify readinessState');
    assertEqual(dataOllamaDown.blocking, false, 'blocking should be false when only ollama is down');

    const form3 = new FormData();
    form3.append('file', blob1, 'test.pdf');
    taskRes = await fetch(`${uploadBase}/tasks`, { method: 'POST', body: form3 });
    if (taskRes.status !== 200) {
      console.error('Test 4 failed payload:', await taskRes.text());
    }
    assertEqual(taskRes.status, 200, 'POST /tasks should succeed even if ollama is down');

    // Test 5: ollama tags ok but chat fails
    mineruOk = true;
    ollamaOk = true;
    ollamaModels = [{ name: 'qwen3.5:9b' }];
    ollamaResidentModels = [{ name: 'qwen3.5:9b' }];
    ollamaChatOk = false;
    ollamaChatHangs = false;
    let resChatDown = await fetch(`${uploadBase}/ops/dependency-health`);
    let dataChatDown = await resChatDown.json();
    assertEqual(dataChatDown.dependencies.ollama.ok, false, 'ollama.ok should be false when chat fails');
    assertEqual(dataChatDown.dependencies.ollama.chatOk, false, 'ollama.chatOk should be false');
    assertEqual(dataChatDown.dependencies.ollama.error.includes('Smoke test HTTP 503'), true, 'Should include smoke test error');
    assertEqual(dataChatDown.dependencies.ollama.failureKind, 'chat-http-error', 'ollama HTTP chat failure should be classified');
    assertEqual(dataChatDown.dependencies.ollama.readinessState, 'chat-http-error', 'ollama HTTP chat failure should set readinessState');
    assertEqual(dataChatDown.dependencies.ollama.readinessBlocking, true, 'ollama HTTP chat failure should be AI-readiness blocking');

    // Test 5b: cold model chat timeout is explicit
    ollamaOk = true;
    ollamaModels = [{ name: 'qwen3.5:9b' }];
    ollamaResidentModels = [];
    ollamaChatOk = true;
    ollamaChatHangs = true;
    let resColdTimeout = await fetch(`${uploadBase}/ops/dependency-health`);
    let dataColdTimeout = await resColdTimeout.json();
    assertEqual(dataColdTimeout.dependencies.ollama.ok, false, 'ollama.ok should be false when cold chat times out');
    assertEqual(dataColdTimeout.dependencies.ollama.chatOk, false, 'ollama.chatOk should be false when cold chat times out');
    assertEqual(dataColdTimeout.dependencies.ollama.warmState, 'cold-before-chat', 'cold timeout should preserve cold-before-chat warmState');
    assertEqual(dataColdTimeout.dependencies.ollama.coldStartChatTimeout, true, 'cold timeout should set coldStartChatTimeout');
    assertEqual(dataColdTimeout.dependencies.ollama.failureKind, 'cold-start-chat-timeout', 'cold timeout should be classified separately');
    assertEqual(dataColdTimeout.dependencies.ollama.readinessState, 'cold-start-chat-timeout', 'cold timeout should set readinessState');
    assertEqual(dataColdTimeout.dependencies.ollama.readinessBlocking, true, 'cold timeout should block AI readiness');
    assertEqual(dataColdTimeout.dependencies.ollama.blockingParse, false, 'cold timeout should not block parse/upload');

    // Test 5c: resident model chat timeout is not labeled as cold start
    ollamaResidentModels = [{ name: 'qwen3.5:9b' }];
    let resWarmTimeout = await fetch(`${uploadBase}/ops/dependency-health`);
    let dataWarmTimeout = await resWarmTimeout.json();
    assertEqual(dataWarmTimeout.dependencies.ollama.ok, false, 'ollama.ok should be false when warm chat times out');
    assertEqual(dataWarmTimeout.dependencies.ollama.warmState, 'resident-before-chat', 'warm timeout should preserve resident-before-chat warmState');
    assertEqual(dataWarmTimeout.dependencies.ollama.warmChatTimeout, true, 'warm timeout should set warmChatTimeout');
    assertEqual(dataWarmTimeout.dependencies.ollama.coldStartChatTimeout, false, 'warm timeout should not be labeled as cold start');
    assertEqual(dataWarmTimeout.dependencies.ollama.failureKind, 'warm-chat-timeout', 'warm timeout should be classified separately');
    assertEqual(dataWarmTimeout.dependencies.ollama.readinessState, 'warm-chat-timeout', 'warm timeout should set readinessState');
    ollamaChatHangs = false;
    ollamaChatOk = true;

    // Test 6: strict no-skeleton mode fails when required Ollama model is missing
    ollamaOk = true;
    ollamaChatOk = true;
    ollamaChatHangs = false;
    ollamaModels = [{ name: 'qwen3.5:0.8b' }];
    ollamaResidentModels = [{ name: 'qwen3.5:9b' }];
    lastOllamaChatBody = null;
    let resMissingModel = await fetch(`${uploadBase}/ops/dependency-health`);
    let dataMissingModel = await resMissingModel.json();
    assertEqual(dataMissingModel.dependencies.ollama.ok, false, 'ollama.ok should be false when required model is missing');
    assertEqual(dataMissingModel.dependencies.ollama.error, 'Missing required Ollama model: qwen3.5:9b', 'missing model error should name required model');
    assertEqual(dataMissingModel.dependencies.ollama.readinessState, 'model-missing', 'missing model should set readinessState');
    assertEqual(dataMissingModel.dependencies.ollama.blockingAi, true, 'missing model should block AI readiness');
    assertEqual(lastOllamaChatBody, null, 'ollama smoke should not run when required model is missing');
    assertEqual(dataMissingModel.blocking, false, 'missing ollama model should not block parse');

  } finally {
    child.kill();
    dummyServer.close();
    dbServer.close();
  }

  console.log(`\nResults: ${passedCount} passed, ${failedCount} failed`);
  if (failedCount > 0) process.exit(1);
}

runTest().catch((err) => {
  console.error(err);
  process.exit(1);
});
