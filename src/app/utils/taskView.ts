import type { Material } from '../../store/types';
import { TASK_STATUS_TERMS } from './taskTerms';

/**
 * ParseTask 接口定义（对齐后端 db-server.mjs）
 */
export interface ParseTask {
  id: string;
  materialId?: string | number;
  engine?: string;
  stage?: string;
  state?: string;
  progress?: number;
  message?: string;
  errorMessage?: string | null;
  createdAt?: string;
  updatedAt?: string;
  completedAt?: string | null;
  retryOf?: string | null;
  metadata?: Record<string, any>;
}

/**
 * 任务展示桶类型
 */
export type TaskBucket = 'queued' | 'processing' | 'reviewing' | 'completed' | 'failed' | 'canceled' | 'unknown';

function isDirectMineruProcessing(task: ParseTask | null | undefined): boolean {
  const status = String(task?.metadata?.directMineruStatus || task?.metadata?.mineruStatus || '').toLowerCase();
  return ['processing', 'running', 'pending', 'queued'].includes(status);
}

function isLocalMineruTimeout(task: ParseTask | null | undefined): boolean {
  return task?.metadata?.localTimeoutOccurred === true || task?.metadata?.localTimeout === true;
}

function getAiFailureClassification(task: ParseTask | null | undefined): any {
  return task?.metadata?.aiFailureClassification || null;
}

function isManualRetryEligibleAiFailure(task: ParseTask | null | undefined): boolean {
  const classification = getAiFailureClassification(task);
  return task?.metadata?.aiManualRetryEligible === true || classification?.manualRetryEligible === true;
}

function formatMineruProgressSemantics(obs: any, task?: ParseTask | null): string | null {
  if (!obs) return null;
  const semantics = obs.progressSemantics;

  const level = obs.activityLevel || '';
  const phase = obs.stage?.rawPhase || obs.phase || '';
  const current = obs.stage?.current ?? obs.current;
  const total = obs.stage?.total ?? obs.total;
  const win = obs.window || obs.latestWindow;
  const pageCurrent = win?.pageCurrent ?? win?.pageEnd ?? obs.document?.currentPages;
  const pageTotal = win?.pageTotal ?? obs.document?.totalPages;
  const pieces: string[] = [];

  if (obs.backendProfile) pieces.push(`backend=${obs.backendProfile}`);
  if (phase) pieces.push(`相位 ${phase}${current != null && total != null ? ` ${current}/${total}` : ''}`);
  if (win?.index != null && win?.total != null) pieces.push(`批次 ${win.index}/${win.total}`);
  if (pageCurrent != null && pageTotal != null) pieces.push(`页 ${pageCurrent}/${pageTotal}`);

  const directProcessing = isDirectMineruProcessing(task);
  const localTimeout = isLocalMineruTimeout(task);
  const staleObservation = level === 'log-observation-stale' || obs.observationStale;
  const activeRawLog = ['active-progress', 'active-stage-change', 'active-business-log'].includes(level);

  if (directProcessing && localTimeout && activeRawLog) {
    return pieces.length
      ? `本地等待已超时，但 MinerU API 仍在 processing；原始日志显示仍在推进：${pieces.join('，')}`
      : '本地等待已超时，但 MinerU API 仍在 processing；原始日志显示仍在推进';
  }
  if (directProcessing && localTimeout && staleObservation) {
    return pieces.length
      ? `本地等待已超时，但 MinerU API 仍在 processing；日志观测滞后：${pieces.join('，')}`
      : '本地等待已超时，但 MinerU API 仍在 processing；日志观测滞后，不能按终态失败处理';
  }
  if (directProcessing && staleObservation) {
    return pieces.length
      ? `MinerU API 仍在 processing；日志观测滞后：${pieces.join('，')}`
      : 'MinerU API 仍在 processing；日志观测滞后，不能按终态失败处理';
  }
  if (semantics?.message) return String(semantics.message);

  if (level === 'api-alive-only') return 'MinerU API 可达，但未见可归因业务进展';
  if (staleObservation) {
    return pieces.length ? `MinerU 正在解析，但日志观测滞后：${pieces.join('，')}` : 'MinerU 正在解析，但日志观测滞后/不可用';
  }
  if (level === 'log-observation-missing' || level === 'log-observation-unavailable' || level === 'log-observation-no-business-signal') {
    return 'MinerU 已提交/正在处理，但暂无可归因业务日志';
  }
  if (pieces.length) return `MinerU 正在解析：${pieces.join('，')}`;
  return null;
}

