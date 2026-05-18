const TERMINAL_STATES = new Set(['completed', 'review-pending', 'failed', 'canceled', 'confirmed']);
const PARSE_RUNNING_STAGES = new Set(['mineru-processing', 'mineru-queued', 'result-fetching']);
const DIRECT_PROCESSING_STATUSES = new Set(['processing', 'running', 'pending', 'queued']);
const DIRECT_COMPLETED_STATUSES = new Set(['done', 'success', 'completed', 'succeeded', 'finished', 'complete']);
const DIRECT_FAILED_STATUSES = new Set(['failed', 'error', 'failure', 'canceled', 'cancelled']);

function normalizeStatus(value) {
  return String(value || '').trim().toLowerCase();
}

function firstTimestamp(...values) {
  for (const value of values) {
    if (value) return value;
  }
  return null;
}

function hasArtifacts(task = {}) {
  const metadata = task.metadata || {};
  return Number(metadata.parsedFilesCount || task.parsedFilesCount || 0) > 0 ||
    Boolean(metadata.markdownObjectName) ||
    Boolean(metadata.zipObjectName) ||
    Boolean(metadata.artifactManifestObjectName) ||
    Boolean(metadata.parsedPrefix);
}

function readLogState(observation) {
  const activityLevel = observation?.activityLevel || observation?.progressSemantics?.activityLevel || null;
  if (!observation) return 'missing';

  if (observation.sidecar_missing) return 'sidecar_missing';
  if (observation.container_mount_stale) return 'container_mount_stale';

  if (activityLevel === 'fast-complete-no-business-signal') return 'terminal-diagnostic';

  const isStale = activityLevel === 'log-observation-stale' || observation?.observationStale === true || observation?.progressSemantics?.freshness === 'stale';
  const isFresh = ['active-progress', 'active-stage-change', 'active-business-log'].includes(activityLevel || '');

  if (observation.observer === 'host-mineru-log-observer') {
    if (isStale) return 'sidecar_stale';
    if (isFresh) return 'sidecar_fresh';
  }

  if (isStale) return 'stale';
  if (isFresh) return 'fresh';
  if (activityLevel === 'api-alive-only') return 'api-alive-only';
  if (activityLevel?.startsWith('log-observation-')) return 'missing';
  return activityLevel || 'unknown';
}

function readAiState(task = {}) {
  const metadata = task.metadata || {};
  if (metadata.aiFailureKind || metadata.aiStatus === 'failed' || (task.stage === 'ai' && task.state === 'failed')) return 'failed';
  if (task.state === 'ai-running') return 'running';
  if (task.state === 'ai-pending') return 'pending';
  if (task.state === 'review-pending' || metadata.aiStatus === 'analyzed') return 'analyzed';
  return metadata.aiStatus || null;
}

function phaseFromTask(task = {}, directMineruStatus = '') {
  if (task.state === 'ai-pending' || task.state === 'ai-running' || task.stage === 'ai') return 'ai';
  if (task.state === 'review-pending') return 'review';
  if (TERMINAL_STATES.has(String(task.state || ''))) return 'terminal';
  if (task.stage === 'result-store' || task.stage === 'complete') return 'result-ingestion';
  if (task.stage === 'mineru-processing' || task.stage === 'mineru-queued' || DIRECT_PROCESSING_STATUSES.has(directMineruStatus)) return 'parse';
  return 'unknown';
}

function defaultOperatorMessage({ phase, lagKind, directMineruStatus, logState, aiState, dbState, dbStage }) {
  if (lagKind === 'db-behind-direct-mineru') return 'MinerU API 已完成，Luceon 正在同步解析结果';
  if (lagKind === 'log-stale-after-terminal') return '任务已进入终态，日志通道无新增业务进度';
  if (lagKind === 'dependency-health-readiness-only') return '依赖健康检查仅代表就绪性，不代表单个任务进度';
  if (lagKind === 'ai-after-parse') return aiState === 'failed'
    ? 'MinerU 解析已完成，AI 识别失败，需人工判断后续处理'
    : 'MinerU 解析已完成，已进入 AI/审核阶段';
  if (directMineruStatus && DIRECT_FAILED_STATUSES.has(directMineruStatus)) return 'MinerU API 返回终态失败';

  if (logState === 'sidecar_missing' && dbState === 'running') return 'MinerU 正在处理，但主宿主机观测通道异常 (sidecar missing)';
  if (logState === 'container_mount_stale' && dbState === 'running') return 'MinerU 正在处理，容器挂载观测滞后 (container mount stale)';

  const isTerminal = TERMINAL_STATES.has(dbState || '');
  if (!isTerminal && directMineruStatus && DIRECT_PROCESSING_STATUSES.has(directMineruStatus)) return 'MinerU API 仍在处理';
  if ((logState === 'stale' || logState === 'sidecar_stale') && dbState === 'running') return '任务仍在处理中，但日志观测滞后';
  if (phase === 'result-ingestion') return '解析产物同步中';
  if (phase === 'review') return 'AI 识别完成，待人工复核';
  if (phase === 'ai') return 'AI 元数据识别阶段';
  return dbStage || dbState ? `任务状态 ${dbState || 'unknown'}/${dbStage || 'unknown'}` : '任务进度待确认';
}

