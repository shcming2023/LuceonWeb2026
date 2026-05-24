const ACTIVE_STATES = new Set([
  'pending',
  'running',
  'review-pending-partial',
  'cost-decision'
]);

const ASSET_VERSION_RE = /^v(\d+)$/;

export function parseAssetVersionNumber(version) {
  if (typeof version !== 'string') return null;
  const match = version.match(ASSET_VERSION_RE);
  return match ? parseInt(match[1], 10) : null;
}

export function compareAssetVersions(left, right) {
  const leftNum = parseAssetVersionNumber(left);
  const rightNum = parseAssetVersionNumber(right);
  if (leftNum === null || rightNum === null) return null;
  return leftNum - rightNum;
}

export function allocateAssetVersion(task, serviceName = 'toc-rebuild') {
  const cleanJobs = task?.metadata?.cleanServiceJobs || {};
  const currentJob = cleanJobs[serviceName];

  if (currentJob && ACTIVE_STATES.has(currentJob.cleanState || currentJob.status || currentJob.state)) {
    return {
      assetVersion: currentJob.assetVersion || currentJob.asset_version || 'v1',
      isActiveDuplicate: true,
      jobId: currentJob.jobId || currentJob.job_id
    };
  }

  let maxVersionNum = 0;
  for (const job of Object.values(cleanJobs)) {
    const ver = job.assetVersion || job.asset_version;
    const versionNum = parseAssetVersionNumber(ver);
    if (versionNum !== null) {
      maxVersionNum = Math.max(maxVersionNum, versionNum);
    }
  }

  const cleanMaterials = task?.materialMetadata?.cleanMaterials || task?.metadata?.cleanMaterials || {};
  for (const mat of Object.values(cleanMaterials)) {
    const ver = mat.assetVersion || mat.latestVersion;
    const versionNum = parseAssetVersionNumber(ver);
    if (versionNum !== null) {
      maxVersionNum = Math.max(maxVersionNum, versionNum);
    }
  }

  return {
    assetVersion: `v${maxVersionNum + 1}`,
    isActiveDuplicate: false,
    jobId: null
  };
}

export function resolveAssetVersion(task, serviceName = 'toc-rebuild', {
  targetAssetVersion = null,
  previousAssetVersion = null,
} = {}) {
  const allocation = allocateAssetVersion(task, serviceName);
  const defaultAllocatedAssetVersion = allocation.assetVersion;

  if (targetAssetVersion === undefined || targetAssetVersion === null || targetAssetVersion === '') {
    return {
      ...allocation,
      defaultAllocatedAssetVersion,
      targetAssetVersion: null,
      resolvedBy: 'default',
    };
  }

  const targetVersionNum = parseAssetVersionNumber(targetAssetVersion);
  if (targetVersionNum === null) {
    const error = new Error('invalid-target-asset-version');
    error.code = 'BLOCKED_INVALID_TARGET_ASSET_VERSION';
    throw error;
  }

  const defaultCompare = compareAssetVersions(targetAssetVersion, defaultAllocatedAssetVersion);
  if (defaultCompare === null || defaultCompare < 0) {
    const error = new Error('target-asset-version-below-default');
    error.code = 'BLOCKED_TARGET_ASSET_VERSION_BELOW_DEFAULT';
    throw error;
  }

  if (previousAssetVersion) {
    const previousCompare = compareAssetVersions(targetAssetVersion, previousAssetVersion);
    if (previousCompare === null || previousCompare <= 0) {
      const error = new Error('target-asset-version-not-greater-than-previous');
      error.code = 'BLOCKED_TARGET_ASSET_VERSION_NOT_GREATER_THAN_PREVIOUS';
      throw error;
    }
  }

  return {
    ...allocation,
    assetVersion: targetAssetVersion,
    defaultAllocatedAssetVersion,
    targetAssetVersion,
    resolvedBy: 'targetAssetVersion',
  };
}
