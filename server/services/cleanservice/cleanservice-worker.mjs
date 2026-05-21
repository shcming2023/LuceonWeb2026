import { loadCleanServiceConfig } from './config.mjs';
import { createCleanServiceClient } from './protocol.mjs';
import { buildCanonicalRawMaterialRef } from './raw-material-adapter.mjs';
import { allocateAssetVersion } from './asset-version.mjs';

const ELIGIBLE_TASK_STATES = new Set([
  'review-pending',
  'completed',
  'done',
  'ai-pending',
  'ai-running',
]);

const INELIGIBLE_TASK_STATES = new Set([
  'failed',
  'canceled',
  'cancelled',
]);

const ACTIVE_OR_TERMINAL_CLEAN_STATES = new Set([
  'pending',
  'running',
  'review-pending-partial',
  'completed',
  'skipped',
  'cost-decision',
  'hard-limit-failed',
  'timeout',
  'protocol-failure',
  'skipped-policy',
  'not-applicable'
]);

export function isCleanServiceTaskEligible(task = {}, { serviceName = 'toc-rebuild' } = {}) {
  if (!task?.id || !task?.materialId) return false;
  if (INELIGIBLE_TASK_STATES.has(task.state)) return false;
  if (!ELIGIBLE_TASK_STATES.has(task.state) && task.metadata?.mineruStatus !== 'completed') return false;

  const job = task.metadata?.cleanServiceJobs?.[serviceName];
  if (job && ACTIVE_OR_TERMINAL_CLEAN_STATES.has(job.cleanState || job.status || job.state)) return false;

  const { isActiveDuplicate } = allocateAssetVersion(task, serviceName);
  if (isActiveDuplicate) return false;

  // Check if it has any evidence (legacy or canonical) to process
  const metadata = task.metadata || {};
  const parsedFilesCount = Number(metadata.parsedFilesCount || 0);
  const hasLegacy = Boolean(metadata.artifactManifestObjectName) ||
    Boolean(metadata.markdownObjectName) ||
    (Boolean(metadata.parsedPrefix) && parsedFilesCount > 0);
  const hasCanonical = Boolean(metadata.rawMaterial?.mineru?.contentListV2);

  if (!hasLegacy && !hasCanonical) return false;

  return true;
}

export function buildCleanServiceJobRequest(task = {}, config = loadCleanServiceConfig(), { submittedAt = new Date().toISOString() } = {}) {
  const serviceName = config.serviceName || 'toc-rebuild';
  const { assetVersion } = allocateAssetVersion(task, serviceName);

  const inputRef = buildCanonicalRawMaterialRef(task);
  inputRef.source.endpoint = config.storageEndpoint;
  inputRef.source.use_ssl = config.storageUseSsl;

  return {
    job_id: `luceon-${task.id}-${serviceName}-${assetVersion}`,
    material_id: task.materialId,
    parse_task_id: task.id,
    asset_version: assetVersion,
    submitted_at: submittedAt,
    submitted_by: config.submittedBy,
    inputs: [inputRef],
    sink: {
      type: 'minio',
      bucket: task.metadata?.cleanOutputBucket || 'eduassets-clean',
      prefix: `${serviceName}/${task.materialId}/${assetVersion}/`,
      endpoint: config.storageEndpoint,
      use_ssl: config.storageUseSsl,
    },
    callback_secret_ref: config.callbackSecretRef,
    options: {
      max_cost_cny: config.costPolicy?.hardLimitCny ?? 8,
    },
  };
}

export class CleanServiceWorker {
  constructor({
    config = loadCleanServiceConfig(),
    taskSource,
    client = createCleanServiceClient({ config }),
    persistence,
    now = () => new Date().toISOString(),
  } = {}) {
    this.config = config;
    this.taskSource = taskSource;
    this.client = client;
    this.persistence = persistence;
    this.now = now;
  }

