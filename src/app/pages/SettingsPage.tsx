import { useState, useEffect, useRef } from 'react';
import { Save, Eye, EyeOff, Bot, ScanLine, Database, CheckCircle, XCircle, Loader, Download, Upload, HardDrive, AlertTriangle, Plus, Trash2, ChevronUp, ChevronDown, ToggleLeft, ToggleRight, RefreshCw, Tag } from 'lucide-react';
import { toast } from 'sonner';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAppStore } from '../../store/appContext';
import type { AiConfig, AiProvider, MinerUConfig, MinioConfig } from '../../store/types';
import { checkLocalMinerUHealth } from '../../utils/mineruLocalApi';
type ActiveTab = 'ai' | 'mineru' | 'storage' | 'backup';

// ─── 提示词字段中文标签映射 ──────────────────────────────────
const PROMPT_LABELS: Record<string, string> = {
  title:        '资料名称',
  subject:      '学科识别',
  grade:        '年级识别',
  materialType: '资料类型',
  language:     '语言识别',
  country:      '国家/地区',
  tags:         '标签提取',
  summary:      '内容摘要',
};

const LOCAL_STORAGE_KEYS = [
  'app_ai_config',
  'app_mineru_config',
  'app_minio_config',
  'app_materials',
  'app_process_tasks',
  'app_tasks',
  'app_products',
  'app_batch_processing',
  'app_asset_details',
  'app_flexible_tags',
  'app_ai_rules',
  'app_ai_rule_settings',
];

const DEFAULT_CAPACITY_LIMITS = {
  dbSoftLimitMB: 100,
  storageSoftLimitGB: 20,
};

type CapacityLimits = typeof DEFAULT_CAPACITY_LIMITS;

type BackupConfirmState =
  | { kind: 'json'; fileName: string; data: unknown }
  | { kind: 'full'; fileName: string; file: File; mode: 'replace' | 'merge' };

type ImportResult = {
  mode: 'replace' | 'merge' | 'json';
  importedObjects?: number;
  removedExistingObjects?: number;
  skippedObjects?: number;
  materialsCount?: number;
  backupPath?: string;
};

