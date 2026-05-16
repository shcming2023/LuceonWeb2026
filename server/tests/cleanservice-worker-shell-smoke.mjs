import assert from 'node:assert/strict';
import { loadCleanServiceConfig } from '../services/cleanservice/config.mjs';
import {
  CleanServiceWorker,
  buildCleanServiceJobRequest,
  isCleanServiceTaskEligible,
} from '../services/cleanservice/cleanservice-worker.mjs';

function objectRef(object) {
  return {
    bucket: 'eduassets-clean',
    object,
    size_bytes: 256,
    content_type: object.endsWith('.md') ? 'text/markdown' : 'application/json',
    sha256: 'abc123',
  };
}

function completedJob({ taskId = 'task-clean-1', materialId = 'mat-clean-1', unresolved = 0, cost = 0.8 } = {}) {
  return {
    job_id: `luceon-${taskId}-toc-rebuild-v1`,
    status: 'completed',
    service_name: 'toc-rebuild',
    service_version: '1.0.0',
    protocol_version: 'v1',
    material_id: materialId,
    parse_task_id: taskId,
    asset_version: 'v1',
    submitted_at: '2026-05-16T00:00:00.000Z',
    finished_at: '2026-05-16T00:00:02.000Z',
    sink: { bucket: 'eduassets-clean', prefix: `toc-rebuild/${materialId}/v1/` },
    artifacts: {
      flooded_content: objectRef(`toc-rebuild/${materialId}/v1/flooded_content.json`),
      logic_tree: objectRef(`toc-rebuild/${materialId}/v1/logic_tree.json`),
      readable_tree: objectRef(`toc-rebuild/${materialId}/v1/readable_tree.md`),
      skeleton: objectRef(`toc-rebuild/${materialId}/v1/skeleton.json`),
      provenance: objectRef(`toc-rebuild/${materialId}/v1/provenance.json`),
    },
    provenance: {
      schema: 'luceon-provenance/v1',
      service: { name: 'toc-rebuild', version: '1.0.0', protocol_version: 'v1' },
      asset: { material_id: materialId, asset_version: 'v1' },
      job: { job_id: `luceon-${taskId}-toc-rebuild-v1`, parse_task_id: taskId },
    },
    stats: {
      tokens: { total: 2048 },
      cost_cny_actual: cost,
      unresolved_anchor_count: unresolved,
    },
    error: null,
  };
}

function eligibleTask(overrides = {}) {
  return {
    id: 'task-clean-1',
    materialId: 'mat-clean-1',
    state: 'review-pending',
    metadata: {
      mineruStatus: 'completed',
      parsedFilesCount: 12,
      artifactManifestObjectName: 'parsed/mat-clean-1/artifact-manifest.json',
      parsedPrefix: 'parsed/mat-clean-1/',
    },
    ...overrides,
  };
}

