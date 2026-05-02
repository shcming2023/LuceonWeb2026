import { execSync } from 'child_process';
import http from 'http';

console.log('=== Luceon2026 Tier 2 Standard Pre-check ===');

try {
  execSync('docker info', { stdio: 'ignore' });
  console.log('✅ Docker daemon: Running');
} catch {
  console.error('❌ Docker daemon is not running');
  process.exit(1);
}

try {
  execSync('docker compose -f docker-compose.yml -f docker-compose.tier2-standard.yml -f docker-compose.override.yml config --quiet', { stdio: 'ignore' });
  console.log('✅ Compose config: Passed');
} catch (e) {
  console.error('❌ Compose config check failed');
  process.exit(1);
}

const checkEndpoint = (url, name) => {
  return new Promise((resolve) => {
    const req = http.get(url, (res) => {
      resolve(res.statusCode === 200 || res.statusCode === 401 || res.statusCode === 403 || res.statusCode === 404);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(2000, () => resolve(false));
  });
};

const runChecks = async () => {
  const isCmsUp = await checkEndpoint('http://127.0.0.1:8080/cms/', 'CMS Frontend');
  const isMinioUp = await checkEndpoint('http://127.0.0.1:19001/', 'MinIO Console');
  const isOllamaUp = await checkEndpoint('http://127.0.0.1:11434/', 'Ollama');

  console.log('\n--- Service Status ---');
  console.log(`${isCmsUp ? '✅' : '❌'} CMS Frontend (8080): ${isCmsUp ? 'Running' : 'Not reachable'}`);
  console.log(`${isMinioUp ? '✅' : '❌'} MinIO Console (19001): ${isMinioUp ? 'Running' : 'Not reachable'}`);
  console.log(`${isOllamaUp ? '✅' : '❌'} Ollama API (11434): ${isOllamaUp ? 'Running' : 'Not reachable'}`);

  if (!isCmsUp || !isMinioUp || !isOllamaUp) {
    console.error('❌ Essential local services are not reachable.');
    process.exit(1);
  }

  try {
    const ollamaTags = execSync('docker exec cms-ollama-local ollama list', { encoding: 'utf8' });
    const targetModel = process.env.OLLAMA_TIER2_MODEL || 'qwen3.5:0.8b';
    if (ollamaTags.includes(targetModel)) {
      console.log(`✅ Ollama Model: ${targetModel} exists.`);
    } else {
      console.log(`⚠️  Ollama Model: ${targetModel} missing. Attempting to pull...`);
      try {
         execSync(`docker exec cms-ollama-local ollama pull ${targetModel}`, { stdio: 'inherit' });
         console.log(`✅ Successfully pulled ${targetModel}`);
      } catch (e) {
         console.error(`❌ Failed to pull ${targetModel}.`);
         process.exit(1);
      }
    }
  } catch (e) {
    console.error('❌ Failed to execute ollama list inside container', e.message);
    process.exit(1);
  }

  // Check backend dependency-health
  try {
    const healthRes = await fetch('http://127.0.0.1:8080/__proxy/upload/ops/dependency-health');
    const healthData = await healthRes.json();
    console.log('\n--- Backend Dependency Health ---');
    console.log(`Blocking: ${healthData.blocking}`);
    console.log(`MinIO: ${healthData.dependencies?.minio?.ok ? '✅' : '❌'}`);
    console.log(`MinerU: ${healthData.dependencies?.mineru?.ok ? '✅' : '❌'}`);
    console.log(`Ollama: ${healthData.dependencies?.ollama?.ok ? '✅' : '❌'}`);

    if (healthData.blocking || !healthData.dependencies?.minio?.ok || !healthData.dependencies?.mineru?.ok || !healthData.dependencies?.ollama?.ok) {
       console.error('❌ Backend Dependency Health indicates blocking or missing dependencies.');
       process.exit(1);
    }
  } catch (e) {
    console.error('❌ Backend Dependency Health check failed. Backend might be down.', e.message);
    process.exit(1);
  }

  console.log('\n✅ Pre-check completed.');
};

runChecks();
