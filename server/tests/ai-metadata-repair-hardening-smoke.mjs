import assert from 'node:assert';

process.env.DISABLE_AI_SKELETON_FALLBACK = 'true';
process.env.ALLOW_AI_SKELETON_FALLBACK = 'false';

const { AiMetadataWorker } = await import('../services/ai/metadata-worker.mjs');
const { BaseProvider } = await import('../services/ai/providers/base.mjs');

const DB_BASE_URL = process.env.DB_BASE_URL || 'http://localhost:8789';
const ORIGINAL_MARKDOWN_SENTINEL = 'ORIGINAL_MARKDOWN_SENTINEL_DO_NOT_REPEAT_IN_REPAIR';

function makeMarkdown() {
  return [
    '# Test material',
    ORIGINAL_MARKDOWN_SENTINEL,
    'This source text is intentionally large enough to catch repair-prompt repetition.',
    'x'.repeat(22000),
  ].join('\n');
}

function makeFetchMock({ updates }) {
  return async (url, options = {}) => {
    const href = String(url);
    const method = options.method || 'GET';

    if (href === `${DB_BASE_URL}/settings`) {
      return {
        ok: true,
        json: async () => ({
          aiConfig: {
            providers: [{ id: 'ollama', provider: 'ollama', enabled: true, priority: 1 }],
            ollamaTwoPassJsonRepair: true,
            temperature: 0.1,
          },
        }),
      };
    }

    if (href === `${DB_BASE_URL}/tasks/parse-test`) {
      if (method === 'PATCH') return { ok: true, json: async () => ({}) };
      return {
        ok: true,
        json: async () => ({
          id: 'parse-test',
          state: 'completed',
          metadata: {
            originalFilename: 'repair-hardening.pdf',
            originalFileSize: 1234,
            mimeType: 'application/pdf',
            objectName: 'originals/mat-test/source.pdf',
            parsedPrefix: 'parsed/mat-test/',
            markdownObjectName: 'parsed/mat-test/full.md',
            parsedFilesCount: 1,
            mineruExecutionProfile: { backendEffective: 'pipeline' },
          },
        }),
      };
    }

    if (href === `${DB_BASE_URL}/materials/mat-test`) {
      return {
        ok: true,
        json: async () => ({
          id: 'mat-test',
          fileName: 'repair-hardening.pdf',
          fileSize: 1234,
          mimeType: 'application/pdf',
          metadata: {
            objectName: 'originals/mat-test/source.pdf',
            parsedPrefix: 'parsed/mat-test/',
            markdownObjectName: 'parsed/mat-test/full.md',
            parsedFilesCount: 1,
          },
        }),
      };
    }

    if (href === `${DB_BASE_URL}/ai-metadata-jobs/ai-job-test` && method === 'PATCH') {
      const body = JSON.parse(options.body || '{}');
      updates.push(body);
      return { ok: true, json: async () => ({}) };
    }

    if (href === `${DB_BASE_URL}/task-events`) {
      return { ok: true, json: async () => ({}) };
    }

    return { ok: true, json: async () => ({}) };
  };
}

function makeMinio() {
  return {
    getFileStream: async () => ({
      [Symbol.asyncIterator]: async function* () {
        yield Buffer.from(makeMarkdown());
      },
    }),
  };
}

function makeJob() {
  return {
    id: 'ai-job-test',
    parseTaskId: 'parse-test',
    materialId: 'mat-test',
    inputMarkdownObjectName: 'parsed/mat-test/full.md',
  };
}

