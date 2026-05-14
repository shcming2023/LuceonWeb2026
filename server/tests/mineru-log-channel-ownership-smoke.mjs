import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import {
  createFastCompleteMineruObservation,
  inspectMineruLogChannelOwnership,
  MINERU_LOG_STALE_MS,
  parseLatestMineruProgress,
} from '../lib/ops-mineru-log-parser.mjs';
import { buildNonTerminalMineruLogObservationWarning } from '../services/mineru/local-adapter.mjs';

const originalEnv = {
  MINERU_ERR_LOG_PATH: process.env.MINERU_ERR_LOG_PATH,
  MINERU_LOG_PATH: process.env.MINERU_LOG_PATH,
  MINERU_LOG_SOURCE_CONTEXT: process.env.MINERU_LOG_SOURCE_CONTEXT,
};

function restoreEnv() {
  for (const [key, value] of Object.entries(originalEnv)) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
}

async function withScratch(fn) {
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'luceon-mineru-log-channel-'));
  const oldCwd = process.cwd();
  try {
    process.chdir(scratch);
    await fn(scratch);
  } finally {
    process.chdir(oldCwd);
    restoreEnv();
    fs.rmSync(scratch, { recursive: true, force: true });
  }
}

async function inspectWithLogs({ scratch, errLog, outLog, nowMs = Date.now(), globalObservation = null }) {
  process.env.MINERU_ERR_LOG_PATH = errLog;
  process.env.MINERU_LOG_PATH = outLog;
  process.env.MINERU_LOG_SOURCE_CONTEXT = 'host-filesystem-test';
  return inspectMineruLogChannelOwnership({ nowMs, globalObservation });
}