export function isTerminalTask(task = {}) {
  return TERMINAL_STATES.has(String(task.state || ''));
}

export function buildProgressSnapshot(task = {}, options = {}) {
  const metadata = task.metadata || {};
  const observation = options.logObservation || metadata.mineruObservedProgress || null;
  const directMineruStatus = normalizeStatus(
    options.directMineruStatus ||
    options.directMineruData?.status ||
    options.directMineruData?.state ||
    metadata.directMineruStatus ||
    metadata.mineruStatus
  );
  const dbState = task.state || null;
  const dbStage = task.stage || null;
  const aiState = readAiState(task);
  const logState = options.logState || readLogState(observation);
  const phase = phaseFromTask(task, directMineruStatus);
  const terminalTask = isTerminalTask(task);
  const directCompleted = DIRECT_COMPLETED_STATUSES.has(directMineruStatus);
  const directFailed = DIRECT_FAILED_STATUSES.has(directMineruStatus);
  const directProcessing = DIRECT_PROCESSING_STATUSES.has(directMineruStatus);
  const dbParseRunning = dbState === 'running' && PARSE_RUNNING_STAGES.has(dbStage);
  const parsedArtifactsPresent = hasArtifacts(task);

  let lagKind = 'none';
  let source = 'db';
  let sourcePriority = 'db';
  let freshness = 'unknown';
  let confidence = 'medium';

  if (options.dependencyHealthReadinessOnly) {
    lagKind = 'dependency-health-readiness-only';
    source = 'mixed';
    sourcePriority = 'db';
    freshness = 'unknown';
    confidence = 'medium';
  } else if (directCompleted && dbParseRunning) {
    lagKind = 'db-behind-direct-mineru';
    source = 'mixed';
    sourcePriority = 'direct-mineru';
    freshness = 'fresh';
    confidence = 'high';
  } else if (terminalTask && logState === 'stale') {
    lagKind = 'log-stale-after-terminal';
    source = 'mixed';
    sourcePriority = aiState === 'failed' ? 'ai' : 'db';
    freshness = 'terminal';
    confidence = 'high';
  } else if ((dbStage === 'ai' || aiState === 'failed' || aiState === 'running' || aiState === 'pending') && metadata.mineruStatus === 'completed') {
    lagKind = 'ai-after-parse';
    source = 'mixed';
    sourcePriority = 'ai';
    freshness = terminalTask ? 'terminal' : 'fresh';
    confidence = parsedArtifactsPresent ? 'high' : 'medium';
  } else if (directFailed) {
    source = 'direct-mineru';
    sourcePriority = 'direct-mineru';
    freshness = 'terminal';
    confidence = 'high';
  } else if (terminalTask) {
    source = aiState === 'failed' ? 'ai' : 'db';
    sourcePriority = aiState === 'failed' ? 'ai' : 'db';
    freshness = 'terminal';
    confidence = 'high';
  } else if (directProcessing) {
    source = (logState === 'fresh' || logState === 'sidecar_fresh') ? 'mixed' : 'direct-mineru';
    sourcePriority = 'direct-mineru';
    freshness = (logState === 'fresh' || logState === 'sidecar_fresh') ? 'fresh' : 'unknown';
    confidence = (logState === 'fresh' || logState === 'sidecar_fresh') ? 'high' : 'medium';
  } else if (logState === 'fresh' || logState === 'sidecar_fresh') {
    source = 'log';
    sourcePriority = 'log';
    freshness = 'fresh';
    confidence = 'medium';
  } else if (logState === 'stale' || logState === 'sidecar_stale' || logState === 'container_mount_stale') {
    source = 'mixed';
    sourcePriority = 'db';
    freshness = 'stale';
    confidence = 'low';
  }

  const operatorMessage = options.operatorMessage || defaultOperatorMessage({
    phase,
    lagKind,
    directMineruStatus,
    logState,
    aiState,
    dbState,
    dbStage
  });

  return {
    version: 'progress-snapshot-v0.1',
    phase,
    source,
    sourcePriority,
    observedAt: firstTimestamp(
      options.observedAt,
      options.directMineruData?.updated_at,
      options.directMineruData?.completed_at,
      options.directMineruData?.started_at,
      observation?.progressSemantics?.lastObservedAt,
      observation?.lastProgressObservedAt,
      metadata.mineruLastStatusAt,
      task.updatedAt,
      task.createdAt
    ),
    freshness,
    confidence,
    lagKind,
    directMineruStatus: directMineruStatus || null,
    dbState,
    dbStage,
    logState,
    aiState,
    operatorMessage,
  };
}

export function attachProgressSnapshot(task = {}, options = {}) {
  return {
    ...task,
    progressSnapshot: buildProgressSnapshot(task, options)
  };
}

export function summarizeProgressSnapshotForTask(task = {}, options = {}) {
  return buildProgressSnapshot(task, options);
}
