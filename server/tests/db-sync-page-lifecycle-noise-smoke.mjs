import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const sourcePath = new URL('../../src/store/appContext.tsx', import.meta.url);
const source = await readFile(sourcePath, 'utf8');

assert.match(source, /let dbSyncPageLifecycleEnding = false;/);
assert.match(source, /window\.addEventListener\('pagehide', markPageLifecycleEnding, \{ capture: true \}\);/);
assert.match(source, /window\.addEventListener\('beforeunload', markPageLifecycleEnding, \{ capture: true \}\);/);

assert.match(source, /function isTransientFetchCancellation\(err: unknown, msg: string\)/);
assert.match(source, /text\.includes\('failed to fetch'\)/);
assert.match(source, /text\.includes\('abort'\)/);
assert.match(source, /text\.includes\('networkerror'\)/);

const handlerMatch = source.match(/function handleDbWriteError\(operation: string, err: unknown, silent = false\) \{([\s\S]*?)\n\}/);
assert.ok(handlerMatch, 'handleDbWriteError should exist');
const handler = handlerMatch[1];

assert.match(handler, /if \(dbSyncPageLifecycleEnding && isTransientFetchCancellation\(err, msg\)\) \{/);
assert.match(handler, /console\.debug\(`\[db-sync\] \$\{operation\} cancelled during page lifecycle change:`, msg\);/);
assert.match(handler, /return;/);
assert.match(handler, /dbFailCount\+\+;/);
assert.match(handler, /console\.warn\(`\[db-sync\] \$\{operation\} failed \(silent\):`, msg\);/);
assert.match(handler, /console\.warn\(`\[db-sync\] \$\{operation\} failed \(count=\$\{dbFailCount\}\):`, msg\);/);

const lifecycleReturnIndex = handler.indexOf('cancelled during page lifecycle change');
const failCountIndex = handler.indexOf('dbFailCount++');
assert.ok(lifecycleReturnIndex >= 0 && failCountIndex >= 0 && lifecycleReturnIndex < failCountIndex,
  'page-lifecycle cancellation should return before incrementing the real db failure counter');

console.log('db-sync page lifecycle noise smoke passed');
