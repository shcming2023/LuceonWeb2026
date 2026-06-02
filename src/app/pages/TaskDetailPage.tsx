import { useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  ArrowLeft, RefreshCw, FileText, Clock, AlertTriangle, CheckCircle2, Loader2, XCircle,
  ChevronDown, ChevronRight, Brain, RotateCw, Sparkles, ShieldCheck,
  LayoutDashboard, File, Download, Database, Eye, MoreVertical, Boxes
} from 'lucide-react';
import { toast } from 'sonner';
import { MarkdownTab } from '../components/PreviewTabPanel';
import { MetadataTab } from '../components/MetadataTab';
import { PDFPreviewPanel } from '../components/PDFPreviewPanel';
import { renderMarkdown } from '../utils/markdown';
import { TASK_ACTION_TERMS, TASK_ACTION_TOOLTIPS, getTaskStatusLabel } from '../utils/taskTerms';
import { deriveMineruProgressLine, deriveTaskDisplayStatus } from '../utils/taskView';
import { DropdownMenu } from '../components/DropdownMenu';
import { CleanMaterialSummaryCard } from '../components/CleanMaterialSummaryCard';
import { buildCleanMaterialView } from '../utils/cleanMaterialView';
import { MainlinePipelinePanel } from '../components/MainlinePipelinePanel';
import { buildMainlinePipelineView } from '../utils/mainlinePipeline';

/**
 * ParseTask 详情数据结构
 */
interface ParseTask {
  id: string;
  materialId?: string;
  engine?: string;
  stage?: string;
  state?: string;
  progress?: number;
  message?: string;
  errorMessage?: string;
  createdAt?: string;
  updatedAt?: string;
  completedAt?: string;
  metadata?: Record<string, any>;
  optionsSnapshot?: Record<string, any>;
}

/**
 * 关联 Material 的资源状态摘要（用于动作按钮禁用判断）
 */
interface ResourceStatus {
  materialExists: boolean;
  originalExists: boolean;    // Material 有 objectName
  markdownExists: boolean;    // Material 有 markdownObjectName 或 task.metadata.markdownObjectName
  loaded: boolean;
}

/**
 * TaskEvent 事件日志数据结构
 */
interface TaskEvent {
  id: string;
  taskId: string;
  taskType?: string;
  level?: string;
  event?: string;
  message?: string;
  payload?: Record<string, unknown>;
  createdAt?: string;
}

/**
 * AiMetadataJob 数据结构
 */
interface AiMetadataJob {
  id: string;
  materialId?: string;
  parseTaskId: string;
  state: string;
  progress?: number;
  providerId?: string;
  model?: string;
  inputMarkdownObjectName?: string;
  confidence?: number | null;
  needsReview?: boolean;
  result?: Record<string, unknown>;
  errorMessage?: string;
  createdAt?: string;
  updatedAt?: string;
}

/**
 * 根据状态返回对应的样式类名和图标
 * @param state - 任务状态字符串
 * @returns 包含 badgeClass 和 Icon 组件的对象
 */
function getStateStyle(state: string | undefined) {
  switch (state) {
    case 'uploading':
    case 'pending':
      return { badgeClass: 'bg-slate-100 text-slate-700', Icon: Clock, animate: false };
    case 'running':
    case 'result-store':
    case 'ai-pending':
    case 'ai-running':
      return { badgeClass: 'bg-blue-100 text-blue-700 border border-blue-200', Icon: Loader2, animate: true };
    case 'review-pending':
      return { badgeClass: 'bg-amber-100 text-amber-700 border border-amber-200', Icon: ShieldCheck, animate: false };
    case 'completed':
      return { badgeClass: 'bg-green-100 text-green-700', Icon: CheckCircle2, animate: false };
    case 'failed':
      return { badgeClass: 'bg-red-100 text-red-700', Icon: XCircle, animate: false };
    case 'canceled':
      return { badgeClass: 'bg-gray-100 text-gray-500 border border-gray-200', Icon: XCircle, animate: false };
    default:
      return { badgeClass: 'bg-slate-100 text-slate-700', Icon: Clock, animate: false };
  }
}

/**
 * 根据 AI Job 状态返回样式
 * @param state - AI Job 状态字符串
 * @returns 包含 badgeClass 的对象
 */
function getAiJobStateStyle(state: string | undefined) {
  switch (state) {
    case 'running':
      return { badgeClass: 'bg-purple-100 text-purple-700 border border-purple-200', icon: '⏳' };
    case 'confirmed':
    // 兼容旧数据
    case 'succeeded':
      return { badgeClass: 'bg-green-100 text-green-700', icon: '✅' };
    case 'review-pending':
      return { badgeClass: 'bg-amber-100 text-amber-700 border border-amber-200', icon: '🔍' };
    case 'failed':
      return { badgeClass: 'bg-red-100 text-red-700', icon: '❌' };
    case 'pending':
    default:
      return { badgeClass: 'bg-amber-100 text-amber-700', icon: '🕐' };
  }
}

function getAiJobOutcome(job: AiMetadataJob) {
  const result = job.result || {};
  const provider = String(result.aiClassificationProvider || job.providerId || '').toLowerCase();
  const deterministicRepairSucceeded = Boolean(
    result.aiClassificationDeterministicRepairSucceeded ||
    result.deterministicRepairSucceeded ||
    result.aiClassificationRepairSucceeded
  );
  const degradedReason = String(result.aiClassificationDegradedReason || result.degradedReason || '');
  const failureKind = String((result.rawTrace as any)?.firstPass?.failureKind || result.failureKind || '');

  if (job.state === 'failed') {
    return {
      label: 'AI 识别失败',
      detail: job.errorMessage || failureKind || 'AI 任务失败，需重新触发或排查模型服务。',
      className: 'text-red-700 bg-red-50 border-red-100'
    };
  }

  if (provider === 'skeleton' || degradedReason.includes('skeleton')) {
    return {
      label: '骨架兜底结果',
      detail: degradedReason || '当前结果来自骨架兜底，不应视为真实 AI 识别完成。',
      className: 'text-amber-700 bg-amber-50 border-amber-100'
    };
  }

  if (job.state === 'review-pending' && deterministicRepairSucceeded) {
    return {
      label: 'AI 已完成 · 自动规范化 · 待复核',
      detail: 'Ollama 已返回可用草稿，结构问题已确定性修复；这是待人工复核，不是依赖阻塞。',
      className: 'text-emerald-700 bg-emerald-50 border-emerald-100'
    };
  }

  if (job.state === 'review-pending') {
    return {
      label: 'AI 已完成 · 待复核',
      detail: job.needsReview || job.confidence == null || job.confidence < 0.8
        ? '结果需要人工复核或补全分类置信度。'
        : '结果等待人工确认。',
      className: 'text-amber-700 bg-amber-50 border-amber-100'
    };
  }

  if (['confirmed', 'succeeded', 'completed'].includes(job.state)) {
    return {
      label: 'AI 已确认',
      detail: 'AI 元数据识别已完成并确认。',
      className: 'text-green-700 bg-green-50 border-green-100'
    };
  }

  if (job.state === 'running') {
    return {
      label: 'AI 识别进行中',
      detail: '正在调用 AI 元数据识别。',
      className: 'text-purple-700 bg-purple-50 border-purple-100'
    };
  }

  return {
    label: '等待 AI 识别',
    detail: 'AI 元数据任务已创建，等待执行。',
    className: 'text-slate-700 bg-slate-50 border-slate-100'
  };
}

/**
 * 根据事件 level 返回时间线节点样式
 * @param level - 事件级别 (info / error / warn)
 * @returns 包含 dotClass 和 textClass 的对象
 */
function getEventStyle(level: string | undefined) {
  if (level === 'error') return { dotClass: 'bg-red-500', textClass: 'text-red-700' };
  if (level === 'warn') return { dotClass: 'bg-yellow-500', textClass: 'text-yellow-700' };
  return { dotClass: 'bg-blue-500', textClass: 'text-slate-700' };
}

/**
 * TaskDetailPage - 任务详情页
 *
 * 展示单个 ParseTask 的完整状态信息、关联 AI Metadata Job 和事件时间线。
 * 路由：/tasks/:id
 */