async function main() {
  console.log('--- MinerU Log Channel Ownership Smoke Test Start ---');

  await withScratch(async (scratch) => {
    const missingErr = path.join(scratch, 'missing.err.log');
    const missingOut = path.join(scratch, 'missing.out.log');
    const diagnostics = await inspectWithLogs({ scratch, errLog: missingErr, outLog: missingOut });

    assert.equal(diagnostics.summaryState, 'missing');
    assert.equal(diagnostics.sources[0].state, 'missing');
    assert.equal(diagnostics.sidecar.runningState, 'not-observed');
    assert.equal(diagnostics.selectedSource.logSourceBaseName, 'missing.err.log');
    assert.equal(diagnostics.selectedSource.logSourcePath, undefined);
    console.log('Case 1 Pass: missing log file is distinct and host paths are not exposed');
  });

  await withScratch(async (scratch) => {
    const emptyErr = path.join(scratch, 'empty.err.log');
    const missingOut = path.join(scratch, 'missing.out.log');
    fs.writeFileSync(emptyErr, '');

    const diagnostics = await inspectWithLogs({ scratch, errLog: emptyErr, outLog: missingOut });
    assert.equal(diagnostics.summaryState, 'empty');

    const parsed = await parseLatestMineruProgress(null, null, { backendEffective: 'pipeline' });
    assert.equal(parsed.activityLevel, 'log-observation-empty');
    assert.match(parsed.observationStaleReason, /empty/);
    console.log('Case 2 Pass: empty log file is distinct from missing/unreadable');
  });

  await withScratch(async (scratch) => {
    const staleErr = path.join(scratch, 'stale.err.log');
    const missingOut = path.join(scratch, 'missing.out.log');
    fs.writeFileSync(staleErr, 'GET /health 200 OK\n');
    const staleMs = Date.now() - MINERU_LOG_STALE_MS - 60_000;
    fs.utimesSync(staleErr, new Date(staleMs), new Date(staleMs));

    const diagnostics = await inspectWithLogs({
      scratch,
      errLog: staleErr,
      outLog: missingOut,
      nowMs: Date.now(),
    });
    assert.equal(diagnostics.summaryState, 'stale');
    assert.equal(diagnostics.sources[0].state, 'stale');
    console.log('Case 3 Pass: stale log file is distinct');
  });

  await withScratch(async (scratch) => {
    const validErr = path.join(scratch, 'valid.err.log');
    const missingOut = path.join(scratch, 'missing.out.log');
    fs.writeFileSync(validErr, [
      '2026-05-14 09:30:00 | INFO | Pipeline processing-window multi-file run. doc_count=1, total_pages=12, window_size=64, total_batches=1',
      '2026-05-14 09:30:01 | INFO | Pipeline processing window batch 1/1: 12/12 pages, batch_pages=12, doc_slices=sample.pdf:1-12',
      'Predict: 50%|#####     | 6/12 [00:10<00:10, 1.67s/it]',
    ].join('\n'));

    const diagnostics = await inspectWithLogs({ scratch, errLog: validErr, outLog: missingOut });
    assert.equal(diagnostics.summaryState, 'valid-business-progress');
    assert.equal(diagnostics.selectedSource.signals.hasBusinessSignal, true);
    assert.equal(diagnostics.selectedSource.signals.progressCount, 1);
    const parsed = await parseLatestMineruProgress(null, null, { backendEffective: 'pipeline' });
    assert.equal(parsed.activityLevel, 'active-progress');
    assert.equal(parsed.signals.hasBusinessSignal, true);
    assert.equal(parsed.logSource.configuredBy, 'MINERU_ERR_LOG_PATH');
    console.log('Case 4 Pass: valid business progress lines are detected');
  });

  await withScratch(async (scratch) => {
    const emptyErr = path.join(scratch, 'configured-empty.err.log');
    const emptyOut = path.join(scratch, 'configured-empty.out.log');
    const fallbackDir = path.join(scratch, 'uat', 'scratch');
    const fallbackLog = path.join(fallbackDir, 'mineru-api.log');
    fs.mkdirSync(fallbackDir, { recursive: true });
    fs.writeFileSync(emptyErr, '');
    fs.writeFileSync(emptyOut, '');
    fs.writeFileSync(fallbackLog, [
      '2026-05-08 08:09:00 | INFO | Pipeline processing-window multi-file run. doc_count=1, total_pages=99, window_size=64, total_batches=2',
      'Predict: 99%|######### | 98/99 [00:10<00:01, 1.00s/it]',
    ].join('\n'));
    const staleMs = Date.now() - MINERU_LOG_STALE_MS - 60_000;
    fs.utimesSync(fallbackLog, new Date(staleMs), new Date(staleMs));

    await inspectWithLogs({ scratch, errLog: emptyErr, outLog: emptyOut });
    const parsed = await parseLatestMineruProgress(null, null, { backendEffective: 'pipeline' });
    assert.equal(parsed.activityLevel, 'log-observation-empty');
    assert.equal(parsed.signals?.hasBusinessSignal, undefined);
    assert.equal(parsed.phase, undefined);
    assert.equal(parsed.progressSemantics.phase, null);
    assert.equal(parsed.progressSemantics.freshness, 'missing');
    assert.equal(parsed.logSource.logSourceSelectedReason, 'file-empty');
    assert.equal(
      parsed.ignoredDiagnosticLogSource.logSourceSelectedReason,
      'workspace-scratch-fallback-ignored-when-configured-logs-explicit'
    );
    assert.equal(parsed.ignoredDiagnosticLogSource.diagnostic.hasBusinessSignal, true);
    console.log('Case 5 Pass: stale workspace scratch fallback cannot outrank explicit empty configured logs');
  });

  {
    const fastComplete = createFastCompleteMineruObservation({
      mineruTaskId: 'mineru-fast-complete',
      taskId: 'task-fast-complete',
      taskState: 'completed',
      taskStage: 'review-pending',
      completedAt: new Date().toISOString(),
    });
    assert.equal(fastComplete.activityLevel, 'fast-complete-no-business-signal');
    assert.equal(fastComplete.signals.hasBusinessSignal, false);
    assert.equal(fastComplete.phase == null, true);
    assert.equal(fastComplete.percent == null, true);
    assert.equal(fastComplete.progressSemantics.freshness, 'completed-diagnostic');
    console.log('Case 6 Pass: fast-complete without business signal is not fabricated into progress');
  }

  await withScratch(async (scratch) => {
    const emptyErr = path.join(scratch, 'inflight-empty.err.log');
    const missingOut = path.join(scratch, 'missing.out.log');
    fs.writeFileSync(emptyErr, '');
    await inspectWithLogs({ scratch, errLog: emptyErr, outLog: missingOut });
    const parsed = await parseLatestMineruProgress(null, null, { backendEffective: 'pipeline' });
    const warning = buildNonTerminalMineruLogObservationWarning(parsed, 'processing');
    assert.equal(parsed.activityLevel, 'log-observation-empty');
    assert.equal(warning.kind, 'mineru-log-observation-diagnostic-only');
    assert.notEqual(parsed.activityLevel, 'failed-confirmed');
    console.log('Case 7 Pass: in-flight MinerU API state is not terminally failed solely by an empty log channel');
  });

  {
    const recentObservation = {
      observerCheckedAt: new Date().toISOString(),
      observer: 'host-mineru-log-observer',
    };
    const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'luceon-mineru-sidecar-'));
    try {
      const missingErr = path.join(scratch, 'missing.err.log');
      const missingOut = path.join(scratch, 'missing.out.log');
      const diagnostics = await inspectWithLogs({
        scratch,
        errLog: missingErr,
        outLog: missingOut,
        globalObservation: recentObservation,
      });
      assert.equal(diagnostics.sidecar.expected, true);
      assert.equal(diagnostics.sidecar.runningState, 'observed-recent');
      assert.equal(diagnostics.sidecar.runningObserved, true);
      console.log('Case 8 Pass: sidecar expected/running state is reported without process management');
    } finally {
      restoreEnv();
      fs.rmSync(scratch, { recursive: true, force: true });
    }
  }

  console.log('--- MinerU Log Channel Ownership Smoke Test Passed ---');
}

main().catch((error) => {
  restoreEnv();
  console.error(error);
  process.exit(1);
});
