const ACTIVE_STATES = new Set([
  'pending',
  'running',
  'review-pending-partial',
  'cost-decision'
]);

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
    if (ver) {
      const match = ver.match(/^v(\d+)$/);
      if (match) {
        maxVersionNum = Math.max(maxVersionNum, parseInt(match[1], 10));
      }
    }
  }

  const cleanMaterials = task?.materialMetadata?.cleanMaterials || task?.metadata?.cleanMaterials || {};
  for (const mat of Object.values(cleanMaterials)) {
    const ver = mat.assetVersion || mat.latestVersion;
    if (ver) {
      const match = ver.match(/^v(\d+)$/);
      if (match) {
        maxVersionNum = Math.max(maxVersionNum, parseInt(match[1], 10));
      }
    }
  }

  return {
    assetVersion: `v${maxVersionNum + 1}`,
    isActiveDuplicate: false,
    jobId: null
  };
}
