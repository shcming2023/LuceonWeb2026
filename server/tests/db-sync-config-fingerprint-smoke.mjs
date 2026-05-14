import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const sourcePath = new URL('../../src/store/appContext.tsx', import.meta.url);
const source = await readFile(sourcePath, 'utf8');

function count(pattern) {
  return [...source.matchAll(pattern)].length;
}

assert.match(source, /function persistenceFingerprint\(value: unknown\): string/);
assert.match(source, /const aiConfigFingerprintRef\s+=\s+useRef<string \| null>\(null\)/);
assert.match(source, /const mineruConfigFingerprintRef\s+=\s+useRef<string \| null>\(null\)/);
assert.match(source, /const minioConfigFingerprintRef\s+=\s+useRef<string \| null>\(null\)/);
assert.match(source, /const secretsFingerprintRef\s+=\s+useRef<string \| null>\(null\)/);

assert.ok(count(/aiConfigFingerprintRef\.current = persistenceFingerprint/g) >= 2);
assert.ok(count(/mineruConfigFingerprintRef\.current = persistenceFingerprint/g) >= 2);
assert.ok(count(/minioConfigFingerprintRef\.current = persistenceFingerprint/g) >= 2);
assert.ok(count(/secretsFingerprintRef\.current = persistenceFingerprint/g) >= 2);

assert.match(source, /if \(aiConfigFingerprintRef\.current !== fingerprint\) \{[\s\S]*?dbPut\('\/settings\/aiConfig', sanitized\);[\s\S]*?\}/);
assert.match(source, /if \(mineruConfigFingerprintRef\.current !== fingerprint\) \{[\s\S]*?dbPut\('\/settings\/mineruConfig', sanitized\);[\s\S]*?\}/);
assert.match(source, /if \(minioConfigFingerprintRef\.current !== fingerprint\) \{[\s\S]*?dbPut\('\/settings\/minioConfig', sanitized\);[\s\S]*?\}/);
assert.match(source, /if \(secretsFingerprintRef\.current !== secretsFingerprint\) \{[\s\S]*?dbPut\('\/secrets', secretsPayload\);[\s\S]*?\}/);

assert.equal(count(/dbPut\('\/secrets'/g), 2, 'Only seed and fingerprint-guarded sync may write /secrets');

console.log('db-sync config fingerprint smoke passed');
