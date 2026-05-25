type PipelineMaterial = {
  metadata?: Record<string, any> | null;
  mineruStatus?: string | null;
  aiStatus?: string | null;
  title?: string | null;
};

type StepState = 'done' | 'current' | 'blocked' | 'pending';

export interface MainlinePipelineStep {
  key: string;
  label: string;
  state: StepState;
  detail: string;
  meta?: string | null;
}

export interface MainlinePipelineView {
  steps: MainlinePipelineStep[];
  completedCount: number;
  currentLabel: string;
  cleanVersion: string | null;
  raw2CleanDecision: string | null;
}

function asRecord(value: unknown): Record<string, any> {
  return value && typeof value === 'object' ? value as Record<string, any> : {};
}

function cleanString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null;
}

function stateIn(value: unknown, states: string[]) {
  return typeof value === 'string' && states.includes(value);
}

function step(key: string, label: string, state: StepState, detail: string, meta?: string | null): MainlinePipelineStep {
  return { key, label, state, detail, meta };
}

export function buildMainlinePipelineView({
  material,
  task,
}: {
  material?: PipelineMaterial | null;
  task?: { state?: string | null; stage?: string | null; metadata?: Record<string, any> | null; id?: string | number | null } | null;
}): MainlinePipelineView {
  const metadata = asRecord(material?.metadata);
  const taskMetadata = asRecord(task?.metadata);
  const cleanMaterial = asRecord(asRecord(metadata.cleanMaterials)['toc-rebuild']);
  const cleanTask = asRecord(asRecord(taskMetadata.cleanServiceJobs)['toc-rebuild']);
  const raw2cleanMaterial = asRecord(metadata.rawMaterial2CleanMaterial);
  const raw2cleanTask = asRecord(asRecord(taskMetadata.rawMaterial2CleanMaterialJobs)['raw-material-2-clean-material']);

  const hasPdf = Boolean(metadata.objectName || metadata.fileUrl || metadata.originalObjectName);
  const mineruDone = material?.mineruStatus === 'completed'
    || stateIn(task?.state, ['completed', 'review-pending', 'done'])
    || Boolean(metadata.markdownObjectName || metadata.markdownUrl || metadata.parsedFilesCount);
  const mineruRunning = material?.mineruStatus === 'processing' || stateIn(task?.state, ['processing', 'ai-pending', 'ai-running']);
  const aiDone = material?.aiStatus === 'analyzed'
    || stateIn(task?.state, ['review-pending', 'completed', 'done'])
    || Boolean(metadata.aiAnalyzedAt || metadata.aiClassification || metadata.aiTags);
  const aiRunning = material?.aiStatus === 'analyzing' || stateIn(task?.state, ['ai-running']);
  const cleanVersion = cleanString(cleanMaterial.latestVersion)
    || cleanString(cleanMaterial.assetVersion)
    || cleanString(cleanTask.assetVersion);
  const cleanJobId = cleanString(cleanTask.jobId) || cleanString(cleanMaterial.jobId);
  const cleanDone = Boolean(cleanVersion || cleanJobId || cleanMaterial.provenanceObjectName);
  const rawMaterialDone = Boolean(metadata.rawMaterial || metadata.markdownObjectName || metadata.parsedFilesCount || mineruDone);
  const raw2CleanDecision = cleanString(asRecord(raw2cleanMaterial.currentDecision).state)
    || cleanString(asRecord(raw2cleanTask.decision).state)
    || cleanString(raw2cleanTask.status);
  const raw2CleanAccepted = raw2CleanDecision === 'accepted';

  const steps = [
    step(
      'pdf',
      '提交 PDF',
      hasPdf ? 'done' : 'current',
      hasPdf ? '原始文件已入库' : '等待上传 PDF',
      cleanString(metadata.fileName) || null,
    ),
    step(
      'mineru',
      'MinerU 解析',
      mineruDone ? 'done' : mineruRunning ? 'current' : hasPdf ? 'pending' : 'blocked',
      mineruDone ? '解析产物已生成' : mineruRunning ? '解析进行中' : hasPdf ? '等待解析' : '需要先提交 PDF',
      metadata.parsedFilesCount != null ? `${metadata.parsedFilesCount} 个产物` : null,
    ),
    step(
      'ai',
      'AI 元数据识别',
      aiDone ? 'done' : aiRunning ? 'current' : mineruDone ? 'pending' : 'blocked',
      aiDone ? '元数据已识别' : aiRunning ? '识别进行中' : mineruDone ? '等待 AI 识别' : '需要 MinerU 产物',
      cleanString(metadata.subject) || cleanString(metadata.grade),
    ),
    step(
      'toc',
      '目录重建',
      cleanDone ? 'done' : aiDone ? 'current' : 'blocked',
      cleanDone ? 'toc-rebuild 已生成' : aiDone ? '待执行目录重建' : '需要 AI/解析基础',
      cleanVersion || cleanJobId,
    ),
    step(
      'raw',
      'Raw Material 输出',
      rawMaterialDone ? 'done' : cleanDone ? 'current' : 'blocked',
      rawMaterialDone ? '解析证据可追溯' : cleanDone ? '等待固化 Raw Material' : '需要解析与目录证据',
      cleanString(asRecord(metadata.rawMaterial).version) || (rawMaterialDone ? 'v1 evidence' : null),
    ),
    step(
      'clean',
      'Clean Material',
      raw2CleanAccepted ? 'done' : cleanDone ? 'current' : 'pending',
      raw2CleanAccepted ? 'candidate accepted，最终质量待收口' : cleanDone ? 'Raw2Clean/最终清洗待完成' : '待开发完成',
      raw2CleanDecision || null,
    ),
  ];

  const completedCount = steps.filter((item) => item.state === 'done').length;
  const currentLabel = steps.find((item) => item.state === 'current')?.label
    || steps.find((item) => item.state === 'pending')?.label
    || '主线已闭合';

  return {
    steps,
    completedCount,
    currentLabel,
    cleanVersion,
    raw2CleanDecision,
  };
}
