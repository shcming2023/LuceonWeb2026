import assert from 'node:assert';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { parseLatestMineruProgress } from '../lib/ops-mineru-log-parser.mjs';

const oldEnv = {
  MINERU_ERR_LOG_PATH: process.env.MINERU_ERR_LOG_PATH,
  MINERU_LOG_PATH: process.env.MINERU_LOG_PATH,
  MINERU_LOG_SOURCE_CONTEXT: process.env.MINERU_LOG_SOURCE_CONTEXT,
};

function restoreEnv() {
  for (const [key, value] of Object.entries(oldEnv)) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
}

async function main() {
  console.log('--- MinerU Log Observation Transport Smoke Test Start ---');

  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'luceon-mineru-log-observer-'));
  const oldCwd = process.cwd();
  const errLog = path.join(scratch, 'mineru-api.err.log');
  const missingLog = path.join(scratch, 'missing.log');
  const logSecond = '2026-05-07 13:06:48';
  const logSecondMs = new Date(logSecond).getTime();

  try {
    process.env.MINERU_ERR_LOG_PATH = errLog;
    process.env.MINERU_LOG_PATH = missingLog;
    process.env.MINERU_LOG_SOURCE_CONTEXT = 'host-filesystem-test';

    fs.writeFileSync(errLog, [
      `${logSecond} | INFO | Hybrid processing window 1/1: pages 1-4/4`,
      `${logSecond} | INFO | Processing pages: 100%|##########| 4/4 [00:01<00:00, 3.21it/s]`,
    ].join('\n'));

    const tolerated = await parseLatestMineruProgress(
      new Date(logSecondMs + 500).toISOString(),
      null,
      { backendEffective: 'pipeline' }
    );
    assert.equal(tolerated.activityLevel, 'active-progress');
    assert.equal(tolerated.signals.hasBusinessSignal, true);
    assert.equal(tolerated.logSource.logSourceContext, 'host-filesystem-test');
    console.log('Case 1 Pass: host log source is explicit and second-granularity timestamp tolerance keeps valid business logs');

    const outsideTolerance = await parseLatestMineruProgress(
      new Date(logSecondMs + 1500).toISOString(),
      null,
      { backendEffective: 'pipeline' }
    );
    assert.equal(outsideTolerance.signals.hasBusinessSignal, false);
    assert.equal(outsideTolerance.activityLevel, 'log-observation-no-business-signal');
    console.log('Case 2 Pass: observations outside timestamp tolerance remain excluded');

    process.env.MINERU_ERR_LOG_PATH = path.join(scratch, 'missing-err.log');
    process.env.MINERU_LOG_PATH = path.join(scratch, 'missing-out.log');
    process.chdir(scratch);
    const missing = await parseLatestMineruProgress(null, null, { backendEffective: 'pipeline' });
    assert.equal(missing.activityLevel, 'log-observation-missing');
    assert.equal(missing.logSource.logSourceContext, 'host-filesystem-test');
    assert.match(missing.observationStaleReason, /log file does not exist/);
    console.log('Case 3 Pass: missing log-source diagnostics keep the real observer source context');
  } finally {
    process.chdir(oldCwd);
    restoreEnv();
    fs.rmSync(scratch, { recursive: true, force: true });
  }

  console.log('--- MinerU Log Observation Transport Smoke Test Passed ---');
}

main().catch((error) => {
  restoreEnv();
  console.error(error);
  process.exit(1);
});
