/**
 * server/services/cleanservice/orchestration-runner.mjs
 *
 * CleanService Minimal Orchestration Runner (MockSafe, NoRuntime).
 * Composes accepted building blocks into one deterministic flow.
 * Enforces dry-run metadata apply, dependency injection, and zero reset/cleanup.
 */

import { isCleanServiceTaskEligible, buildCleanServiceJobRequest } from './cleanservice-worker.mjs';
import { allocateAssetVersion } from './asset-version.mjs';
import { verifyCleanServiceOutputArtifacts } from './output-verifier.mjs';
import { buildVerifiedCleanOutputMetadataCandidate } from './metadata-summary.mjs';
import { buildCleanMetadataPersistencePlan } from './metadata-persistence.mjs';
import { applyCleanMetadataPersistencePlan } from './metadata-apply-executor.mjs';

/**
 * Orchestrates a single-sample CleanService toc-rebuild pipeline.
 *
 * @param {Object} params Parameters.
 * @param {Object} params.task Task DB record.
 * @param {Object} params.material Material DB record.
 * @param {Object} params.config CleanService configuration.
 * @param {Object} params.deps Injected dependencies.
 * @param {Function} [params.now] Optional clock generator.
 * @returns {Promise<Object>} Bounded orchestration outcome.
 */
