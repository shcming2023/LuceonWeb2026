/**
 * 批处理上传控制器（P1 Patch: 列表退场重构）
 *
 * - BatchProcessingController: 无 UI 后台组件，逐个提交 pending 队列到 /__proxy/upload/tasks，
 *   成功后立即从队列移除，仅保留"正在提交中"的短生命周期队列。
 * - batchRegisterFiles / batchGetFile / batchRemoveFile: 运行时内存中保存 File 二进制句柄。
 *
 * 已移除：
 * - BatchUploadModal（可见列表 UI）
 * - BatchProgressFab（右下角悬浮球）
 * - 长时间无进度 toast
 * - tracking / completed / failed 等终态在本地队列的保留
 * - 任务状态轮询（任务进度一律到 /cms/tasks 查看）
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'sonner';
import { useAppStore } from '../../store/appContext';
import type { BatchQueueItem } from '../../store/types';
import { generateNumericIdFromUuid } from '../../utils/id';
import { appendMineruTaskOptions } from '../utils/mineruTaskOptions';

/* ── 运行时文件句柄管理 ───────────────────────────────────── */

const runtimeFileMap: Map<string, File> =
  (globalThis as { __luceonBatchFileMap?: Map<string, File> }).__luceonBatchFileMap ||
  ((globalThis as { __luceonBatchFileMap?: Map<string, File> }).__luceonBatchFileMap = new Map<string, File>());

/**
 * 将文件句柄注册到运行时内存中，供 BatchProcessingController 使用。
 * @param items - 包含 id 和 file 的数组
 */
export function batchRegisterFiles(items: Array<{ id: string; file: File }>) {
  for (const it of items) runtimeFileMap.set(it.id, it.file);
}

/**
 * 从运行时内存获取文件句柄。
 * @param id - 队列项 ID
 * @returns File 对象或 undefined
 */
function batchGetFile(id: string) {
  return runtimeFileMap.get(id);
}

/**
 * 从运行时内存清除文件句柄。
 * @param id - 队列项 ID
 */
function batchRemoveFile(id: string) {
  runtimeFileMap.delete(id);
}

/* ── 网络工具 ────────────────────────────────────────────── */

/**
 * 带超时的 fetch 封装。
 * @param input - 请求地址
 * @param init - 请求选项，可额外传入 timeoutMs 控制超时
 * @returns Response
 */
