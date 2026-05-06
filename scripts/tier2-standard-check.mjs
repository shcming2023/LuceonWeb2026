import { execSync } from 'child_process';

console.log('=== Luceon2026 Tier 2 Standard Pre-check ===');
console.log('Scope: current local real runtime, not online MinerU compatibility.');

function normalizeHostUrl(value, fallback) {
  const raw = String(value || fallback).replace(/\/+$/, '');
  return raw.replace('host.docker.internal', '127.0.0.1');
}

async function checkHttp(url, okStatuses = [200]) {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
    await res.arrayBuffer().catch(() => null);
    return { ok: okStatuses.includes(res.status), status: res.status };
  } catch (error) {
    return { ok: false, error: error.message };
  }
}

try {
  execSync('docker info', { stdio: 'ignore' });
  console.log('PASS Docker daemon: running');
} catch {
  console.error('FAIL Docker daemon is not running');
  process.exit(1);
}

try {
  execSync('docker compose -f docker-compose.yml -f docker-compose.tier2-standard.yml -f docker-compose.override.yml config --quiet', { stdio: 'ignore' });
  console.log('PASS Compose config: valid');
} catch {
  console.error('FAIL Compose config check failed');
  process.exit(1);
}

const cmsPort = process.env.CMS_PORT || '8080';
const cmsBase = process.env.BASE_URL || `http://127.0.0.1:${cmsPort}`;
const mineruEndpoint = normalizeHostUrl(process.env.LOCAL_MINERU_ENDPOINT, 'http://127.0.0.1:8083');
const ollamaEndpoint = normalizeHostUrl(process.env.OLLAMA_API_URL, 'http://127.0.0.1:11434');
const targetModel = process.env.OLLAMA_TIER2_MODEL || 'qwen3.5:9b';

const cms = await checkHttp(`${cmsBase}/cms/`);
const mineru = await checkHttp(`${mineruEndpoint}/health`);
const ollamaTags = await checkHttp(`${ollamaEndpoint}/api/tags`);

console.log('\n--- Service Status ---');
console.log(`${cms.ok ? 'PASS' : 'FAIL'} CMS Frontend (${cmsBase}/cms/): ${cms.status || cms.error}`);
console.log(`${mineru.ok ? 'PASS' : 'FAIL'} MinerU (${mineruEndpoint}/health): ${mineru.status || mineru.error}`);
console.log(`${ollamaTags.ok ? 'PASS' : 'FAIL'} Ollama (${ollamaEndpoint}/api/tags): ${ollamaTags.status || ollamaTags.error}`);

if (!cms.ok || !mineru.ok || !ollamaTags.ok) process.exit(1);

try {
  const tagsRes = await fetch(`${ollamaEndpoint}/api/tags`, { signal: AbortSignal.timeout(5000) });
  const tags = await tagsRes.json();
  const models = (tags.models || []).map((item) => item.name || '');
  if (!models.some((name) => name.includes(targetModel))) {
    console.error(`FAIL Ollama model missing: ${targetModel}`);
    process.exit(1);
  }
  console.log(`PASS Ollama model available: ${targetModel}`);
} catch (error) {
  console.error(`FAIL Ollama model check failed: ${error.message}`);
  process.exit(1);
}

try {
  const healthRes = await fetch(`${cmsBase}/__proxy/upload/ops/dependency-health`, { signal: AbortSignal.timeout(20000) });
  const healthData = await healthRes.json();
  console.log('\n--- Backend Dependency Health ---');
  console.log(`blocking=${healthData.blocking}`);
  console.log(`minio=${healthData.dependencies?.minio?.ok}`);
  console.log(`mineru=${healthData.dependencies?.mineru?.ok}`);
  console.log(`ollama=${healthData.dependencies?.ollama?.ok}`);

  if (healthData.blocking || !healthData.dependencies?.minio?.ok || !healthData.dependencies?.mineru?.ok || !healthData.dependencies?.ollama?.ok) {
    console.error('FAIL backend dependency health has blocking or missing dependency');
    process.exit(1);
  }
} catch (error) {
  console.error(`FAIL backend dependency health check failed: ${error.message}`);
  process.exit(1);
}

console.log('\nPASS Tier 2 Standard pre-check completed.');
