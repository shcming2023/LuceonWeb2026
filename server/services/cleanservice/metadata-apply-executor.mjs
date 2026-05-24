/**
 * server/services/cleanservice/metadata-apply-executor.mjs
 *
 * CleanService Single-Sample Verified Metadata Apply Executor.
 * Responsible for applying a pre-merged persistence plan to the DB with strict gates.
 */

/**
 * Traverses an object deeply to check for potential full artifact textual contents
 * or large data structures that do not belong in metadata summaries.
 *
 * @param {Object} obj Target object to inspect.
 * @returns {boolean} True if full content is detected, false otherwise.
 */
export function hasFullContentInMetadata(obj) {
  if (!obj || typeof obj !== 'object') return false;

  // Quick string check for typical content structure keys
  const str = JSON.stringify(obj);
  if (
    str.includes('"blocks"') ||
    str.includes('"paragraphs"') ||
    str.includes('"nodes"') ||
    str.includes('"children"') ||
    str.includes('"parsedArtifacts"')
  ) {
    return true;
  }

  // Deep recursive check
  const stack = [obj];
  while (stack.length > 0) {
    const current = stack.pop();
    if (!current || typeof current !== 'object') continue;

    for (const [key, val] of Object.entries(current)) {
      // Artifact roles should only be valid, short ObjectRefs
      if (['flooded_content', 'logic_tree', 'readable_tree', 'skeleton', 'unresolved_anchors', 'provenance', 'metrics'].includes(key)) {
        if (val && typeof val === 'object') {
          const allowedKeys = new Set(['bucket', 'object', 'size_bytes', 'sizeBytes', 'sha256', 'content_type', 'contentType']);
          for (const k of Object.keys(val)) {
            if (!allowedKeys.has(k)) {
              return true; // Extraneous key -> might be parsed content
            }
          }
        } else if (typeof val === 'string' && val.length > 500) {
          return true; // Large markdown/json string
        }
      }

      // Safeguard against very large text strings or lists
      if (typeof val === 'string' && val.length > 1000) {
        return true;
      }
      if (Array.isArray(val)) {
        if (val.length > 20) return true; // Only small warnings/errors array are allowed
        for (const item of val) {
          if (item && typeof item === 'object') stack.push(item);
        }
      } else if (val && typeof val === 'object') {
        stack.push(val);
      }
    }
  }

  return false;
}

function isCompletedCleanJob(job = {}) {
  return job.status === 'completed' || job.cleanState === 'completed';
}

function canDryRunExplicitNewVersionOverExistingMetadata({
  plan,
  existingTaskJob,
  existingMaterialJob,
  targetJobId,
  targetVersion,
}) {
  if (plan?.newVersionIntent?.intent !== 'create-new-version') return false;
  if (!existingTaskJob || !existingMaterialJob) return false;
  if (!targetJobId || !targetVersion) return false;

  const previousVersion = plan.newVersionIntent.previousAssetVersion;
  const previousJobId = plan.newVersionIntent.previousJobId;
  if (!previousVersion || !previousJobId) return false;
  if (targetVersion === previousVersion) return false;

  return existingTaskJob.jobId === previousJobId &&
    existingTaskJob.assetVersion === previousVersion &&
    existingMaterialJob.latestVersion === previousVersion &&
    isCompletedCleanJob(existingTaskJob) &&
    existingMaterialJob.status === 'completed';
}

/**
 * Applies the CleanService verified metadata persistence plan to the database.
 *
 * @param {Object} params Parameters.
 * @param {Object} params.plan CleanService persistence plan.
 * @param {string} params.taskId Target Task ID.
 * @param {string} params.materialId Target Material ID.
 * @param {Object} params.dbClient DB client instance for updateTask & updateMaterial.
 * @param {Object} params.existingTask Current task state from DB.
 * @param {Object} params.existingMaterial Current material state from DB.
 * @param {boolean} [params.allowRealApply=false] Set to true to execute real writes.
 * @returns {Promise<Object>} Execution result summary.
 */
