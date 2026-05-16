import assert from 'node:assert/strict';
import { loadCleanServiceConfig, summarizeCleanServiceAvailability } from '../services/cleanservice/config.mjs';
import { createCleanServiceClient, normalizeCleanServiceTransportError } from '../services/cleanservice/protocol.mjs';
import { evaluateCleanCostPolicy, mapCleanStateToTaskIntent } from '../services/cleanservice/states.mjs';
import { verifyCleanServiceOutput } from '../services/cleanservice/output-verifier.mjs';

function objectRef(object) {
  return {
    bucket: 'eduassets-clean',
    object,
    size_bytes: 128,
    content_type: object.endsWith('.md') ? 'text/markdown' : 'application/json',
    sha256: 'abc123',
  };
}

function completedJob(overrides = {}) {
  return {
    job_id: 'luceon-task-1-toc-rebuild-1',
    status: 'completed',
    service_name: 'toc-rebuild',
    service_version: '1.0.0',
    protocol_version: 'v1',
    material_id: 'mat-clean-1',
    parse_task_id: 'task-clean-1',
    asset_version: 'v1',
    submitted_at: '2026-05-16T00:00:00.000Z',
    started_at: '2026-05-16T00:00:01.000Z',
    finished_at: '2026-05-16T00:00:02.000Z',
    sink: { bucket: 'eduassets-clean', prefix: 'toc-rebuild/mat-clean-1/v1/' },
    artifacts: {
      flooded_content: objectRef('toc-rebuild/mat-clean-1/v1/flooded_content.json'),
      logic_tree: objectRef('toc-rebuild/mat-clean-1/v1/logic_tree.json'),
      readable_tree: objectRef('toc-rebuild/mat-clean-1/v1/readable_tree.md'),
      skeleton: objectRef('toc-rebuild/mat-clean-1/v1/skeleton.json'),
      provenance: objectRef('toc-rebuild/mat-clean-1/v1/provenance.json'),
    },
    provenance: {
      schema: 'luceon-provenance/v1',
      service: { name: 'toc-rebuild', version: '1.0.0', protocol_version: 'v1' },
      asset: { material_id: 'mat-clean-1', asset_version: 'v1' },
      job: { job_id: 'luceon-task-1-toc-rebuild-1', parse_task_id: 'task-clean-1' },
    },
    stats: {
      tokens: { total: 1200 },
      cost_cny_estimated: 0.8,
      cost_cny_actual: 0.8,
      unresolved_anchor_count: 0,
    },
    error: null,
    ...overrides,
  };
}

async function main() {
  console.log('=== CleanService Foundation Smoke ===');

  const defaultConfig = loadCleanServiceConfig({});
  assert.equal(defaultConfig.enabled, false);
  assert.equal(defaultConfig.status, 'not-enabled');
  assert.equal(summarizeCleanServiceAvailability(defaultConfig).productLabel, '未启用');

  let transportCalls = 0;
  const disabledClient = createCleanServiceClient({
    config: defaultConfig,
    transport: async () => {
      transportCalls++;
      return completedJob();
    },
  });
  const disabledResult = await disabledClient.submitJob({ job_id: 'unused' });
  assert.equal(disabledResult.job.cleanState, 'not-enabled');
  assert.equal(transportCalls, 0, 'disabled CleanService must not call injected transport');

  const enabledConfig = loadCleanServiceConfig({
    CLEANSERVICE_ENABLED: 'true',
    CLEANSERVICE_ENDPOINT: 'http://cleanservice.invalid',
    CLEANSERVICE_API_KEY: 'test-only',
  });
  const successClient = createCleanServiceClient({
    config: enabledConfig,
    transport: async ({ action }) => {
      assert.equal(action, 'submitJob');
      return completedJob();
    },
  });
  const success = await successClient.submitJob({ job_id: 'luceon-task-1-toc-rebuild-1' });
  assert.equal(success.ok, true);
  assert.equal(success.job.cleanState, 'completed');
  assert.equal(success.metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'].productLabel, '目录结构已完成');
  assert.equal(success.metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'].artifacts.flooded_content.object.endsWith('flooded_content.json'), true);
  assert.equal(success.metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'].artifacts.flooded_content.content, undefined);

  const partialClient = createCleanServiceClient({
    config: enabledConfig,
    transport: async () => completedJob({
      stats: {
        tokens: { total: 1600 },
        cost_cny_actual: 1.2,
        unresolved_anchor_count: 2,
      },
    }),
  });
  const partial = await partialClient.queryJob('luceon-task-1-toc-rebuild-1');
  assert.equal(partial.job.cleanState, 'review-pending-partial');
  assert.deepEqual(mapCleanStateToTaskIntent(partial.job.cleanState, { unresolvedAnchorCount: 2 }), {
    cleanState: 'review-pending-partial',
    productLabel: '部分完成待复核',
    taskIntent: 'review-pending',
    cleanReview: 'partial-unresolved-anchors',
    unresolvedAnchorCount: 2,
    shouldBlockCurrentAiMetadata: false,
  });

  const softCost = evaluateCleanCostPolicy({ costCnyProjected: 5.01 }, enabledConfig.costPolicy);
  assert.equal(softCost.cleanState, 'cost-decision');
  assert.equal(softCost.decisionRequired, true);

  const hardCostClient = createCleanServiceClient({
    config: enabledConfig,
    transport: async () => completedJob({ stats: { cost_cny_actual: 8.01, unresolved_anchor_count: 0 } }),
  });
  const hardCost = await hardCostClient.submitJob({});
  assert.equal(hardCost.job.cleanState, 'hard-limit-failed');
  assert.equal(hardCost.costDecision.hardFailed, true);

  const timeout = normalizeCleanServiceTransportError(new Error('request timeout after 30000ms'));
  assert.equal(timeout.job.cleanState, 'timeout');
  assert.equal(timeout.job.error.code, 'timeout');

  const missingProvenance = verifyCleanServiceOutput(completedJob({
    artifacts: {
      flooded_content: objectRef('toc-rebuild/mat-clean-1/v1/flooded_content.json'),
      logic_tree: objectRef('toc-rebuild/mat-clean-1/v1/logic_tree.json'),
      readable_tree: objectRef('toc-rebuild/mat-clean-1/v1/readable_tree.md'),
      skeleton: objectRef('toc-rebuild/mat-clean-1/v1/skeleton.json'),
    },
    provenance: null,
  }));
  assert.equal(missingProvenance.ok, false);
  assert.equal(missingProvenance.cleanState, 'protocol-failure');
  assert.equal(missingProvenance.errors.includes('missing-artifact:provenance'), true);

  const rawFallback = verifyCleanServiceOutput(completedJob({ rawMineruOutput: true }));
  assert.equal(rawFallback.ok, false);
  assert.equal(rawFallback.errors.includes('raw-mineru-output-not-clean-success'), true);

  console.log('PASS cleanservice foundation smoke');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