function hasParsedArtifactEvidence(task: ParseTask): boolean {
  const metadata = task.metadata || {};
  return Number(metadata.parsedFilesCount || 0) > 0 ||
    Boolean(metadata.markdownObjectName) ||
    Boolean(metadata.parsedPrefix) ||
    Boolean(metadata.resultZipObjectName) ||
    Boolean(metadata.parsedObjectName);
}

function getParsedArtifactCount(task: ParseTask): number {
  const metadata = task.metadata || {};
  return Number(metadata.parsedFilesCount || (task as any).parsedFilesCount || 0) || 0;
}

function isTerminalSuccessfulTask(task: ParseTask): boolean {
  return task.state === 'review-pending' || task.state === 'completed';
}

function isInFlightOnlyMineruObservation(obs: any): boolean {
  if (!obs) return true;
  const level = obs.activityLevel || obs.progressSemantics?.activityLevel || '';
  return level === 'log-observation-missing' ||
    level === 'log-observation-unavailable' ||
    level === 'log-observation-unreadable' ||
    level === 'log-observation-no-business-signal' ||
    level === 'log-observation-stale' ||
    level === 'api-alive-only' ||
    Boolean(obs.observationStale);
}

function isNoAttributedTerminalDiagnosticLine(line: string | null | undefined): boolean {
  if (!line) return false;
  return line.includes('MinerU 已完成，但本次未捕获可归因业务进度日志');
}

function formatLastKnownMineruProgress(obs: any): string | null {
  if (!obs || isInFlightOnlyMineruObservation(obs)) return null;
  const line = formatMineruProgressSemantics(obs);
  if (isNoAttributedTerminalDiagnosticLine(line)) return null;
  if (!line) return null;
  return line.replace(/^MinerU 正在解析[：:]?\s*/, '').replace(/^MinerU 正在处理，但日志观测滞后[：:]?\s*/, '');
}

function deriveTerminalSuccessMineruCompletionLine(task: ParseTask): string | null {
  const metadata = task.metadata || {};
  if (!isTerminalSuccessfulTask(task)) return null;
  if (metadata.mineruStatus !== 'completed') return null;
  if (!hasParsedArtifactEvidence(task)) return null;

  const parsedCount = getParsedArtifactCount(task);
  const artifactPart = parsedCount > 0 ? `解析产物 ${parsedCount} 个` : '解析产物已生成';
  const lastKnownProgress = formatLastKnownMineruProgress(metadata.mineruObservedProgress);
  if (lastKnownProgress) return `MinerU 已完成，${artifactPart}；最后可见进度：${lastKnownProgress}`;
  return `MinerU 已完成，${artifactPart}`;
}

function deriveTerminalMineruCompletionLine(task: ParseTask): string | null {
  const metadata = task.metadata || {};
  if (metadata.mineruStatus !== 'completed') return null;
  if (!hasParsedArtifactEvidence(task)) return null;

  const obs = metadata.mineruObservedProgress;
  if (obs?.activityLevel === 'fast-complete-no-business-signal' ||
      obs?.progressSemantics?.activityLevel === 'fast-complete-no-business-signal') {
    return formatMineruProgressSemantics(obs) || 'MinerU 已完成，但本次未捕获可归因业务进度日志';
  }

  if (isInFlightOnlyMineruObservation(obs)) {
    return 'MinerU 已完成，但本次未捕获可归因业务进度日志';
  }

  return null;
}

