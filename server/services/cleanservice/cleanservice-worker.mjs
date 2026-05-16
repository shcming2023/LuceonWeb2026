import { loadCleanServiceConfig } from './config.mjs';
import { createCleanServiceClient } from './protocol.mjs';

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
]);

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

function hasParsedArtifactEvidence(task = {}) {
  const metadata = task.metadata || {};
  const parsedFilesCount = Number(metadata.parsedFilesCount || 0);
  return Boolean(metadata.artifactManifestObjectName) ||
    Boolean(metadata.markdownObjectName) ||
    (Boolean(metadata.parsedPrefix) && parsedFilesCount > 0);
}

function hasExistingCleanJob(task = {}, serviceName) {
  const job = task.metadata?.cleanServiceJobs?.[serviceName];
  if (!job) return false;
  return ACTIVE_OR_TERMINAL_CLEAN_STATES.has(job.status || job.cleanState || job.state);
}

export function isCleanServiceTaskEligible(task = {}, { serviceName = 'toc-rebuild' } = {}) {
  if (!task?.id || !task?.materialId) return false;
  if (INELIGIBLE_TASK_STATES.has(task.state)) return false;
  if (!ELIGIBLE_TASK_STATES.has(task.state) && task.metadata?.mineruStatus !== 'completed') return false;
  if (!hasParsedArtifactEvidence(task)) return false;
  if (hasExistingCleanJob(task, serviceName)) return false;
  return true;
}

function buildInputObjectRef(task = {}) {
  const metadata = task.metadata || {};
  if (metadata.artifactManifestObjectName) {
    return {
      role: 'mineru-artifact-manifest',
      source: {
        type: 'minio',
        bucket: metadata.artifactManifestBucket || 'eduassets-parsed',
        object: metadata.artifactManifestObjectName,
      },
    };
  }
  if (metadata.markdownObjectName) {
    return {
      role: 'mineru-markdown',
      source: {
        type: 'minio',
        bucket: metadata.markdownBucket || 'eduassets-parsed',
        object: metadata.markdownObjectName,
      },
    };
  }
  const parsedFilesCount = Number(metadata.parsedFilesCount || 0);
  if (!metadata.parsedPrefix || parsedFilesCount <= 0) {
    throw new Error('cleanservice-input-object-ref-missing: expected artifactManifestObjectName, markdownObjectName, or parsedPrefix with parsedFilesCount > 0');
  }
  return {
    role: 'mineru-parsed-prefix',
    source: {
      type: 'minio',
      bucket: metadata.parsedBucket || 'eduassets-parsed',
      object: metadata.parsedPrefix,
    },
  };
}

export function buildCleanServiceJobRequest(task = {}, config = loadCleanServiceConfig()) {
  const serviceName = config.serviceName || 'toc-rebuild';
  const assetVersion = task.metadata?.cleanServiceNextVersion || 'v1';
  return {
    job_id: `luceon-${task.id}-${serviceName}-${assetVersion}`,
    material_id: task.materialId,
    parse_task_id: task.id,
    asset_version: assetVersion,
    inputs: [buildInputObjectRef(task)],
    sink: {
      type: 'minio',
      bucket: task.metadata?.cleanOutputBucket || 'eduassets-clean',
      prefix: `${serviceName}/${task.materialId}/${assetVersion}/`,
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

    const request = buildCleanServiceJobRequest(eligible, this.config);
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