export async function runCleanServiceTocRebuildOnce({
  task,
  material,
  config,
  deps = {},
  now = () => new Date().toISOString(),
}) {
  const getNow = typeof now === 'function' ? now : () => new Date().toISOString();

  // 1. Preflight - Enabled Check
  if (!config || !config.enabled) {
    return {
      ok: true,
      status: 'disabled-noop',
      classification: 'disabled-noop',
      reason: 'CleanService is disabled by config',
      observedAt: getNow(),
    };
  }

  // 2. Preflight - Task & Material Target Check
  if (!task || !material) {
    return {
      ok: false,
      status: 'BLOCKED_DB_TARGET_NOT_FOUND',
      classification: 'BLOCKED_DB_TARGET_NOT_FOUND',
      reason: 'Task or Material target record is null or undefined',
      observedAt: getNow(),
    };
  }

  if (String(task.materialId) !== String(material.id)) {
    return {
      ok: false,
      status: 'BLOCKED_SCOPE_WOULD_EXPAND',
      classification: 'BLOCKED_SCOPE_WOULD_EXPAND',
      reason: `Scope mismatch: task.materialId (${task.materialId}) !== material.id (${material.id})`,
      observedAt: getNow(),
    };
  }

  const serviceName = config.serviceName || 'toc-rebuild';

  // Preflight - Intent Validation Check (MUST run before any metadata checks or allocation)
  if (config && config.intent !== undefined) {
    if (config.intent === 'create-new-version') {
      if (!config.newVersionReason || typeof config.newVersionReason !== 'string' || config.newVersionReason.trim() === '') {
        return {
          ok: false,
          status: 'BLOCKED_NEW_VERSION_REASON_REQUIRED',
          classification: 'BLOCKED_NEW_VERSION_REASON_REQUIRED',
          reason: 'Explicit create-new-version intent requires a non-empty newVersionReason',
          observedAt: getNow(),
        };
      }
    } else {
      return {
        ok: false,
        status: 'BLOCKED_UNSUPPORTED_CLEANSERVICE_INTENT',
        classification: 'BLOCKED_UNSUPPORTED_CLEANSERVICE_INTENT',
        reason: `Unsupported CleanService intent: ${config.intent}`,
        observedAt: getNow(),
      };
    }
  }

  // 3. Preflight - Current State Noop Check & Explicit New-Version Precondition Check (MUST run before allocateAssetVersion)
  const existingTaskJob = task.metadata?.cleanServiceJobs?.[serviceName];
  const existingMaterialJob = material.metadata?.cleanMaterials?.[serviceName];

  const isRerunRequested = config && config.intent === 'create-new-version';

  // Explicit new-version precondition gate: must have aligned, completed, two-sided history with a jobId
  if (isRerunRequested) {
    if (!existingTaskJob || !existingMaterialJob) {
      return {
        ok: false,
        status: 'BLOCKED_EXISTING_TOC_REBUILD_METADATA',
        classification: 'BLOCKED_EXISTING_TOC_REBUILD_METADATA',
        reason: 'Explicit create-new-version intent requires existing completed toc-rebuild metadata on both task and material',
        observedAt: getNow(),
      };
    }

    const assetVersionAligned = existingTaskJob.assetVersion === existingMaterialJob.latestVersion;
    const taskCompleted = existingTaskJob.status === 'completed' || existingTaskJob.cleanState === 'completed';
    const materialCompleted = existingMaterialJob.status === 'completed';
    const jobIdExists = !!existingTaskJob.jobId;

    if (!assetVersionAligned || !taskCompleted || !materialCompleted || !jobIdExists) {
      return {
        ok: false,
        status: 'BLOCKED_EXISTING_TOC_REBUILD_METADATA',
        classification: 'BLOCKED_EXISTING_TOC_REBUILD_METADATA',
        reason: 'Explicit create-new-version intent requires completed, aligned historical metadata with a valid jobId',
        observedAt: getNow(),
      };
    }
  }

  // Only if rerun is requested and has successfully passed the precondition checks,
  // we bypass the CURRENT_CLEAN_MATERIAL_NOOP check and the incompatible checks.
  const hasNewVersionIntent = isRerunRequested;

  if (existingTaskJob && existingMaterialJob && !hasNewVersionIntent) {
    const assetVersionAligned = existingTaskJob.assetVersion === existingMaterialJob.latestVersion;
    const taskCompleted = existingTaskJob.status === 'completed' || existingTaskJob.cleanState === 'completed';
    const materialCompleted = existingMaterialJob.status === 'completed';
    const jobIdExists = !!existingTaskJob.jobId;

    if (assetVersionAligned && taskCompleted && materialCompleted && jobIdExists) {
      return {
        ok: true,
        status: 'CURRENT_CLEAN_MATERIAL_NOOP',
        classification: 'CURRENT_CLEAN_MATERIAL_NOOP',
        materialId: material.id,
        taskId: task.id,
        serviceName,
        assetVersion: existingTaskJob.assetVersion,
        jobId: existingTaskJob.jobId,
        cleanState: existingTaskJob.cleanState || existingTaskJob.status || 'completed',
        reason: 'Already-applied completed clean material matches task and material current records exactly',
        observedAt: getNow(),
      };
    }
  }

  const { assetVersion } = allocateAssetVersion(task, serviceName);
  const jobId = `luceon-${task.id}-${serviceName}-${assetVersion}`;

  // 3. Preflight - Already Applied Noop Check
  if (existingTaskJob && existingMaterialJob) {
    const taskMatches = existingTaskJob.jobId === jobId && existingTaskJob.assetVersion === assetVersion;
    const materialMatches = existingMaterialJob.latestVersion === assetVersion;
    if (taskMatches && materialMatches) {
      return {
        ok: true,
        status: 'ALREADY_APPLIED_NOOP',
        classification: 'ALREADY_APPLIED_NOOP',
        reason: 'Target metadata jobId and assetVersion are already exactly persisted in both task and material records',
        jobId,
        assetVersion,
        observedAt: getNow(),
      };
    }
  }

  // 4. Preflight - Incompatible Existing Metadata Check
  if ((existingTaskJob || existingMaterialJob) && !hasNewVersionIntent) {
    const taskMatches = existingTaskJob && existingTaskJob.jobId === jobId && existingTaskJob.assetVersion === assetVersion;
    const materialMatches = existingMaterialJob && existingMaterialJob.latestVersion === assetVersion;
    if (!taskMatches || !materialMatches) {
      return {
        ok: false,
        status: 'BLOCKED_EXISTING_TOC_REBUILD_METADATA',
        classification: 'BLOCKED_EXISTING_TOC_REBUILD_METADATA',
        reason: 'Incompatible existing toc-rebuild metadata exists in task or material records',
        observedAt: getNow(),
      };
    }
  }

  // 5. Preflight - Task Eligibility Check
  const eligible = hasNewVersionIntent || isCleanServiceTaskEligible(task, { serviceName });
  if (!eligible) {
    return {
      ok: true,
      status: 'no-eligible-task',
      classification: 'no-eligible-task',
      reason: 'Task is not eligible for CleanService processing',
      observedAt: getNow(),
    };
  }

  // 6. Request Planning
  const request = buildCleanServiceJobRequest(task, config, { submittedAt: getNow() });

  // 7. Submit Job Mock
  const submitJobFn = deps.submitJob;
  if (typeof submitJobFn !== 'function') {
    return {
      ok: false,
      status: 'BLOCKED_RUNTIME_DEPENDENCY_LEAK',
      classification: 'BLOCKED_RUNTIME_DEPENDENCY_LEAK',
      reason: 'submitJob dependency is not configured/injected',
      observedAt: getNow(),
    };
  }

  const submitResult = await submitJobFn(request);
  if (!submitResult || !submitResult.ok) {
    return {
      ok: false,
      status: 'DISPATCH_FAILURE',
      classification: 'DISPATCH_FAILURE',
      reason: 'Job dispatch failed',
      error: submitResult?.job?.error || 'Unknown dispatch error',
      observedAt: getNow(),
    };
  }

  // 8. Query Job Mock
  const queryJobFn = deps.queryJob;
  if (typeof queryJobFn !== 'function') {
    return {
      ok: false,
      status: 'BLOCKED_RUNTIME_DEPENDENCY_LEAK',
      classification: 'BLOCKED_RUNTIME_DEPENDENCY_LEAK',
      reason: 'queryJob dependency is not configured/injected',
      observedAt: getNow(),
    };
  }

  const queryResult = await queryJobFn(request.job_id);
  if (!queryResult || !queryResult.ok || !queryResult.job) {
    return {
      ok: false,
      status: 'protocol-failure',
      classification: 'protocol-failure',
      reason: 'Job query failed or returned empty payload',
      error: queryResult?.job?.error || 'Unknown query error',
      observedAt: getNow(),
    };
  }

  const job = queryResult.job;
  const jobStatus = job.status;

  if (jobStatus === 'failed') {
    const cleanState = job.cleanState || 'protocol-failure';
    return {
      ok: false,
      status: cleanState,
      classification: cleanState,
      reason: 'Job execution failed during query phase',
      error: job.error || 'Query returned failed or invalid job status',
      observedAt: getNow(),
    };
  }

  // Handle known active in-progress job states
  if (['submitted', 'queued', 'pending', 'running', 'processing'].includes(jobStatus)) {
    return {
      ok: true,
      status: 'ORCHESTRATION_IN_PROGRESS',
      classification: 'ORCHESTRATION_IN_PROGRESS',
      reason: `Job is currently in active state: ${jobStatus}`,
      jobId: request.job_id,
      observedAt: getNow(),
    };
  }

  // Handle unknown/unsupported job states
  if (jobStatus !== 'completed') {
    return {
      ok: false,
      status: 'UNSUPPORTED_STATUS',
      classification: 'UNSUPPORTED_STATUS',
      reason: `Job query returned an unsupported or unknown status: ${jobStatus}`,
      observedAt: getNow(),
    };
  }

  // 9. Verify Mock Output
  const verifyFn = deps.verifyCleanServiceOutputArtifacts || verifyCleanServiceOutputArtifacts;
  const reader = deps.artifactReader;
  if (!reader) {
    return {
      ok: false,
      status: 'BLOCKED_RUNTIME_DEPENDENCY_LEAK',
      classification: 'BLOCKED_RUNTIME_DEPENDENCY_LEAK',
      reason: 'artifactReader dependency is not injected',
      observedAt: getNow(),
    };
  }

  const inputRef = request.inputs?.[0] || {};
  const rawMaterialMineru = task.metadata?.rawMaterial?.mineru?.contentListV2 || {};

  // Extract raw input SHA256 using hierarchical priority
  const expectedSha256 = inputRef.hash ||
                         inputRef.source?.sha256 ||
                         inputRef.sha256 ||
                         rawMaterialMineru.sha256 ||
                         null;

  // Extract raw input sizeBytes (avoiding any sample-level hardcoding)
  let expectedSizeBytes = rawMaterialMineru.size_bytes ??
                           rawMaterialMineru.sizeBytes ??
                           inputRef.source?.size_bytes ??
                           inputRef.source?.sizeBytes ??
                           inputRef.size_bytes ??
                           inputRef.sizeBytes ??
                           null;

  // Support injected mock fact for sizeBytes if not found elsewhere
  if (expectedSizeBytes === null && typeof deps.mockSizeBytes === 'number') {
    expectedSizeBytes = deps.mockSizeBytes;
  }
  if (expectedSizeBytes === null && typeof task.metadata?.mockSizeBytes === 'number') {
    expectedSizeBytes = task.metadata.mockSizeBytes;
  }

  const rawInput = {
    bucket: inputRef.source?.bucket || inputRef.bucket || rawMaterialMineru.bucket || null,
    object: inputRef.source?.object || inputRef.object || rawMaterialMineru.object || null,
  };

  if (expectedSha256) {
    rawInput.sha256 = expectedSha256;
  }

  if (typeof expectedSizeBytes === 'number') {
    rawInput.sizeBytes = expectedSizeBytes;
  }

  const verifierOptions = {
    expected: {
      materialId: task.materialId,
      assetVersion: request.asset_version,
      jobId: request.job_id,
      rawInput,
    },
    artifactReader: reader,
  };

  const verifyResult = await verifyFn(queryResult.job, verifierOptions);
  if (!verifyResult || !verifyResult.ok) {
    const cleanState = verifyResult?.cleanState || 'protocol-failure';
    return {
      ok: false,
      status: cleanState,
      classification: cleanState,
      reason: 'CleanService output verification failed',
      errors: verifyResult?.errors || ['Verification failed'],
      observedAt: getNow(),
    };
  }

  // 10. Build Ingestion Candidate
  const candidateFn = deps.buildVerifiedCleanOutputMetadataCandidate || buildVerifiedCleanOutputMetadataCandidate;
  const candidate = candidateFn({
    job: queryResult.job,
    verification: verifyResult,
    now: getNow,
  });

  if (!candidate || !candidate.ok || !candidate.shouldPersist) {
    const cleanState = candidate?.cleanState || 'protocol-failure';
    const errors = candidate?.verificationSummary?.errors || [];
    const classification = errors.includes('BLOCKED_VERIFIER_CONTRACT_GAP')
      ? 'BLOCKED_VERIFIER_CONTRACT_GAP'
      : cleanState;
    return {
      ok: false,
      status: classification,
      classification,
      reason: 'Candidate metadata building failed',
      errors,
      observedAt: getNow(),
    };
  }

  // 11. Build Persistence Plan
  const planFn = deps.buildCleanMetadataPersistencePlan || buildCleanMetadataPersistencePlan;
  const plan = planFn({
    candidate,
    existingTask: task,
    existingMaterial: material,
    now: getNow,
  });

  if (!plan || !plan.ok || !plan.shouldApply) {
    return {
      ok: false,
      status: 'BLOCKED_PLAN_NOT_APPLYABLE',
      classification: 'BLOCKED_PLAN_NOT_APPLYABLE',
      reason: plan?.reason || 'Persistence plan generation failed',
      errors: plan?.errors || [],
      observedAt: getNow(),
    };
  }

  // 12. Apply Persistence Plan (Strict Dry-Run enforcement)
  const applyFn = deps.applyCleanMetadataPersistencePlan || applyCleanMetadataPersistencePlan;
  const applyResult = await applyFn({
    plan,
    taskId: task.id,
    materialId: material.id,
    dbClient: deps.dbClient,
    existingTask: task,
    existingMaterial: material,
    allowRealApply: false, // strictly dry-run by contract
  });

  // 13. Format Bounded Result Shape (Filters out heavy text arrays)
  const filteredVerificationSummary = candidate.verificationSummary ? {
    ok: candidate.verificationSummary.ok,
    cleanState: candidate.verificationSummary.cleanState,
    errors: candidate.verificationSummary.errors || [],
    warnings: candidate.verificationSummary.warnings || [],
    unresolvedAnchorCount: candidate.verificationSummary.unresolvedAnchorCount || 0,
    inputSizeBytes: candidate.verificationSummary.inputSizeBytes || 0,
    sourceInput: candidate.verificationSummary.sourceInput ? {
      bucket: candidate.verificationSummary.sourceInput.bucket,
      object: candidate.verificationSummary.sourceInput.object,
      sha256: candidate.verificationSummary.sourceInput.sha256,
      sizeBytes: candidate.verificationSummary.sourceInput.sizeBytes,
    } : null,
    costSource: candidate.verificationSummary.costSource || 'unavailable',
  } : null;

  return {
    ok: applyResult.ok,
    status: applyResult.classification || 'DRY_RUN_SUCCESS',
    classification: applyResult.classification || 'DRY_RUN_SUCCESS',
    jobId: request.job_id,
    materialId: material.id,
    taskId: task.id,
    assetVersion: request.asset_version,
    dryRun: true,
    audit: plan.audit ? {
      costSource: plan.audit.costSource,
      tokensTotal: plan.audit.tokensTotal,
      cleanState: plan.audit.cleanState,
      timestamp: plan.audit.timestamp,
      newVersionIntent: config.intent === 'create-new-version' ? {
        intent: config.intent,
        triggerReason: config.newVersionReason,
        previousAssetVersion: existingTaskJob?.assetVersion || null,
        previousJobId: existingTaskJob?.jobId || null,
        newAssetVersion: request.asset_version,
      } : null,
    } : null,
    warnings: plan.warnings || [],
    verificationSummary: filteredVerificationSummary,
    observedAt: getNow(),
  };
}
