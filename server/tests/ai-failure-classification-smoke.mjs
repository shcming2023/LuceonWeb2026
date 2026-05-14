import assert from 'node:assert';

process.env.DISABLE_AI_SKELETON_FALLBACK = 'true';
process.env.ALLOW_AI_SKELETON_FALLBACK = 'false';

const {
  buildAiFailureClassification,
  sanitizeProviderBaseUrl,
} = await import('../services/ai/metadata-worker.mjs');

function makeProvider() {
  return {
    id: 'ollama',
    model: 'qwen3.5:9b',
    baseUrl: 'http://user:secret@localhost:11434?token=hidden',
    timeoutMs: 180000,
  };
}

function testProviderTimeoutPhases() {
  const provider = makeProvider();
  const firstPass = buildAiFailureClassification({
    error: {
      message: 'TimeoutError: The operation was aborted due to timeout',
      timeoutKind: 'abort-timeout',
      details: { durationMs: 180004, timeoutMs: 180000 },
    },
    phaseName: 'first-pass',
    providerId: 'ollama',
    provider,
  });
  assert.equal(firstPass.kind, 'first-pass-provider-timeout');
  assert.equal(firstPass.aiPhase, 'first-pass');
  assert.equal(firstPass.manualRetryEligible, true);
  assert.equal(firstPass.autoRetryAllowed, false);
  assert.equal(firstPass.baseUrl, 'http://localhost:11434');

  const repairPass = buildAiFailureClassification({
    error: {
      message: 'Headers Timeout Error',
      details: { timeoutKind: 'headers-timeout', durationMs: 180001, timeoutMs: 180000 },
    },
    phaseName: 'repair-pass',
    providerId: 'ollama',
    provider,
  });
  assert.equal(repairPass.kind, 'repair-pass-provider-timeout');
  assert.equal(repairPass.aiPhase, 'repair-pass');
  assert.equal(repairPass.manualRetryEligibilityStatus, 'eligible-manual-only');

  const repairRetryPass = buildAiFailureClassification({
    error: {
      message: 'Body Timeout Error',
      details: { timeoutKind: 'body-timeout', durationMs: 180002, timeoutMs: 180000 },
    },
    phaseName: 'repair-retry-pass',
    providerId: 'ollama',
    provider,
  });
  assert.equal(repairRetryPass.kind, 'repair-retry-pass-provider-timeout');
  assert.equal(repairRetryPass.aiPhase, 'repair-retry-pass');
}

function testProviderUnreachableAndSemanticFailures() {
  const provider = makeProvider();
  const unreachable = buildAiFailureClassification({
    error: {
      message: 'fetch failed',
      cause: { code: 'ECONNREFUSED', message: 'connect ECONNREFUSED 127.0.0.1:11434' },
    },
    phaseName: 'first-pass',
    providerId: 'ollama',
    provider,
  });
  assert.equal(unreachable.kind, 'provider-unreachable');
  assert.equal(unreachable.aiPhase, 'provider-unreachable');
  assert.equal(unreachable.manualRetryEligible, true);

  const jsonParse = buildAiFailureClassification({
    failureKind: 'json_parse_failure',
    phaseName: 'first-pass',
    providerId: 'ollama',
    provider,
    reason: 'Unexpected end of JSON input',
  });
  assert.equal(jsonParse.kind, 'json-parse-failure');
  assert.equal(jsonParse.aiPhase, 'json-parse');
  assert.equal(jsonParse.manualRetryEligible, false);

  const schemaValidation = buildAiFailureClassification({
    failureKind: 'schema_validation_failure',
    phaseName: 'first-pass',
    providerId: 'ollama',
    provider,
    reason: 'missing primary_facets',
  });
  assert.equal(schemaValidation.kind, 'schema-validation-failure');
  assert.equal(schemaValidation.aiPhase, 'schema-validation');
  assert.equal(schemaValidation.manualRetryEligible, false);
}

function testStrictSkeletonBlockPreservesUnderlyingManualEligibility() {
  const provider = makeProvider();
  const timeout = buildAiFailureClassification({
    error: { message: 'TimeoutError', timeoutKind: 'abort-timeout' },
    phaseName: 'first-pass',
    providerId: 'ollama',
    provider,
  });
  const strictBlock = buildAiFailureClassification({
    failureKind: 'strict_no_skeleton_fallback_block',
    phaseName: 'strict-skeleton-block',
    providerId: 'ollama',
    provider,
    underlying: timeout,
  });
  assert.equal(strictBlock.kind, 'strict-no-skeleton-fallback-block');
  assert.equal(strictBlock.aiPhase, 'strict-skeleton-block');
  assert.equal(strictBlock.autoRetryAllowed, false);
  assert.equal(strictBlock.manualRetryEligible, true);
  assert.equal(strictBlock.underlying.kind, 'first-pass-provider-timeout');
}

function main() {
  assert.equal(sanitizeProviderBaseUrl('http://user:secret@example.test:11434/path?token=hidden#frag'), 'http://example.test:11434/path');
  testProviderTimeoutPhases();
  testProviderUnreachableAndSemanticFailures();
  testStrictSkeletonBlockPreservesUnderlyingManualEligibility();
  console.log('SUCCESS: ai-failure-classification-smoke passed');
}

main();