export function TaskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [task, setTask] = useState<ParseTask | null>(null);
  const [material, setMaterial] = useState<any | null>(null);
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [aiJobs, setAiJobs] = useState<AiMetadataJob[]>([]);
  const [initialLoading, setInitialLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [optionsExpanded, setOptionsExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'markdown' | 'pdf' | 'metadata' | 'events'>('overview');
  const [eventFilter, setEventFilter] = useState<'all' | 'key' | 'error' | 'system'>('all');
  const [tocRebuildRunning, setTocRebuildRunning] = useState(false);
  const hasLoadedOnceRef = useRef(false);

  // ── Markdown 预览相关状态 ──────────────────────────────────
  const [mdContent, setMdContent] = useState('');
  const [mdLoading, setMdLoading] = useState(false);
  const [mdError, setMdError] = useState('');

  const [rebuiltMdContent, setRebuiltMdContent] = useState('');
  const [rebuiltMdLoading, setRebuiltMdLoading] = useState(false);
  const [rebuiltMdError, setRebuiltMdError] = useState('');

  // ── 元数据编辑相关状态 ────────────────────────────────────
  const [metaForm, setMetaForm] = useState({
    language: '',
    grade: '',
    subject: '',
    country: '',
    type: '',
    summary: '',
  });

  const updateMeta = (key: keyof typeof metaForm, val: string) =>
    setMetaForm((prev) => ({ ...prev, [key]: val }));

  useEffect(() => {
    const hash = location.hash.replace(/^#/, '');
    const hashToTab: Record<string, typeof activeTab> = {
      review: 'metadata',
      metadata: 'metadata',
      markdown: 'markdown',
      pdf: 'pdf',
      events: 'events',
      overview: 'overview',
    };
    if (hash && hashToTab[hash]) {
      setActiveTab(hashToTab[hash]);
    }
  }, [location.hash]);

  const isMetaDirty = !!material && (
    metaForm.language !== (material.metadata?.language || '')
    || metaForm.grade !== (material.metadata?.grade || '')
    || metaForm.subject !== (material.metadata?.subject || '')
    || metaForm.country !== (material.metadata?.country || '')
    || metaForm.type !== (material.metadata?.type || '')
    || metaForm.summary !== (material.metadata?.summary || '')
  );
  const [resourceStatus, setResourceStatus] = useState<ResourceStatus>({
    materialExists: true,
    originalExists: true,
    markdownExists: true,
    loaded: false,
  });

  const cleanMaterialView = useMemo(
    () => buildCleanMaterialView({ material, task }),
    [material, task],
  );
  const tocRebuildJob = task?.metadata?.cleanServiceJobs?.['toc-rebuild'] as any | undefined;
  const tocRebuildJobRunning = ['running', 'pending'].includes(String(tocRebuildJob?.status || tocRebuildJob?.cleanState || ''));
  const rebuiltMarkdownArtifactKey = useMemo(
    () => cleanMaterialView.artifacts
      .map((artifact) => `${artifact.role}:${artifact.bucket || ''}:${artifact.object}:${artifact.sha256 || ''}`)
      .join('|'),
    [cleanMaterialView.artifacts],
  );

  /**
   * 从后端加载任务详情、事件日志、关联 AI Jobs 和 Material 资源状态
   */
  const fetchData = async (options?: { background?: boolean }) => {
    if (!id) return;
    const background = options?.background === true;
    const shouldUseInitialLoading = !background && !hasLoadedOnceRef.current;

    if (shouldUseInitialLoading) {
      setInitialLoading(true);
    } else {
      setRefreshing(true);
    }

    if (!background) setNotFound(false);
    try {
      const [taskRes, eventsRes, aiJobsRes] = await Promise.all([
        fetch(`/__proxy/db/tasks/${encodeURIComponent(id)}`),
        fetch(`/__proxy/db/task-events?taskId=${encodeURIComponent(id)}`),
        fetch(`/__proxy/db/ai-metadata-jobs?parseTaskId=${encodeURIComponent(id)}`),
      ]);

      if (taskRes.status === 404) {
        setNotFound(true);
        setTask(null);
        setEvents([]);
        setAiJobs([]);
        return;
      }
      if (!taskRes.ok) throw new Error(`获取任务失败: HTTP ${taskRes.status}`);

      const taskData = await taskRes.json();
      setTask(taskData);
      hasLoadedOnceRef.current = true;

      if (eventsRes.ok) {
        const eventsData = await eventsRes.json();
        setEvents(Array.isArray(eventsData) ? eventsData : []);
      }

      if (aiJobsRes.ok) {
        const aiJobsData = await aiJobsRes.json();
        setAiJobs(Array.isArray(aiJobsData) ? aiJobsData : []);
      }

      // 加载关联 Material 信息，判断资源状态
      if (taskData.materialId) {
        try {
          const matRes = await fetch(`/__proxy/db/materials/${encodeURIComponent(String(taskData.materialId))}`);
          if (matRes.status === 404) {
            setResourceStatus({ materialExists: false, originalExists: false, markdownExists: false, loaded: true });
            setMaterial(null);
          } else if (matRes.ok) {
            const mat = await matRes.json();
            setMaterial(mat);
            setResourceStatus({
              materialExists: true,
              originalExists: !!(mat.metadata?.objectName),
              markdownExists: !!(mat.metadata?.markdownObjectName || taskData.metadata?.markdownObjectName),
              loaded: true,
            });
          } else {
            setResourceStatus({ materialExists: false, originalExists: false, markdownExists: false, loaded: true });
            setMaterial(null);
          }
        } catch {
          setResourceStatus({ materialExists: false, originalExists: false, markdownExists: false, loaded: true });
          setMaterial(null);
        }
      } else {
        // 无 materialId 的任务
        setResourceStatus({ materialExists: false, originalExists: false, markdownExists: false, loaded: true });
        setMaterial(null);
      }
    } catch (err) {
      toast.error('加载任务详情失败', { description: String(err) });
    } finally {
      if (shouldUseInitialLoading) setInitialLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    hasLoadedOnceRef.current = false;
    setInitialLoading(true);
    setRefreshing(false);
    setNotFound(false);
    setTask(null);
    setMaterial(null);
    setEvents([]);
    setAiJobs([]);
    fetchData();
  }, [id]);

  // ── 元数据回填监听 ──────────────────────────────────────────
  useEffect(() => {
    if (!material) return;
    setMetaForm({
      language: material.metadata?.language || '',
      grade: material.metadata?.grade || '',
      subject: material.metadata?.subject || '',
      country: material.metadata?.country || '',
      type: material.metadata?.type || '',
      summary: material.metadata?.summary || '',
    });
  }, [
    material?.id,
    material?.metadata?.language,
    material?.metadata?.grade,
    material?.metadata?.subject,
    material?.metadata?.country,
    material?.metadata?.type,
    material?.metadata?.summary,
  ]);

  // ── Markdown 内容获取（参考 AssetDetailPage） ──────────────
  useEffect(() => {
    const mdObj = material?.metadata?.markdownObjectName || task?.metadata?.markdownObjectName;
    const mdUrl = material?.metadata?.markdownUrl;
    if (!id || (!mdObj && !mdUrl)) return;

    setMdLoading(true);
    setMdError('');

    (async () => {
      try {
        let url = mdUrl;
        if (!url && mdObj) {
          const r = await fetch(`/__proxy/upload/presign?objectName=${encodeURIComponent(mdObj)}`, { cache: 'no-store' });
          const d = await r.json();
          url = d?.url;
        }
        if (!url) throw new Error('无法获取 Markdown 访问地址');
        let res = await fetch(url, { cache: 'no-store' });
        if (res.status === 403 && mdObj) {
          const r = await fetch(`/__proxy/upload/presign?objectName=${encodeURIComponent(mdObj)}`, { cache: 'no-store' });
          const d = await r.json();
          const retryUrl = d?.url;
          if (retryUrl) res = await fetch(retryUrl, { cache: 'no-store' });
        }
        if (!res.ok) throw new Error(`读取失败: HTTP ${res.status}`);
        setMdContent(await res.text());
      } catch (e) {
        setMdError(e instanceof Error ? e.message : String(e));
      } finally {
        setMdLoading(false);
      }
    })();
  }, [id, material?.metadata?.markdownObjectName, material?.metadata?.markdownUrl, task?.metadata?.markdownObjectName]);

  // ── Rebuilt Markdown 内容获取 ──────────────────────────────────
  useEffect(() => {
    const rebuiltArtifact = cleanMaterialView.artifacts.find(a => a.role === 'rebuilt_markdown');
    if (!id || !rebuiltArtifact?.object) return;

    setRebuiltMdLoading(true);
    setRebuiltMdError('');

    (async () => {
      try {
        const bucket = rebuiltArtifact.bucket || '';
        const url = `/__proxy/upload/proxy-file?objectName=${encodeURIComponent(rebuiltArtifact.object)}${bucket ? `&bucket=${encodeURIComponent(bucket)}` : ''}`;
        let res = await fetch(url, { cache: 'no-store' });
        if (!res.ok) throw new Error(`读取失败: HTTP ${res.status}`);
        setRebuiltMdContent(await res.text());
      } catch (e) {
        setRebuiltMdError(e instanceof Error ? e.message : String(e));
      } finally {
        setRebuiltMdLoading(false);
      }
    })();
  }, [id, rebuiltMarkdownArtifactKey]);

  // ── SSE 增量刷新（PRD v0.4 §10.2.2）──────────────────────
  const sseRef = useRef<EventSource | null>(null);
  const sseRefreshTimerRef = useRef<number | null>(null);
  useEffect(() => {
    if (!id) return;
    if (sseRef.current) return;
    try {
      const es = new EventSource(`/__proxy/upload/tasks/stream?taskId=${encodeURIComponent(id)}`);
      sseRef.current = es;
      es.addEventListener('task-update', () => {
        if (sseRefreshTimerRef.current != null) window.clearTimeout(sseRefreshTimerRef.current);
        sseRefreshTimerRef.current = window.setTimeout(() => {
          sseRefreshTimerRef.current = null;
          fetchData({ background: true });
        }, 1000);
      });
      es.onerror = () => { /* 自动重连 */ };
    } catch (e) {
      console.warn('[TaskDetailPage] SSE init failed', e);
    }
    return () => {
      sseRef.current?.close();
      sseRef.current = null;
      if (sseRefreshTimerRef.current != null) window.clearTimeout(sseRefreshTimerRef.current);
      sseRefreshTimerRef.current = null;
    };
  }, [id]);

  useEffect(() => {
    if (!id || !tocRebuildJobRunning) return;
    const timer = window.setInterval(() => {
      fetchData({ background: true });
    }, 5000);
    return () => window.clearInterval(timer);
  }, [id, tocRebuildJobRunning]);

  // ── 任务动作（Retry/Reparse/Re-AI/Cancel）──────────────
  const callAction = async (action: 'retry' | 'reparse' | 're-ai' | 'cancel') => {
    if (!id) return;
    try {
      const res = await fetch(`/__proxy/upload/tasks/${encodeURIComponent(id)}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const payload = await res.json().catch(() => ({} as any));
      if (!res.ok) throw new Error(payload?.error || `HTTP ${res.status}`);
      const verb = `已${TASK_ACTION_TERMS[action]}`;
      toast.success(verb, { description: payload?.newTaskId ? `新任务 ${payload.newTaskId}` : undefined });
      if (action === 'retry' && payload?.newTaskId) {
        navigate(`/tasks/${encodeURIComponent(payload.newTaskId)}`);
      } else {
        fetchData({ background: true });
      }
    } catch (err) {
      toast.error(`${action} 失败`, { description: String(err) });
    }
  };

  // ── 审核提交（W2-2） ────────────────────────────────────────
  const handleReview = async () => {
    if (!id) return;
    try {
      const res = await fetch(`/__proxy/upload/tasks/${encodeURIComponent(id)}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metadata: { ...metaForm },
          notes: '人工审核确认',
        }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.error || `HTTP ${res.status}`);
      toast.success('审核通过', { description: `任务已进入 completed` });
      fetchData({ background: true });
    } catch (err) {
      toast.error('审核提交失败', { description: String(err) });
    }
  };

  const handleSaveMetadata = async () => {
    const materialId = task?.materialId;
    if (!materialId) {
      toast.error('保存元数据失败', { description: '当前任务没有关联 materialId' });
      return;
    }
    try {
      const res = await fetch(`/__proxy/db/materials/${encodeURIComponent(String(materialId))}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metadata: { ...metaForm },
          updateTime: Date.now(),
        }),
      });
      const payload = await res.json().catch(() => ({} as any));
      if (!res.ok) throw new Error(payload?.error || `HTTP ${res.status}`);
      toast.success('元数据已保存');
      fetchData({ background: true });
    } catch (err) {
      toast.error('保存元数据失败', { description: String(err) });
    }
  };

  const handleTocRebuild = async (options?: { cleanserviceRerun?: boolean }) => {
    if (!id) return;
    setTocRebuildRunning(true);
    try {
      const res = await fetch(`/__proxy/upload/tasks/${encodeURIComponent(id)}/toc-rebuild`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(options?.cleanserviceRerun
          ? { trigger: 'operator-manual', mode: 'cleanservice-rerun', cleanservice: true, forceNewVersion: true, tocRebuildMode: 'bounded' }
          : { trigger: 'operator-manual' }),
      });
      const payload = await res.json().catch(() => ({} as any));
      if (!res.ok) throw new Error(payload?.error || `HTTP ${res.status}`);
      if (payload?.accepted || payload?.status === 'running') {
        toast.success(options?.cleanserviceRerun ? 'Popo 目录重建已提交后台执行' : '目录重建已提交后台执行', {
          description: payload?.jobId || payload?.prefix,
        });
      } else {
        toast.success(options?.cleanserviceRerun ? 'Popo 目录重建已完成' : '目录重建已完成', { description: payload?.prefix || payload?.jobId });
      }
      await fetchData({ background: true });
    } catch (err) {
      toast.error('目录重建失败', { description: String(err) });
    } finally {
      setTocRebuildRunning(false);
    }
  };

  // ── ZIP 下载（W2-3） ────────────────────────────────────────
  const handleDownloadZip = async () => {
    const materialId = task?.materialId;
    if (!materialId) return;
    try {
      toast.info('正在打包解析产物...');
      const r = await fetch('/__proxy/upload/parsed-zip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ materialId }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({ error: `HTTP ${r.status}` }));
        throw new Error(err.error || `HTTP ${r.status}`);
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `parsed-${material?.title || materialId}.zip`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('解析产物 ZIP 已下载');
    } catch (err) {
      toast.error(`下载失败: ${String(err)}`);
    }
  };

  // ─── 加载中 ──────────────────────────────────────────────────
  if (initialLoading) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <p className="text-sm text-slate-500">加载任务详情...</p>
        </div>
      </div>
    );
  }

  // ─── 未找到 ──────────────────────────────────────────────────
  if (notFound || !task) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-3 text-center">
          <AlertTriangle className="w-10 h-10 text-amber-400" />
          <h2 className="text-lg font-semibold text-slate-800">任务不存在</h2>
          <p className="text-sm text-slate-500">ID: {id}</p>
          <button
            onClick={() => navigate('/tasks')}
            className="mt-2 px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
          >
            ← 返回任务列表
          </button>
        </div>
      </div>
    );
  }

  // ─── 正常渲染 ────────────────────────────────────────────────
  const stateStyle = getStateStyle(task.state);

  // 资源状态感知：根据 Material 和文件存在性决定按钮是否可用
  const canRetry = task.state === 'failed' && resourceStatus.materialExists && resourceStatus.originalExists;
  const canReparse = ['failed', 'completed', 'review-pending', 'canceled'].includes(String(task.state))
    && resourceStatus.materialExists && resourceStatus.originalExists;
  const canReAi = ['failed', 'completed', 'review-pending'].includes(String(task.state))
    && resourceStatus.materialExists && resourceStatus.markdownExists;
  const canCancel = ['pending', 'running', 'ai-pending', 'ai-running', 'review-pending', 'result-store'].includes(String(task.state)) ||
                    ['mineru-queued', 'mineru-processing', 'submit-failed-retryable', 'result-fetching'].includes(String(task.stage));
  const taskDisplayStatus = deriveTaskDisplayStatus(task as any);
  const mineruProgressLine = deriveMineruProgressLine(task as any);
  const mainlineView = buildMainlinePipelineView({ material, task });
  const canTocRebuild = ['review-pending', 'completed'].includes(String(task.state))
    && resourceStatus.materialExists
    && resourceStatus.markdownExists
    && !cleanMaterialView.present
    && !tocRebuildJobRunning;
  const allowedPopoStates = ['review-pending', 'completed', 'failed', 'canceled'];
  const isPopoStateAllowed = allowedPopoStates.includes(String(task.state));
  const hasZip = Boolean(material?.metadata?.zipObjectName || task.metadata?.zipObjectName);

  const canPopoRerun = isPopoStateAllowed
    && resourceStatus.materialExists
    && hasZip
    && !tocRebuildJobRunning;

  const popoRerunDisabledReason = (() => {
    if (canPopoRerun) return '调用 MinerU-Popo CleanService 异步重跑目录重建（使用新版本）';
    if (!resourceStatus.materialExists) return 'Popo 重新目录重建不可用：关联的原始资料 (Material) 已被删除';
    if (!isPopoStateAllowed) return `Popo 重新目录重建不可用：任务当前状态为 ${getTaskStatusLabel(task.state)}，仅支持 review-pending/completed/failed/canceled`;
    if (!hasZip) return 'Popo 重新目录重建不可用：缺少 MinerU 结果 zip 产物，无法重新清洗';
    if (tocRebuildJobRunning) return 'Popo 重新目录重建不可用：当前已有一个正在运行中或等待中的重建任务';
    return 'Popo 重新目录重建不可用：未满足前置条件';
  })();

  const tocRebuildDisabledReason = cleanMaterialView.present
    ? '当前任务已存在目录重建结果'
    : (canTocRebuild ? '基于 MinerU Markdown 手动生成目录重建 Clean Material' : '需要任务进入待复核/完成并具备 Markdown 产物');

  // 资源缺失提示文案
  const resourceWarning = (() => {
    if (!resourceStatus.loaded) return null;
    if (!resourceStatus.materialExists) return '关联的原始资料已被删除，无法重跑。请重新上传文件创建新任务';
    if (!resourceStatus.originalExists) return '原始文件已删除，无法重新解析。请重新上传文件';
    if (!resourceStatus.markdownExists && ['completed', 'review-pending', 'failed'].includes(String(task.state))) {
      return 'Markdown 产物缺失，无法重跑 AI 识别。请先执行 Reparse';
    }
    return null;
  })();

  return (
    <div className="p-6 h-full overflow-y-auto space-y-6">
      {/* ── 顶部导航栏与面包屑 ────────────────────────────────────────── */}
      <div className="flex flex-col gap-4 mb-4">
        <nav className="flex items-center text-sm text-slate-500 font-medium">
          <button onClick={() => navigate('/tasks')} className="hover:text-blue-600 transition-colors">任务管理</button>
          <ChevronRight className="w-4 h-4 mx-2 text-slate-300" />
          <span className="text-slate-800">任务详情</span>
        </nav>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/tasks')}
              className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
              title="返回任务列表"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                任务详情
              </h1>
              <p className="text-xs text-slate-400 mt-1 font-mono tracking-tight">{task.id}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchData({ background: true })}
              className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-60 shadow-sm"
              title="刷新"
              disabled={refreshing}
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Layer 1: Current Conclusion */}
        {(() => {
          const isReviewPending = task.state === 'review-pending';
          const isCompleted = task.state === 'completed';

          const completedItems = [
            'PDF',
            resourceStatus.markdownExists && 'MinerU',
            aiJobs.some(j => ['completed', 'succeeded', 'confirmed', 'review-pending'].includes(j.state)) && 'AI Metadata',
            cleanMaterialView.present && '目录重建',
            mainlineView.steps.find(s => s.key === 'raw')?.state === 'done' && 'Raw Material',
            (material?.metadata?.rawMaterial2CleanMaterial as any)?.currentDecision?.state === 'accepted' && 'Clean Material',
          ].filter(Boolean);

          const pendingItems = [
            !resourceStatus.markdownExists && 'MinerU',
            aiJobs.length === 0 && 'AI Metadata',
            !cleanMaterialView.present && '目录重建',
            mainlineView.steps.find(s => s.key === 'raw')?.state !== 'done' && 'Raw Material',
            (!material?.metadata?.rawMaterial2CleanMaterial || (material?.metadata?.rawMaterial2CleanMaterial as any)?.currentDecision?.state !== 'accepted') && 'Clean Material 最终接受',
          ].filter(Boolean);

          let nextAction = '等待流水线系统处理';
          if (isReviewPending) nextAction = '检查 Markdown 对比 + 确认元数据';
          else if (isCompleted) nextAction = '检查最终产物质量';
          else if (['failed', 'canceled'].includes(task.state || '')) nextAction = '排查错误日志或重试';

          return (
            <div className="bg-slate-900 border border-slate-800 rounded-lg shadow-md p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              <div className="flex-1">
                <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                  <LayoutDashboard className="w-5 h-5 text-blue-400" />
                  当前结论 (Current Conclusion)
                </h2>
                <div className="space-y-2 text-sm">
                  <div className="flex gap-3">
                    <span className="text-slate-400 w-16">当前：</span>
                    <span className="text-white font-medium">{getTaskStatusLabel(task.state)} ({task.stage || '无'})</span>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-slate-400 w-16">已完成：</span>
                    <span className="text-emerald-400 font-medium">{completedItems.join(' / ') || '无'}</span>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-slate-400 w-16">未完成：</span>
                    <span className="text-amber-400 font-medium">{pendingItems.join(' / ') || '无'}</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 w-full md:w-auto md:min-w-[320px]">
                <p className="text-xs text-slate-400 mb-2 uppercase font-semibold tracking-wider">下一步行动 (Next Action)</p>
                <p className="text-lg font-bold text-blue-400 mb-4">{nextAction}</p>
                <div className="flex flex-wrap gap-2">
                  {isReviewPending && (
                    <button onClick={handleReview} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-bold flex items-center justify-center gap-2 transition-colors">
                      <ShieldCheck className="w-4 h-4" /> 审核通过
                    </button>
                  )}
                  <DropdownMenu
                    trigger={({ open, setOpen }) => (
                      <button onClick={() => setOpen(!open)} className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded text-sm font-medium transition-colors flex items-center gap-2 whitespace-nowrap">
                        <MoreVertical className="w-4 h-4" /> 更多操作
                      </button>
                    )}
                    items={[
                      { kind: 'item', label: `重试 (${TASK_ACTION_TERMS.retry})`, disabled: !canRetry, onClick: () => callAction('retry') },
                      { kind: 'item', label: `重新解析 (${TASK_ACTION_TERMS.reparse})`, disabled: !canReparse, onClick: () => callAction('reparse') },
                      { kind: 'item', label: `重跑AI (${TASK_ACTION_TERMS['re-ai']})`, disabled: !canReAi, onClick: () => callAction('re-ai') },
                      { kind: 'item', label: '目录重建 (TocRebuild)', disabled: !canTocRebuild || tocRebuildRunning, onClick: () => handleTocRebuild() },
                      { kind: 'item', label: '调用 Popo 重新目录重建', disabled: !canPopoRerun || tocRebuildRunning, onClick: () => handleTocRebuild({ cleanserviceRerun: true }), title: popoRerunDisabledReason || '默认使用 bounded MPS profile' },
                      { kind: 'item', label: '下载产物 ZIP', disabled: !(['completed', 'review-pending', 'failed'].includes(String(task.state)) && resourceStatus.markdownExists), onClick: handleDownloadZip },
                      { kind: 'item', label: '取消任务', danger: true, disabled: !canCancel, onClick: () => {
                          const mineruTaskId = task.metadata?.mineruTaskId;
                          const msg = mineruTaskId ? '确定要取消吗？' : '确定要取消该任务吗？';
                          if (window.confirm(msg)) callAction('cancel');
                        }
                      }
                    ]}
                  />
                  {tocRebuildJob && (
                    <div className="basis-full rounded border border-slate-700 bg-slate-900/60 px-3 py-2 text-xs text-slate-300">
                      <span className="font-semibold text-slate-100">目录重建：</span>
                      <span>{tocRebuildJob.productLabel || tocRebuildJob.status || tocRebuildJob.cleanState}</span>
                      {tocRebuildJob.jobId && <span className="ml-2 text-slate-500">{tocRebuildJob.jobId}</span>}
                      {tocRebuildJob.error?.message && <span className="block mt-1 text-red-300">{tocRebuildJob.error.message}</span>}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })()}
      </div>

      {/* ── 资源缺失警告 ────────────────────────────────────── */}
      {resourceWarning && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-amber-800">资源不可用</p>
            <p className="text-sm text-amber-700 mt-1">{resourceWarning}</p>
          </div>
        </div>
      )}

      {/* ── Tabs 切换栏 (W2-1) ────────────────────────────── */}
      <div className="flex border-b border-slate-200 gap-1 bg-white px-1 pt-1 rounded-t-lg">
        {[
          { id: 'overview', label: '概览', icon: LayoutDashboard },
          { id: 'markdown', label: 'Markdown', icon: FileText },
          { id: 'pdf', label: '原件预览', icon: File },
          { id: 'metadata', label: '元数据', icon: Database },
          { id: 'events', label: '事件日志', icon: Clock },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as any)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-semibold border-b-2 transition-all ${
              activeTab === t.id
                ? 'border-blue-600 text-blue-700 bg-blue-50/50 rounded-t-md'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab 内容面板 ────────────────────────────────────── */}
      <div className="min-h-0 flex-1">
        {activeTab === 'overview' && (
          <div className="space-y-6 h-full flex flex-col">
            {/* Layer 2: Primary Inspection Surface */}
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex flex-col h-[700px] shrink-0">
              <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <Eye className="w-4 h-4 text-blue-500" />
                  主检视区 (Primary Inspection Surface)
                </h2>
                <div className="text-xs text-slate-500">PDF 原件 | MinerU Markdown | Rebuilt Markdown</div>
              </div>

              <div className="flex-1 min-h-0 flex">
                {/* PDF Pane */}
                <div className="flex-[0.8] flex flex-col border-r border-slate-200 bg-slate-100">
                  <div className="px-3 py-1.5 bg-slate-200/50 border-b border-slate-200 text-xs font-bold text-slate-700 flex items-center gap-1.5">
                    <File className="w-3.5 h-3.5 text-red-500" />
                    PDF 原件
                  </div>
                  <div className="flex-1 min-h-0 overflow-hidden relative">
                    <PDFPreviewPanel objectName={material?.metadata?.objectName} />
                  </div>
                </div>

                {/* MinerU Markdown Pane */}
                <div className="flex-1 flex flex-col border-r border-slate-200 bg-white">
                  <div className="px-3 py-1.5 bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-700 flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-blue-500" />
                    MinerU Markdown (full.md)
                  </div>
                  <div className="flex-1 min-h-0 overflow-y-auto">
                    <MarkdownTab content={mdContent} loading={mdLoading} error={mdError} />
                  </div>
                </div>

                {/* Rebuilt Markdown Pane */}
                <div className="flex-1 flex flex-col bg-white">
                  <div className="px-3 py-1.5 bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-700 flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-emerald-500" />
                    Rebuilt Markdown (rebuilt_markdown.md)
                  </div>
                  <div className="flex-1 min-h-0 overflow-y-auto">
                    {cleanMaterialView.artifacts.some(a => a.role === 'rebuilt_markdown') ? (
                      <MarkdownTab content={rebuiltMdContent} loading={rebuiltMdLoading} error={rebuiltMdError} />
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-3 p-6 text-center bg-slate-50/30">
                        <FileText className="w-8 h-8 opacity-20" />
                        <p className="text-sm font-medium">暂无完整重建 Markdown，仅有目录树产物</p>
                        <p className="text-xs opacity-70 max-w-[200px]">系统尚未生成 rebuilt_markdown.md。请勿将 readable_tree 当作全文使用。</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Layer 3: Evidence Drawer */}
            <details className="group bg-slate-50 border border-slate-200 rounded-lg shadow-sm shrink-0 mb-8">
              <summary className="px-5 py-4 cursor-pointer font-semibold text-slate-700 hover:text-slate-900 list-none flex items-center justify-between select-none">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-slate-400" />
                  证据抽屉 (Evidence Drawer) - 包含全部技术与诊断细节
                </div>
                <div className="w-5 h-5 rounded-full border border-slate-200 flex items-center justify-center text-slate-400 group-open:rotate-180 transition-transform">
                  <ChevronDown className="w-4 h-4" />
                </div>
              </summary>
              <div className="p-5 pt-0 border-t border-slate-200 space-y-6 mt-4">
            {/* Asset Identity & Next Action */}
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                  {material?.title || material?.metadata?.fileName || material?.metadata?.objectName || task?.metadata?.fileName || task.id}
                </h2>
                <div className="flex items-center gap-3 mt-2 text-sm">
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-medium rounded-full ${stateStyle.badgeClass}`}>
                    <stateStyle.Icon className={`w-3.5 h-3.5 ${stateStyle.animate ? 'animate-spin' : ''}`} />
                    {getTaskStatusLabel(task.state)}
                  </span>
                  {task.stage && (
                    <span className="text-slate-500 font-medium">阶段: <span className="text-slate-700">{task.stage}</span></span>
                  )}
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-400 mb-1 uppercase font-semibold tracking-wider">Next Operator Action</p>
                <p className="text-sm font-bold text-blue-700 bg-blue-50 px-3 py-1.5 rounded border border-blue-100 inline-block">
                  {task.state === 'review-pending' ? '需人工审核并补全元数据' :
                   task.state === 'completed' ? '检查最终产物质量' :
                   ['failed', 'canceled'].includes(task.state || '') ? '排查错误日志或重试' : '等待流水线系统处理'}
                </p>
              </div>
            </div>

            {/* Pipeline Stage Strip */}
            <MainlinePipelinePanel view={mainlineView} compact />

            {/* Output Packets */}
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
              <h2 className="text-base font-bold text-slate-800 mb-4 flex items-center gap-2">
                <Boxes className="w-5 h-5 text-indigo-500" />
                Asset Processing Packets (产物包)
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* PDF 原件 */}
                <div className="border border-slate-200 rounded-lg p-4 bg-slate-50 flex flex-col justify-between">
                  <div>
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 text-sm mb-1">
                      <FileText className="w-4 h-4 text-red-500" /> PDF 原件
                    </h3>
                    <p className="text-xs text-slate-500 truncate" title={material?.metadata?.objectName || '未上传'}>
                      {material?.metadata?.objectName || '未上传'}
                    </p>
                  </div>
                  {resourceStatus.originalExists && (
                    <button onClick={() => setActiveTab('pdf')} className="mt-3 text-xs font-semibold text-blue-600 hover:text-blue-800 self-start">查看预览 &rarr;</button>
                  )}
                </div>

                {/* MinerU Markdown */}
                <div className="border border-slate-200 rounded-lg p-4 bg-slate-50 flex flex-col justify-between">
                  <div>
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 text-sm mb-1">
                      <FileText className="w-4 h-4 text-blue-500" /> MinerU Markdown
                    </h3>
                    <p className="text-xs text-slate-500">full.md / 完整排版文本</p>
                  </div>
                  {resourceStatus.markdownExists && (
                    <button onClick={() => setActiveTab('markdown')} className="mt-3 text-xs font-semibold text-blue-600 hover:text-blue-800 self-start">查看 / 比对 &rarr;</button>
                  )}
                </div>

                {/* MinerU JSON / Artifacts */}
                <div className="border border-slate-200 rounded-lg p-4 bg-slate-50 flex flex-col justify-between">
                  <div>
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 text-sm mb-1">
                      <Database className="w-4 h-4 text-amber-500" /> MinerU JSON / Artifacts
                    </h3>
                    <p className="text-xs text-slate-500">content_list, middle, images, zip</p>
                  </div>
                  {(material?.metadata?.parsedFilesCount || resourceStatus.markdownExists) && (
                    <button onClick={handleDownloadZip} className="mt-3 text-xs font-semibold text-blue-600 hover:text-blue-800 self-start">下载 ZIP &rarr;</button>
                  )}
                </div>

                {/* AI Metadata */}
                <div className="border border-slate-200 rounded-lg p-4 bg-slate-50 flex flex-col justify-between">
                  <div>
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 text-sm mb-1">
                      <Brain className="w-4 h-4 text-purple-500" /> AI Metadata
                    </h3>
                    <p className="text-xs text-slate-500 truncate">
                      {material?.metadata?.subject ? `${material.metadata.subject} / ${material.metadata.grade || ''}` : '暂无 AI 识别结果'}
                    </p>
                  </div>
                  {aiJobs.length > 0 && (
                    <button onClick={() => setActiveTab('metadata')} className="mt-3 text-xs font-semibold text-blue-600 hover:text-blue-800 self-start">查看详情 &rarr;</button>
                  )}
                </div>

                {/* 目录重建 Outputs */}
                <div className="border border-slate-200 rounded-lg p-4 bg-slate-50 flex flex-col justify-between md:col-span-2 lg:col-span-2">
                  <div>
                    <h3 className="font-bold text-slate-800 flex items-center gap-2 text-sm mb-2">
                      <Boxes className="w-4 h-4 text-emerald-500" /> 目录重建与 Raw/Clean Material
                    </h3>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="flex items-center gap-1"><CheckCircle2 className={`w-3 h-3 ${cleanMaterialView.artifacts.some(a => a.role === 'readable_tree') ? 'text-emerald-500' : 'text-slate-300'}`} /> readable_tree</div>
                      <div className="flex items-center gap-1"><CheckCircle2 className={`w-3 h-3 ${cleanMaterialView.artifacts.some(a => a.role === 'rebuilt_markdown') ? 'text-emerald-500' : 'text-slate-300'}`} /> rebuilt_markdown</div>
                      <div className="flex items-center gap-1"><CheckCircle2 className={`w-3 h-3 ${cleanMaterialView.artifacts.some(a => a.role === 'logic_tree') ? 'text-emerald-500' : 'text-slate-300'}`} /> logic_tree</div>
                      <div className="flex items-center gap-1"><CheckCircle2 className={`w-3 h-3 ${cleanMaterialView.artifacts.some(a => a.role === 'skeleton') ? 'text-emerald-500' : 'text-slate-300'}`} /> skeleton</div>
                      <div className="flex items-center gap-1"><CheckCircle2 className={`w-3 h-3 ${cleanMaterialView.artifacts.some(a => a.role === 'provenance') || cleanMaterialView.provenanceObjectName ? 'text-emerald-500' : 'text-slate-300'}`} /> provenance</div>
                      <div className="flex items-center gap-1"><CheckCircle2 className={`w-3 h-3 ${material?.metadata?.rawMaterial ? 'text-emerald-500' : 'text-slate-300'}`} /> Raw Material</div>
                      <div className="flex items-center gap-1"><CheckCircle2 className={`w-3 h-3 ${(material?.metadata?.rawMaterial2CleanMaterial as any)?.currentDecision?.state === 'accepted' ? 'text-emerald-500' : 'text-slate-300'}`} /> Clean Material</div>
                    </div>
                  </div>
                  {cleanMaterialView.present && (
                    <div className="mt-3">
                      <CleanMaterialSummaryCard
                        material={material}
                        view={cleanMaterialView}
                        canRebuild={canTocRebuild}
                        rebuildRunning={tocRebuildRunning}
                        rebuildDisabledReason={tocRebuildDisabledReason}
                        onRebuild={handleTocRebuild}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 当前进展 */}
            {(mineruProgressLine || taskDisplayStatus || task.message) && (
              <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-4">
                <p className="text-xs text-slate-400 mb-1 uppercase font-semibold tracking-wider">实时进展</p>
                <p className="text-sm text-slate-700 break-words leading-relaxed">
                  {mineruProgressLine || taskDisplayStatus || task.message}
                </p>
                {mineruProgressLine && task.message && task.message !== mineruProgressLine && (
                  <p className="text-xs text-slate-500 mt-1 break-words leading-relaxed">{task.message}</p>
                )}
              </div>
            )}

            {/* 错误信息 */}
            {task.errorMessage && (
              <div className="p-4 bg-red-50 border border-red-100 rounded-lg">
                <p className="text-xs font-semibold text-red-600 mb-1">错误详情</p>
                <p className="text-sm text-red-700 break-words">{task.errorMessage}</p>
              </div>
            )}

            {/* 诊断信息折叠区 */}
            <details className="group bg-slate-50 border border-slate-200 rounded-lg shadow-sm">
              <summary className="px-5 py-4 cursor-pointer font-semibold text-slate-700 hover:text-slate-900 list-none flex items-center justify-between select-none">
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-slate-400" />
                  Technical Evidence & Diagnostics (技术诊断证据)
                </div>
                <div className="w-5 h-5 rounded-full border border-slate-200 flex items-center justify-center text-slate-400 group-open:rotate-180 transition-transform">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                </div>
              </summary>
              <div className="p-5 pt-0 border-t border-slate-200 space-y-6 mt-4">

            {/* 状态诊断矩阵 */}
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
              <div className="px-5 py-3 bg-slate-50/50 border-b border-slate-100 flex items-center justify-between">
                <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-500" />
                  状态一致性诊断 (Diagnostic Matrix)
                </h2>
                {(() => {
                  const isHealthy = task.state === 'completed' && material?.status === 'completed' && material?.mineruStatus === 'completed' && material?.aiStatus === 'analyzed';
                  const isReviewing = task.state === 'review-pending' && material?.status === 'reviewing' && material?.mineruStatus === 'completed';
                  if (isHealthy) return <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100 uppercase">HEALTHY</span>;
                  if (isReviewing) return <span className="text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100 uppercase">READY FOR REVIEW</span>;
                  if (['failed', 'canceled'].includes(String(task.state))) return <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 uppercase">STOPPED</span>;
                  return <span className="text-[10px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-100 uppercase animate-pulse">PENDING SYNC</span>;
                })()}
              </div>
              <div className="p-5 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">Task State</p>
                  <p className="text-sm font-mono font-bold text-slate-700">{task.state}</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">Material Status</p>
                  <p className="text-sm font-mono font-bold text-slate-700">{material?.status || 'N/A'}</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">MinerU Status</p>
                  <p className="text-sm font-mono font-bold text-slate-700">{material?.mineruStatus || 'N/A'}</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">AI Status</p>
                  <p className="text-sm font-mono font-bold text-slate-700">{material?.aiStatus || 'N/A'}</p>
                </div>
              </div>
            </div>

            {/* 基础信息 */}
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
              <h2 className="text-sm font-semibold text-slate-800 mb-3">基础信息</h2>
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 text-sm">
                <div className="flex justify-between">
                  <dt className="text-slate-400">Material ID</dt>
                  <dd className="text-slate-800 font-mono text-xs">{task.materialId || '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-400">创建时间</dt>
                  <dd className="text-slate-800">{task.createdAt ? new Date(task.createdAt).toLocaleString() : '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-400">更新时间</dt>
                  <dd className="text-slate-800">{task.updatedAt ? new Date(task.updatedAt).toLocaleString() : '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-400">完成时间</dt>
                  <dd className="text-slate-800">{task.completedAt ? new Date(task.completedAt).toLocaleString() : '—'}</dd>
                </div>
              </dl>
            </div>

            {/* MinerU 解析状态 */}
            {!!task.metadata?.mineruTaskId && (
              <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
                <h2 className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
                  <LayoutDashboard className="w-4 h-4 text-blue-500" />
                  MinerU 状态详情
                </h2>
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-slate-400">MinerU Task ID</dt>
                    <dd className="text-slate-800 font-mono text-xs break-all">{String(task.metadata.mineruTaskId)}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-400">当前排队</dt>
                    <dd className="text-slate-800">{task.metadata.mineruQueuedAhead !== undefined ? `${String(task.metadata.mineruQueuedAhead)} (前方)` : '—'}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-400">开始解析时间</dt>
                    <dd className="text-slate-800">{task.metadata.mineruStartedAt ? new Date(String(task.metadata.mineruStartedAt)).toLocaleString() : '—'}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-400">最近状态更新</dt>
                    <dd className="text-slate-800">{task.metadata.mineruLastStatusAt ? new Date(String(task.metadata.mineruLastStatusAt)).toLocaleString() : '—'}</dd>
                  </div>
                </dl>

                {/* MinerU 执行画像 */}
                {task.metadata?.mineruExecutionProfile && (
                  <div className="mt-4 pt-4 border-t border-slate-100">
                    <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                      执行画像
                    </h3>
                    <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 text-sm">
                      <div className="flex justify-between">
                        <dt className="text-slate-400">backend / parseMethod</dt>
                        <dd className="text-slate-800 font-mono text-xs truncate max-w-[200px]" title={task.metadata.mineruExecutionProfile.backendRequested || '—'}>{task.metadata.mineruExecutionProfile.backendRequested || '—'} / {task.metadata.mineruExecutionProfile.parseMethod || '—'}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-slate-400">effectiveBackend</dt>
                        <dd className="text-slate-800 font-mono text-xs">{task.metadata.mineruExecutionProfile.backendEffective || '等待判定'}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-slate-400">enableOcr / enableFormula</dt>
                        <dd className="text-slate-800 font-mono text-xs">{String(task.metadata.mineruExecutionProfile.enableOcr)} / {String(task.metadata.mineruExecutionProfile.enableFormula)}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-slate-400">enableTable / ocrLanguage</dt>
                        <dd className="text-slate-800 font-mono text-xs">{String(task.metadata.mineruExecutionProfile.enableTable)} / {task.metadata.mineruExecutionProfile.ocrLanguage || '—'}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-slate-400">maxPages</dt>
                        <dd className="text-slate-800 font-mono text-xs">{task.metadata.mineruExecutionProfile.maxPages || '—'} (限制参数)</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-slate-400">fileSize</dt>
                        <dd className="text-slate-800 font-mono text-xs">{task.metadata.mineruExecutionProfile.fileSize ? `${(task.metadata.mineruExecutionProfile.fileSize / 1024 / 1024).toFixed(2)} MB` : '—'}</dd>
                      </div>
                    </dl>
                  </div>
                )}

                {/* MinerU 当前日志语义 */}
                {task.metadata?.mineruObservedProgress && (() => {
                  const obs = task.metadata.mineruObservedProgress as any;
                  const operatorLine = deriveMineruProgressLine(task as any) || obs.progressSemantics?.message || null;
                  const semantics = obs.progressSemantics || {};
                  return (
                    <div className="mt-4 pt-4 border-t border-slate-100">
                      <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                        当前日志语义
                      </h3>
                      <div className="bg-slate-50 rounded-lg p-3 border border-slate-100 space-y-2">
                        {operatorLine && (
                          <div className="p-2.5 bg-white rounded-md border border-slate-200">
                            <p className="text-sm font-medium text-slate-800">{operatorLine}</p>
                            <p className="text-xs text-slate-500 mt-1">
                              新鲜度：{semantics.freshness || (obs.observationStale ? 'stale' : 'recent')}
                              {semantics.lastObservedAt && ` · 最近观测 ${new Date(String(semantics.lastObservedAt)).toLocaleString()}`}
                            </p>
                          </div>
                        )}
                        <div className="flex justify-between items-center pb-2 border-b border-slate-200">
                          <span className="text-xs text-slate-500">观测来源</span>
                          <span className="text-sm font-medium text-slate-800">
                            {obs.observer === 'host-mineru-log-observer' ? '宿主机 Sidecar' : '容器本地读取'}
                          </span>
                        </div>
                        {obs.backendProfile && (
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-slate-500">backendProfile</span>
                            <span className="text-sm font-medium text-slate-800">
                              {obs.backendProfile}
                            </span>
                          </div>
                        )}
                        {obs.activityLevel && obs.activityLevel.startsWith('log-observation-') ? (
                          <div className="space-y-2 p-2 bg-amber-50/50 rounded border border-amber-100">
                            <div className="flex items-start gap-2">
                              <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                              <div>
                                <p className="text-sm font-medium text-amber-800">
                                  MinerU 仍在处理，但日志观测通道滞后/不可用
                                </p>
                                <p className="text-xs text-amber-700 mt-0.5">
                                  {obs.observationStaleReason || '未知原因'}
                                </p>
                              </div>
                            </div>

                            {obs.logSource && (
                              <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 text-xs border-t border-amber-100/50 pt-2">
                                <div>
                                  <span className="text-slate-500">日志状态: </span>
                                  <span className="text-slate-700">
                                    {obs.logSource.logSourceExists ? (obs.logSource.logSourceReadable ? '可读取' : '不可读取') : '未找到'}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-slate-500">最后更新: </span>
                                  <span className="text-slate-700">
                                    {obs.logSource.logSourceMtime ? new Date(obs.logSource.logSourceMtime).toLocaleString() : '—'}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-slate-500">距今: </span>
                                  <span className="text-slate-700">
                                    {obs.logSource.logSourceAgeMs != null ? `${Math.floor(obs.logSource.logSourceAgeMs / 1000)} 秒` : '—'}
                                  </span>
                                </div>
                                <div className="col-span-2">
                                  <span className="text-slate-500">检查时间: </span>
                                  <span className="text-slate-700">
                                    {obs.observerCheckedAt || obs.logSource.observerCheckedAt ? new Date(obs.observerCheckedAt || obs.logSource.observerCheckedAt).toLocaleString() : '—'}
                                  </span>
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <>
                            {/* 当前阶段 & 进度 (仅在非滞后状态下显示) */}
                            {obs.stage && obs.activityLevel !== 'log-observation-stale' ? (
                              <>
                                <div className="flex justify-between items-center">
                                  <span className="text-xs text-slate-500">当前阶段</span>
                                  <span className="text-sm font-medium text-slate-800">
                                    {obs.stage.rawPhase || '—'}
                                    {obs.stage.unitType === 'model-units' && ' (模型单元)'}
                                    {obs.stage.unitType === 'ocr-recognition-blocks' && ' (OCR识别块)'}
                                    {obs.stage.unitType === 'table-regions' && ' (表格识别)'}
                                  </span>
                                </div>
                                {(obs.stage.current != null) && (
                                  <div className="flex justify-between items-center">
                                    <span className="text-xs text-slate-500">阶段进度</span>
                                    <span className="text-sm font-medium text-slate-800">
                                      {obs.stage.current}/{obs.stage.total ?? '?'}
                                      {obs.stage.percent != null && ` （${obs.stage.percent}%）`}
                                    </span>
                                  </div>
                                )}
                                {/* 百分比进度条 */}
                                {obs.stage.percent != null && (
                                  <div className="flex items-center gap-2">
                                    <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                                      <div className="h-full bg-blue-500 rounded-full transition-all duration-500" style={{ width: `${obs.stage.percent}%` }} />
                                    </div>
                                    <span className="text-xs font-mono text-slate-500 w-8 text-right">{obs.stage.percent}%</span>
                                  </div>
                                )}
                              </>
                            ) : obs.activityLevel !== 'log-observation-stale' ? (
                              <>
                                {/* 旧格式兼容 */}
                                <div className="flex justify-between items-center">
                                  <span className="text-xs text-slate-500">当前阶段</span>
                                  <span className="text-sm font-medium text-slate-800">
                                    {obs.phase || '暂无结构化日志信号'}
                                  </span>
                                </div>
                                {obs.current != null && (
                                  <div className="flex justify-between items-center">
                                    <span className="text-xs text-slate-500">阶段进度</span>
                                    <span className="text-sm font-medium text-slate-800">
                                      {obs.current}/{obs.total ?? '?'}
                                      {obs.percent != null && ` （${obs.percent}%）`}
                                    </span>
                                  </div>
                                )}
                              </>
                            ) : null}
                          </>
                        )}

                        {/* Hybrid 窗口 */}
                        {(obs.window || obs.latestWindow) && (() => {
                          const w = obs.window || obs.latestWindow;
                          const pageCurrent = w.pageCurrent ?? w.pageEnd;
                          return (
                            <div className="flex justify-between items-center">
                              <span className="text-xs text-slate-500">批次 / 页码</span>
                              <span className="text-sm font-medium text-slate-800">
                                批次 {w.index ?? w.windowCurrent ?? '—'}/{w.total ?? w.windowTotal ?? '—'} · 页 {pageCurrent ?? '—'}/{w.pageTotal ?? '—'}
                              </span>
                            </div>
                          );
                        })()}

                        {/* 文档页数 */}
                        {obs.document && obs.document.totalPages != null && (
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-slate-500">文档页数</span>
                            <span className="text-sm font-medium text-slate-800">
                              共 {obs.document.totalPages} 页
                            </span>
                          </div>
                        )}

                        {/* 最近业务信号时间 */}
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-500">最近进度更新</span>
                          <span className="text-xs text-slate-600">
                            {(() => {
                              const raw = obs.lastProgressObservedAt || obs.observedAt;
                              if (!raw) return '—';
                              const dt = new Date(raw).getTime();
                              if (isNaN(dt)) return '—';
                              const diff = Math.round((Date.now() - dt) / 1000);
                              if (diff < 0) return '刚刚';
                              if (diff < 60) return `${diff} 秒前`;
                              return `${Math.floor(diff / 60)} 分钟前`;
                            })()}
                          </span>
                        </div>
                        {/* 日志文件更新时间 */}
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-500">日志文件更新</span>
                          <span className="text-xs text-slate-600">
                            {obs.logFileUpdatedAt
                              ? new Date(String(obs.logFileUpdatedAt)).toLocaleString()
                              : '—'}
                          </span>
                        </div>
                        {/* 活性等级 — v1.1 全覆盖 */}
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-500">活性状态</span>
                          <span className={`text-xs font-bold px-2 py-0.5 rounded ${(() => {
                            const h = String(task.metadata?.mineruProgressHealth || obs.activityLevel || '');
                            switch (h) {
                              case 'active-progress': return 'bg-green-100 text-green-700';
                              case 'active-stage-change': return 'bg-green-100 text-green-700';
                              case 'active-business-log': return 'bg-blue-100 text-blue-700';
                              case 'api-alive-only': return 'bg-yellow-100 text-yellow-700';
                              case 'no-business-signal': return 'bg-slate-200 text-slate-600';
                              case 'suspected-stale': return 'bg-orange-100 text-orange-700';
                              case 'stale-critical': return 'bg-red-100 text-red-700';
                              case 'failed-confirmed': return 'bg-red-100 text-red-700';
                              case 'log-error-signal': return 'bg-orange-100 text-orange-700';
                              case 'log-observation-stale': return 'bg-amber-100 text-amber-700';
                              default: return 'bg-slate-200 text-slate-600';
                            }
                          })()}`}>
                            {(() => {
                              const h = String(task.metadata?.mineruProgressHealth || obs.activityLevel || '');
                              const labels: Record<string, string> = {
                                'active-progress': '进度推进中',
                                'active-stage-change': '阶段切换中',
                                'active-business-log': '业务日志活跃',
                                'api-alive-only': '仅 API 可达',
                                'no-business-signal': '暂无业务信号',
                                'suspected-stale': '疑似停滞',
                                'stale-critical': '严重停滞',
                                'failed-confirmed': '已确认失败',
                                'log-error-signal': '日志包含错误',
                                'log-observation-stale': '日志观测滞后',
                              };
                              return labels[h] || h || '暂无结构化日志信号';
                            })()}
                          </span>
                        </div>
                        {/* 日志观测滞后警告 */}
                        {(obs.observationStale ||
                          String(task.metadata?.mineruProgressHealth) === 'log-observation-stale') && (
                          <div className="mt-2 p-2.5 bg-amber-50 border border-amber-200 rounded-md">
                            <p className="text-xs font-medium text-amber-800">
                              ⚠ MinerU 仍在处理，但日志观测通道滞后，当前进度可能不是最新。
                            </p>
                            {(obs.stage?.rawPhase || obs.phase) && (
                              <p className="text-xs text-amber-700 mt-1">
                                最后可见进度：{obs.stage?.rawPhase || obs.phase} {obs.stage?.current ?? obs.current ?? '?'}/{obs.stage?.total ?? obs.total ?? '?'}
                                {obs.window && ` · 窗口 ${obs.window.index ?? '—'}/${obs.window.total ?? '—'} · 页 ${obs.window.pageStart ?? '—'}-${obs.window.pageEnd ?? '—'}/${obs.window.pageTotal ?? '—'}`}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* AI Job */}
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
              <h2 className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-500" />
                AI 元数据识别
              </h2>
              {aiJobs.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-4">
                  {task.state === 'ai-pending' ? '等待创建 AI 任务...' : '暂无关联的 AI 任务'}
                </p>
              ) : (
                <div className="space-y-3">
                  {aiJobs.map((job) => {
                    const jobStyle = getAiJobStateStyle(job.state);
                    const jobOutcome = getAiJobOutcome(job);
                    return (
                      <div
                        key={job.id}
                        className="border border-slate-100 rounded-lg p-4 bg-slate-50/50"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-xs font-mono text-slate-500">{job.id}</span>
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full ${jobStyle.badgeClass}`}>
                            {jobStyle.icon} {job.state}
                          </span>
                        </div>
                        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-xs">
                          <div className="flex justify-between">
                            <dt className="text-slate-400">进度</dt>
                            <dd className="text-slate-700">{job.progress ?? 0}%</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-slate-400">Model</dt>
                            <dd className="text-slate-700">{job.model || '—'}</dd>
                          </div>
                          <div className="md:col-span-2 border-t border-slate-100 pt-2 mt-1">
                            <dt className="text-slate-400 mb-1">识别结论</dt>
                            <dd className={`rounded-md border px-3 py-2 ${jobOutcome.className}`}>
                              <div className="font-medium">{jobOutcome.label}</div>
                              <div className="mt-1 text-[11px] leading-relaxed">{jobOutcome.detail}</div>
                            </dd>
                          </div>
                        </dl>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

              </div>
            </details>

            {/* 配置快照 */}
            {task.optionsSnapshot && Object.keys(task.optionsSnapshot).length > 0 && (
              <div className="bg-white border border-slate-200 rounded-lg shadow-sm">
                <button
                  onClick={() => setOptionsExpanded(!optionsExpanded)}
                  className="w-full flex items-center justify-between p-5 text-sm font-semibold text-slate-800 hover:bg-slate-50 transition-colors rounded-lg"
                >
                  <span>配置快照 (optionsSnapshot)</span>
                  {optionsExpanded
                    ? <ChevronDown className="w-4 h-4 text-slate-400" />
                    : <ChevronRight className="w-4 h-4 text-slate-400" />
                  }
                </button>
                {optionsExpanded && (
                  <div className="px-5 pb-5">
                    <pre className="text-xs text-slate-600 bg-slate-50 border border-slate-100 rounded-md p-4 overflow-x-auto max-h-64 overflow-y-auto leading-relaxed">
                      {JSON.stringify(task.optionsSnapshot, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
              </div>
            </details>
          </div>
        )}
        {activeTab === 'markdown' && (
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm h-full overflow-hidden flex flex-col">
            <div className="flex-1 min-h-0 flex">
              <div className={`flex-1 flex flex-col ${rebuiltMdContent ? 'border-r border-slate-200' : ''}`}>
                <div className="px-4 py-2 bg-slate-50 border-b border-slate-200 text-sm font-bold text-slate-700 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-500" />
                  MinerU Markdown (full.md)
                </div>
                <div className="flex-1 min-h-0 overflow-y-auto">
                  <MarkdownTab content={mdContent} loading={mdLoading} error={mdError} />
                </div>
              </div>

              {cleanMaterialView.artifacts.some(a => a.role === 'rebuilt_markdown') && (
                <div className="flex-1 flex flex-col">
                  <div className="px-4 py-2 bg-slate-50 border-b border-slate-200 text-sm font-bold text-slate-700 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-emerald-500" />
                    Rebuilt Markdown (rebuilt_markdown.md)
                  </div>
                  <div className="flex-1 min-h-0 overflow-y-auto">
                    <MarkdownTab content={rebuiltMdContent} loading={rebuiltMdLoading} error={rebuiltMdError} />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'pdf' && (
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm h-full overflow-hidden flex flex-col">
            <div className="flex-1 min-h-0 overflow-y-auto">
              <PDFPreviewPanel objectName={material?.metadata?.objectName} />
            </div>
          </div>
        )}

        {activeTab === 'metadata' && (
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm h-full overflow-hidden flex flex-col p-5">
            <div className="flex-1 min-h-0 overflow-y-auto pr-2">
              <MetadataTab
                materialId={task.materialId || ''}
                material={material}
                metaForm={metaForm}
                updateMeta={updateMeta}
                isDirty={isMetaDirty}
                onSaveMeta={handleSaveMetadata}
              />

              {/* W2-2: 元数据页内的提交审核按钮，与保存元数据分离 */}
              {task.state === 'review-pending' && (
                <div className="mt-6 flex justify-end pt-4 border-t border-slate-100">
                  <button
                    onClick={handleReview}
                    className="flex items-center gap-2 px-6 py-2.5 bg-green-600 text-white rounded-lg text-sm font-bold shadow-md hover:bg-green-700 transition-all transform hover:scale-[1.02] active:scale-95"
                  >
                    <ShieldCheck className="w-4 h-4" /> 提交审核并发布
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'events' && (
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5 h-full overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-800">事件时间线</h2>
              <div className="flex gap-2">
                <button onClick={() => setEventFilter('all')} className={`px-3 py-1 text-xs rounded-full border ${eventFilter === 'all' ? 'bg-slate-800 text-white border-slate-800' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>全部</button>
                <button onClick={() => setEventFilter('key')} className={`px-3 py-1 text-xs rounded-full border ${eventFilter === 'key' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>关键动作</button>
                <button onClick={() => setEventFilter('error')} className={`px-3 py-1 text-xs rounded-full border ${eventFilter === 'error' ? 'bg-red-600 text-white border-red-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>错误/警告</button>
                <button onClick={() => setEventFilter('system')} className={`px-3 py-1 text-xs rounded-full border ${eventFilter === 'system' ? 'bg-slate-200 text-slate-800 border-slate-300' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>系统细节</button>
              </div>
            </div>
            {events.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-6">暂无事件记录</p>
            ) : (() => {
              const filteredEvents = events.filter(evt => {
                if (eventFilter === 'all') return true;
                if (eventFilter === 'error') return evt.level === 'error' || evt.level === 'warn';
                const isKey = [
                  'task-created', 'task-completed', 'task-failed',
                  'mineru-started', 'mineru-completed',
                  'ai-provider-request-started', 'ai-provider-request-succeeded', 'ai-provider-request-failed',
                  'retry-requested', 'reparse-requested', 're-ai-requested', 'cancel-requested', 'review-submitted'
                ].includes(evt.event || '');
                if (eventFilter === 'key') return isKey || evt.level === 'error' || evt.level === 'warn';
                if (eventFilter === 'system') return !isKey && evt.level !== 'error' && evt.level !== 'warn';
                return true;
              });
              if (filteredEvents.length === 0) return <p className="text-sm text-slate-400 text-center py-6">当前过滤条件下无事件记录</p>;
              return (
                <div className="relative pl-6 space-y-0">
                  <div className="absolute left-[9px] top-2 bottom-2 w-px bg-slate-200" />
                  {filteredEvents.map((evt, idx) => {
                    const evtStyle = getEventStyle(evt.level);
                    return (
                      <div key={evt.id || idx} className="relative pb-5 last:pb-0">
                        <div className={`absolute -left-6 top-1.5 w-[10px] h-[10px] rounded-full ring-2 ring-white ${evtStyle.dotClass}`} />
                        <div className="flex flex-col gap-0.5">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-slate-800">{evt.event || '—'}</span>
                            {evt.level === 'error' && <span className="text-[10px] px-1.5 py-0.5 bg-red-100 text-red-600 rounded font-medium">ERROR</span>}
                            {evt.level === 'warn' && <span className="text-[10px] px-1.5 py-0.5 bg-yellow-100 text-yellow-700 rounded font-medium">WARN</span>}
                          </div>
                          <p className={`text-xs ${evtStyle.textClass} break-words`}>{evt.message || ''}</p>
                          <p className="text-[10px] text-slate-400 mt-0.5">
                            {evt.createdAt ? new Date(evt.createdAt).toLocaleString() : '—'}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
}