async function testDeterministicDraftRepairSkipsSecondProviderCall() {
  const updates = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = makeFetchMock({ updates });

  try {
    let calls = 0;
    const worker = new AiMetadataWorker({ minioContext: makeMinio() });
    worker.createProvider = () => ({
      id: 'ollama',
      model: 'qwen3.5:9b',
      extractMetadata: async (markdown) => {
        calls += 1;
        assert(markdown.includes(ORIGINAL_MARKDOWN_SENTINEL), 'first pass should receive sampled original markdown');
        return {
          provider: 'ollama',
          model: 'qwen3.5:9b',
          result: JSON.stringify({
            classification_draft: {
              domain: '01_出版教材与成套课程',
              subject: '英语',
              resource_type: '试卷',
              component_role: '主体资料',
            },
            descriptive_draft: {
              series_title: 'Repair hardening sample',
              title: 'Repair hardening sample',
            },
            candidate_tags: {
              topic_tags: ['reading'],
            },
            evidence: ['The document is an English test paper.'],
            governance: {
              confidence: 'medium',
              human_review_required: true,
            },
          }),
          usage: { total_duration_ms: 12 },
        };
      },
    });

    await worker.processJob(makeJob());

    const terminal = updates.find((update) => update.state === 'review-pending' || update.state === 'confirmed');
    assert(terminal, 'deterministic repair should complete the AI job');
    assert.equal(calls, 1, 'canonical draft should be normalized without an LLM repair pass');
    assert.equal(terminal.result.aiClassificationTwoPassAttempted, true);
    assert.equal(terminal.result.aiClassificationRepairSucceeded, true);
    assert.equal(terminal.result.aiClassificationDeterministicRepairSucceeded, true);
    assert.notEqual(terminal.result.aiClassificationProvider, 'skeleton');
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function testRepairTimeoutStrictModeFailsWithoutSkeletonAndUsesBoundedInput() {
  const updates = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = makeFetchMock({ updates });

  try {
    let calls = 0;
    let repairMarkdown = '';
    let repairPrompt = '';
    const worker = new AiMetadataWorker({ minioContext: makeMinio() });
    worker.createProvider = () => ({
      id: 'ollama',
      model: 'qwen3.5:9b',
      extractMetadata: async (markdown, settings = {}) => {
        calls += 1;
        if (calls === 1) {
          return {
            provider: 'ollama',
            model: 'qwen3.5:9b',
            result: `not json ${ORIGINAL_MARKDOWN_SENTINEL} ${'y'.repeat(24000)}`,
            usage: { total_duration_ms: 10 },
          };
        }

        repairMarkdown = markdown;
        repairPrompt = settings.systemPrompt || '';
        const err = new Error('mock repair timeout');
        err.timeoutKind = 'abort-timeout';
        err.details = {
          timeoutKind: 'abort-timeout',
          durationMs: 25,
          timeoutMs: 25,
          phaseName: 'repair-pass',
          promptLength: repairPrompt.length,
          inputLength: repairMarkdown.length,
          numPredict: settings.num_predict,
        };
        throw err;
      },
    });

    await worker.processJob(makeJob());

    const failed = updates.find((update) => update.state === 'failed');
    assert(failed, 'strict no-skeleton mode should fail the AI job after repair timeout');
    assert.match(failed.errorMessage, /AI 严格模式拦截/);
    assert.equal(failed.aiFailureClassification?.kind, 'strict-no-skeleton-fallback-block');
    assert.equal(failed.aiFailureClassification?.aiPhase, 'strict-skeleton-block');
    assert.equal(failed.aiFailureClassification?.underlying?.kind, 'repair-pass-provider-timeout');
    assert.equal(failed.aiFailureClassification?.underlying?.aiPhase, 'repair-pass');
    assert.equal(failed.metadata?.aiFailureClassification?.autoRetryAllowed, false);
    assert.equal(failed.metadata?.manualRetryEligible, true);
    assert.equal(failed.metadata?.autoRetryAllowed, false);
    assert.equal(calls, 2, 'repair timeout case should attempt exactly one repair pass');
    assert(!repairMarkdown.includes(ORIGINAL_MARKDOWN_SENTINEL), 'repair user content must not repeat original markdown');
    assert(repairMarkdown.length < 1000, `repair user content should be compact, got ${repairMarkdown.length}`);
    assert(repairPrompt.includes('not json'), 'repair prompt should include bounded first-pass output');
    assert(repairPrompt.length < 20000, `repair prompt should be bounded, got ${repairPrompt.length}`);
  } finally {
    globalThis.fetch = originalFetch;
  }
}

function testInvalidLatexEscapesAreRepairedWithoutSkeleton() {
  const provider = new BaseProvider();
  const rawRepairOutput = `{
    "primary_facets": {
      "domain": {"zh": "考试测评与真题"},
      "subject": {"zh": "数学"},
      "resource_type": {"zh": "试卷"},
      "component_role": {"zh": "主体资料"}
    },
    "governance": {
      "confidence": "high",
      "human_review_required": false,
      "risk_flags": []
    },
    "evidence": [
      {
        "type": "content",
        "quote_or_summary": "在 $\\sqcap A B C D$ 中，$\\angle A D F = 9 0 ^ { \\circ }$",
        "supports": ["subject", "resource_type"]
      }
    ]
  }`;

  assert.throws(
    () => JSON.parse(rawRepairOutput),
    /Bad escaped character|Unexpected token/,
    'fixture should reproduce Task 95 invalid JSON escape shape'
  );

  const parsed = provider.parseJsonRobust(rawRepairOutput);
  assert(parsed, 'robust parser should recover invalid JSON string escapes');
  assert.equal(parsed.primary_facets.subject.zh, '数学');
  assert.equal(parsed.evidence[0].quote_or_summary.includes('\\sqcap'), true);
  assert.equal(parsed.evidence[0].quote_or_summary.includes('\\angle'), true);

  const worker = new AiMetadataWorker({});
  const workerParsed = worker.extractJson(rawRepairOutput);
  assert.equal(workerParsed.primary_facets.resource_type.zh, '试卷');
  assert.equal(workerParsed.governance.confidence, 'high');
}

async function main() {
  console.log('--- AI Metadata Repair Hardening Smoke Test Start ---');
  await testDeterministicDraftRepairSkipsSecondProviderCall();
  console.log('Case 1 Pass: deterministic draft repair skips second provider call');
  await testRepairTimeoutStrictModeFailsWithoutSkeletonAndUsesBoundedInput();
  console.log('Case 2 Pass: strict repair timeout fails without skeleton and bounded input');
  testInvalidLatexEscapesAreRepairedWithoutSkeleton();
  console.log('Case 3 Pass: invalid LaTeX escapes are repaired deterministically without skeleton');
  console.log('--- AI Metadata Repair Hardening Smoke Test Passed ---');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