function FieldRow({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-4">
      <div className="w-36 flex-shrink-0 mt-2">
        <label className="text-sm text-gray-500">{label}</label>
        {hint && <p className="text-xs text-gray-400 mt-0.5">{hint}</p>}
      </div>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Input({
  value,
  onChange,
  type = 'text',
  placeholder,
  className = '',
  disabled = false,
}: {
  value: string | number;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      disabled={disabled}
      className={`w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-gray-50 disabled:text-gray-400 ${className}`}
    />
  );
}

function Select({
  value,
  onChange,
  options,
  disabled = false,
}: {
  value: string;
  onChange: (v: string) => void;
  options: Array<{ value: string; label: string }>;
  disabled?: boolean;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-gray-50 disabled:text-gray-400"
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

function Textarea({
  value,
  onChange,
  rows = 3,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  rows?: number;
  placeholder?: string;
}) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      rows={rows}
      placeholder={placeholder}
      className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
    />
  );
}

function formatBytes(bytes: number) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

function getUsageTone(ratio: number) {
  if (ratio >= 0.9) return 'bg-red-500';
  if (ratio >= 0.7) return 'bg-yellow-500';
  return 'bg-green-500';
}

function getUsageTextTone(ratio: number) {
  if (ratio >= 0.9) return 'text-red-600';
  if (ratio >= 0.7) return 'text-yellow-600';
  return 'text-green-600';
}

export function SettingsPage() {
  const { state, dispatch } = useAppStore();
  const location = useLocation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<ActiveTab>('ai');
  const [showKey, setShowKey] = useState(false);
  const [showMinioKeys, setShowMinioKeys] = useState({ access: false, secret: false });
  const jsonImportInputRef = useRef<HTMLInputElement>(null);
  const fullImportInputRef = useRef<HTMLInputElement>(null);

  // 本地副本（保存前不 dispatch）
  const [aiForm, setAiForm] = useState<AiConfig>({ ...state.aiConfig });
  const [mineruForm, setMineruForm] = useState<MinerUConfig>({ ...state.mineruConfig });
  const [minioForm, setMinioForm] = useState<MinioConfig>({ ...state.minioConfig });

  // 测试连接状态
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [localTesting, setLocalTesting] = useState(false);
  const [localTestResult, setLocalTestResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [aiTestingId, setAiTestingId] = useState<string | null>(null);
  const [aiTestResult, setAiTestResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [availableModelsByProvider, setAvailableModelsByProvider] = useState<Record<string, string[]>>({});
  const [fetchingModelsByProvider, setFetchingModelsByProvider] = useState<Record<string, boolean>>({});
  const [testLogs, setTestLogs] = useState<Array<{ ts: number; level: 'info' | 'success' | 'error'; message: string }>>([]);
  const [showTestLogs, setShowTestLogs] = useState(true);
  const testLogEndRef = useRef<HTMLDivElement>(null);
  const [serverDebugLogs, setServerDebugLogs] = useState<Array<{ ts: number; level: string; route?: string; requestId?: string; message: string }>>([]);
  const [serverDebugOpen, setServerDebugOpen] = useState(true);
  const [serverDebugLoading, setServerDebugLoading] = useState(false);
  const [serverDebugSince, setServerDebugSince] = useState<number>(Date.now());
  // 保存中状态
  const [savingMinio, setSavingMinio] = useState(false);
  const [backupLoading, setBackupLoading] = useState(false);
  const [dbStats, setDbStats] = useState<{
    fileSize: number;
    counts: Record<string, number>;
    materialsTotalSizeBytes: number;
    materialsByStatus: Record<string, number>;
    materialsBySubject: Record<string, number>;
  } | null>(null);
  const [storageStats, setStorageStats] = useState<{
    backend: string;
    totalObjects: number;
    totalSize: number;
    buckets: { name: string; objectCount: number; totalSize: number }[];
  } | null>(null);
  const [capacityLimits, setCapacityLimits] = useState<CapacityLimits>(DEFAULT_CAPACITY_LIMITS);
  const [savingCapacity, setSavingCapacity] = useState(false);
  const [fullImportMode, setFullImportMode] = useState<'replace' | 'merge'>('replace');
  const [confirmState, setConfirmState] = useState<BackupConfirmState | null>(null);
  const [confirmInput, setConfirmInput] = useState('');
  const [exportingFull, setExportingFull] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);

  // 切换到 storage tab 时从 upload-server 读取最新配置
  useEffect(() => {
    if (activeTab !== 'storage') return;
    setTestResult(null);
    fetch('/__proxy/upload/settings/storage')
      .then((r) => r.json())
      .then((data) => {
        setMinioForm((prev) => ({
          ...prev,
          storageBackend:  data.storageBackend  ?? prev.storageBackend,
          endpoint:        data.endpoint        ?? prev.endpoint,
          port:            data.port            ?? prev.port,
          useSSL:          data.useSSL          ?? prev.useSSL,
          // 密钥返回 *** 时保留本地 store 中保存的值（若有）
          accessKey:       data.accessKey === '***' ? (state.minioConfig.accessKey || '') : (data.accessKey || ''),
          secretKey:       data.secretKey === '***' ? (state.minioConfig.secretKey || '') : (data.secretKey || ''),
          bucket:          data.bucket          ?? prev.bucket,
          parsedBucket:    data.parsedBucket    ?? prev.parsedBucket,
          presignedExpiry: data.presignedExpiry  ?? prev.presignedExpiry,
        }));
      })
      .catch(() => {/* upload-server 不可用时静默，使用 store 默认值 */});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  useEffect(() => {
    const tab = new URLSearchParams(location.search).get('tab');
    const valid: ActiveTab[] = ['ai', 'mineru', 'storage', 'backup'];
    if (tab && valid.includes(tab as ActiveTab)) {
      setActiveTab(tab as ActiveTab);
    }
  }, [location.search]);

  const switchTab = (tab: ActiveTab) => {
    setActiveTab(tab);
    const next = new URLSearchParams(location.search);
    next.set('tab', tab);
    navigate({ pathname: location.pathname, search: `?${next.toString()}` }, { replace: true });
  };

  useEffect(() => {
    if (activeTab !== 'backup') return;
    void refreshBackupStats();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  useEffect(() => {
    if (!showTestLogs) return;
    testLogEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [testLogs, showTestLogs]);

  const appendTestLog = (level: 'info' | 'success' | 'error', message: string) => {
    const safeMessage = String(message || '').replace(/\s+/g, ' ').trim();
    if (!safeMessage) return;
    setTestLogs((prev) => {
      const next = [...prev, { ts: Date.now(), level, message: safeMessage }];
      return next.length > 200 ? next.slice(next.length - 200) : next;
    });
  };

  const pullServerDebugLogs = async () => {
    setServerDebugLoading(true);
    try {
      const resp = await fetch(`/__proxy/upload/debug/logs?since=${serverDebugSince}&limit=200`);
      const data = await resp.json().catch(() => null);
      const incoming = Array.isArray(data?.logs) ? data.logs : [];
      if (incoming.length > 0) {
        setServerDebugLogs((prev) => {
          const merged = [...prev, ...incoming];
          const dedup = new Map<string, { ts: number; level: string; route?: string; requestId?: string; message: string }>();
          for (const item of merged) {
            const key = `${item?.ts}-${item?.level}-${item?.route}-${item?.requestId}-${item?.message}`;
            dedup.set(key, item);
          }
          const next = Array.from(dedup.values()).sort((a, b) => Number(a.ts) - Number(b.ts));
          return next.length > 400 ? next.slice(next.length - 400) : next;
        });
        const maxTs = Math.max(...incoming.map((l: any) => Number(l?.ts || 0)));
        if (Number.isFinite(maxTs) && maxTs > 0) setServerDebugSince(maxTs + 1);
      }
    } catch (e) {
      toast.error(`拉取服务端日志失败：${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setServerDebugLoading(false);
    }
  };

  const resetServerDebugLogs = () => {
    setServerDebugLogs([]);
    setServerDebugSince(Date.now());
  };

  const updateAi = (patch: Partial<AiConfig>) => setAiForm((prev) => ({ ...prev, ...patch }));
  const updateAiPrompt = (key: keyof AiConfig['prompts'], val: string) =>
    setAiForm((prev) => ({ ...prev, prompts: { ...prev.prompts, [key]: val } }));
  const updateMineru = (patch: Partial<MinerUConfig>) => setMineruForm((prev) => ({ ...prev, ...patch }));
  const updateMinio = (patch: Partial<MinioConfig>) => {
    setMinioForm((prev) => ({ ...prev, ...patch }));
    setTestResult(null);
  };

  const refreshBackupStats = async () => {
    setBackupLoading(true);
    try {
      const [dbResp, storageResp, settingsResp] = await Promise.all([
        fetch('/__proxy/db/stats'),
        fetch('/__proxy/upload/storage-stats'),
        fetch('/__proxy/db/settings'),
      ]);
      const [dbData, storageData, settingsData] = await Promise.all([
        dbResp.json(),
        storageResp.json(),
        settingsResp.json(),
      ]);
      if (!dbResp.ok) throw new Error(dbData.error || `DB HTTP ${dbResp.status}`);
      if (!storageResp.ok) throw new Error(storageData.error || `Storage HTTP ${storageResp.status}`);
      if (!settingsResp.ok) throw new Error(settingsData.error || `Settings HTTP ${settingsResp.status}`);
      setDbStats({
        fileSize: Number(dbData.fileSize || 0),
        counts: dbData.counts || {},
        materialsTotalSizeBytes: Number(dbData.materialsTotalSizeBytes || 0),
        materialsByStatus: dbData.materialsByStatus || {},
        materialsBySubject: dbData.materialsBySubject || {},
      });
      setStorageStats({
        backend: String(storageData.backend || 'unknown'),
        totalObjects: Number(storageData.totalObjects || 0),
        totalSize: Number(storageData.totalSize || 0),
        buckets: Array.isArray(storageData.buckets) ? storageData.buckets : [],
      });
      setCapacityLimits({
        dbSoftLimitMB: Number(settingsData?.capacityLimits?.dbSoftLimitMB || DEFAULT_CAPACITY_LIMITS.dbSoftLimitMB),
        storageSoftLimitGB: Number(settingsData?.capacityLimits?.storageSoftLimitGB || DEFAULT_CAPACITY_LIMITS.storageSoftLimitGB),
      });
    } catch (error) {
      toast.error(`刷新监控失败：${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setBackupLoading(false);
    }
  };

  const handleSaveAi = () => {
    dispatch({ type: 'UPDATE_AI_CONFIG', payload: aiForm });
    appendTestLog('success', 'AI 配置已保存');
    toast.success('AI 配置已保存');
  };

  const handleTestAiProvider = async (provider: AiProvider) => {
    setAiTestingId(provider.id);
    setAiTestResult(null);
    const startedAt = Date.now();
    appendTestLog('info', `开始测试：${provider.name}（model=${provider.model || '(未填)'}）`);
    appendTestLog('info', '请求已发送：POST /__proxy/upload/ai/test');
    const waitingTimer = window.setTimeout(() => {
      appendTestLog('info', `等待响应中...（已等待 ${Math.max(1, Math.round((Date.now() - startedAt) / 1000))}s）`);
    }, 1200);
    try {
      const resp = await fetch('/__proxy/upload/ai/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, mode: 'connectivity' }),
      });
      const data = await resp.json().catch(() => null);
      const requestId = String(data?.requestId || resp.headers.get('x-request-id') || '').trim();
      const elapsedMs = Number(data?.elapsedMs || (Date.now() - startedAt));
      const url = String(data?.url || '').trim();
      const timeoutSec = data?.timeoutSec != null ? String(data.timeoutSec) : '';
      appendTestLog(
        'info',
        `响应：HTTP ${resp.status}${requestId ? ` requestId=${requestId}` : ''}${timeoutSec ? ` timeoutSec=${timeoutSec}` : ''}${url ? ` url=${url}` : ''} elapsedMs=${elapsedMs}`,
      );
      const ok = !!data?.ok;
      const message = String(data?.message || (ok ? '连接成功' : '连接失败'));
      setAiTestResult({ ok, message });
      appendTestLog(ok ? 'success' : 'error', `测试结果：${message}`);
      if (ok) toast.success(message); else toast.error(message);
    } catch (e) {
      const message = `请求失败：${e instanceof Error ? e.message : String(e)}`;
      setAiTestResult({ ok: false, message });
      appendTestLog('error', `测试失败：${message}`);
      toast.error(message);
    } finally {
      window.clearTimeout(waitingTimer);
      setAiTestingId(null);
      void pullServerDebugLogs();
      appendTestLog('info', '已拉取服务端请求日志（upload-server）');
    }
  };

  const fetchModels = async (provider: AiProvider) => {
    const endpoint = provider.apiEndpoint?.trim();
    if (!endpoint) return;

    setFetchingModelsByProvider((prev) => ({ ...prev, [provider.id]: true }));
    appendTestLog('info', `开始拉取模型：${provider.name}（endpoint=${endpoint}）`);
    try {
      const resp = await fetch('/__proxy/upload/settings/ai-models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endpoint }),
      });
      const result = await resp.json().catch(() => null);
      const requestId = String(result?.requestId || resp.headers.get('x-request-id') || '').trim();
      appendTestLog('info', `响应：HTTP ${resp.status}${requestId ? ` requestId=${requestId}` : ''}`);

      if (result?.success && Array.isArray(result?.models) && result.models.length > 0) {
        const models = result.models.filter((m: unknown) => typeof m === 'string' && m.trim() !== '');
        setAvailableModelsByProvider((prev) => ({ ...prev, [provider.id]: models }));
        appendTestLog('success', `拉取成功：${models.length} 个模型`);
        toast.success(`成功获取 ${models.length} 个可用模型`);
        if (!provider.model && models[0]) {
          const providers = aiForm.providers ?? [];
          updateAi({
            providers: providers.map((p) => (p.id === provider.id ? { ...p, model: models[0] } : p)),
          });
          appendTestLog('info', `已自动填入模型：${models[0]}`);
        }
      } else {
        const message = String(result?.error || '未获取到模型列表');
        appendTestLog('error', `拉取失败：${message}`);
        toast.error(message);
        setAvailableModelsByProvider((prev) => ({ ...prev, [provider.id]: [] }));
      }
    } catch (e) {
      const message = `拉取模型失败：${e instanceof Error ? e.message : String(e)}`;
      appendTestLog('error', message);
      toast.error(message);
      setAvailableModelsByProvider((prev) => ({ ...prev, [provider.id]: [] }));
    } finally {
      setFetchingModelsByProvider((prev) => ({ ...prev, [provider.id]: false }));
      void pullServerDebugLogs();
      appendTestLog('info', '已拉取服务端请求日志（upload-server）');
    }
  };

  const handleSaveMineru = () => {
    dispatch({ type: 'UPDATE_MINERU_CONFIG', payload: mineruForm });
    toast.success('MinerU 配置已保存');
  };

  const handleTestLocalMineru = async () => {
    setLocalTesting(true);
    setLocalTestResult(null);
    try {
      const result = await checkLocalMinerUHealth(mineruForm.localEndpoint);
      setLocalTestResult(result);
    } finally {
      setLocalTesting(false);
    }
  };

  const handleTestMinio = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const resp = await fetch('/__proxy/upload/settings/storage/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(minioForm),
      });
      const data = await resp.json();
      setTestResult({ ok: data.ok, message: data.message });
    } catch (e) {
      setTestResult({ ok: false, message: `请求失败：${e instanceof Error ? e.message : String(e)}` });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveMinio = async () => {
    setSavingMinio(true);
    try {
      const resp = await fetch('/__proxy/upload/settings/storage', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(minioForm),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ message: `HTTP ${resp.status}` }));
        throw new Error(err.message || `HTTP ${resp.status}`);
      }
      // 同步到 store（含 localStorage + db-server）
      dispatch({ type: 'UPDATE_MINIO_CONFIG', payload: minioForm });
      toast.success('存储配置已保存');
    } catch (e) {
      toast.error(`保存失败：${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setSavingMinio(false);
    }
  };

  const handleSaveCapacity = async () => {
    setSavingCapacity(true);
    try {
      const payload = {
        dbSoftLimitMB: Math.max(1, Number(capacityLimits.dbSoftLimitMB || DEFAULT_CAPACITY_LIMITS.dbSoftLimitMB)),
        storageSoftLimitGB: Math.max(1, Number(capacityLimits.storageSoftLimitGB || DEFAULT_CAPACITY_LIMITS.storageSoftLimitGB)),
      };
      const response = await fetch('/__proxy/db/settings/capacityLimits', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      setCapacityLimits(payload);
      toast.success('容量阈值已保存');
    } catch (error) {
      toast.error(`保存失败：${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setSavingCapacity(false);
    }
  };

  const clearLocalStateAndReload = () => {
    for (const key of LOCAL_STORAGE_KEYS) {
      localStorage.removeItem(key);
    }
    toast.success('导入成功，页面即将刷新以加载最新数据');
    window.setTimeout(() => window.location.reload(), 1200);
  };

  const handleClearLocalCache = () => {
    try {
      for (const key of LOCAL_STORAGE_KEYS) localStorage.removeItem(key);
      toast.success('已清除本地缓存，页面将刷新');
      window.setTimeout(() => window.location.reload(), 800);
    } catch (e) {
      toast.error(`清除缓存失败：${e instanceof Error ? e.message : String(e)}`);
    }
  };

  const handleExportBackup = async () => {
    try {
      const response = await fetch('/__proxy/db/backup/export');
      if (!response.ok) {
        const data = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `db-metadata-backup-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      toast.success('元数据备份导出成功');
    } catch (error) {
      toast.error(`导出失败：${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const handleImportBackup = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const data = JSON.parse(text);
      // 前置校验：必须含有 materials 字段且为 object（非数组）
      if (!data || typeof data !== 'object' || Array.isArray(data)) {
        toast.error('导入失败：JSON 文件不是合法的对象');
        return;
      }
      if (!('materials' in data) || typeof data.materials !== 'object' || Array.isArray(data.materials)) {
        toast.error('导入失败：JSON 文件缺少合法的 materials 字段，请确认是否为本系统导出的数据库备份');
        return;
      }
      setConfirmState({ kind: 'json', fileName: file.name, data });
    } catch (error) {
      toast.error(`导入失败：${error instanceof Error ? error.message : String(error)}`);
    } finally {
      event.target.value = '';
    }
  };

  const handleFullExportBackup = async () => {
    if (exportingFull) return;

    setExportingFull(true);
    try {
      const response = await fetch('/__proxy/upload/backup/full-export', { method: 'POST' });
      if (!response.ok) {
        const data = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `luceon2026-full-backup-${new Date().toISOString().replace(/[:.]/g, '-')}.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      toast.success('完整资产备份导出成功');
    } catch (error) {
      toast.error(`导出失败：${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setExportingFull(false);
    }
  };

  const handleSelectFullImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setConfirmState({ kind: 'full', fileName: file.name, file, mode: fullImportMode });
    event.target.value = '';
  };

  const handleConfirmImport = async () => {
    if (!confirmState) return;

    try {
      if (confirmState.kind === 'json') {
        const response = await fetch('/__proxy/db/backup/import', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ confirm: true, data: confirmState.data }),
        });
        const result = await response.json().catch(() => null);
        if (!response.ok) {
          throw new Error(result?.error || `HTTP ${response.status}`);
        }
        setConfirmState(null);
        setConfirmInput('');
        setImportResult({
          mode: 'json',
          backupPath: result?.backupPath,
          materialsCount: typeof (confirmState.data as { materials?: Record<string, unknown> }).materials === 'object'
            ? Object.keys((confirmState.data as { materials?: Record<string, unknown> }).materials ?? {}).length
            : undefined,
        });
      } else {
        const formData = new FormData();
        formData.append('file', confirmState.file);
        formData.append('mode', confirmState.mode);
        const response = await fetch('/__proxy/upload/backup/full-import', {
          method: 'POST',
          body: formData,
        });
        const result = await response.json().catch(() => null);
        if (!response.ok) {
          throw new Error(result?.error || `HTTP ${response.status}`);
        }
        setConfirmState(null);
        setConfirmInput('');
        setImportResult({
          mode: confirmState.mode,
          importedObjects: result?.importedObjects,
          removedExistingObjects: result?.removedExistingObjects,
          skippedObjects: result?.skippedObjects,
          materialsCount: result?.materialsCount,
          backupPath: result?.backupPath,
        });
      }
    } catch (error) {
      toast.error(`导入失败：${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const totalUsage = (dbStats?.fileSize || 0) + (storageStats?.totalSize || 0);
  const dbLimitBytes = capacityLimits.dbSoftLimitMB * 1024 * 1024;
  const storageLimitBytes = capacityLimits.storageSoftLimitGB * 1024 * 1024 * 1024;
  const dbUsageRatio = dbLimitBytes > 0 ? (dbStats?.fileSize || 0) / dbLimitBytes : 0;
  const storageUsageRatio = storageLimitBytes > 0 ? (storageStats?.totalSize || 0) / storageLimitBytes : 0;

  return (
    <div className="p-6 space-y-5 max-w-3xl">
      {/* 头部 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">系统设置</h1>
        <p className="text-sm text-gray-500 mt-0.5">配置 AI 识别、MinerU 解析接口及存储后端</p>
      </div>

      {/* Tab */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => switchTab('ai')}
          className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'ai'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-800'
          }`}
        >
          <span className="flex items-center gap-1.5"><Bot size={15} /> AI 识别配置</span>
        </button>
        <button
          onClick={() => switchTab('mineru')}
          className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'mineru'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-800'
          }`}
        >
          <span className="flex items-center gap-1.5"><ScanLine size={15} /> MinerU 配置</span>
        </button>
        <button
          onClick={() => switchTab('storage')}
          className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'storage'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-800'
          }`}
        >
          <span className="flex items-center gap-1.5"><Database size={15} /> 存储配置</span>
        </button>
        <button
          onClick={() => switchTab('backup')}
          className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'backup'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-800'
          }`}
        >
          <span className="flex items-center gap-1.5"><HardDrive size={15} /> 备份与容量</span>
        </button>
        {/* Dictionary tab hidden from normal Settings navigation */}
      </div>

      {/* ===== AI 配置 ===== */}
      {activeTab === 'ai' && (
        <div className="space-y-5">
          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-800">测试日志监控</h2>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowTestLogs((v) => !v)}
                  className="px-2 py-1 text-[11px] rounded border border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
                >
                  {showTestLogs ? '收起' : '展开'}
                </button>
                <button
                  type="button"
                  onClick={() => setTestLogs([])}
                  disabled={testLogs.length === 0}
                  className="px-2 py-1 text-[11px] rounded border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-50"
                >
                  清空
                </button>
              </div>
            </div>
            {showTestLogs && (
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 h-40 overflow-auto font-mono text-[11px] leading-5">
                {testLogs.length === 0 ? (
                  <div className="text-gray-400">暂无日志（点击“测试”或“自动获取”后会在这里记录结果）</div>
                ) : (
                  <div className="space-y-0.5">
                    {testLogs.map((l, idx) => (
                      <div key={`${l.ts}-${idx}`} className="flex gap-2">
                        <span className="text-gray-400 flex-shrink-0">
                          {new Date(l.ts).toLocaleTimeString()}
                        </span>
                        <span
                          className={`flex-1 ${
                            l.level === 'success' ? 'text-green-700' : l.level === 'error' ? 'text-red-700' : 'text-gray-700'
                          }`}
                        >
                          {l.message}
                        </span>
                      </div>
                    ))}
                    <div ref={testLogEndRef} />
                  </div>
                )}
              </div>
            )}
            <p className="text-xs text-gray-400">
              这里记录的是页面发起的“测试连接 / 拉取模型”等操作结果，便于排查配置问题（不等同于服务端容器 stdout 日志）。
            </p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-800">服务端请求日志（upload-server）</h2>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setServerDebugOpen((v) => !v)}
                  className="px-2 py-1 text-[11px] rounded border border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
                >
                  {serverDebugOpen ? '收起' : '展开'}
                </button>
                <button
                  type="button"
                  onClick={() => void pullServerDebugLogs()}
                  disabled={serverDebugLoading}
                  className="px-2 py-1 text-[11px] rounded border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-50"
                >
                  {serverDebugLoading ? '拉取中...' : '拉取'}
                </button>
                <button
                  type="button"
                  onClick={resetServerDebugLogs}
                  className="px-2 py-1 text-[11px] rounded border border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
                >
                  重置
                </button>
              </div>
            </div>
            {serverDebugOpen && (
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 h-40 overflow-auto font-mono text-[11px] leading-5">
                {serverDebugLogs.length === 0 ? (
                  <div className="text-gray-400">暂无日志（执行“测试/拉取模型/本地 MinerU 健康检查”后点“拉取”）</div>
                ) : (
                  <div className="space-y-0.5">
                    {serverDebugLogs.map((l, idx) => (
                      <div key={`${l.ts}-${idx}`} className="flex gap-2">
                        <span className="text-gray-400 flex-shrink-0">{new Date(Number(l.ts)).toLocaleTimeString()}</span>
                        <span className="text-gray-400 flex-shrink-0">{String(l.level || '').padEnd(7, ' ')}</span>
                        <span className="text-gray-400 flex-shrink-0">{l.route ? `${l.route}` : '-'}</span>
                        <span className="text-gray-400 flex-shrink-0">{l.requestId ? `#${l.requestId}` : ''}</span>
                        <span
                          className={`flex-1 ${
                            l.level === 'success' ? 'text-green-700' : l.level === 'error' ? 'text-red-700' : 'text-gray-700'
                          }`}
                        >
                          {l.message}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            <p className="text-xs text-gray-400">
              用于区分“客户端发出请求”与“服务端实际转发/校验/超时”的问题。重点关注 requestId 与 route 的对应关系。
            </p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
            <h2 className="font-semibold text-gray-800">输入控制</h2>
            <FieldRow
              label="Markdown 最大输入字符数"
              hint="建议 <= 200000（约 200K），避免本地模型上下文溢出；系统会自动截断并保留头尾内容以兼顾质量。"
            >
              <Input
                type="number"
                value={Number(aiForm.maxMarkdownChars || 200000)}
                onChange={(v) => updateAi({ maxMarkdownChars: Number(v) })}
              />
            </FieldRow>
            <FieldRow
              label="深度思考模式"
              hint="启用后，Qwen3 等支持 thinking mode 的模型会先进行深度思考再输出结果，可提高复杂文档的分析质量，但会显著增加处理时间和 token 消耗。关闭时添加 /no_think 指令以禁用思考过程。"
            >
              <button
                type="button"
                onClick={() => updateAi({ enableThinking: !aiForm.enableThinking })}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  aiForm.enableThinking
                    ? 'bg-blue-100 text-blue-700 border border-blue-300'
                    : 'bg-gray-100 text-gray-500 border border-gray-200'
                }`}
              >
                {aiForm.enableThinking ? <ToggleRight size={18} /> : <ToggleLeft size={18} />}
                {aiForm.enableThinking ? '已启用' : '已禁用'}
              </button>
            </FieldRow>
          </div>

          {/* 本地大模型配置 */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-800">本地大模型配置 (Local Provider)</h2>
            </div>

            {(() => {
              const providers = aiForm.providers ?? [];
              const realIdx = providers.findIndex(p => p.id === 'ollama' || (p.apiEndpoint || '').includes('11434'));

              if (providers.length === 0) {
                return <p className="text-xs text-gray-400 py-2">暂无提供商配置，请在后端预设配置。</p>;
              }
              if (realIdx === -1) {
                return <p className="text-sm text-amber-600 py-4">未找到本地 Ollama 提供商配置，请在后端预设本地模型配置。</p>;
              }

              const provider = providers[realIdx];
              const updateProvider = (patch: Partial<AiProvider>) => {
                const next = providers.map((p, i) => i === realIdx ? { ...p, ...patch } : p);
                updateAi({ providers: next });
              };

              return (
                <div
                  key={provider.id}
                  className="rounded-lg border p-4 space-y-3 transition-colors border-blue-200 bg-blue-50/30"
                >
                  {/* 标题行 */}
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 text-[10px] font-bold flex items-center justify-center flex-shrink-0">
                      主
                    </span>
                    <input
                      className="flex-1 text-sm font-medium bg-transparent border-b border-transparent focus:border-blue-300 outline-none text-gray-800 min-w-0"
                      value={provider.name}
                      onChange={(e) => updateProvider({ name: e.target.value })}
                      placeholder="提供商名称"
                    />
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <button
                        type="button"
                        onClick={() => void handleTestAiProvider(provider)}
                        disabled={aiTestingId === provider.id}
                        className="px-2 py-1 text-[11px] rounded border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-50"
                        title="测试连接"
                      >
                        {aiTestingId === provider.id ? '测试中...' : '测试'}
                      </button>
                    </div>
                  </div>

                  {/* 字段 */}
                  <div className="grid grid-cols-1 gap-2">
                    <FieldRow label="API 地址">
                      <Input
                        value={provider.apiEndpoint}
                        onChange={(v) => updateProvider({ apiEndpoint: v })}
                        placeholder="https://api.example.com/v1/chat/completions"
                      />
                    </FieldRow>
                    <div className="grid grid-cols-2 gap-2">
                      <FieldRow label="API Key">
                        <div className="relative">
                          <Input
                            type="password"
                            value={provider.apiKey}
                            onChange={(v) => updateProvider({ apiKey: v })}
                            placeholder={provider.id === 'ollama' ? '本地无需填写' : 'sk-...'}
                          />
                        </div>
                      </FieldRow>
                      <FieldRow label="模型名称">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between gap-2">
                            <div className="text-xs text-gray-400 truncate">
                              {provider.id === 'ollama' ? 'Ollama 可自动拉取已安装模型' : '非 Ollama 本地服务可能需要手动输入'}
                            </div>
                            <button
                              type="button"
                              onClick={() => void fetchModels(provider)}
                              disabled={!!fetchingModelsByProvider[provider.id] || !provider.apiEndpoint?.trim()}
                              className="flex items-center gap-1 text-[11px] px-2 py-1 rounded border border-gray-200 bg-white text-blue-600 hover:bg-blue-50 disabled:opacity-50"
                              title="自动获取本地模型"
                            >
                              {fetchingModelsByProvider[provider.id] ? <Loader size={12} className="animate-spin" /> : <RefreshCw size={12} />}
                              自动获取
                            </button>
                          </div>

                          {(availableModelsByProvider[provider.id] ?? []).length > 0 ? (
                            <Select
                              value={provider.model}
                              onChange={(v) => updateProvider({ model: v })}
                              options={[
                                { value: '', label: '请选择模型' },
                                ...((availableModelsByProvider[provider.id] ?? []).map((m) => ({ value: m, label: m }))),
                                ...(provider.model && !(availableModelsByProvider[provider.id] ?? []).includes(provider.model)
                                  ? [{ value: provider.model, label: `${provider.model}（自定义）` }]
                                  : []),
                              ]}
                            />
                          ) : (
                            <Input
                              value={provider.model}
                              onChange={(v) => updateProvider({ model: v })}
                              placeholder="例如: qwen3.5:9b"
                            />
                          )}

                          {(availableModelsByProvider[provider.id] ?? []).length > 0 && (
                            <Input
                              value={provider.model}
                              onChange={(v) => updateProvider({ model: v })}
                              placeholder="也可手动输入（非列表模型）"
                            />
                          )}
                        </div>
                      </FieldRow>
                    </div>
                    <FieldRow label="超时（秒）">
                      <Input
                        type="number"
                        value={provider.timeout}
                        onChange={(v) => updateProvider({ timeout: Number(v) })}
                      />
                    </FieldRow>
                  </div>
                </div>
              );
            })()}

            <p className="text-xs text-gray-400">
              * AI 分析默认使用本地模型提供商进行处理。Ollama 作为本地模型服务无需填写 API Key。
            </p>
          </div>

          {aiTestResult && (
            <div className={`flex items-start gap-2 p-3 rounded-lg text-sm ${aiTestResult.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              <span>{aiTestResult.message}</span>
            </div>
          )}

          {/* 提示词配置 */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <h2 className="font-semibold text-gray-800">识别提示词</h2>
            {(Object.keys(aiForm.prompts) as (keyof AiConfig['prompts'])[]).map((key) => (
              <FieldRow key={key} label={PROMPT_LABELS[key] ?? key}>
                <Textarea
                  value={aiForm.prompts[key]}
                  onChange={(v) => updateAiPrompt(key, v)}
                  rows={2}
                />
              </FieldRow>
            ))}
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleSaveAi}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Save size={15} /> 保存 AI 配置
            </button>
          </div>
        </div>
      )}

      {/* ===== MinerU 配置 ===== */}
      {activeTab === 'mineru' && (
        <div className="space-y-5">
          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <h2 className="font-semibold text-gray-800">接口参数</h2>
            {true && (
              <>
                <FieldRow label="本地地址" hint="留空则默认使用 http://host.docker.internal:8083">
                  <Input
                    value={mineruForm.localEndpoint}
                    onChange={(v) => updateMineru({ localEndpoint: v })}
                    placeholder="http://localhost:8083"
                  />
                </FieldRow>
                <FieldRow label="本地超时（秒）">
                  <Input
                    type="number"
                    value={mineruForm.localTimeout}
                    onChange={(v) => updateMineru({ localTimeout: Number(v) })}
                  />
                </FieldRow>
                <FieldRow label="本地解析后端" hint="pipeline 为默认稳定路径；hybrid/vlm 使用本地 MinerU 的视觉模型能力，资源消耗更高，需先确认本机 MinerU 服务支持。">
                  <Select
                    value={mineruForm.localBackend || 'pipeline'}
                    onChange={(v) => updateMineru({ localBackend: v })}
                    options={[
                      { value: 'pipeline', label: 'pipeline（推荐/默认）' },
                      { value: 'hybrid-auto-engine', label: 'hybrid-auto-engine（旧版兼容）' },
                      { value: 'vlm-auto-engine', label: 'vlm-auto-engine（高精度/耗时）' },
                    ]}
                  />
                </FieldRow>
                <FieldRow label="max_pages">
                  <Input
                    type="number"
                    value={mineruForm.localMaxPages}
                    onChange={(v) => updateMineru({ localMaxPages: Number(v) })}
                  />
                </FieldRow>
                <FieldRow label="OCR 语言">
                  <Input
                    value={mineruForm.localOcrLanguage}
                    onChange={(v) => updateMineru({ localOcrLanguage: v })}
                    placeholder="ch"
                  />
                </FieldRow>
                {localTestResult && (
                  <div className={`flex items-start gap-2 p-3 rounded-lg text-sm ${localTestResult.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                    {localTestResult.ok
                      ? <CheckCircle size={16} className="mt-0.5 flex-shrink-0" />
                      : <XCircle size={16} className="mt-0.5 flex-shrink-0" />}
                    <span>{localTestResult.message}</span>
                  </div>
                )}
              </>
            )}
            {/* 模型版本已弃用并隐藏 */}
          </div>

          {/* 功能开关 */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
            <h2 className="font-semibold text-gray-800">功能开关</h2>
            {[
              { key: 'enableOcr',     label: 'OCR 识别' },
              { key: 'enableFormula', label: '公式识别' },
              { key: 'enableTable',   label: '表格识别' },
            ].map((item) => {
              const val = mineruForm[item.key as keyof MinerUConfig] as boolean;
              return (
                <label key={item.key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer">
                  <span className="text-sm text-gray-700">{item.label}</span>
                  <input
                    type="checkbox"
                    checked={val}
                    onChange={(e) => updateMineru({ [item.key]: e.target.checked })}
                    className="w-4 h-4 rounded"
                  />
                </label>
              );
            })}
            <FieldRow label="识别语言">
              <Input
                value={mineruForm.language}
                onChange={(v) => updateMineru({ language: v })}
                placeholder="ch"
              />
            </FieldRow>
          </div>

          <div className="flex justify-end">
            {true && (
              <button
                onClick={handleTestLocalMineru}
                disabled={localTesting}
                className="mr-3 flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                {localTesting ? <Loader size={14} className="animate-spin" /> : <ScanLine size={14} />}
                {localTesting ? '测试中...' : '测试本地连接'}
              </button>
            )}
            <button
              onClick={handleSaveMineru}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Save size={15} /> 保存 MinerU 配置
            </button>
          </div>
        </div>
      )}

      {/* ===== 存储配置 ===== */}
      {activeTab === 'storage' && (
        <div className="space-y-5">
          {/* 存储后端 */}

          {/* MinIO 连接参数 */}
          <div className="bg-white rounded-xl border p-5 space-y-4 transition-opacity border-gray-200">
            <h2 className="font-semibold text-gray-800">MinIO 连接参数</h2>
            <FieldRow label="端点地址" hint="主机名或 IP，不含协议">
              <Input
                value={minioForm.endpoint}
                onChange={(v) => updateMinio({ endpoint: v })}
                placeholder="minio 或 192.168.1.100"
              />
            </FieldRow>
            <FieldRow label="端口">
              <Input
                type="number"
                value={minioForm.port}
                onChange={(v) => updateMinio({ port: Number(v) })}
                placeholder="9000"
              />
            </FieldRow>
            <FieldRow label="使用 SSL">
              <label className="flex items-center gap-2 cursor-pointer mt-2">
                <input
                  type="checkbox"
                  checked={minioForm.useSSL}
                  onChange={(e) => updateMinio({ useSSL: e.target.checked })}
                  className="w-4 h-4 rounded"
                />
                <span className="text-sm text-gray-700">启用 HTTPS</span>
              </label>
            </FieldRow>
            <FieldRow label="Access Key">
              <div className="relative">
                <Input
                  type={showMinioKeys.access ? 'text' : 'password'}
                  value={minioForm.accessKey}
                  onChange={(v) => updateMinio({ accessKey: v })}
                  placeholder="minioadmin"
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowMinioKeys((p) => ({ ...p, access: !p.access }))}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showMinioKeys.access ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </FieldRow>
            <FieldRow label="Secret Key">
              <div className="relative">
                <Input
                  type={showMinioKeys.secret ? 'text' : 'password'}
                  value={minioForm.secretKey}
                  onChange={(v) => updateMinio({ secretKey: v })}
                  placeholder="minioadmin"
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowMinioKeys((p) => ({ ...p, secret: !p.secret }))}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showMinioKeys.secret ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </FieldRow>
            <FieldRow label="原始资料 Bucket" hint="存放上传原始文件的存储桶">
              <Input
                value={minioForm.bucket}
                onChange={(v) => updateMinio({ bucket: v })}
                placeholder="eduassets"
              />
            </FieldRow>
            <FieldRow label="解析产物 Bucket" hint="存放 MinerU 解析输出物的存储桶">
              <Input
                value={minioForm.parsedBucket}
                onChange={(v) => updateMinio({ parsedBucket: v })}
                placeholder="eduassets-parsed"
              />
            </FieldRow>
            <FieldRow label="URL 有效期" hint="预签名 URL 有效秒数">
              <Input
                type="number"
                value={minioForm.presignedExpiry}
                onChange={(v) => updateMinio({ presignedExpiry: Number(v) })}
                placeholder="3600"
              />
            </FieldRow>
          </div>

          {/* 测试结果 */}
          {testResult && (
            <div className={`flex items-start gap-2 p-3 rounded-lg text-sm ${testResult.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {testResult.ok
                ? <CheckCircle size={16} className="mt-0.5 flex-shrink-0" />
                : <XCircle size={16} className="mt-0.5 flex-shrink-0" />}
              <span>{testResult.message}</span>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex items-center justify-between">
            <button
              onClick={handleTestMinio}
              disabled={testing}
              className="flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {testing ? <Loader size={14} className="animate-spin" /> : <Database size={14} />}
              {testing ? '测试中...' : '测试连接'}
            </button>
            <button
              onClick={handleSaveMinio}
              disabled={savingMinio}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {savingMinio ? <Loader size={15} className="animate-spin" /> : <Save size={15} />}
              {savingMinio ? '保存中...' : '保存存储配置'}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'backup' && (
        <div className="space-y-5">
          <input
            ref={jsonImportInputRef}
            type="file"
            accept="application/json,.json"
            className="hidden"
            onChange={handleImportBackup}
          />
          <input
            ref={fullImportInputRef}
            type="file"
            accept=".zip,application/zip"
            className="hidden"
            onChange={handleSelectFullImport}
          />

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <p className="text-xs text-gray-500">JSON 数据库大小</p>
              <p className="mt-1 text-2xl font-semibold text-gray-900">{formatBytes(dbStats?.fileSize || 0)}</p>
              <p className="mt-1 text-xs text-gray-400">materials {dbStats?.counts?.materials || 0} · settings {dbStats?.counts?.settings || 0}</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <p className="text-xs text-gray-500">对象存储占用</p>
              <p className="mt-1 text-2xl font-semibold text-gray-900">{formatBytes(storageStats?.totalSize || 0)}</p>
              <p className="mt-1 text-xs text-gray-400">{storageStats?.backend || 'unknown'} · {storageStats?.totalObjects || 0} 个对象</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <p className="text-xs text-gray-500">总占用</p>
              <p className="mt-1 text-2xl font-semibold text-gray-900">{formatBytes(totalUsage)}</p>
              <p className="mt-1 text-xs text-gray-400">数据库 + 文件存储</p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-800">容量管理</h2>
              <button
                onClick={refreshBackupStats}
                disabled={backupLoading}
                className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                {backupLoading ? <Loader size={14} className="animate-spin" /> : <HardDrive size={14} />}
                {backupLoading ? '刷新中...' : '刷新统计'}
              </button>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FieldRow label="数据库软上限">
                <Input
                  type="number"
                  value={capacityLimits.dbSoftLimitMB}
                  onChange={(v) => setCapacityLimits((prev) => ({ ...prev, dbSoftLimitMB: Number(v) }))}
                />
              </FieldRow>
              <FieldRow label="对象存储软上限">
                <Input
                  type="number"
                  value={capacityLimits.storageSoftLimitGB}
                  onChange={(v) => setCapacityLimits((prev) => ({ ...prev, storageSoftLimitGB: Number(v) }))}
                />
              </FieldRow>
            </div>
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                  <span>JSON 数据库</span>
                  <span className={getUsageTextTone(dbUsageRatio)}>
                    {formatBytes(dbStats?.fileSize || 0)} / {formatBytes(dbLimitBytes)}
                  </span>
                </div>
                <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                  <div className={`h-full ${getUsageTone(dbUsageRatio)}`} style={{ width: `${Math.min(dbUsageRatio * 100, 100)}%` }} />
                </div>
                <p className={`mt-1 text-xs ${getUsageTextTone(dbUsageRatio)}`}>
                  使用率 {(dbUsageRatio * 100).toFixed(1)}% · 剩余 {formatBytes(Math.max(dbLimitBytes - (dbStats?.fileSize || 0), 0))}
                </p>
              </div>
              <div>
                <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                  <span>对象存储</span>
                  <span className={getUsageTextTone(storageUsageRatio)}>
                    {formatBytes(storageStats?.totalSize || 0)} / {formatBytes(storageLimitBytes)}
                  </span>
                </div>
                <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                  <div className={`h-full ${getUsageTone(storageUsageRatio)}`} style={{ width: `${Math.min(storageUsageRatio * 100, 100)}%` }} />
                </div>
                <p className={`mt-1 text-xs ${getUsageTextTone(storageUsageRatio)}`}>
                  使用率 {(storageUsageRatio * 100).toFixed(1)}% · 剩余 {formatBytes(Math.max(storageLimitBytes - (storageStats?.totalSize || 0), 0))}
                </p>
              </div>
            </div>
            {(dbUsageRatio >= 0.7 || storageUsageRatio >= 0.7) && (
              <div className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm ${dbUsageRatio >= 0.9 || storageUsageRatio >= 0.9 ? 'border-red-200 bg-red-50 text-red-700' : 'border-yellow-200 bg-yellow-50 text-yellow-700'}`}>
                <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />
                <span>接近容量上限，建议清理或扩容。</span>
              </div>
            )}
            <div className="flex justify-end">
              <button
                onClick={handleSaveCapacity}
                disabled={savingCapacity}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {savingCapacity ? <Loader size={14} className="animate-spin" /> : <Save size={14} />}
                {savingCapacity ? '保存中...' : '保存容量阈值'}
              </button>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <h2 className="font-semibold text-gray-800">对象存储明细</h2>
            <div className="space-y-3">
              {(storageStats?.buckets || []).map((bucket) => (
                <div key={bucket.name} className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{bucket.name}</p>
                    <p className="text-xs text-gray-400">{bucket.objectCount} 个对象</p>
                  </div>
                  <p className="text-sm text-gray-700">{formatBytes(bucket.totalSize)}</p>
                </div>
              ))}
              {(storageStats?.buckets || []).length === 0 && (
                <div className="text-sm text-gray-400">当前没有可用的桶统计信息</div>
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <h2 className="font-semibold text-gray-800">容量画像</h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-lg bg-gray-50 p-4">
                <p className="text-xs text-gray-500">资料总字节数</p>
                <p className="mt-1 text-lg font-semibold text-gray-900">{formatBytes(dbStats?.materialsTotalSizeBytes || 0)}</p>
              </div>
              <div className="rounded-lg bg-gray-50 p-4">
                <p className="text-xs text-gray-500">学科覆盖</p>
                <p className="mt-1 text-lg font-semibold text-gray-900">{Object.keys(dbStats?.materialsBySubject || {}).length} 个学科</p>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-700">按状态分布</p>
                {Object.entries(dbStats?.materialsByStatus || {}).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm text-gray-700">
                    <span>{key}</span>
                    <span>{value}</span>
                  </div>
                ))}
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-700">按学科分布</p>
                {Object.entries(dbStats?.materialsBySubject || {}).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm text-gray-700">
                    <span>{key}</span>
                    <span>{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <h2 className="font-semibold text-gray-800">备份导出 (安全操作)</h2>
            <div className="rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
              导出元数据 JSON 仅保存数据库记录，不包含 MinIO 文件。完整资产备份会打包原始资料、解析产物与数据库快照。
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-lg border border-gray-200 p-4 space-y-3">
                <p className="font-medium text-gray-800">JSON 元数据备份</p>
                <p className="text-xs text-gray-500">适合快速迁移数据库记录，文件体积小。</p>
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleExportBackup}
                    className="flex items-center gap-2 px-4 py-2 text-sm border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50"
                  >
                    <Download size={14} /> 导出元数据 JSON
                  </button>
                </div>
              </div>
              <div className="rounded-lg border border-gray-200 p-4 space-y-3">
                <p className="font-medium text-gray-800">完整资产备份</p>
                <p className="text-xs text-gray-500">包含完整的 JSON 数据库、MinIO 原始资料与解析产物文件。</p>
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleFullExportBackup}
                    disabled={exportingFull}
                    className="flex items-center gap-2 px-4 py-2 text-sm border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {exportingFull ? <Loader size={14} className="animate-spin" /> : <Download size={14} />}
                    {exportingFull ? '正在导出...' : '导出完整资产'}
                  </button>
                </div>
                {exportingFull && (
                  <p className="text-xs text-amber-600">正在打包完整资产，大容量备份可能耗时较长，请勿重复点击。</p>
                )}
              </div>
            </div>
          </div>

          <div className="bg-red-50 rounded-xl border border-red-200 p-5 space-y-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="text-red-600" size={20} />
              <h2 className="font-semibold text-red-800">危险区域 (Danger Zone) - 导入与恢复</h2>
            </div>
            <div className="rounded-lg border border-red-100 bg-white/60 px-4 py-3 text-sm text-red-700">
              警告：导入操作可能会覆盖或修改现有的生产数据。进行导入前，强烈建议先执行一次上方的数据导出备份。
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-lg border border-red-200 p-4 space-y-3 bg-white">
                <p className="font-medium text-red-800">导入元数据 JSON</p>
                <p className="text-xs text-red-600/80">将覆盖当前数据库记录。</p>
                <button
                  onClick={() => jsonImportInputRef.current?.click()}
                  className="flex items-center gap-2 px-4 py-2 text-sm border border-red-200 rounded-lg text-red-700 hover:bg-red-50"
                >
                  <Upload size={14} /> 导入元数据 JSON
                </button>
              </div>
              <div className="rounded-lg border border-red-200 p-4 space-y-3 bg-white">
                <p className="font-medium text-red-800">导入完整资产</p>
                <p className="text-xs text-red-600/80">选择导入模式并上传压缩包。</p>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => fullImportInputRef.current?.click()}
                    className="flex items-center gap-2 px-4 py-2 text-sm border border-red-200 rounded-lg text-red-700 hover:bg-red-50"
                  >
                    <Upload size={14} /> 导入完整资产
                  </button>
                </div>
                <div className="flex gap-4 text-sm text-red-800 mt-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      checked={fullImportMode === 'replace'}
                      onChange={() => setFullImportMode('replace')}
                    />
                    <span className="font-semibold">replace 覆盖恢复</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      checked={fullImportMode === 'merge'}
                      onChange={() => setFullImportMode('merge')}
                    />
                    <span>merge 仅补缺失</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {confirmState && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-5 space-y-4">
              <div className="flex items-start gap-3">
                <AlertTriangle size={18} className="mt-0.5 text-red-600" />
                <div className="space-y-1">
                  <p className="font-semibold text-red-700">危险操作确认</p>
                  {confirmState.kind === 'json' ? (
                    <p className="text-sm text-red-700">
                      导入元数据 JSON 会覆盖当前数据库，并自动创建 .bak 备份。MinIO 文件不会被恢复。
                    </p>
                  ) : confirmState.mode === 'replace' ? (
                    <div className="space-y-2">
                      <p className="text-sm text-red-700">
                        <strong>replace 模式</strong>：将清空 MinIO 原始桶与解析桶中的所有对象，再写入备份包内容。
                        <br />
                        <span className="font-semibold">MinIO 文件删除不可回滚</span>；db-server 会自动创建 .bak 备份可回滚数据库。
                      </p>
                      <p className="text-sm text-red-700">请在下方输入 <strong>REPLACE</strong> 以确认此危险操作：</p>
                      <input
                        type="text"
                        value={confirmInput}
                        onChange={(e) => setConfirmInput(e.target.value)}
                        placeholder="输入 REPLACE"
                        className="w-full px-3 py-2 text-sm border border-red-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-300 bg-white"
                      />
                    </div>
                  ) : (
                    <p className="text-sm text-red-700">
                      merge 模式：仅补充数据库与 MinIO 中缺失的对象，不覆盖已有数据。
                    </p>
                  )}
                  <p className="text-xs text-red-600">待导入文件：{confirmState.fileName}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleConfirmImport}
                  disabled={
                    confirmState.kind === 'full' && confirmState.mode === 'replace'
                      ? confirmInput !== 'REPLACE'
                      : false
                  }
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Upload size={14} /> 确认导入
                </button>
                <button
                  onClick={() => { setConfirmState(null); setConfirmInput(''); }}
                  className="px-4 py-2 text-sm border border-red-200 text-red-700 rounded-lg hover:bg-white"
                >
                  取消
                </button>
              </div>
            </div>
          )}

          {importResult && (
            <div className="rounded-xl border border-green-200 bg-green-50 p-5 space-y-4">
              <div className="flex items-start gap-3">
                <CheckCircle size={18} className="mt-0.5 text-green-600" />
                <div className="space-y-1">
                  <p className="font-semibold text-green-700">恢复完成</p>
                  <p className="text-xs text-green-600">
                    模式：{importResult.mode === 'json' ? 'JSON 元数据' : importResult.mode}
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {importResult.materialsCount !== undefined && (
                  <div className="rounded-lg bg-white border border-green-100 px-4 py-3">
                    <p className="text-xs text-gray-500">资料记录数</p>
                    <p className="text-lg font-semibold text-gray-900">{importResult.materialsCount}</p>
                  </div>
                )}
                {importResult.importedObjects !== undefined && (
                  <div className="rounded-lg bg-white border border-green-100 px-4 py-3">
                    <p className="text-xs text-gray-500">已导入对象</p>
                    <p className="text-lg font-semibold text-gray-900">{importResult.importedObjects}</p>
                  </div>
                )}
                {importResult.removedExistingObjects !== undefined && (
                  <div className="rounded-lg bg-white border border-green-100 px-4 py-3">
                    <p className="text-xs text-gray-500">已清除旧对象</p>
                    <p className="text-lg font-semibold text-gray-900">{importResult.removedExistingObjects}</p>
                  </div>
                )}
                {importResult.skippedObjects !== undefined && (
                  <div className="rounded-lg bg-white border border-green-100 px-4 py-3">
                    <p className="text-xs text-gray-500">跳过（已存在）</p>
                    <p className="text-lg font-semibold text-gray-900">{importResult.skippedObjects}</p>
                  </div>
                )}
                {importResult.backupPath && (
                  <div className="rounded-lg bg-white border border-green-100 px-4 py-3 col-span-2 sm:col-span-3">
                    <p className="text-xs text-gray-500">.bak 备份路径</p>
                    <p className="text-xs font-mono text-gray-700 break-all">{importResult.backupPath}</p>
                  </div>
                )}
              </div>
              <button
                onClick={() => { setImportResult(null); clearLocalStateAndReload(); }}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                完成并刷新页面
              </button>
            </div>
          )}
        </div>
      )}




    </div>
  );
}
