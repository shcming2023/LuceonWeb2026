export const CLEAN_STAGE_STATES = Object.freeze({
  NOT_ENABLED: 'not-enabled',
  NOT_APPLICABLE: 'not-applicable',
  PENDING: 'pending',
  RUNNING: 'running',
  REVIEW_PENDING_PARTIAL: 'review-pending-partial',
  COMPLETED: 'completed',
  SKIPPED: 'skipped',
  COST_DECISION: 'cost-decision',
  HARD_LIMIT_FAILED: 'hard-limit-failed',
  TIMEOUT: 'timeout',
  PROTOCOL_FAILURE: 'protocol-failure',
});

const STATE_LABELS = Object.freeze({
  [CLEAN_STAGE_STATES.NOT_ENABLED]: '未启用',
  [CLEAN_STAGE_STATES.NOT_APPLICABLE]: '不适用',
  [CLEAN_STAGE_STATES.PENDING]: '等待目录重建',
  [CLEAN_STAGE_STATES.RUNNING]: '目录重建中',
  [CLEAN_STAGE_STATES.REVIEW_PENDING_PARTIAL]: '部分完成待复核',
  [CLEAN_STAGE_STATES.COMPLETED]: '目录结构已完成',
  [CLEAN_STAGE_STATES.SKIPPED]: '目录重建已跳过',
  [CLEAN_STAGE_STATES.COST_DECISION]: '成本待决策',
  [CLEAN_STAGE_STATES.HARD_LIMIT_FAILED]: '目录重建失败',
  [CLEAN_STAGE_STATES.TIMEOUT]: '目录重建失败',
  [CLEAN_STAGE_STATES.PROTOCOL_FAILURE]: '目录重建失败',
});

const TASK_INTENTS = Object.freeze({
  [CLEAN_STAGE_STATES.NOT_ENABLED]: 'none',
  [CLEAN_STAGE_STATES.NOT_APPLICABLE]: 'none',
  [CLEAN_STAGE_STATES.PENDING]: 'pending',
  [CLEAN_STAGE_STATES.RUNNING]: 'running',
  [CLEAN_STAGE_STATES.REVIEW_PENDING_PARTIAL]: 'review-pending',
  [CLEAN_STAGE_STATES.COMPLETED]: 'completed',
  [CLEAN_STAGE_STATES.SKIPPED]: 'skipped',
  [CLEAN_STAGE_STATES.COST_DECISION]: 'review-pending',
  [CLEAN_STAGE_STATES.HARD_LIMIT_FAILED]: 'failed',
  [CLEAN_STAGE_STATES.TIMEOUT]: 'failed',
  [CLEAN_STAGE_STATES.PROTOCOL_FAILURE]: 'failed',
});

export function getCleanStageLabel(cleanState) {
  return STATE_LABELS[cleanState] || STATE_LABELS[CLEAN_STAGE_STATES.PROTOCOL_FAILURE];
}

export function mapCleanStateToTaskIntent(cleanState, details = {}) {
  const taskIntent = TASK_INTENTS[cleanState] || 'failed';
  const unresolvedAnchorCount = Number(details.unresolvedAnchorCount || 0);
  const cleanReview = cleanState === CLEAN_STAGE_STATES.REVIEW_PENDING_PARTIAL
    ? 'partial-unresolved-anchors'
    : (cleanState === CLEAN_STAGE_STATES.COST_DECISION ? 'cost-decision-required' : null);

  return {
    cleanState,
    productLabel: getCleanStageLabel(cleanState),
    taskIntent,
    cleanReview,
    unresolvedAnchorCount,
    shouldBlockCurrentAiMetadata: false,
  };
}

export function evaluateCleanCostPolicy(stats = {}, policy = {}) {
  const softLimitCny = Number.isFinite(Number(policy.softLimitCny)) ? Number(policy.softLimitCny) : 5;
  const hardLimitCny = Number.isFinite(Number(policy.hardLimitCny)) ? Number(policy.hardLimitCny) : 8;
  const observed = Math.max(
    Number(stats.costCnyProjected || 0),
    Number(stats.cost_cny_projected || 0),
    Number(stats.costCnyEstimated || 0),
    Number(stats.cost_cny_estimated || 0),
    Number(stats.costCnyActual || 0),
    Number(stats.cost_cny_actual || 0),
  );

  if (observed >= hardLimitCny) {
    return {
      cleanState: CLEAN_STAGE_STATES.HARD_LIMIT_FAILED,
      decisionRequired: false,
      hardFailed: true,
      observedCostCny: observed,
      message: `CleanService cost ${observed} reached hard limit ${hardLimitCny}`,
    };
  }

  if (observed >= softLimitCny) {
    return {
      cleanState: CLEAN_STAGE_STATES.COST_DECISION,
      decisionRequired: true,
      hardFailed: false,
      observedCostCny: observed,
      message: `CleanService cost ${observed} reached soft limit ${softLimitCny}`,
    };
  }

  return {
    cleanState: null,
    decisionRequired: false,
    hardFailed: false,
    observedCostCny: observed,
    message: null,
  };
}