  async tickOnce() {
    if (!this.config.enabled) {
      return {
        ok: true,
        status: 'disabled-noop',
        scanned: 0,
        submitted: 0,
        persisted: 0,
        serviceName: this.config.serviceName,
        observedAt: this.now(),
      };
    }

    if (!this.taskSource || typeof this.taskSource.listTasks !== 'function') {
      return { ok: false, status: 'missing-task-source', scanned: 0, submitted: 0, persisted: 0 };
    }
    if (!this.client || typeof this.client.submitJob !== 'function') {
      return { ok: false, status: 'missing-cleanservice-client', scanned: 0, submitted: 0, persisted: 0 };
    }
    if (!this.persistence || typeof this.persistence.persistMetadataPatch !== 'function') {
      return { ok: false, status: 'missing-persistence-adapter', scanned: 0, submitted: 0, persisted: 0 };
    }

    const tasks = await this.taskSource.listTasks();
    const eligible = tasks.find((task) => isCleanServiceTaskEligible(task, { serviceName: this.config.serviceName }));
    if (!eligible) {
      return {
        ok: true,
        status: 'no-eligible-task',
        scanned: tasks.length,
        submitted: 0,
        persisted: 0,
        serviceName: this.config.serviceName,
        observedAt: this.now(),
      };
    }

    let request;
    try {
      request = buildCleanServiceJobRequest(eligible, this.config, { submittedAt: this.now() });
    } catch (err) {
      if (err.code === 'skipped-policy' || err.code === 'not-applicable') {
        const cleanState = err.code;
        const { assetVersion } = allocateAssetVersion(eligible, this.config.serviceName);
        const jobId = `luceon-${eligible.id}-${this.config.serviceName}-${assetVersion}`;
        await this.persistence.persistMetadataPatch({
          taskId: eligible.id,
          materialId: eligible.materialId,
          serviceName: this.config.serviceName,
          metadataPatch: {
            taskMetadata: {
              cleanServiceJobs: {
                [this.config.serviceName]: {
                  jobId,
                  cleanState,
                  assetVersion,
                  serviceName: this.config.serviceName,
                  protocolVersion: 'v1',
                  parseTaskId: eligible.id,
                  materialId: eligible.materialId,
                  input: eligible.metadata?.rawMaterial?.mineru?.contentListV2 ? {
                    role: 'mineru-content',
                    bucket: eligible.metadata.rawMaterial.mineru.contentListV2.bucket,
                    object: eligible.metadata.rawMaterial.mineru.contentListV2.object
                  } : null,
                  sink: {
                    bucket: eligible.metadata?.cleanOutputBucket || 'eduassets-clean',
                    prefix: `${this.config.serviceName}/${eligible.materialId}/${assetVersion}/`
                  },
                  updatedAt: this.now()
                }
              }
            }
          },
          cleanState,
          observedAt: this.now(),
        });
        return {
          ok: true,
          status: cleanState,
          scanned: tasks.length,
          submitted: 0,
          persisted: 1,
          taskId: eligible.id,
          materialId: eligible.materialId,
          cleanState,
          serviceName: this.config.serviceName,
          observedAt: this.now(),
        };
      }
      // Re-throw other errors
      throw err;
    }

    const result = await this.client.submitJob(request);
    await this.persistence.persistMetadataPatch({
      taskId: eligible.id,
      materialId: eligible.materialId,
      serviceName: this.config.serviceName,
      jobRequest: request,
      metadataPatch: result.metadataPatch,
      cleanState: result.job?.cleanState,
      observedAt: this.now(),
    });

    return {
      ok: result.ok,
      status: 'submitted-one',
      scanned: tasks.length,
      submitted: 1,
      persisted: 1,
      taskId: eligible.id,
      materialId: eligible.materialId,
      jobId: request.job_id,
      cleanState: result.job?.cleanState,
      serviceName: this.config.serviceName,
      observedAt: this.now(),
    };
  }
}
