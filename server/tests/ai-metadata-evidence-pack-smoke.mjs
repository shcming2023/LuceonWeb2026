import assert from 'node:assert';
import { buildEvidencePack } from '../services/ai/metadata-evidence-pack.mjs';
import { AiMetadataWorker, shouldUseEvidencePack } from '../services/ai/metadata-worker.mjs';

async function runTests() {
  console.log('--- AI Metadata Evidence Pack Smoke Test ---');

  // Test 1: Heading Outline Extraction
  console.log('Test 1: Heading Outline Extraction');
  const sampleMd = `
# Chapter 1
some text
## Exercise
1. Algebra
some text
### Final
  `;
  const pack1 = buildEvidencePack(sampleMd, { filename: 'test.md' });
  const outline = pack1.content.split('=== HEADING OUTLINE ===')[1].split('=== REPRESENTATIVE BODY SNIPPETS ===')[0];
  assert.ok(outline.includes('# Chapter 1'));
  assert.ok(outline.includes('## Exercise'));
  assert.ok(outline.includes('1. Algebra'));
  assert.ok(outline.includes('### Final'));
  console.log('Test 1 Pass ✅');

  // Test 2: Filename Signals
  console.log('Test 2: Filename Signals');
  const filename2 = 'Cambridge IGCSE(0580) Core and Extended Mathematics_2018(Cambridge University Press).pdf';
  const pack2 = buildEvidencePack('mock content', { filename: filename2 });
  const filenameSignals = pack2.content.split('=== FILENAME SIGNALS ===')[1].split('=== DOCUMENT SHAPE ===')[0];
  assert.ok(filenameSignals.includes('Cambridge'));
  assert.ok(filenameSignals.includes('IGCSE'));
  assert.ok(filenameSignals.includes('0580'));
  assert.ok(filenameSignals.includes('Core'));
  assert.ok(filenameSignals.includes('Extended'));
  assert.ok(filenameSignals.includes('Mathematics'));
  assert.ok(filenameSignals.includes('2018'));
  console.log('Test 2 Pass ✅');

  // Test 2A: Adaptive input-selection thresholds
  console.log('Test 2A: Adaptive input-selection thresholds');
  const mediumLargeSelection = shouldUseEvidencePack(50001, { fileSize: 1, parsedFilesCount: 1 });
  assert.equal(mediumLargeSelection.useEvidencePack, true);
  assert.deepEqual(mediumLargeSelection.reasons, ['markdown-length']);
  assert.equal(mediumLargeSelection.thresholds.markdownLength, 50000);

  const fileSizeSelection = shouldUseEvidencePack(1000, { fileSize: 10000001, parsedFilesCount: 1 });
  assert.equal(fileSizeSelection.useEvidencePack, true);
  assert.deepEqual(fileSizeSelection.reasons, ['source-file-size']);
  assert.equal(fileSizeSelection.thresholds.fileSize, 10000000);

  const parsedFilesSelection = shouldUseEvidencePack(1000, { fileSize: 1, parsedFilesCount: 51 });
  assert.equal(parsedFilesSelection.useEvidencePack, true);
  assert.deepEqual(parsedFilesSelection.reasons, ['parsed-files-count']);
  assert.equal(parsedFilesSelection.thresholds.parsedFilesCount, 50);

  const shortSelection = shouldUseEvidencePack(50000, { fileSize: 10000000, parsedFilesCount: 50 });
  assert.equal(shortSelection.useEvidencePack, false);
  assert.deepEqual(shortSelection.reasons, []);

  const task29Selection = shouldUseEvidencePack(104823, { fileSize: 15157403, parsedFilesCount: 99 });
  assert.equal(task29Selection.useEvidencePack, true);
  assert.deepEqual(task29Selection.reasons, ['markdown-length', 'source-file-size', 'parsed-files-count']);
  console.log('Test 2A Pass ✅');

  // Test 3: Worker selects evidence pack for large document
  console.log('Test 3: Worker selects evidence pack for large document');
  let workerResult = null;
  const mockMinio3 = {
    getFileStream: async () => ({ [Symbol.asyncIterator]: async function* () { yield Buffer.from('a'.repeat(200000)); } }),
    saveObject: async () => {}
  };
  const worker3 = new AiMetadataWorker(mockMinio3);
  worker3.executeWithFallback = async (provider, markdown, settings, prompt) => {
    return {
      provider: 'ollama', model: 'test',
      result: '{"classification_draft": {"domain": {"zh": "test"}}, "evidence": []}',
      rawResponse: '{}',
      traceDetails: { rawLooksTruncated: false },
      usage: {}
    };
  };
  worker3.transition = async (job, update) => { workerResult = update.result; };
  await worker3.processJob({ id: 'test-job-3', parseTaskId: 't3', inputMarkdownObjectName: 'x.md' });
  assert.equal(workerResult.aiClassificationSamplingMode, 'evidence-pack-v0.3');
  assert.equal(workerResult.aiClassificationInputOriginalLength, 200000);
  assert.ok(workerResult.aiClassificationInputSampledLength < 30000);
  assert.deepEqual(workerResult.aiClassificationInputSelectionReasons, ['markdown-length']);
  assert.equal(workerResult.aiClassificationInputSelectionThresholds.markdownLength, 50000);
  assert.ok(workerResult.aiClassificationRawTrace.input.sections.evidenceCandidates);
  assert.equal(workerResult.aiClassificationRawTrace.input.triggerReasons[0], 'markdown-length');
  assert.ok(workerResult.aiClassificationRawTrace.input.inputHash.startsWith('sha256:'));
  console.log('Test 3 Pass ✅');

  // Test 3A: Worker selects evidence pack for task-29-like medium-large PDF shape
  console.log('Test 3A: Worker selects evidence pack for task-29-like medium-large PDF shape');
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    const href = String(url);
    if (href.includes('/tasks/t29')) {
      return { ok: true, json: async () => ({
        id: 't29',
        state: 'completed',
        metadata: {
          originalFilename: 'G7_Workbook_ready_to_print.pdf',
          originalFileSize: 15157403,
          objectName: 'originals/mat-task-29/source.pdf',
          markdownObjectName: 'parsed/mat-task-29/full.md',
          parsedFilesCount: 99,
          mimeType: 'application/pdf'
        }
      }) };
    }
    if (href.includes('/settings')) return { ok: true, json: async () => ({}) };
    if (href.includes('/task-events')) return { ok: true, json: async () => ({}) };
    return { ok: true, json: async () => ({}) };
  };
  try {
    const mockMinio29 = {
      getFileStream: async () => ({ [Symbol.asyncIterator]: async function* () { yield Buffer.from('a'.repeat(104823)); } }),
      saveObject: async () => {}
    };
    const worker29 = new AiMetadataWorker(mockMinio29);
    worker29.executeWithFallback = async () => {
      return {
        provider: 'ollama',
        model: 'test',
        result: '{"classification_draft": {"domain": {"zh": "test"}}, "evidence": []}',
        rawResponse: '{}',
        traceDetails: { rawLooksTruncated: false },
        usage: {}
      };
    };
    worker29.transition = async (job, update) => { workerResult = update.result; };
    await worker29.processJob({ id: 'test-job-29', parseTaskId: 't29', inputMarkdownObjectName: 'x.md' });
    assert.equal(workerResult.aiClassificationSamplingMode, 'evidence-pack-v0.3');
    assert.equal(workerResult.aiClassificationInputOriginalLength, 104823);
    assert.ok(workerResult.aiClassificationInputSampledLength < 30000);
    assert.deepEqual(workerResult.aiClassificationInputSelectionReasons, ['markdown-length', 'source-file-size', 'parsed-files-count']);
    assert.equal(workerResult.aiClassificationRawTrace.input.observed.markdownLength, 104823);
    assert.equal(workerResult.aiClassificationRawTrace.input.observed.fileSize, 15157403);
    assert.equal(workerResult.aiClassificationRawTrace.input.observed.parsedFilesCount, 99);
    assert.ok(workerResult.aiClassificationInputHash.startsWith('sha256:'));
  } finally {
    globalThis.fetch = originalFetch;
  }
  console.log('Test 3A Pass ✅');

  // Test 4: Worker uses legacy sampler for small document
  console.log('Test 4: Worker uses legacy sampler for small document');
  const mockMinio4 = {
    getFileStream: async () => ({ [Symbol.asyncIterator]: async function* () { yield Buffer.from('small doc'); } }),
    saveObject: async () => {}
  };
  const worker4 = new AiMetadataWorker(mockMinio4);
  worker4.executeWithFallback = async (provider, markdown, settings, prompt) => {
    return {
      provider: 'ollama', model: 'test',
      result: '{"primary_facets": {"domain": {"zh": "test"}}, "evidence": [], "governance": {"confidence": "high"}}',
      rawResponse: '{}',
      traceDetails: { rawLooksTruncated: false },
      usage: {}
    };
  };
  worker4.transition = async (job, update) => { workerResult = update.result; };
  await worker4.processJob({ id: 'test-job-4', parseTaskId: 't4', inputMarkdownObjectName: 'x.md' });
  assert.equal(workerResult.aiClassificationSamplingMode, 'legacy-sampler-v0.2');
  assert.equal(workerResult.aiClassificationInputOriginalLength, 9);
  assert.ok(workerResult.aiClassificationInputSampledLength >= 9);
  assert.deepEqual(workerResult.aiClassificationInputSelectionReasons, []);
  console.log('Test 4 Pass ✅');

  // Test 5: Draft Repair
  console.log('Test 5: Draft Repair mapping');
  const mockMinio5 = {
    getFileStream: async () => ({ [Symbol.asyncIterator]: async function* () { yield Buffer.from('a'.repeat(200000)); } }),
    saveObject: async () => {}
  };
  const worker5 = new AiMetadataWorker(mockMinio5);
  let callCount5 = 0;
  worker5._runProviderPass = async (provider, job, settings, prompt, options) => {
    callCount5++;
    if (callCount5 === 1) {
      assert.ok(prompt.includes('classification_draft'), 'First pass should use draft prompt');
      return {
        provider: 'ollama', model: 'test',
        result: '{"classification_draft": {"domain": "考试测评与真题", "subject": "数学", "collection": "Cambridge IGCSE", "level": "IGCSE", "resource_type": "练习册", "component_role": "主体资料"}, "evidence": [{"type": "content", "quote_or_summary": "Test evidence", "supports": []}]}',
        rawResponse: '{"classification_draft": {"domain": "考试测评与真题", "subject": "数学", "collection": "Cambridge IGCSE", "level": "IGCSE", "resource_type": "练习册", "component_role": "主体资料"}, "evidence": [{"type": "content", "quote_or_summary": "Test evidence", "supports": []}]}',
        traceDetails: { rawLooksTruncated: false },
        usage: {}
      };
    } else {
      assert.ok(prompt.includes('**草稿内容（可能是旧式 JSON、扁平 JSON、或自然语言草稿，或包含 classification_draft 的草稿 JSON）：**'), 'Repair prompt should be updated');
      return {
        provider: 'ollama', model: 'test',
        result: '{"primary_facets": {"domain": {"zh": "02_考试测评与真题"}, "subject": {"zh": "数学"}, "collection": {"zh": "Cambridge IGCSE"}, "level": {"zh": "IGCSE"}, "resource_type": {"zh": "练习册"}, "component_role": {"zh": "主体资料"}}, "governance": {"confidence": "high"}, "evidence": [{"type": "content", "quote_or_summary": "Test evidence", "supports": []}]}',
        rawResponse: '{"primary_facets": {"domain": {"zh": "02_考试测评与真题"}, "subject": {"zh": "数学"}, "collection": {"zh": "Cambridge IGCSE"}, "level": {"zh": "IGCSE"}, "resource_type": {"zh": "练习册"}, "component_role": {"zh": "主体资料"}}, "governance": {"confidence": "high"}, "evidence": [{"type": "content", "quote_or_summary": "Test evidence", "supports": []}]}',
        traceDetails: { rawLooksTruncated: false },
        usage: {}
      };
    }
  };
  worker5.transition = async (job, update) => { workerResult = update.result; };
  await worker5.processJob({ id: 'test-job-5', parseTaskId: 't5', inputMarkdownObjectName: 'x.md' });
  assert.equal(workerResult.aiClassificationV02.controlled_classification.domain.id, '02_考试测评与真题');
  assert.equal(workerResult.aiClassificationV02.controlled_classification.subject.zh, '数学');
  assert.equal(workerResult.aiClassificationV02.controlled_classification.collection.id, 'Cambridge IGCSE');
  assert.equal(workerResult.aiClassificationV02.controlled_classification.level.id, 'IGCSE');
  assert.equal(workerResult.aiClassificationV02.controlled_classification.resource_type.zh, '练习册');
  assert.equal(workerResult.aiClassificationV02.controlled_classification.component_role.zh, '主体资料');
  assert.equal(workerResult.aiClassificationDegraded, undefined);
  console.log('Test 5 Pass ✅');

  console.log('--- AI Metadata Evidence Pack Smoke Test Success ---');
}

runTests().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
