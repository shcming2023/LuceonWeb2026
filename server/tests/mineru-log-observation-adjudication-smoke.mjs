/**
 * Focused smoke for MinerU log-observation adjudication.
 *
 * Verifies:
 * - log-observation-unreadable/stale while MinerU API is still processing is diagnostic-only;
 * - explicit MinerU API failed status still fails.
 */

import fs from 'fs';
import path from 'path';
import { processWithLocalMinerU } from '../services/mineru/local-adapter.mjs';

let testsPassed = 0;
let testsFailed = 0;

function assert(condition, message) {
  if (!condition) {
    console.error(`FAILED: ${message}`);
    testsFailed += 1;
    return;
  }
  testsPassed += 1;
}

function makeJsonResponse(payload, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => 'application/json' },
    json: async () => payload,
    text: async () => JSON.stringify(payload)
  };
}

async function* pdfStream() {
  yield Buffer.from('%PDF-1.4\n');
}

function makeBaseTask(id) {
  return {
    id,
    materialId: `${id}-material`,
    createdAt: new Date(Date.now() - 60_000).toISOString(),
    metadata: {},
    optionsSnapshot: {
      localEndpoint: 'http://mineru-test',
      backend: 'pipeline',
      enableOcr: true,
      enableFormula: true,
      enableTable: true,
      maxPages: 10
    }
  };
}

async function withStaleEmptyLog(fn) {
  const previousLogPath = process.env.MINERU_LOG_PATH;
  const previousErrLogPath = process.env.MINERU_ERR_LOG_PATH;
  const scratchDir = path.join(process.cwd(), 'uat', 'scratch');
  fs.mkdirSync(scratchDir, { recursive: true });
  const staleLogPath = path.join(scratchDir, 'mineru-log-observation-adjudication-empty.log');
  fs.writeFileSync(staleLogPath, '');
  const staleTime = new Date(Date.now() - 900_000);
  fs.utimesSync(staleLogPath, staleTime, staleTime);
  process.env.MINERU_LOG_PATH = staleLogPath;
  process.env.MINERU_ERR_LOG_PATH = staleLogPath;

  try {
    await fn();
  } finally {
    if (previousLogPath == null) delete process.env.MINERU_LOG_PATH;
    else process.env.MINERU_LOG_PATH = previousLogPath;
    if (previousErrLogPath == null) delete process.env.MINERU_ERR_LOG_PATH;
    else process.env.MINERU_ERR_LOG_PATH = previousErrLogPath;
  }
}

async function runProcessingDiagnosticOnlyTest() {
  console.log('Test 1: processing + unreadable/stale log observation stays non-terminal');
  const updates = [];
  const saved = [];
  let statusCalls = 0;
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async (url, options = {}) => {
    const urlString = String(url);
    if (urlString === 'http://mineru-test/health') return { status: 200 };
    if (urlString === 'http://mineru-test/tasks' && options.method === 'POST') {
      return makeJsonResponse({ task_id: 'mineru-log-processing' });
    }
    if (urlString === 'http://mineru-test/tasks/mineru-log-processing') {
      statusCalls += 1;
      if (statusCalls === 1) {
        return makeJsonResponse({
          status: 'processing',
          started_at: new Date(Date.now() - 30_000).toISOString()
        });
      }
      return makeJsonResponse({ status: 'completed', started_at: new Date(Date.now() - 30_000).toISOString() });
    }
    if (urlString === 'http://mineru-test/tasks/mineru-log-processing/result') {
      return makeJsonResponse({ md_content: '# parsed ok' });
    }
    return originalFetch(url, options);
  };

  try {
    const result = await processWithLocalMinerU({
      task: makeBaseTask('log-diagnostic-nonterminal'),
      material: { fileSize: 1024 },
      fileStream: pdfStream(),
      fileName: 'sample.pdf',
      mimeType: 'application/pdf',
      timeoutMs: 5000,
      minioContext: {
        saveObject: async (...args) => { saved.push(args); },
        saveMarkdown: async (...args) => { saved.push(args); }
      },
      updateProgress: async (update) => { updates.push(update); }
    });

    const warningUpdate = updates.find((update) => update.metadata?.mineruLogObservationWarning);
    assert(result.markdown === '# parsed ok', 'MinerU result should complete successfully');
    assert(warningUpdate !== undefined, 'Processing log observation issue should be retained as warning metadata');
    assert(
      warningUpdate?.metadata?.mineruLogObservationWarning?.kind === 'mineru-log-observation-diagnostic-only',
      'Warning should be marked diagnostic-only'
    );
    assert(!updates.some((update) => update.state === 'failed'), 'No failed progress update should be emitted');
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function runApiFailureStillFailsTest() {
  console.log('Test 2: explicit MinerU API failed status remains terminal');
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async (url, options = {}) => {
    const urlString = String(url);
    if (urlString === 'http://mineru-test/health') return { status: 200 };
    if (urlString === 'http://mineru-test/tasks' && options.method === 'POST') {
      return makeJsonResponse({ task_id: 'mineru-api-failed' });
    }
    if (urlString === 'http://mineru-test/tasks/mineru-api-failed') {
      return makeJsonResponse({ status: 'failed', error: 'PDF parsing internal error: corrupted file' });
    }
    return originalFetch(url, options);
  };

  try {
    let caught = null;
    try {
      await processWithLocalMinerU({
        task: makeBaseTask('api-failure-terminal'),
        material: { fileSize: 1024 },
        fileStream: pdfStream(),
        fileName: 'corrupted.pdf',
        mimeType: 'application/pdf',
        timeoutMs: 5000,
        minioContext: {
          saveObject: async () => {},
          saveMarkdown: async () => {}
        },
        updateProgress: async () => {}
      });
    } catch (error) {
      caught = error;
    }

    assert(caught instanceof Error, 'MinerU API failed status should throw');
    assert(String(caught?.message || '').includes('corrupted file'), 'Thrown error should preserve MinerU API failure evidence');
  } finally {
    globalThis.fetch = originalFetch;
  }
}

await withStaleEmptyLog(async () => {
  await runProcessingDiagnosticOnlyTest();
  await runApiFailureStillFailsTest();
});

console.log(`Results: ${testsPassed} passed, ${testsFailed} failed`);
if (testsFailed > 0) process.exit(1);
