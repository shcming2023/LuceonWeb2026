import { spawn } from 'child_process';
import assert from 'assert';

const PORT = 18089;
const BASE_URL = `http://127.0.0.1:${PORT}`;

async function runTest() {
  console.log('--- Dependency Supervisor Smoke Test ---');

  // Start the supervisor on an isolated port.
  const supervisor = spawn('node', ['ops/luceon-dependency-supervisor.mjs'], {
    env: { ...process.env, SUPERVISOR_PORT: PORT.toString() },
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
  }
}

runTest().catch(err => {
  console.error('Smoke test failed');
  process.exit(1);
});
