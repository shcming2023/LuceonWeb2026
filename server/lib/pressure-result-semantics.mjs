function getMetadata(task) {
  return task?.metadata || {};
}

function isSuccessLike(task) {
  return task?.state === 'completed' || task?.state === 'review-pending' || task?.state === 'confirmed';
}

function isRetryableAiResidual(task) {
  const metadata = getMetadata(task);
  const classification = metadata.aiFailureClassification;
  return task?.state === 'failed' &&
    (task?.stage === 'ai' || metadata.aiStatus === 'failed' || classification) &&
    (metadata.aiManualRetryEligible === true || classification?.manualRetryEligible === true);
}

function hasSystemicFailureSignal(task) {
  const metadata = getMetadata(task);
  if (metadata.infrastructureFailure === true || metadata.systemicFailure === true) return true;
  if (metadata.mineruRuntimeProgressTruth?.terminalFailure === true) return true;
  return task?.state === 'failed' && !isRetryableAiResidual(task);
}

function isActiveWithProgress(task) {
  const metadata = getMetadata(task);
  const truth = metadata.mineruRuntimeProgressTruth;
  return Boolean(truth?.rawLogAdvancing || truth?.terminalFailure === false) ||
    (task?.state === 'running' && task?.stage === 'mineru-processing');
}

export function classifyPressureRunOutcome(tasks = []) {
  const counts = {
    total: tasks.length,
    successLike: 0,
    retryableAiResidual: 0,
    systemicFailureSignal: 0,
    activeWithProgress: 0,
    queuedOrRunning: 0
  };

  for (const task of tasks) {
    if (isSuccessLike(task)) counts.successLike += 1;
    if (isRetryableAiResidual(task)) counts.retryableAiResidual += 1;
    if (hasSystemicFailureSignal(task)) counts.systemicFailureSignal += 1;
    if (isActiveWithProgress(task)) counts.activeWithProgress += 1;
    if (['pending', 'running', 'ai-pending', 'ai-running'].includes(task?.state || '')) {
      counts.queuedOrRunning += 1;
    }
  }

  const hasAnySuccess = counts.successLike > 0;
  const hasOnlyRetryableResidualFailures = counts.systemicFailureSignal === 0 && counts.retryableAiResidual > 0;
  const systemicFailure = counts.systemicFailureSignal > 0 && !hasAnySuccess;

  if (systemicFailure) {
    return {
      outcome: 'systemic-failure',
      systemicFailure: true,
      partialSuccess: false,
      counts
    };
  }

  if (hasAnySuccess && hasOnlyRetryableResidualFailures) {
    return {
      outcome: 'partial-success-with-retryable-ai-residuals',
      systemicFailure: false,
      partialSuccess: true,
      counts
    };
  }

  if (hasAnySuccess && counts.systemicFailureSignal === 0) {
    return {
      outcome: counts.queuedOrRunning > 0 ? 'partial-success-with-active-work' : 'success-or-reviewable',
      systemicFailure: false,
      partialSuccess: counts.queuedOrRunning > 0 || counts.activeWithProgress > 0,
      counts
    };
  }

  return {
    outcome: counts.queuedOrRunning > 0 ? 'in-progress' : 'inconclusive',
    systemicFailure: false,
    partialSuccess: false,
    counts
  };
}