export async function applyCleanMetadataPersistencePlan({
  plan,
  taskId,
  materialId,
  dbClient,
  existingTask,
  existingMaterial,
  allowRealApply = false,
}) {
  // 1. Gate Check: Plan OK
  if (!plan || plan.ok !== true) {
    return {
      ok: false,
      applied: false,
      operationCount: 0,
      classification: 'BLOCKED_PLAN_NOT_APPLYABLE',
      reason: plan?.reason || 'Plan is invalid or planning failed',
    };
  }

  // 2. Gate Check: Planner explicitly authorized apply
  if (plan.shouldApply !== true) {
    return {
      ok: false,
      applied: false,
      operationCount: 0,
      classification: 'BLOCKED_PLAN_NOT_APPLYABLE',
      reason: 'Plan shouldApply is false',
    };
  }

  // 3. Identity Check: Plan target matches call target
  if (String(plan.materialId) !== String(materialId) || String(plan.parseTaskId) !== String(taskId)) {
    return {
      ok: false,
      applied: false,
      operationCount: 0,
      classification: 'BLOCKED_SCOPE_WOULD_EXPAND',
      reason: `Plan IDs (${plan.materialId}/${plan.parseTaskId}) mismatch call target (${materialId}/${taskId})`,
    };
  }

  // 4. DB Existence Checks
  if (!existingTask || !existingMaterial) {
    return {
      ok: false,
      applied: false,
      operationCount: 0,
      classification: 'BLOCKED_DB_TARGET_NOT_FOUND',
      reason: 'Task or Material target record does not exist in DB',
    };
  }

  const serviceName = plan.serviceName || 'toc-rebuild';

  // 5. Already Applied vs Incompatible Existing Metadata Conflict Checks
  const existingTaskJob = existingTask.metadata?.cleanServiceJobs?.[serviceName];
  const existingMaterialJob = existingMaterial.metadata?.cleanMaterials?.[serviceName];

  if (existingTaskJob || existingMaterialJob) {
    const targetJobId = plan.taskPatch?.metadata?.cleanServiceJobs?.[serviceName]?.jobId;
    const targetVersion = plan.taskPatch?.metadata?.cleanServiceJobs?.[serviceName]?.assetVersion;

    const taskMatches = existingTaskJob &&
      existingTaskJob.jobId === targetJobId &&
      existingTaskJob.assetVersion === targetVersion;

    const materialMatches = existingMaterialJob &&
      existingMaterialJob.latestVersion === targetVersion;

    const dryRunExplicitNewVersionAllowed = !allowRealApply && canDryRunExplicitNewVersionOverExistingMetadata({
      plan,
      existingTaskJob,
      existingMaterialJob,
      targetJobId,
      targetVersion,
    });

    if (taskMatches && materialMatches) {
      return {
        ok: true,
        applied: false,
        operationCount: 0,
        classification: 'ALREADY_APPLIED_NOOP',
        reason: 'Target metadata jobId and assetVersion are already exactly persisted in both task and material records',
      };
    } else if (dryRunExplicitNewVersionAllowed) {
      // Continue through patch-scope/full-content checks before the dry-run success boundary.
    } else {
      return {
        ok: false,
        applied: false,
        operationCount: 0,
        classification: 'BLOCKED_EXISTING_TOC_REBUILD_METADATA',
        reason: 'Incompatible existing toc-rebuild metadata exists in task or material records',
      };
    }
  }

  // 6. Patch Scope Check: Only modify 'metadata' key
  const taskPatchKeys = Object.keys(plan.taskPatch || {});
  const materialPatchKeys = Object.keys(plan.materialPatch || {});

  if (taskPatchKeys.some(k => k !== 'metadata') || materialPatchKeys.some(k => k !== 'metadata')) {
    return {
      ok: false,
      applied: false,
      operationCount: 0,
      classification: 'BLOCKED_PATCH_SCOPE_VIOLATION',
      reason: 'Patches try to modify keys outside the "metadata" root property',
    };
  }

  // 7. Full Content Check: Block embedded parsed artifact data bodies
  if (hasFullContentInMetadata(plan.taskPatch) || hasFullContentInMetadata(plan.materialPatch)) {
    return {
      ok: false,
      applied: false,
      operationCount: 0,
      classification: 'BLOCKED_FULL_CONTENT_IN_METADATA',
      reason: 'Patches contain full artifact document data or unauthorized structures in metadata',
    };
  }

  // 8. Controlled Apply Boundary Check
  if (!allowRealApply) {
    return {
      ok: true,
      applied: false,
      operationCount: 0,
      classification: 'DRY_RUN_SUCCESS',
      reason: 'Dry-run verification completed successfully. No real writes performed.',
    };
  }

  // 9. Atomic Multi-PATCH Execution (Exactly 0 or 2 PATCHes)
  console.log(`[apply-executor] Writing task metadata for ${taskId}...`);
  const taskOk = await dbClient.updateTask(taskId, plan.taskPatch);
  if (!taskOk) {
    return {
      ok: false,
      applied: false,
      operationCount: 1,
      classification: 'DB_APPLY_FAILED',
      reason: `Failed to execute PATCH for task ${taskId}`,
    };
  }

  console.log(`[apply-executor] Writing material metadata for ${materialId}...`);
  const materialOk = await dbClient.updateMaterial(materialId, plan.materialPatch);
  if (!materialOk) {
    // CRITICAL FAILURE STATE: Task was patched successfully but Material update failed.
    // ROLLBACK IS STRICTLY FORBIDDEN by task contract.
    console.error('[apply-executor] CRITICAL: Task patch succeeded but Material patch failed! Rollback forbidden.');
    return {
      ok: false,
      applied: true, // Mark applied=true since one write was committed
      operationCount: 2,
      classification: 'PARTIAL_DB_APPLY_REQUIRES_LUCEON_REVIEW',
      reason: 'Task metadata was successfully updated but material metadata update failed. STOPPED FOR MANUAL AUDIT.',
    };
  }

  return {
    ok: true,
    applied: true,
    operationCount: 2,
    classification: 'APPLIED_SINGLE_SAMPLE_METADATA',
    reason: 'CleanService metadata persistence plan successfully applied to both records.',
  };
}
