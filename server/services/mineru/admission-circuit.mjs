const DEFAULT_COOLDOWN_MS = 60_000;

export const MINERU_ADMISSION_MESSAGE = 'MinerU 当前不可接收新任务，文件未收取，请稍后重试。';

export function getAdmissionCooldownMs() {
  const raw = Number(process.env.MINERU_ADMISSION_CIRCUIT_COOLDOWN_MS);
  if (Number.isFinite(raw) && raw >= 0) return raw;
  return DEFAULT_COOLDOWN_MS;
}

export function normalizeMineruAdmissionCircuit(input = {}) {
  const nowIso = new Date().toISOString();
  const state = input?.state === 'open' ? 'open' : 'closed';
  return {
    version: 'mineru-admission-circuit.v0.1',
    state,
    reason: input?.reason || null,
    message: state === 'open' ? (input?.message || MINERU_ADMISSION_MESSAGE) : null,
    openedAt: input?.openedAt || null,
    closedAt: input?.closedAt || null,
    cooldownUntil: input?.cooldownUntil || null,
    lastSubmitProbe: input?.lastSubmitProbe || null,
    lastSuccessfulSubmitAt: input?.lastSuccessfulSubmitAt || null,
    closeCriteria: input?.closeCriteria || {
      submitProbeOk: false,
      cooldownElapsed: state !== 'open',
      activeTaskClean: true,
      dependencyBlockingClear: true,
    },
    counts: input?.counts || {
      parsePending: 0,
      parseRunning: 0,
      aiPending: 0,
      aiRunning: 0,
    },
    updatedAt: input?.updatedAt || nowIso,
  };
}

export function isMineruAdmissionCircuitOpen(circuit) {
  return normalizeMineruAdmissionCircuit(circuit).state === 'open';
}

export async function readMineruAdmissionCircuit(dbBaseUrl) {
  try {
    const resp = await fetch(`${dbBaseUrl}/settings`, { signal: AbortSignal.timeout(2000) });
    if (!resp.ok) return normalizeMineruAdmissionCircuit();
    const settings = await resp.json().catch(() => ({}));
    return normalizeMineruAdmissionCircuit(settings?.mineruAdmissionCircuit);
  } catch {
    return normalizeMineruAdmissionCircuit();
  }
}

export async function writeMineruAdmissionCircuit(dbBaseUrl, state) {
  const normalized = normalizeMineruAdmissionCircuit(state);
  try {
    const resp = await fetch(`${dbBaseUrl}/settings/mineruAdmissionCircuit`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(normalized),
      signal: AbortSignal.timeout(2000),
    });
    if (!resp.ok) {
      return { ok: false, state: normalized, error: `settings write HTTP ${resp.status}` };
    }
    return { ok: true, state: normalized };
  } catch (error) {
    return { ok: false, state: normalized, error: error.message };
  }
}

function probeFailureShouldOpen(probe = {}) {
  if (probe.ok === true) return false;
  const status = Number(probe.status || 0);
  if (status >= 500) return true;
  const error = String(probe.error || '').toLowerCase();
  return error.includes('timeout') ||
    error.includes('econnrefused') ||
    error.includes('missing task_id') ||
    error.includes('missing taskid') ||
    error.includes('invalid json');
}

export function summarizeAdmissionCounts({ tasks = [], aiJobs = [] } = {}) {
  return {
    parsePending: tasks.filter((task) => task?.state === 'pending').length,
    parseRunning: tasks.filter((task) => task?.state === 'running' || task?.state === 'result-store').length,
    aiPending: aiJobs.filter((job) => job?.state === 'pending' || job?.status === 'pending').length,
    aiRunning: aiJobs.filter((job) => job?.state === 'running' || job?.status === 'running').length,
  };
}

export function isActiveTaskSnapshotClean(activeSnapshot = {}) {
  return !activeSnapshot?.activeTask &&
    !activeSnapshot?.currentProcessingTask &&
    (activeSnapshot?.queuedTasks || []).length === 0 &&
    (activeSnapshot?.completedButNotIngestedTasks || []).length === 0 &&
    (activeSnapshot?.driftTasks || []).length === 0 &&
    (activeSnapshot?.takeoverRequiredTasks || []).length === 0;
}

