import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { mkdtemp, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { buildFixtureRawCode } from '../../scripts/rawcode2cleancode-pilot.mjs';
import { runRawCode2CleanCodeUatRunner } from '../../scripts/rawcode2cleancode-runner.mjs';

async function makeFixtureSample(root, n) {
  const fixtureRoot = join(root, `fixture-${n}`);
  const rawBundleDir = await buildFixtureRawCode(fixtureRoot);
  return {
    sampleId: `fixture-${n}-chapter-001`,
    rawBundleDir,
    chapterId: 'chapter_001',
    title: `Fixture ${n}`,
  };
}

function fakeProcessSample({ failAt = null, calls = [] } = {}) {
  return async ({ sample, index, mode, phaseLabel }) => {
    calls.push({ sampleId: sample.sampleId, index, mode, phaseLabel });
    if (failAt && failAt.index === index && failAt.mode === mode && (!failAt.phaseLabel || failAt.phaseLabel === phaseLabel)) {
      return {
        ok: false,
        stage: failAt.stage || 'rawcode2cleancode-local-clean',
        code: failAt.code || 'INJECTED_FAILURE',
        reason: failAt.reason || 'injected failure',
        operationCounts: {},
        readinessClaimed: false,
      };
    }
    return {
      ok: true,
      stage: 'rawcode2cleancode-fixture-processor',
      status: 'PASS',
      evidence: {
        input: { rawBundleDir: sample.rawBundleDir, chapterId: sample.chapterId },
        output: { simulated: true },
        sideEffects: { db_writes: 0, minio_writes: 0, runtime_worker_posts: 0 },
      },
      operationCounts: {
        localRawBundleRead: 1,
        localCleanBundleWrite: 1,
        llmApiCall: 0,
        dbWrite: 0,
        minioWrite: 0,
        runtimeWorkerPost: 0,
      },
      readinessClaimed: false,
    };
  };
}

const tmpRoot = await mkdtemp(join(tmpdir(), 'rawcode2cleancode-smoke-'));

try {
  const samples = [
    await makeFixtureSample(tmpRoot, 1),
    await makeFixtureSample(tmpRoot, 2),
    await makeFixtureSample(tmpRoot, 3),
  ];

  console.log('=== RawCode2CleanCode UAT Runner Smoke ===');

  {
    console.log('  [1] fixture dry-run produces PASS CleanCode and zero production side effects...');
    const outDir = join(tmpRoot, 'dry-run-out');
    const result = await runRawCode2CleanCodeUatRunner({
      samples: [samples[0]],
      mode: 'dry-run',
      operatorId: 'local-operator',
      outDir,
      cleaner: 'deterministic',
      deps: { now: () => '2026-06-04T00:00:00.000Z', manifestSha: 'a'.repeat(64) },
    });
    assert.equal(result.ok, true, JSON.stringify(result, null, 2));
    assert.equal(result.realRunExecuted, false);
    assert.equal(result.completedSampleCount, 1);
    assert.equal(result.samples[0].status, 'PASS');
    assert.equal(result.operationCounts.dbWrite, 0);
    assert.equal(result.operationCounts.minioWrite, 0);
    assert.equal(result.operationCounts.runtimeWorkerPost, 0);
    assert.equal(result.readinessClaimed, false);
    assert.equal(result.samples[0].readinessClaimed, false);
    assert.equal(existsSync(result.samples[0].evidence.output.cleanMd), true);
  }

  {
    console.log('  [2] llm-dry-run generates audit evidence and NEEDS_REVIEW without LLM API calls...');
    const outDir = join(tmpRoot, 'llm-dry-run-out');
    const result = await runRawCode2CleanCodeUatRunner({
      samples: [samples[1]],
      mode: 'dry-run',
      operatorId: 'local-operator',
      outDir,
      cleaner: 'llm-dry-run',
      deps: { now: () => '2026-06-04T00:01:00.000Z', manifestSha: 'b'.repeat(64) },
    });
    assert.equal(result.ok, true, JSON.stringify(result, null, 2));
    assert.equal(result.samples[0].status, 'NEEDS_REVIEW');
    assert.equal(result.samples[0].evidence.cleaner.effective, 'llm-dry-run');
    assert.equal(result.operationCounts.llmApiCall, 0);
    assert.equal(existsSync(join(result.samples[0].evidence.output.auditDir, 'llm_prompt.txt')), true);
    assert.equal(result.readinessClaimed, false);
  }

  {
    console.log('  [3] rejects empty list, hard-cap overflow, duplicates, missing operator, unconfirmed real, and missing raw bundle...');
    const deps = { processSample: fakeProcessSample() };
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples: [], mode: 'dry-run', operatorId: 'op', deps })).code, 'EMPTY_SAMPLE_LIST');
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples, mode: 'dry-run', operatorId: 'op', hardCap: 2, deps })).code, 'HARD_CAP_EXCEEDED');
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples: [...samples, await makeFixtureSample(tmpRoot, 4)], mode: 'dry-run', operatorId: 'op', hardCap: 4, deps })).code, 'ENTRY_HARD_CAP_EXCEEDED');
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples: [samples[0], samples[0]], mode: 'dry-run', operatorId: 'op', deps })).code, 'DUPLICATE_SAMPLE');
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples: [samples[0]], mode: 'dry-run', deps })).code, 'MISSING_OPERATOR');
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples: [samples[0]], mode: 'real', operatorId: 'op', deps })).code, 'REAL_RUN_NOT_CONFIRMED');
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples: [{ ...samples[0], rawBundleDir: join(tmpRoot, 'not-found') }], mode: 'dry-run', operatorId: 'op', deps })).code, 'RAW_BUNDLE_NOT_FOUND');
  }

  {
    console.log('  [4] stop-on-first-failure blocks later samples...');
    const calls = [];
    const result = await runRawCode2CleanCodeUatRunner({
      samples,
      mode: 'dry-run',
      operatorId: 'local-operator',
      deps: {
        processSample: fakeProcessSample({
          calls,
          failAt: { index: 1, mode: 'dry-run', stage: 'validator', code: 'QUALITY_BLOCKED' },
        }),
        now: () => '2026-06-04T00:02:00.000Z',
        manifestSha: 'c'.repeat(64),
      },
    });
    assert.equal(result.ok, false);
    assert.equal(result.stopped.order, 2);
    assert.equal(result.stopped.code, 'QUALITY_BLOCKED');
    assert.deepEqual(calls.map((call) => call.sampleId), [samples[0].sampleId, samples[1].sampleId]);
    assert.equal(result.readinessClaimed, false);
  }

  {
    console.log('  [5] failed real-mode preflight prevents real execution...');
    const calls = [];
    const result = await runRawCode2CleanCodeUatRunner({
      samples,
      mode: 'real',
      operatorId: 'local-operator',
      confirmRealRun: true,
      deps: {
        processSample: fakeProcessSample({
          calls,
          failAt: { index: 0, mode: 'dry-run', phaseLabel: 'preflight', stage: 'preflight', code: 'PREFLIGHT_STOP' },
        }),
        now: () => '2026-06-04T00:03:00.000Z',
        manifestSha: 'd'.repeat(64),
      },
    });
    assert.equal(result.ok, false);
    assert.equal(result.code, 'PREFLIGHT_FAILED');
    assert.equal(result.realRunExecuted, false);
    assert.deepEqual(calls.map((call) => call.mode), ['dry-run']);
    assert.equal(result.readinessClaimed, false);
  }

  {
    console.log('  [6] real mode runs preflight then local real phase with zero production side effects...');
    const calls = [];
    const result = await runRawCode2CleanCodeUatRunner({
      samples: [samples[0], samples[1]],
      mode: 'real',
      operatorId: 'local-operator',
      confirmRealRun: true,
      deps: {
        processSample: fakeProcessSample({ calls }),
        now: () => '2026-06-04T00:04:00.000Z',
        manifestSha: 'e'.repeat(64),
      },
    });
    assert.equal(result.ok, true, JSON.stringify(result, null, 2));
    assert.equal(result.realRunExecuted, true);
    assert.equal(result.preflight.operationCounts.dbWrite, 0);
    assert.equal(result.operationCounts.dbWrite, 0);
    assert.deepEqual(calls.map((call) => call.mode), ['dry-run', 'dry-run', 'real', 'real']);
    assert.equal(result.readinessClaimed, false);
  }

  console.log('RawCode2CleanCode UAT runner smoke passed.');
} finally {
  await rm(tmpRoot, { recursive: true, force: true });
}