async function main() {
  console.log('=== CleanService Worker Shell Smoke ===');

  let scanCalls = 0;
  let submitCalls = 0;
  let persistCalls = 0;
  const disabledWorker = new CleanServiceWorker({
    config: loadCleanServiceConfig({}),
    taskSource: { listTasks: async () => { scanCalls++; return [eligibleTask()]; } },
    client: { submitJob: async () => { submitCalls++; return {}; } },
    persistence: { persistMetadataPatch: async () => { persistCalls++; } },
    now: () => '2026-05-16T00:00:00.000Z',
  });
  const disabled = await disabledWorker.tickOnce();
  assert.equal(disabled.status, 'disabled-noop');
  assert.equal(disabled.scanned, 0);
  assert.equal(scanCalls, 0, 'disabled worker must not scan tasks');
  assert.equal(submitCalls, 0, 'disabled worker must not submit jobs');
  assert.equal(persistCalls, 0, 'disabled worker must not persist metadata');

  assert.equal(isCleanServiceTaskEligible(eligibleTask()), true);
  assert.equal(isCleanServiceTaskEligible(eligibleTask({ state: 'failed' })), false);
  assert.equal(isCleanServiceTaskEligible(eligibleTask({ state: 'canceled' })), false);
  assert.equal(isCleanServiceTaskEligible(eligibleTask({ metadata: { mineruStatus: 'completed' } })), false);
  assert.equal(isCleanServiceTaskEligible(eligibleTask({ metadata: { parsedPrefix: 'parsed/x/', parsedFilesCount: 0 } })), false);
  assert.equal(isCleanServiceTaskEligible(eligibleTask({ metadata: { parsedPrefix: 'parsed/x/', parsedFilesCount: 1 } })), true);
  assert.equal(isCleanServiceTaskEligible(eligibleTask({
    metadata: {
      mineruStatus: 'completed',
      parsedFilesCount: 12,
      artifactManifestObjectName: 'parsed/mat-clean-1/artifact-manifest.json',
      cleanServiceJobs: { 'toc-rebuild': { status: 'running' } },
    },
  })), false);
  assert.equal(isCleanServiceTaskEligible(eligibleTask({
    metadata: {
      mineruStatus: 'completed',
      parsedFilesCount: 12,
      artifactManifestObjectName: 'parsed/mat-clean-1/artifact-manifest.json',
      cleanServiceJobs: { 'toc-rebuild': { status: 'completed' } },
    },
  })), false);

  const enabledConfig = loadCleanServiceConfig({
    CLEANSERVICE_ENABLED: 'true',
    CLEANSERVICE_ENDPOINT: 'http://cleanservice.invalid',
    CLEANSERVICE_API_KEY: 'test-only',
  });
  const jobRequest = buildCleanServiceJobRequest(eligibleTask(), enabledConfig);
  assert.equal(jobRequest.job_id, 'luceon-task-clean-1-toc-rebuild-v1');
  assert.equal(jobRequest.inputs[0].role, 'mineru-artifact-manifest');
  assert.equal(jobRequest.options.max_cost_cny, 8);
  assert.throws(
    () => buildCleanServiceJobRequest(eligibleTask({ metadata: { mineruStatus: 'completed' } }), enabledConfig),
    /cleanservice-input-object-ref-missing/,
  );

  const markdownRequest = buildCleanServiceJobRequest(eligibleTask({
    metadata: {
      markdownObjectName: 'parsed/mat-clean-1/full.md',
      parsedPrefix: 'parsed/mat-clean-1/',
      parsedFilesCount: 12,
    },
  }), enabledConfig);
  assert.equal(markdownRequest.inputs[0].role, 'mineru-markdown');
  assert.equal(markdownRequest.inputs[0].source.object, 'parsed/mat-clean-1/full.md');

  const parsedPrefixRequest = buildCleanServiceJobRequest(eligibleTask({
    metadata: {
      parsedPrefix: 'parsed/mat-clean-1/',
      parsedFilesCount: 12,
    },
  }), enabledConfig);
  assert.equal(parsedPrefixRequest.inputs[0].role, 'mineru-parsed-prefix');
  assert.equal(parsedPrefixRequest.inputs[0].source.object, 'parsed/mat-clean-1/');

  const persisted = [];
  const submittedRequests = [];
  const worker = new CleanServiceWorker({
    config: enabledConfig,
    taskSource: {
      listTasks: async () => [
        eligibleTask({ id: 'task-no-evidence', materialId: 'mat-no-evidence', metadata: { mineruStatus: 'processing' } }),
        eligibleTask(),
        eligibleTask({ id: 'task-second', materialId: 'mat-second' }),
      ],
    },
    client: {
      submitJob: async (request) => {
        submittedRequests.push(request);
        return {
          ok: true,
          job: { ...completedJob(), cleanState: 'completed' },
          metadataPatch: {
            taskMetadata: {
              cleanServiceJobs: {
                'toc-rebuild': {
                  status: 'completed',
                  productLabel: '目录结构已完成',
                  artifacts: {
                    flooded_content: objectRef('toc-rebuild/mat-clean-1/v1/flooded_content.json'),
                    provenance: objectRef('toc-rebuild/mat-clean-1/v1/provenance.json'),
                  },
                  stats: { tokensTotal: 2048, costCnyActual: 0.8, unresolvedAnchorCount: 0 },
                },
              },
            },
            materialMetadata: {
              cleanMaterials: {
                'toc-rebuild': {
                  status: 'completed',
                  productLabel: '目录结构已完成',
                  provenanceObjectName: 'toc-rebuild/mat-clean-1/v1/provenance.json',
                  stats: { tokensTotal: 2048, costCnyActual: 0.8, unresolvedAnchorCount: 0 },
                },
              },
            },
          },
        };
      },
    },
    persistence: {
      persistMetadataPatch: async (patch) => {
        persisted.push(patch);
      },
    },
    now: () => '2026-05-16T00:00:03.000Z',
  });
  const result = await worker.tickOnce();
  assert.equal(result.status, 'submitted-one');
  assert.equal(result.submitted, 1);
  assert.equal(result.persisted, 1);
  assert.equal(submittedRequests.length, 1, 'worker must dispatch at most one job per tick');
  assert.equal(persisted.length, 1);
  assert.equal(persisted[0].taskId, 'task-clean-1');
  assert.equal(persisted[0].materialId, 'mat-clean-1');
  assert.equal(persisted[0].metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'].artifacts.flooded_content.object, 'toc-rebuild/mat-clean-1/v1/flooded_content.json');
  assert.equal(persisted[0].metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'].artifacts.flooded_content.content, undefined);
  assert.equal(persisted[0].metadataPatch.materialMetadata.cleanMaterials['toc-rebuild'].provenanceObjectName, 'toc-rebuild/mat-clean-1/v1/provenance.json');

  const partialPersisted = [];
  const partialWorker = new CleanServiceWorker({
    config: enabledConfig,
    taskSource: { listTasks: async () => [eligibleTask()] },
    client: {
      submitJob: async () => ({
        ok: true,
        job: { ...completedJob({ unresolved: 3 }), cleanState: 'review-pending-partial' },
        metadataPatch: {
          taskMetadata: {
            cleanServiceJobs: {
              'toc-rebuild': {
                status: 'review-pending-partial',
                productLabel: '部分完成待复核',
                taskIntent: 'review-pending',
                cleanReview: 'partial-unresolved-anchors',
                stats: { unresolvedAnchorCount: 3 },
              },
            },
          },
          materialMetadata: {
            cleanMaterials: {
              'toc-rebuild': {
                status: 'review-pending-partial',
                productLabel: '部分完成待复核',
                stats: { unresolvedAnchorCount: 3 },
              },
            },
          },
        },
      }),
    },
    persistence: { persistMetadataPatch: async (patch) => partialPersisted.push(patch) },
  });
  const partialResult = await partialWorker.tickOnce();
  assert.equal(partialResult.cleanState, 'review-pending-partial');
  assert.equal(partialPersisted[0].metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'].cleanReview, 'partial-unresolved-anchors');

  const hardFailurePersisted = [];
  const hardFailureWorker = new CleanServiceWorker({
    config: enabledConfig,
    taskSource: { listTasks: async () => [eligibleTask()] },
    client: {
      submitJob: async () => ({
        ok: false,
        job: { ...completedJob({ cost: 8.01 }), cleanState: 'hard-limit-failed' },
        metadataPatch: {
          taskMetadata: {
            cleanServiceJobs: {
              'toc-rebuild': {
                status: 'hard-limit-failed',
                productLabel: '目录重建失败',
                taskIntent: 'failed',
                stats: { costCnyActual: 8.01 },
              },
            },
          },
          materialMetadata: {
            cleanMaterials: {
              'toc-rebuild': {
                status: 'hard-limit-failed',
                productLabel: '目录重建失败',
                stats: { costCnyActual: 8.01 },
              },
            },
          },
        },
      }),
    },
    persistence: { persistMetadataPatch: async (patch) => hardFailurePersisted.push(patch) },
  });
  const hardFailure = await hardFailureWorker.tickOnce();
  assert.equal(hardFailure.cleanState, 'hard-limit-failed');
  assert.equal(hardFailurePersisted[0].metadataPatch.taskMetadata.cleanServiceJobs['toc-rebuild'].taskIntent, 'failed');

  console.log('PASS cleanservice worker shell smoke');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
