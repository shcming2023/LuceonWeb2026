import assert from 'node:assert/strict';
import {
  buildRaw2CleanOperatorRunnerSample,
  runRawMaterial2CleanMaterialOperatorRunner,
} from '../services/rawmaterial2cleanmaterial/operator-runner.mjs';

function sample(n) {
  return buildRaw2CleanOperatorRunnerSample({
    materialId: `mat-${n}`,
    taskId: `task-${n}`,
    title: `Sample ${n}`,
    rawSeed: {
      object: `mineru/mat-${n}/v1/content_list_v2.json`,
      sha256: `${n}`.repeat(64).slice(0, 64),
      size_bytes: 100 + n,
    },
  });
}

function fakeProcessSample({ failAt = null, calls = [] } = {}) {
  return async ({ sample: inputSample, index, mode, phaseLabel }) => {
    calls.push({ materialId: inputSample.materialId, taskId: inputSample.taskId, index, mode, phaseLabel });
    if (failAt && failAt.index === index && failAt.mode === mode) {
      return {
        ok: false,
        stage: failAt.stage || 'artifact-verify',
        code: failAt.code || 'INJECTED_FAILURE',
        reason: failAt.reason || 'injected failure',
        operationCounts: {},
      };
    }
    return {
      ok: true,
      stage: 'completed',
      evidence: {
        rawSeed: inputSample.rawSeed,
        cleanService: {
          jobId: `luceon-${inputSample.taskId}-toc-rebuild-v1`,
          assetVersion: 'v1',
          submitted: mode === 'real',
        },
        candidate: {
          bucket: 'eduassets-clean',
          object: inputSample.candidateObject,
          sha256: `${index}`.repeat(64).slice(0, 64),
          size_bytes: 1000 + index,
        },
        dbPatchCount: mode === 'real' ? 2 : 0,
        productSurface: mode === 'real' ? { discoverable: true, decision: 'accepted' } : null,
      },
      operationCounts: mode === 'real'
        ? {
            rawSeedPutObject: 1,
            cleanServicePost: 1,
            raw2cleanCandidatePutObject: 1,
            dbPatch: 2,
          }
        : {},
    };
  };
}

const samples = [sample(1), sample(2), sample(3)];

console.log('=== RawMaterial2CleanMaterial Operator Runner Smoke ===');

{
  console.log('  [1] dry-run happy path preserves order and has zero write/POST counts...');
  const calls = [];
  const result = await runRawMaterial2CleanMaterialOperatorRunner({
    samples,
    mode: 'dry-run',
    operatorId: 'local-operator',
    deps: { processSample: fakeProcessSample({ calls }), now: () => '2026-05-25T06:54:52.000Z' },
  });
  assert.equal(result.ok, true, JSON.stringify(result, null, 2));
  assert.equal(result.realRunExecuted, false);
  assert.equal(result.completedSampleCount, 3);
  assert.deepEqual(calls.map((call) => call.materialId), ['mat-1', 'mat-2', 'mat-3']);
  assert.equal(result.operationCounts.rawSeedPutObject, 0);
  assert.equal(result.operationCounts.cleanServicePost, 0);
  assert.equal(result.operationCounts.dbPatch, 0);
  assert.equal(result.readinessClaimed, false);
  assert.equal(result.samples.every((item) => item.readinessClaimed === false), true);
}

{
  console.log('  [2] real mode runs preflight then real with fake dependencies...');
  const calls = [];
  const result = await runRawMaterial2CleanMaterialOperatorRunner({
    samples,
    mode: 'real',
    operatorId: 'local-operator',
    confirmRealRun: true,
    deps: { processSample: fakeProcessSample({ calls }), now: () => '2026-05-25T06:54:52.000Z' },
  });
  assert.equal(result.ok, true, JSON.stringify(result, null, 2));
  assert.equal(result.realRunExecuted, true);
  assert.equal(result.preflight.operationCounts.cleanServicePost, 0);
  assert.equal(result.operationCounts.rawSeedPutObject, 3);
  assert.equal(result.operationCounts.cleanServicePost, 3);
  assert.equal(result.operationCounts.raw2cleanCandidatePutObject, 3);
  assert.equal(result.operationCounts.dbPatch, 6);
  assert.deepEqual(calls.map((call) => call.mode), ['dry-run', 'dry-run', 'dry-run', 'real', 'real', 'real']);
  assert.equal(result.readinessClaimed, false);
}

{
  console.log('  [3] rejects empty list, hard-cap overflow, duplicates, missing operator, and unconfirmed real mode...');
  const deps = { processSample: fakeProcessSample() };
  assert.equal((await runRawMaterial2CleanMaterialOperatorRunner({ samples: [], mode: 'dry-run', operatorId: 'op', deps })).code, 'EMPTY_SAMPLE_LIST');
  assert.equal((await runRawMaterial2CleanMaterialOperatorRunner({ samples: [...samples, sample(4)], mode: 'dry-run', operatorId: 'op', deps })).code, 'HARD_CAP_EXCEEDED');
  assert.equal((await runRawMaterial2CleanMaterialOperatorRunner({ samples: [sample(1), sample(1)], mode: 'dry-run', operatorId: 'op', deps })).code, 'DUPLICATE_SAMPLE');
  assert.equal((await runRawMaterial2CleanMaterialOperatorRunner({ samples, mode: 'dry-run', deps })).code, 'MISSING_OPERATOR');
  assert.equal((await runRawMaterial2CleanMaterialOperatorRunner({ samples, mode: 'real', operatorId: 'op', deps })).code, 'REAL_RUN_NOT_CONFIRMED');
}

{
  console.log('  [4] stop-on-first-failure blocks later samples...');
  const calls = [];
  const result = await runRawMaterial2CleanMaterialOperatorRunner({
    samples,
    mode: 'dry-run',
    operatorId: 'local-operator',
    deps: {
      processSample: fakeProcessSample({
        calls,
        failAt: { index: 1, mode: 'dry-run', stage: 'raw-seed-preflight', code: 'RAW_SEED_MISMATCH' },
      }),
    },
  });
  assert.equal(result.ok, false);
  assert.equal(result.stopped.order, 2);
  assert.equal(result.stopped.code, 'RAW_SEED_MISMATCH');
  assert.deepEqual(calls.map((call) => call.materialId), ['mat-1', 'mat-2']);
}

{
  console.log('  [5] failed preflight prevents real-mode execution...');
  const calls = [];
  const result = await runRawMaterial2CleanMaterialOperatorRunner({
    samples,
    mode: 'real',
    operatorId: 'local-operator',
    confirmRealRun: true,
    deps: {
      processSample: fakeProcessSample({
        calls,
        failAt: { index: 0, mode: 'dry-run', stage: 'preflight', code: 'PREFLIGHT_STOP' },
      }),
    },
  });
  assert.equal(result.ok, false);
  assert.equal(result.code, 'PREFLIGHT_FAILED');
  assert.equal(result.realRunExecuted, false);
  assert.deepEqual(calls.map((call) => call.mode), ['dry-run']);
  assert.equal(result.readinessClaimed, false);
}

console.log('RawMaterial2CleanMaterial operator runner smoke passed.');

