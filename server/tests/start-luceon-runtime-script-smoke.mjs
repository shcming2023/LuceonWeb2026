import assert from 'assert/strict';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../..');
const scriptPath = path.join(repoRoot, 'ops/start-luceon-runtime.sh');
const script = fs.readFileSync(scriptPath, 'utf8');

assert.match(script, /set -euo pipefail/, 'startup script must fail fast on unset variables and failed commands');
assert.match(script, /wait_for_http\(\)/, 'startup script must wait for HTTP dependencies');
assert.match(script, /ensure_mineru\(\)/, 'startup script must detect and start MinerU');
assert.match(script, /MINERU_START_TIMEOUT_SEC/, 'startup script must bound MinerU startup wait');
assert.match(script, /tmux has-session -t "\$1"/, 'startup script must inspect managed tmux sessions');
assert.match(script, /ops\/dependency-health/, 'startup script must verify upload dependency-health');
assert.match(script, /wait_for_dependency_health/, 'startup script must wait for final dependency health');
assert.match(script, /ALLOW_DEGRADED_START/, 'startup script must make degraded startup explicit');
assert.doesNotMatch(script, /mineruSubmitProbe=true/, 'startup script must not run MinerU submit probes by default');

console.log('start-luceon-runtime-script-smoke PASS');
