import { parseLatestMineruProgress, inspectMineruLogChannelOwnership } from './ops-mineru-log-parser.mjs';

function isLocalMineruTask(task) {
  return task?.engine === 'local-mineru' && task.state !== 'canceled' && !task.metadata?.canceledAt;
}

function hasMineruParsedArtifacts(task) {
  const metadata = task?.metadata || {};
  return Number(metadata.parsedFilesCount || 0) > 0 ||
    Boolean(metadata.markdownObjectName) ||
    Boolean(metadata.zipObjectName) ||
    Boolean(metadata.artifactManifestObjectName);
}

function isHistoricalTerminalAiFailure(task) {
  if (!isLocalMineruTask(task)) return false;
  if (task.state !== 'failed') return false;
  if (task.metadata?.mineruStatus !== 'completed') return false;
  if (!task.metadata?.mineruTaskId) return false;
  if (!hasMineruParsedArtifacts(task)) return false;

  return task.stage === 'ai' ||
    task.stage === 'ai-running' ||
    task.stage === 'ai-pending' ||
    Boolean(task.aiJobId || task.metadata?.aiJobId) ||
    String(task.message || '').includes('AI');
}

export function classifyMineruActiveTasks(tasks = []) {
  const runningWithMineru = tasks.filter(t =>
    isLocalMineruTask(t) &&
    t.state === 'running' &&
    t.metadata?.mineruTaskId &&
    ['mineru-processing', 'mineru-queued', 'result-fetching'].includes(t.stage)
  );

  const driftTasks = tasks.filter(t =>
    isLocalMineruTask(t) &&
    t.metadata?.mineruTaskId &&
    (
      t.state === 'pending' ||
      (t.state === 'running' && (t.stage === 'upload' || t.stage === 'process'))
    )
  );

  const completedButNotIngestedTasks = tasks.filter(t =>
    isLocalMineruTask(t) &&
    t.metadata?.mineruTaskId &&
    t.metadata?.mineruStatus === 'completed' &&
    !hasMineruParsedArtifacts(t)
  );

  const submitRetryableTasks = tasks.filter(t =>
    isLocalMineruTask(t) &&
    (t.stage === 'submit-failed-retryable' || t.message?.includes('可重试'))
  );

  const historicalAiFailureTasks = tasks.filter(isHistoricalTerminalAiFailure);

  const takeoverRequiredTasks = tasks.filter(t =>
    isLocalMineruTask(t) &&
    t.metadata?.mineruTaskId &&
    !isHistoricalTerminalAiFailure(t) &&
    (
      (t.state === 'failed' && t.metadata?.mineruStatus === 'completed') ||
      (t.state === 'running' && t.stage === 'mineru-processing' && t.metadata?.mineruStatus === 'completed')
    )
  );

  return {
    runningWithMineru,
    driftTasks,
    completedButNotIngestedTasks,
    submitRetryableTasks,
    historicalAiFailureTasks,
    takeoverRequiredTasks,
  };
}