export function deriveTaskDisplayStatus(task: ParseTask | null | undefined): string {
  if (!task) return '待处理';
  if (task.state === 'failed') {
    if (task.stage === 'ai' || getAiFailureClassification(task) || task.metadata?.aiStatus === 'failed') {
      if (isManualRetryEligibleAiFailure(task)) {
        return 'AI 识别失败，待人工判断是否手动重试';
      }
      return 'AI 识别失败，需人工查看';
    }
    if (task.metadata?.mineruTaskId && task.metadata?.mineruStatus === 'completed' && !task.metadata?.parsedFilesCount) {
      return 'MinerU 已完成，结果待接管';
    }
    if (task.stage === 'submit-failed-retryable' || task.message?.includes('可重试')) {
      return '提交 MinerU 失败，可重试';
    }
  }

  if (task.stage === 'mineru-queued') return 'MinerU 排队中';
  if (task.stage === 'mineru-processing') {
    return formatMineruProgressSemantics(task.metadata?.mineruObservedProgress, task) || task.message || 'MinerU 正在解析';
  }
  if (task.stage === 'result-store') return '解析产物同步中';
  if (task.state === 'ai-pending') return 'AI 元数据识别待执行';
  if (task.state === 'ai-running') return 'AI 元数据识别中';
  return STATE_LABELS[task.state || ''] || '未知';
}

export function deriveMineruProgressLine(task: ParseTask | null | undefined): string | null {
  if (!task) return null;
  const terminalSuccessLine = deriveTerminalSuccessMineruCompletionLine(task);
  if (terminalSuccessLine) return terminalSuccessLine;
  const terminalCompletionLine = deriveTerminalMineruCompletionLine(task);
  if (terminalCompletionLine) return terminalCompletionLine;
  if (task.state === 'completed' || task.state === 'review-pending') return null;
  return formatMineruProgressSemantics(task.metadata?.mineruObservedProgress, task);
}

/**
 * 根据任务状态派生展示桶 (PRD v0.4 §6.3)
 */
export function deriveTaskBucket(state: string | undefined, stage?: string): TaskBucket {
  if (!state) return 'unknown';

  if (state === 'running' && stage === 'mineru-queued') return 'queued';

  switch (state) {
    case 'uploading':
    case 'pending':
    case 'ai-pending':
      return 'queued';
    case 'running':
    case 'result-store':
    case 'ai-running':
      return 'processing';
    case 'review-pending':
      return 'reviewing';
    case 'completed':
      return 'completed';
    case 'failed':
      return 'failed';
    case 'canceled':
      return 'canceled';
    default:
      return 'unknown';
  }
}

/**
 * 活跃任务状态集合 (PRD v0.4 修订建议 §9.1)
 */
const ACTIVE_STATES = new Set([
  'pending',
  'running',
  'result-store',
  'ai-pending',
  'ai-running',
  'review-pending'
]);

/**
 * 从任务列表中找到属于特定素材的“当前任务”
 * 规则：
 * 1. 优先返回 active 任务
 * 2. 若无 active 任务，返回最近更新的任务 (updatedAt || createdAt)
 */
export function deriveCurrentTask(materialId: string | number, tasks: ParseTask[]): ParseTask | null {
  const myTasks = tasks.filter(t => String(t.materialId) === String(materialId));
  if (myTasks.length === 0) return null;

  // 1. 寻找 active 任务
  const activeTask = myTasks.find(t => ACTIVE_STATES.has(t.state || ''));
  if (activeTask) return activeTask;

  // 2. 寻找最近的任务
  return myTasks.sort((a, b) => {
    const timeA = new Date(a.updatedAt || a.createdAt || 0).getTime();
    const timeB = new Date(b.updatedAt || b.createdAt || 0).getTime();
    return timeB - timeA;
  })[0];
}

/**
 * 派生素材的任务视图视图 (P0 收口任务 1)
 */
