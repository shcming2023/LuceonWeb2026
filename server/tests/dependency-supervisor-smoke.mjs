import { spawn } from 'child_process';
import assert from 'assert';
import fs from 'fs';
import os from 'os';
import path from 'path';

const PORT = 18089;
const BASE_URL = `http://127.0.0.1:${PORT}`;

async function runTest() {
  console.log('--- Dependency Supervisor Smoke Test ---');
  const mockBin = fs.mkdtempSync(path.join(os.tmpdir(), 'luceon-supervisor-mock-bin-'));
  fs.writeFileSync(path.join(mockBin, 'tmux'), `#!/bin/sh
if [ "$1" = "list-sessions" ]; then
  printf 'mineru_api\\nmineru_gradio\\nluceon-sidecar\\n'
  exit 0
fi
if [ "$1" = "has-session" ] && [ "$2" = "-t" ] && [ "$3" = "luceon-sidecar" ]; then
  exit 0
fi
exit 1
`);
  fs.writeFileSync(path.join(mockBin, 'curl'), `#!/bin/sh
case "$*" in
  *11434/api/tags*) printf '{"models":[]}'; exit 0 ;;
  *8083/health*) printf '{"status":"ok"}'; exit 0 ;;
  *) exit 7 ;;
esac
`);
  fs.chmodSync(path.join(mockBin, 'tmux'), 0o755);
  fs.chmodSync(path.join(mockBin, 'curl'), 0o755);

  // Start the supervisor on an isolated port.
  const supervisor = spawn('node', ['ops/luceon-dependency-supervisor.mjs'], {
    env: { ...process.env, SUPERVISOR_PORT: PORT.toString(), PATH: `${mockBin}:${process.env.PATH}` },
    stdio: ['ignore', 'pipe', 'pipe']
  });

  let outputLog = '';
  supervisor.stdout.on('data', d => { outputLog += d.toString(); });
  supervisor.stderr.on('data', d => { outputLog += d.toString(); });

  for (let i = 0; i < 30; i++) {
    try {
      const probe = await fetch(`${BASE_URL}/status`);
      if (probe.ok) break;
    } catch {
      // server not ready yet
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  try {
    // 1. Test /status
    const statusRes = await fetch(`${BASE_URL}/status`);
    const statusData = await statusRes.json();
    assert.strictEqual(statusData.ok, true, 'Status should be ok');
    assert.ok(statusData.sessions, 'Status should return sessions object');
    assert.strictEqual(typeof statusData.sessions.mineru, 'boolean', 'mineru session should be boolean');
    assert.strictEqual(typeof statusData.sessions.sidecar, 'boolean', 'sidecar session should be boolean');
    assert.strictEqual(typeof statusData.sessions.ollama, 'boolean', 'ollama session should be boolean');
    assert.strictEqual(statusData.sessions.mineru, false, 'managed mineru session should be absent in mock');
    assert.strictEqual(statusData.sessions.sidecar, true, 'managed sidecar session should be present in mock');
    assert.strictEqual(statusData.services.mineruReachable, true, 'mineru reachability should be separate from tmux ownership');
    assert.strictEqual(statusData.services.ollamaReachable, true, 'ollama reachability should be separate from tmux ownership');
    assert.ok(statusData.ownership, 'Status should return ownership object');
    assert.strictEqual(statusData.ownership.mineru.managed, false);
    assert.strictEqual(statusData.ownership.mineru.reachable, true);
    assert.deepEqual(statusData.ownership.mineru.unmanagedSessions, ['mineru_api', 'mineru_gradio']);
    assert.match(statusData.ownership.mineru.warning, /reachable but not managed/);
    assert.match(statusData.ownership.ollama.warning, /reachable but not managed/);
    console.log('✅ /status returns correctly');

    // 2. Test invalid action returns 400
    const invalidRes = await fetch(`${BASE_URL}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'rm -rf /' })
    });
    assert.strictEqual(invalidRes.status, 400, 'Invalid action should return 400');
    console.log('✅ Invalid action returns 400');

    // 3. Test missing action returns 400
    const missingRes = await fetch(`${BASE_URL}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    assert.strictEqual(missingRes.status, 400, 'Missing action should return 400');
    console.log('✅ Missing action returns 400');

    console.log('--- Dependency Supervisor Smoke Test Passed ---');
  } catch (e) {
    console.error('Test error:', e);
    console.log('Supervisor output:', outputLog);
    throw e;
  } finally {
    supervisor.kill();
    fs.rmSync(mockBin, { recursive: true, force: true });
  }
}

runTest().catch(err => {
  console.error('Smoke test failed');
  process.exit(1);
});