export function registerMineruDiagnosticsRoutes(app, getDbBaseUrl) {
  app.get('/ops/mineru/diagnostics', async (req, res) => {
    const dbBaseUrl = getDbBaseUrl();

    let localEndpoint = process.env.LOCAL_MINERU_ENDPOINT || 'http://host.docker.internal:8083';
    try {
      const setResp = await fetch(`${dbBaseUrl}/settings`, { signal: AbortSignal.timeout(1000) });
      if (setResp.ok) {
        const settings = await setResp.json();
        if (settings?.mineruConfig?.localEndpoint) localEndpoint = settings.mineruConfig.localEndpoint;
      }
    } catch (ee) { /* ignore */ }

    if (localEndpoint.includes('localhost') || localEndpoint.includes('127.0.0.1')) {
      localEndpoint = localEndpoint.replace(/localhost|127\.0\.0\.1/g, 'host.docker.internal');
    }
    localEndpoint = localEndpoint.replace(/\/+$/, '');

    const result = {
      ok: true,
      mineru: { endpoint: localEndpoint, healthy: false, processingTasks: 0, queuedTasks: 0, maxConcurrentRequests: 1 },
      luceon: { activeTasks: [], knownMineruTaskIds: [], mineruQueuedTasks: [], mineruProcessingTasks: [] },
      diagnosis: { status: 'unknown', kind: 'unknown', message: '', blockingMineruTaskId: null, safeToAutoRecover: false },
      logObservation: null,
      takeoverRequiredTasks: [],
      historicalAiFailureTasks: [],
      completedButNotIngestedTasks: [],
      submitRetryableTasks: [],
      observabilityDetails: {
        realMineruLifecycle: 'unknown',
        dbTaskState: 'unknown',
        hostLogFreshness: null,
        containerLogFreshness: null,
        activeDisplaySource: 'none'
      }
    };

    // 1. Fetch MinerU health
    try {
      const healthRes = await fetch(`${localEndpoint}/health`, { signal: AbortSignal.timeout(3000) });
      if (healthRes.ok) {
        const data = await healthRes.json();
        result.mineru.healthy = true;
        result.mineru.processingTasks = data.processing_tasks || 0;
        result.mineru.queuedTasks = data.queued_tasks || 0;
        result.mineru.maxConcurrentRequests = data.max_concurrent_requests || 1;
      } else {
        result.diagnosis.status = 'unreachable';
        result.diagnosis.message = `MinerU HTTP ${healthRes.status}`;
        return res.json(result);
      }
    } catch (e) {
      result.diagnosis.status = 'unreachable';
      result.diagnosis.message = `MinerU 连接失败: ${e.message}`;
      return res.json(result);
    }

    // 2. Fetch Luceon Tasks
    let tasks = [];
    try {
      const tasksRes = await fetch(`${dbBaseUrl}/tasks`, { signal: AbortSignal.timeout(3000) });
      if (tasksRes.ok) {
        tasks = await tasksRes.json();
        const activeStates = ['pending', 'running', 'result-store', 'ai-pending', 'ai-running'];
        const classifiedTasks = classifyMineruActiveTasks(tasks);

        result.luceon.activeTasks = tasks.filter(t => activeStates.includes(t.state)).map(t => t.id);
        result.luceon.mineruQueuedTasks = tasks.filter(t => t.stage === 'mineru-queued').map(t => t.id);
        result.luceon.mineruProcessingTasks = tasks.filter(t => t.stage === 'mineru-processing').map(t => t.id);

        result.completedButNotIngestedTasks = classifiedTasks.completedButNotIngestedTasks.map(t => t.id);
        result.submitRetryableTasks = classifiedTasks.submitRetryableTasks.map(t => t.id);
        result.takeoverRequiredTasks = classifiedTasks.takeoverRequiredTasks.map(t => t.id);
        result.historicalAiFailureTasks = classifiedTasks.historicalAiFailureTasks.map(t => t.id);

        if (result.luceon.mineruProcessingTasks.length > 0) {
          const targetTaskId = result.luceon.mineruProcessingTasks[0];
          const targetTask = tasks.find(t => t.id === targetTaskId);
          if (targetTask) {
            const minObservedAt = targetTask.metadata?.mineruStartedAt || targetTask.updatedAt || targetTask.createdAt;
            result.logObservation = await parseLatestMineruProgress(minObservedAt, targetTask.metadata?.mineruObservedProgress, targetTask.metadata?.mineruExecutionProfile).catch(() => null);
          }
        }

        // Find all known MinerU task IDs
        const knownIdsMap = new Map();
        for (const t of tasks) {
          if (t.metadata?.mineruTaskId) {
            knownIdsMap.set(t.metadata.mineruTaskId, t);
          }
        }
        result.luceon.knownMineruTaskIds = Array.from(knownIdsMap.keys());
        result.luceon.knownMineruTaskMap = Object.fromEntries(knownIdsMap);
      } else {
        result.diagnosis.status = 'error';
        result.diagnosis.message = '无法从 db-server 获取 Luceon 任务';
        return res.json(result);
      }
    } catch (e) {
      result.diagnosis.status = 'error';
      result.diagnosis.message = `无法连接到 db-server 获取 Luceon 任务: ${e.message}`;
      return res.json(result);
    }

    // 3. Diagnosis Logic
    if (result.mineru.processingTasks === 0) {
      result.diagnosis.status = 'healthy';
      result.diagnosis.kind = 'idle';
      result.diagnosis.message = 'MinerU 当前空闲';

      // Calculate observability details even when idle
      let targetTaskForDiagnostics = tasks.find(isLocalMineruTask);
      if (targetTaskForDiagnostics) {
        await populateObservabilityDetails(result, targetTaskForDiagnostics);
      } else {
        result.observabilityDetails = {
          realMineruLifecycle: 'idle',
          dbTaskState: 'none',
          hostLogFreshness: null,
          containerLogFreshness: null,
          activeDisplaySource: 'none'
        };
      }
      return res.json(result);
    }

    // processingTasks > 0
    let actualProcessingMineruTaskId = null;
    let actualProcessingLuceonTaskInfo = null;
    let actualMineruTaskStartedAt = null;
    let foundLuceonTaskProcessing = result.luceon.mineruProcessingTasks.length > 0;

    // Deep check known MinerU tasks if MinerU says it's processing
    if (!foundLuceonTaskProcessing) {
      for (const mTaskId of result.luceon.knownMineruTaskIds) {
        try {
          const tRes = await fetch(`${localEndpoint}/tasks/${mTaskId}`, { signal: AbortSignal.timeout(1000) });
          if (tRes.ok) {
            const tData = await tRes.json();
            if (tData.status === 'processing' || tData.status === 'running' || (tData.started_at && !['done', 'success', 'completed', 'succeeded', 'failed'].includes(tData.status))) {
              actualProcessingMineruTaskId = mTaskId;
              actualProcessingLuceonTaskInfo = result.luceon.knownMineruTaskMap[mTaskId];
              actualMineruTaskStartedAt = tData.started_at;
              break;
            }
          }
        } catch (e) { /* ignore */ }
      }
    }

    if (foundLuceonTaskProcessing) {
      result.diagnosis.status = 'busy';
      result.diagnosis.kind = 'luceon-processing';
      result.diagnosis.message = 'MinerU 正被 Luceon 已知任务占用';
      result.diagnosis.blockingMineruTaskId = 'known-luceon-task';
    } else if (actualProcessingMineruTaskId) {
      if (actualProcessingLuceonTaskInfo && ['failed', 'canceled'].includes(actualProcessingLuceonTaskInfo.state)) {
        result.diagnosis.status = 'blocked';
        result.diagnosis.kind = 'known-failed-but-mineru-processing';
        result.diagnosis.message = 'Luceon 任务已进入失败/取消终态，但 MinerU 仍在处理该内部任务，当前解析槽位被历史任务占用。';
        result.diagnosis.blockingMineruTaskId = actualProcessingMineruTaskId;
        result.diagnosis.blockingLuceonTaskId = actualProcessingLuceonTaskInfo.id;
        result.diagnosis.safeToAutoRecover = false;

        const minObservedAt = actualMineruTaskStartedAt || actualProcessingLuceonTaskInfo.metadata?.mineruStartedAt || actualProcessingLuceonTaskInfo.updatedAt || actualProcessingLuceonTaskInfo.createdAt;
        result.logObservation = await parseLatestMineruProgress(minObservedAt, actualProcessingLuceonTaskInfo.metadata?.mineruObservedProgress, actualProcessingLuceonTaskInfo.metadata?.mineruExecutionProfile).catch(() => null);
      } else {
        result.diagnosis.status = 'busy';
        result.diagnosis.kind = 'luceon-processing';
        result.diagnosis.message = 'MinerU 正被 Luceon 已知任务占用';
        result.diagnosis.blockingMineruTaskId = actualProcessingMineruTaskId;
      }
    } else {
      result.diagnosis.status = 'blocked';
      result.diagnosis.kind = 'orphan-processing-blocker';
      result.diagnosis.message = 'MinerU 当前被未知任务占用，Luceon 队列暂停推进';
      result.diagnosis.blockingMineruTaskId = 'unknown (MinerU API 当前不提供任务列表)';
      result.diagnosis.safeToAutoRecover = false;
    }

    // Populate observabilityDetails for processing cases
    let targetTaskForDiagnostics = null;
    if (result.luceon.mineruProcessingTasks.length > 0) {
      const targetTaskId = result.luceon.mineruProcessingTasks[0];
      targetTaskForDiagnostics = tasks.find(t => t.id === targetTaskId);
    } else if (actualProcessingLuceonTaskInfo) {
      targetTaskForDiagnostics = actualProcessingLuceonTaskInfo;
    } else {
      targetTaskForDiagnostics = tasks.find(isLocalMineruTask);
    }

    if (targetTaskForDiagnostics) {
      await populateObservabilityDetails(result, targetTaskForDiagnostics);
    }

    res.json(result);
  });

  app.post('/ops/mineru/recover', async (req, res) => {
    const isDryRun = req.body?.dryRun !== false; // default true
    const confirm = req.body?.confirm === true;

    if (isDryRun || !confirm) {
      return res.json({
        ok: true,
        dryRun: true,
        wouldRestartMineru: true,
        reason: "orphan-processing-blocker",
        instructions: [
          "停止 mineru_api tmux session",
          "重新启动 conda mineru-api",
          "运行 node server/tests/mineru-deep-check.mjs",
          "确认 queued tasks 继续推进"
        ]
      });
    }

    // For safety, this task doesn't require actual restart implementation if dry-run is provided
    return res.json({
      ok: false,
      error: '服务端直接重启尚未实现，请参考 dryRun 提供的 instructions 手动清障。'
    });
  });
}