export interface MaterialTaskView {
  materialId: string;
  title: string;
  fileName?: string;
  currentTask: ParseTask | null;
  latestTask: ParseTask | null;
  taskState?: string;
  bucket: TaskBucket;
  displayStatus: string;
  failureMessage?: string;
  taskUrl?: string;
  hasStateDrift: boolean;
  driftReason?: string;
}

const STATE_LABELS: Record<string, string> = TASK_STATUS_TERMS;

export function deriveMaterialTaskView(
  material: Material | undefined,
  tasks: ParseTask[],
  options?: { tasksLoaded?: boolean }
): MaterialTaskView {
  // P0 防御：material 未定义时返回安全默认值
  if (!material) {
    return {
      materialId: 'unknown',
      title: '加载中...',
      currentTask: null,
      latestTask: null,
      taskState: undefined,
      bucket: 'unknown',
      displayStatus: '加载中...',
      hasStateDrift: false,
    };
  }

  const tasksLoaded = options?.tasksLoaded ?? true; // 默认认为已加载完成，除非显式传入 false
  const currentTask = deriveCurrentTask(material.id, tasks);
  const bucket = deriveTaskBucket(currentTask?.state, currentTask?.stage);

  // 基础信息
  const view: MaterialTaskView = {
    materialId: String(material.id),
    title: material.title, // 优先使用 Material.title
    fileName: material.metadata?.fileName,
    currentTask,
    latestTask: currentTask,
    taskState: currentTask?.state,
    bucket,
    displayStatus: currentTask ? deriveTaskDisplayStatus(currentTask) : '待处理',
    failureMessage: currentTask?.errorMessage || currentTask?.message,
    taskUrl: currentTask ? `/tasks/${currentTask.id}` : undefined,
    hasStateDrift: false,
  };

  // P0 Task 6: 覆盖特定状态语义
  if (currentTask) {
    if (currentTask.state === 'failed') {
      if (currentTask.metadata?.mineruTaskId && currentTask.metadata?.mineruStatus === 'completed' && !currentTask.metadata?.parsedFilesCount) {
        view.displayStatus = 'MinerU 已完成，结果待接管';
      } else if (currentTask.stage === 'submit-failed-retryable' || currentTask.message?.includes('可重试')) {
        view.displayStatus = '提交 MinerU 失败，可重试';
      }
    }
  }

  // 状态漂移/需审计判断
  if (currentTask) {
    const ts = currentTask.state;
    // 1. 任务失败但素材仍显示处理中
    if ((ts === 'failed' || ts === 'canceled') && material.status === 'processing') {
      view.hasStateDrift = true;
      view.driftReason = '任务已终止但素材状态未同步';
    }
    // 2. 任务已完成但素材缺少必要字段
    if (ts === 'completed' && !material.metadata?.markdownObjectName) {
      view.hasStateDrift = true;
      view.driftReason = '任务显示完成但缺少解析产物';
    }
    // P0/P1 修复：3. 任务已完成但 Material 元数据仍残留 processing
    if (ts === 'completed' && material.metadata?.mineruStatus === 'processing') {
      view.hasStateDrift = true;
      view.driftReason = 'Material 元数据残留 processing';
    }
  } else if (tasksLoaded) {
    // 只有在任务列表确实加载完成，且依然找不到任务时，才报告漂移
    // 无任务但素材处于 processing
    if (material.status === 'processing') {
      view.hasStateDrift = true;
      view.driftReason = '暂无关联任务 / 无关联';
      // 强制把显示状态改为无关联，避免显示“正在解析”
      view.displayStatus = '暂无关联任务 / 无关联';
    } else if (material.metadata?.mineruStatus === 'processing') {
      view.hasStateDrift = true;
      view.driftReason = '暂无关联任务 / 无关联';
      view.displayStatus = '暂无关联任务 / 无关联';
    } else {
      view.displayStatus = '暂无关联任务 / 无关联';
    }
  }

  return view;
}
