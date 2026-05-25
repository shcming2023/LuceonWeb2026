import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';

const cliPath = resolve('scripts/raw2clean-operator-runner.mjs');
const fixtureManifest = resolve('server/tests/fixtures/raw2clean-operator-manifest.json');

function runCli(args) {
  const result = spawnSync(process.execPath, [cliPath, ...args], {
    cwd: resolve('.'),
    encoding: 'utf8',
  });
  const output = result.stdout.trim() || result.stderr.trim();
  let json = null;
  try {
    json = JSON.parse(output);
  } catch (error) {
    assert.fail(`CLI did not return JSON. status=${result.status}\nstdout=${result.stdout}\nstderr=${result.stderr}`);
  }
  return { status: result.status, stdout: result.stdout, stderr: result.stderr, json };
}

console.log('=== RawMaterial2CleanMaterial Operator Entry Smoke ===');

{
  console.log('  [1] default dry-run reads manifest and emits run-level evidence...');
  const dir = await mkdtemp(join(tmpdir(), 'raw2clean-operator-entry-'));
  const out = join(dir, 'evidence.json');
  const result = runCli(['--manifest', fixtureManifest, '--out', out]);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.json.ok, true, JSON.stringify(result.json, null, 2));
  assert.equal(result.json.requestedMode, 'dry-run');
  assert.equal(result.json.realRunExecuted, false);
  assert.equal(result.json.operatorId, 'fixture-operator');
  assert.equal(result.json.hardCap, 3);
  assert.equal(result.json.operationCounts.rawSeedPutObject, 0);
  assert.equal(result.json.operationCounts.cleanServicePost, 0);
  assert.equal(result.json.operationCounts.dbPatch, 0);
  assert.equal(result.json.operatorEntry.processor.liveSideEffectsEnabled, false);
  assert.equal(result.json.evidenceSurface.manifest.sampleCount, 3);
  assert.equal(result.json.evidenceSurface.summary.readinessClaimed, false);
  const outJson = JSON.parse(await readFile(out, 'utf8'));
  assert.equal(outJson.runId, result.json.runId);
}

{
  console.log('  [2] real mode is blocked unless explicitly confirmed...');
  const result = runCli(['--manifest', fixtureManifest, '--mode', 'real']);
  assert.equal(result.status, 1);
  assert.equal(result.json.code, 'REAL_RUN_NOT_CONFIRMED');
  assert.equal(result.json.readinessClaimed, false);
}

{
  console.log('  [3] fixture real mode remains side-effect-free after confirmation...');
  const result = runCli(['--manifest', fixtureManifest, '--mode', 'real', '--confirm-real']);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.json.ok, true, JSON.stringify(result.json, null, 2));
  assert.equal(result.json.realRunExecuted, true);
  assert.equal(result.json.operationCounts.rawSeedPutObject, 0);
  assert.equal(result.json.operationCounts.cleanServicePost, 0);
  assert.equal(result.json.operationCounts.raw2cleanCandidatePutObject, 0);
  assert.equal(result.json.operationCounts.dbPatch, 0);
  assert.equal(result.json.operatorEntry.processor.liveSideEffectsEnabled, false);
}

{
  console.log('  [4] entry-level hard cap cannot be raised above 3...');
  const result = runCli(['--manifest', fixtureManifest, '--hard-cap', '4']);
  assert.equal(result.status, 1);
  assert.equal(result.json.code, 'ENTRY_HARD_CAP_EXCEEDED');
}

{
  console.log('  [5] runner hard cap blocks manifest overflow...');
  const dir = await mkdtemp(join(tmpdir(), 'raw2clean-operator-entry-'));
  const manifest = join(dir, 'manifest.json');
  const base = JSON.parse(await readFile(fixtureManifest, 'utf8'));
  base.samples.push({ materialId: 'mat-4', taskId: 'task-4' });
  await writeFile(manifest, JSON.stringify(base, null, 2));
  const result = runCli(['--manifest', manifest]);
  assert.equal(result.status, 1);
  assert.equal(result.json.code, 'HARD_CAP_EXCEEDED');
}

{
  console.log('  [6] unknown processor is explicitly blocked...');
  const result = runCli(['--manifest', fixtureManifest, '--processor', 'live']);
  assert.equal(result.status, 1);
  assert.equal(result.json.code, 'UNSUPPORTED_PROCESSOR');
}

console.log('RawMaterial2CleanMaterial operator entry smoke passed.');
