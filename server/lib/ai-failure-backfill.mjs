export function extractAiFailureClassification(update = {}) {
  return update.aiFailureClassification ||
    update.metadata?.aiFailureClassification ||
    update.result?.aiFailureClassification ||
    null;
}

export function buildAiFailureBackfillMetadata({ update = {}, job = {}, analyzedAt = new Date().toISOString() } = {}) {
  const classification = extractAiFailureClassification(update);
  if (!classification) return {};

  const manualRetryEligible = classification.manualRetryEligible === true;
  return {
    aiFailureClassification: classification,
    aiFailureKind: classification.kind || null,
    aiFailurePhase: classification.aiPhase || classification.phase || null,
    aiFailureTimeoutKind: classification.timeoutKind || null,
    aiFailureDurationMs: classification.durationMs ?? null,
    aiFailureTimeoutMs: classification.timeoutMs ?? null,
    aiFailureProviderId: classification.providerId || classification.provider || null,
    aiFailureModel: classification.model || null,
    aiFailureBaseUrl: classification.baseUrl || null,
    aiAutoRetryAllowed: false,
    aiManualRetryEligible: manualRetryEligible,
    aiManualRetryEligibilityStatus: classification.manualRetryEligibilityStatus ||
      (manualRetryEligible ? 'eligible-manual-only' : 'not-eligible'),
    aiManualRetryEligibilityReason: classification.manualRetryEligibilityReason || null,
    aiFailureRecordedAt: analyzedAt,
    aiJobId: job.id || update.aiJobId || null
  };
}

export function buildAiFailureTaskMessage(update = {}) {
  if (update.state !== 'failed') {
    return `AI 识别完成: ${update.state}${update.needsReview ? ' (待人工复核)' : ''}`;
  }

  const classification = extractAiFailureClassification(update);
  if (classification?.manualRetryEligible === true) {
    return 'AI 识别失败：已归类为可人工评估手动重试的残留失败';
  }
  return 'AI 识别失败：需人工查看失败原因';
}