async function populateObservabilityDetails(result, targetTask) {
  const minObservedAt = targetTask.metadata?.mineruStartedAt || targetTask.updatedAt || targetTask.createdAt;
  const logChannelDiagnostics = await inspectMineruLogChannelOwnership({
    minObservedAt,
    nowMs: Date.now()
  }).catch(() => null);

  if (logChannelDiagnostics) {
    const hostLog = logChannelDiagnostics.sources.find(s => s.logSourceContext === 'host-filesystem');
    const containerLog = logChannelDiagnostics.sources.find(s => s.logSourceContext === 'container-mounted-log');

    result.observabilityDetails = {
      realMineruLifecycle: targetTask.metadata?.mineruStatus || 'unknown',
      dbTaskState: `${targetTask.state || 'unknown'} / ${targetTask.stage || 'unknown'}`,
      hostLogFreshness: hostLog ? {
        exists: hostLog.exists,
        size: hostLog.size,
        mtime: hostLog.mtime,
        ageMs: hostLog.ageMs,
        state: hostLog.state
      } : null,
      containerLogFreshness: containerLog ? {
        exists: containerLog.exists,
        size: containerLog.size,
        mtime: containerLog.mtime,
        ageMs: containerLog.ageMs,
        state: containerLog.state
      } : null,
      activeDisplaySource: logChannelDiagnostics.selectedSource ? {
        logSourceContext: logChannelDiagnostics.selectedSource.logSourceContext,
        logSourceBaseName: logChannelDiagnostics.selectedSource.logSourceBaseName,
        state: logChannelDiagnostics.selectedSource.state,
        ageMs: logChannelDiagnostics.selectedSource.ageMs
      } : 'none'
    };
  }
}
