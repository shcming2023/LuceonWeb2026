export const TASK_ACTION_TERMS = {
  retry: '重试',
  reparse: '重新解析',
  're-ai': '重新 AI',
  cancel: '取消',
};

export const TASK_ACTION_TOOLTIPS = {
  retry: '克隆新任务重跑',
  reparse: '仅重跑解析阶段',
  're-ai': '仅重跑 AI 元数据阶段',
  cancel: '取消该任务',
};

export const TASK_STATUS_TERMS = {
  uploading: '上传中',
  pending: '等待中',
  running: '解析中',
  'result-store': '产物落库',
  'ai-pending': '等待 AI',
  'ai-running': 'AI 分析中',
  'review-pending': '待复核',
  completed: '已完成',
  failed: '失败',
  canceled: '已取消',
};


export function getTaskStatusLabel(state: string | undefined): string {
  if (!state) return '未知';
  return TASK_STATUS_TERMS[state as keyof typeof TASK_STATUS_TERMS] || state;
}