export async function openMineruAdmissionCircuit(dbBaseUrl, reason, details = {}) {
  const previous = await readMineruAdmissionCircuit(dbBaseUrl);
  const nowIso = new Date().toISOString();
  const cooldownUntil = new Date(Date.now() + getAdmissionCooldownMs()).toISOString();
  return writeMineruAdmissionCircuit(dbBaseUrl, {
    ...previous,
    state: 'open',
    reason: reason || previous.reason || 'mineru-submit-path-unavailable',
    message: MINERU_ADMISSION_MESSAGE,
    openedAt: previous.state === 'open' ? (previous.openedAt || nowIso) : nowIso,
    closedAt: null,
    cooldownUntil,
    lastSubmitProbe: details.lastSubmitProbe || previous.lastSubmitProbe || null,
    closeCriteria: {
      submitProbeOk: false,
      cooldownElapsed: false,
      activeTaskClean: details.activeTaskClean === true,
      dependencyBlockingClear: details.dependencyBlockingClear === true,
    },
    counts: details.counts || previous.counts,
    updatedAt: nowIso,
  });
}

export async function recordMineruSubmitProbeForAdmission(dbBaseUrl, {
  submitProbe,
  activeSnapshot,
  dependencyBlockingClear,
  counts,
} = {}) {
  const previous = await readMineruAdmissionCircuit(dbBaseUrl);
  const nowMs = Date.now();
  const nowIso = new Date(nowMs).toISOString();
  const activeTaskClean = isActiveTaskSnapshotClean(activeSnapshot);
  const normalizedProbe = submitProbe ? { ...submitProbe, observedAt: nowIso } : null;

  if (submitProbe?.ok === true) {
    const cooldownUntilMs = previous.cooldownUntil ? new Date(previous.cooldownUntil).getTime() : 0;
    const cooldownElapsed = !Number.isFinite(cooldownUntilMs) || cooldownUntilMs <= nowMs;
    const canClose = cooldownElapsed && activeTaskClean && dependencyBlockingClear === true;
    const next = {
      ...previous,
      state: canClose ? 'closed' : previous.state,
      reason: canClose ? null : (previous.reason || 'mineru-submit-recovery-pending'),
      message: canClose ? null : MINERU_ADMISSION_MESSAGE,
      closedAt: canClose ? nowIso : previous.closedAt,
      lastSubmitProbe: normalizedProbe,
      lastSuccessfulSubmitAt: nowIso,
      closeCriteria: {
        submitProbeOk: true,
        cooldownElapsed,
        activeTaskClean,
        dependencyBlockingClear: dependencyBlockingClear === true,
      },
      counts: counts || previous.counts,
      updatedAt: nowIso,
    };
    return writeMineruAdmissionCircuit(dbBaseUrl, next);
  }

  if (probeFailureShouldOpen(submitProbe)) {
    const status = submitProbe?.status ? `HTTP ${submitProbe.status}` : 'submit-probe-failed';
    return openMineruAdmissionCircuit(dbBaseUrl, `mineru-submit-probe-${status}`, {
      lastSubmitProbe: normalizedProbe,
      activeTaskClean,
      dependencyBlockingClear: dependencyBlockingClear === true,
      counts,
    });
  }

  const next = {
    ...previous,
    lastSubmitProbe: normalizedProbe || previous.lastSubmitProbe,
    closeCriteria: {
      submitProbeOk: submitProbe?.ok === true,
      cooldownElapsed: previous.state !== 'open',
      activeTaskClean,
      dependencyBlockingClear: dependencyBlockingClear === true,
    },
    counts: counts || previous.counts,
    updatedAt: nowIso,
  };
  return writeMineruAdmissionCircuit(dbBaseUrl, next);
}

export function createMemoryMineruAdmissionCircuitStore(initialState = {}) {
  let state = normalizeMineruAdmissionCircuit(initialState);
  return {
    async read() {
      return normalizeMineruAdmissionCircuit(state);
    },
    async open(reason, details = {}) {
      const nowIso = new Date().toISOString();
      state = normalizeMineruAdmissionCircuit({
        ...state,
        state: 'open',
        reason,
        message: MINERU_ADMISSION_MESSAGE,
        openedAt: state.openedAt || nowIso,
        closedAt: null,
        cooldownUntil: new Date(Date.now() + getAdmissionCooldownMs()).toISOString(),
        lastSubmitProbe: details.lastSubmitProbe || state.lastSubmitProbe,
        updatedAt: nowIso,
      });
      return { ok: true, state };
    },
    async recordProbe(args) {
      const fakeDb = 'memory://mineru-admission';
      const previousFetch = globalThis.fetch;
      globalThis.fetch = async (url, options = {}) => {
        if (String(url).endsWith('/settings') && !options.method) {
          return { ok: true, json: async () => ({ mineruAdmissionCircuit: state }) };
        }
        if (String(url).endsWith('/settings/mineruAdmissionCircuit')) {
          state = normalizeMineruAdmissionCircuit(JSON.parse(options.body || '{}'));
          return { ok: true, json: async () => ({ ok: true }) };
        }
        return previousFetch(url, options);
      };
      try {
        return await recordMineruSubmitProbeForAdmission(fakeDb, args);
      } finally {
        globalThis.fetch = previousFetch;
      }
    },
  };
}