async function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit & { timeoutMs?: number } = {}) {
  const { timeoutMs, ...rest } = init;
  const controller = new AbortController();
  const t = timeoutMs != null ? timeoutMs : 60_000;
  const timer = setTimeout(() => controller.abort(), t);
  try {
    return await fetch(input, { ...rest, signal: controller.signal });
  } catch (error) {
    const name = (error as { name?: string } | null)?.name;
    if (name === 'AbortError') {
      throw new Error(`请求超时（${Math.round(t / 1000)}s）`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

/* ── BatchProcessingController（无 UI 后台组件） ────────── */

/**
 * 批处理上传控制器。
 * 无任何 DOM 渲染，仅在后台按顺序从 pending 队列拾取文件，
 * 逐个提交到 /__proxy/upload/tasks。
 * 提交成功后立即从本地队列移除（不保留 tracking/completed/failed）。
 * 全部提交完毕后自动停止队列并 toast 汇总。
 *
 * @returns null（无 UI）
 */
export function BatchProcessingController() {
  const { state, dispatch } = useAppStore();
  const [working, setWorking] = useState(false);
  /** 本轮队列运行期间的提交统计 */
  const statsRef = useRef({
    submitted: 0,
    failed: 0,
    failReasons: [] as string[],
    auditLogs: [] as Array<{
      fileName: string;
      materialId: string;
      taskId?: string;
      ok: boolean;
      error?: string;
      timestamp: string;
    }>
  });
  /** 用于更新相同的 toast */
  const toastIdRef = useRef<string | number | null>(null);

  const items = state.batchProcessing.items;
  const running = state.batchProcessing.running;
  const paused = state.batchProcessing.paused;

  const nextPending = useMemo(
    () => items.find((i) => i.status === 'pending'),
    [items],
  );

  // 当前是否有正在上传中的项
  const activeUploading = useMemo(
    () => items.find((i) => i.status === 'uploading'),
    [items],
  );

  useEffect(() => {
    if (!running || paused || working) return;

    const stats = statsRef.current;
    const processed = stats.submitted + stats.failed;
    const total = items.length + processed;

    // 没有待提交项，且没有正在上传中的项 → 队列完成
    if (!nextPending && !activeUploading) {
      if (toastIdRef.current) {
        toast.dismiss(toastIdRef.current);
        toastIdRef.current = null;
      }

      if (stats.submitted > 0 || stats.failed > 0) {
        // 输出持久化的详细审计日志到控制台
        console.group(`[Luceon Batch Upload Audit Log] ${new Date().toLocaleString()}`);
        console.log(`Total: ${total}, Submitted: ${stats.submitted}, Failed: ${stats.failed}`);
        console.table(stats.auditLogs);
        console.groupEnd();

        // 挂载到全局，方便在浏览器 DevTools 中查询
        (globalThis as any).__luceonLastBatchAudit = {
          timestamp: new Date().toISOString(),
          total,
          submitted: stats.submitted,
          failed: stats.failed,
          logs: stats.auditLogs,
        };

        if (stats.failed === 0) {
          toast.success(`已提交 ${stats.submitted} 个文件，任务状态请在任务管理查看`, {
            description: `成功率: 100% (${stats.submitted}/${total})。对账单已输出至控制台，可在 DevTools 中输入 __luceonLastBatchAudit 查看。`,
            duration: 6000,
            action: {
              label: '前往任务管理',
              onClick: () => { window.location.href = '/cms/tasks'; },
            },
          });
        } else {
          const uniqueReasons = [...new Set(stats.failReasons)].slice(0, 3);
          toast.error(`${stats.failed} 个文件提交失败`, {
            description: [
              `成功: ${stats.submitted}/${total}，失败: ${stats.failed}/${total}`,
              ...uniqueReasons,
              `详细失败对账单请在 DevTools 控制台查看 (window.__luceonLastBatchAudit)`
            ].filter(Boolean).join('；'),
            duration: 10000,
          });
        }
        // 重置统计
        statsRef.current = { submitted: 0, failed: 0, failReasons: [], auditLogs: [] };
      }

      // 停止队列并清空残余
      dispatch({ type: 'BATCH_CLEAR' });
      return;
    }

    if (total > 0) {
      const msg = `正在批量上传 (${processed}/${total})...`;
      if (!toastIdRef.current) {
        toastIdRef.current = toast.loading(msg, { duration: Infinity });
      } else {
        toast.loading(msg, { id: toastIdRef.current, duration: Infinity });
      }
    }

    if (!nextPending) return;

    const file = batchGetFile(nextPending.id);
    if (!file) {
      // 文件句柄丢失（刷新页面导致），直接移除
      statsRef.current.failed += 1;
      statsRef.current.failReasons.push('文件句柄丢失（可能刷新页面导致）');
      dispatch({ type: 'BATCH_REMOVE_ITEM', payload: { id: nextPending.id } });
      return;
    }

    /**
     * 处理单个文件的上传提交。
     * @param item - 队列项
     * @param f - 对应的 File 对象
     */
    const processOne = async (item: BatchQueueItem, f: File) => {
      let materialId = item.materialId;
      try {
        // 健康检查
        const uploadHealth = await fetchWithTimeout('/__proxy/upload/health', { timeoutMs: 5000 }).catch(() => null);
        if (!uploadHealth?.ok) throw new Error('上传服务不可用（/__proxy/upload/health）');

        // 标记为上传中
        dispatch({
          type: 'BATCH_UPDATE_ITEM',
          payload: { id: item.id, updates: { status: 'uploading', progress: 10, message: '正在提交上传...' } },
        });

        if (!materialId) {
          materialId = generateNumericIdFromUuid();
          dispatch({ type: 'BATCH_UPDATE_ITEM', payload: { id: item.id, updates: { materialId } } });
        }

        const formData = new FormData();
        formData.append('file', f);
        formData.append('materialId', String(materialId));

        appendMineruTaskOptions(formData, state.mineruConfig);

        const uploadRes = await fetchWithTimeout('/__proxy/upload/tasks', {
          method: 'POST',
          body: formData,
          timeoutMs: 120_000,
        });

        if (!uploadRes.ok) {
          const errText = await uploadRes.text();
          let errPayload: { message?: string; error?: string; code?: string } | null = null;
          try {
            errPayload = JSON.parse(errText);
          } catch {
            errPayload = null;
          }
          const errMessage = errPayload?.message || errPayload?.error || errText;
          throw new Error(`上传失败: HTTP ${uploadRes.status} - ${errMessage}`);
        }

        const uploadResult = await uploadRes.json();
        const taskId = String(uploadResult?.taskId || '').trim();
        const objectName = String(uploadResult?.objectName || '').trim();
        if (!taskId) throw new Error('后端未返回 taskId（任务未确认创建）');
        if (!objectName) {
          throw new Error('上传成功但未获得 objectName（未写入 MinIO）。请检查存储后端配置。');
        }

        // 创建前端 Material 记录
        const fileName = String(uploadResult?.fileName || f.name || '').trim() || f.name;
        const title = fileName.replace(/\.[^.]+$/, '');
        dispatch({
          type: 'ADD_MATERIAL',
          payload: {
            id: materialId,
            title,
            type: (fileName.split('.').pop() || 'FILE').toUpperCase(),
            size: `${(f.size / 1024 / 1024).toFixed(1)} MB`,
            sizeBytes: f.size,
            uploadTime: '刚刚',
            uploadTimestamp: Date.now(),
            status: 'processing',
            mineruStatus: 'pending',
            aiStatus: 'pending',
            tags: [],
            metadata: {
              relativePath: item.path,
              objectName,
              fileName,
              provider: uploadResult?.provider,
              mimeType: uploadResult?.mimeType,
              processingStage: 'mineru',
              processingMsg: '等待后端队列处理',
              processingProgress: '0',
              processingUpdatedAt: new Date().toISOString(),
            },
            uploader: '当前用户',
          },
        });

        // 成功 → 立即从队列移除，不保留 tracking
        batchRemoveFile(item.id);
        dispatch({ type: 'BATCH_REMOVE_ITEM', payload: { id: item.id } });
        statsRef.current.submitted += 1;
        statsRef.current.auditLogs.push({
          fileName,
          materialId: String(materialId),
          taskId,
          ok: true,
          timestamp: new Date().toISOString(),
        });
      } catch (error) {
        const raw = error instanceof Error ? error.message : String(error);
        const lowered = raw.toLowerCase();

        // 尝试对账：网络中断但后端可能已成功
        const canReconcile = materialId != null
          && (lowered.includes('aborted') || lowered.includes('timeout') || lowered.includes('network') || lowered.includes('failed to fetch'));
        if (canReconcile) {
          try {
            const [taskResp, matResp] = await Promise.all([
              fetchWithTimeout('/__proxy/db/tasks', { timeoutMs: 5000 }).catch(() => null),
              fetchWithTimeout(`/__proxy/db/materials/${encodeURIComponent(String(materialId))}`, { timeoutMs: 5000 }).catch(() => null),
            ]);
            if (taskResp?.ok && matResp?.ok) {
              const tasks = await taskResp.json().catch(() => null);
              const material = await matResp.json().catch(() => null);
              const related = Array.isArray(tasks)
                ? tasks.find((t: Record<string, unknown>) => String(t?.materialId) === String(materialId))
                : null;
              const reconcileObjectName = String(material?.metadata?.objectName || '').trim();
              if (related && reconcileObjectName) {
                // 对账成功，视为提交成功
                batchRemoveFile(item.id);
                dispatch({ type: 'BATCH_REMOVE_ITEM', payload: { id: item.id } });
                statsRef.current.submitted += 1;
                statsRef.current.auditLogs.push({
                  fileName: f.name,
                  materialId: String(materialId),
                  taskId: related.id,
                  ok: true,
                  timestamp: new Date().toISOString(),
                });
                return;
              }
            }
          } catch {
            // 对账失败，继续走失败路径
          }
        }

        // 提交失败 → 立即移除，记录失败
        batchRemoveFile(item.id);
        dispatch({ type: 'BATCH_REMOVE_ITEM', payload: { id: item.id } });
        statsRef.current.failed += 1;
        statsRef.current.failReasons.push(raw.length > 80 ? raw.slice(0, 80) + '…' : raw);
        statsRef.current.auditLogs.push({
          fileName: f.name,
          materialId: String(materialId || ''),
          ok: false,
          error: raw,
          timestamp: new Date().toISOString(),
        });
      }
    };

    setWorking(true);
    processOne(nextPending, file).finally(() => {
      setWorking(false);
    });
  }, [dispatch, items, nextPending, activeUploading, paused, running, working]);

  return null;
}
