import fs from 'fs';
import path from 'path';

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8080';

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function runTest() {
  console.log(`=== Luceon2026 Markdown Upload Regression Test ===`);
  console.log(`BASE_URL: ${BASE_URL}`);

  // 1. Dependency Health Check
  console.log(`\n[1] Checking Dependency Health...`);
  const healthRes = await fetch(`${BASE_URL}/__proxy/upload/ops/dependency-health`);
  if (!healthRes.ok) {
    throw new Error(`Health check failed with status: ${healthRes.status}`);
  }
  const healthData = await healthRes.json();
  console.log(`Dependency Health Summary:
  Blocking: ${healthData.blocking}
  MinIO OK: ${healthData.dependencies?.minio?.ok}
  MinerU OK: ${healthData.dependencies?.mineru?.ok}
  Ollama OK: ${healthData.dependencies?.ollama?.ok}`);

  if (healthData.blocking) {
    throw new Error(`Test Failed: Environment is blocking. Details: ${JSON.stringify(healthData, null, 2)}`);
  }

  // 2. Create and Upload Markdown File
  console.log(`\n[2] Uploading Markdown File...`);
  const timestamp = Date.now();
  const filename = `uat-md-regression-${timestamp}.md`;
  const fileContent = `# Regression Test ${timestamp}\nThis is an automated test.`;

  const formData = new FormData();
  formData.append('file', new Blob([fileContent], { type: 'text/markdown' }), filename);

  const uploadRes = await fetch(`${BASE_URL}/__proxy/upload/tasks`, {
    method: 'POST',
    body: formData
  });

  if (!uploadRes.ok) {
    const errorText = await uploadRes.text();
    throw new Error(`Upload failed HTTP ${uploadRes.status}: ${errorText}`);
  }

  const uploadData = await uploadRes.json();
  console.log(`Uploaded file name: ${filename}`);
  console.log(`materialId: ${uploadData.materialId}`);
  console.log(`taskId: ${uploadData.taskId}`);

  const materialId = uploadData.materialId;
  const taskId = uploadData.taskId;

  // 3. Poll Task State
  console.log(`\n[3] Polling Task State (Timeout: 60s)...`);
  let taskState = '';
  let aiJobId = null;
  const startTime = Date.now();

  while (Date.now() - startTime < 60000) {
    const taskRes = await fetch(`${BASE_URL}/__proxy/db/tasks/${taskId}`);
    if (taskRes.ok) {
      const taskObj = await taskRes.json();
      taskState = taskObj.state;
      aiJobId = taskObj.aiJobId || aiJobId;

      console.log(`  Task state: ${taskState} (progress: ${taskObj.progress}%)`);
      if (['review-pending', 'completed', 'failed'].includes(taskState)) {
        break;
      }
    }
    await sleep(2000);
  }

  console.log(`Final task state: ${taskState}`);
  if (!['review-pending', 'completed'].includes(taskState)) {
    throw new Error(`Task did not reach a valid final state in time. Expected 'review-pending' or 'completed', got: ${taskState}`);
  }

  // 4. Verify DB Entities
  console.log(`\n[4] Verifying DB Entities...`);
  const matRes = await fetch(`${BASE_URL}/__proxy/db/materials/${materialId}`);
  if (!matRes.ok) throw new Error(`Material ${materialId} not found in DB`);
  console.log(`  Material DB entity exists.`);

  let aiJobState = 'unknown';
  if (aiJobId) {
    const aiRes = await fetch(`${BASE_URL}/__proxy/db/ai-metadata-jobs/${aiJobId}`);
    if (aiRes.ok) {
      const aiObj = await aiRes.json();
      aiJobState = aiObj.state;
      console.log(`  AI job state: ${aiJobState}`);
      if (!['review-pending', 'completed'].includes(aiJobState)) {
        throw new Error(`AI Job state is invalid. Expected 'review-pending' or 'completed', got: ${aiJobState}`);
      }
    } else {
      throw new Error(`AI Job ${aiJobId} not found in DB`);
    }
  } else {
    throw new Error(`No AI Job ID attached to task.`);
  }

  // 5. Verify MinIO Objects via Nginx Proxy
  console.log(`\n[5] Verifying MinIO Objects...`);

  const rawUrl = `${BASE_URL}/minio/eduassets/originals/${materialId}/source.md`;
  const rawRes = await fetch(rawUrl, { method: 'HEAD' });
  const rawHasSource = rawRes.ok;
  console.log(`MinIO raw object check (source.md): ${rawHasSource ? 'Pass' : 'Fail'}`);
  if (!rawHasSource) throw new Error(`Source markdown object missing in MinIO (${rawUrl} returned HTTP ${rawRes.status})`);

  const fullMdUrl = `${BASE_URL}/minio/eduassets-parsed/parsed/${materialId}/full.md`;
  const manifestUrl = `${BASE_URL}/minio/eduassets-parsed/parsed/${materialId}/artifact-manifest.json`;

  const fullMdRes = await fetch(fullMdUrl, { method: 'HEAD' });
  const manifestRes = await fetch(manifestUrl, { method: 'HEAD' });

  const parsedHasFullMd = fullMdRes.ok;
  const parsedHasManifest = manifestRes.ok;

  console.log(`MinIO parsed object check (full.md): ${parsedHasFullMd ? 'Pass' : 'Fail'}`);
  console.log(`MinIO parsed object check (artifact-manifest.json): ${parsedHasManifest ? 'Pass' : 'Fail'}`);

  if (!parsedHasFullMd || !parsedHasManifest) {
    throw new Error(`Parsed markdown objects missing in MinIO`);
  }

  // 6. Consistency Audit
  console.log(`\n[6] Running Consistency Audit...`);
  const auditRes = await fetch(`${BASE_URL}/__proxy/upload/audit/consistency`);
  const auditData = await auditRes.json();
  console.log(`Consistency audit result: ok=${auditData.ok}`);
  console.log(`  Findings count: ${auditData.findings?.length || 0}`);

  if (!auditData.ok) {
    console.warn(`  Audit OK is false, displaying findings:`);
    console.dir(auditData.findings, { depth: null });
    throw new Error(`Consistency audit failed with ok=false`);
  }

  console.log(`\n✅ Markdown Upload Regression Test Passed!`);
  process.exit(0);
}

runTest().catch(err => {
  console.error(`\n❌ Test Failed:`, err);
  process.exit(1);
});
