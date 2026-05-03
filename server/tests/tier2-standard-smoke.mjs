const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8080';

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function runTest() {
  console.log(`=== Luceon2026 Tier 2 Standard Smoke Test ===`);
  console.log(`BASE_URL: ${BASE_URL}`);

  // 1. Dependency Health Check
  console.log(`\n[1] Checking Dependency Health...`);
  const healthRes = await fetch(`${BASE_URL}/__proxy/upload/ops/dependency-health`);
  if (!healthRes.ok) throw new Error(`Health check failed with status: ${healthRes.status}`);

  const healthData = await healthRes.json();
  console.log(`Dependency Health Summary:
  Blocking: ${healthData.blocking}
  MinIO OK: ${healthData.dependencies?.minio?.ok}
  MinerU OK: ${healthData.dependencies?.mineru?.ok}
  Ollama OK: ${healthData.dependencies?.ollama?.ok}`);

  if (healthData.blocking) {
    throw new Error(`Test Failed: Environment is blocking. Details: ${JSON.stringify(healthData, null, 2)}`);
  }

  // 2. Markdown Upload
  console.log(`\n[2] Uploading Markdown File (Smoke Test)...`);
  const timestamp = Date.now();
  const mdFilename = `tier2-std-md-${timestamp}.md`;
  const mdContent = `# Standard Test ${timestamp}\nTesting Markdown flow.`;

  const mdFormData = new FormData();
  mdFormData.append('file', new Blob([mdContent], { type: 'text/markdown' }), mdFilename);

  const mdUploadRes = await fetch(`${BASE_URL}/__proxy/upload/tasks`, {
    method: 'POST',
    body: mdFormData
  });

  if (!mdUploadRes.ok) throw new Error(`Upload failed HTTP ${mdUploadRes.status}`);
  const mdUploadData = await mdUploadRes.json();
  console.log(`Uploaded Markdown file: ${mdFilename}, Task ID: ${mdUploadData.taskId}`);

  // 3. Small PDF Upload (Triggering MinerU pipeline)
  console.log(`\n[3] Uploading Small PDF (Smoke Test)...`);

  // Generating a highly minimal PDF file buffer using base64 containing the text "Hello World"
  const helloWorldPdfB64 = "JVBERi0xLjQKMSAwIG9iaiA8PC9UeXBlIC9DYXRhbG9nIC9QYWdlcyAyIDAgUiA+PiBlbmRvYmogMiAwIG9iaiA8PC9UeXBlIC9QYWdlcyAvS2lkcyBbMyAwIFJdIC9Db3VudCAxID4+IGVuZG9iaiAzIDAgb2JqIDw8L1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCAyMDAgMjAwXSAvQ29udGVudHMgNCAwIFIgL1Jlc291cmNlcyA8PC9Gb250IDw8L0YxIDUgMCBSPj4+PiA+PiBlbmRvYmogNCAwIG9iaiA8PC9MZW5ndGggNDM+PiBzdHJlYW0gQlQvRjEgMjQgVGYgMTAgMTAwIFRkIChIZWxsbyBXb3JsZCkgVGoKRVQKZW5kc3RyZWFtIGVuZG9iaiA1IDAgb2JqIDw8L1R5cGUgL0ZvbnQgL1N1YnR5cGUgL1R5cGUxIC9CYXNlRm9udCAvSGVsdmV0aWNhID4+IGVuZG9iagp4cmVmCjAgNgowMDAwMDAwMDAwIDY1NTM1IGYKMDAwMDAwMDAwOSAwMDAwMCBuCjAwMDAwMDAwNTYgMDAwMDAgbgowMDAwMDAwMTExIDAwMDAwIG4KMDAwMDAwMDIxMiAwMDAwMCBuCjAwMDAwMDAzMDUgMDAwMDAgbgp0cmFpbGVyIDw8L1NpemUgNiAvUm9vdCAxIDAgUj4+CnN0YXJ0eHJlZgozOTMKJSVFT0Y=";
  const pdfBuffer = Buffer.from(helloWorldPdfB64, 'base64');

  const pdfFilename = `tier2-std-pdf-${timestamp}.pdf`;
  const pdfFormData = new FormData();
  pdfFormData.append('file', new Blob([pdfBuffer], { type: 'application/pdf' }), pdfFilename);

  const pdfUploadRes = await fetch(`${BASE_URL}/__proxy/upload/tasks`, {
    method: 'POST',
    body: pdfFormData
  });

  if (!pdfUploadRes.ok) throw new Error(`PDF Upload failed HTTP ${pdfUploadRes.status}`);
  const pdfUploadData = await pdfUploadRes.json();
  const pdfTaskId = pdfUploadData.taskId;
  console.log(`Uploaded PDF file: ${pdfFilename}, Task ID: ${pdfTaskId}`);

  // 4. Poll PDF Task to ensure it enters pipeline and completes AI
  console.log(`\n[4] Polling PDF Task State (Waiting for MinerU + AI pipeline completion)...`);
  let pdfState = '';
  let pollAttempts = 0;
  let enteredMinerUPipeline = false;
  let aiCompleted = false;
  let lastTaskObj = null;

  while (pollAttempts < 30) {
    const taskRes = await fetch(`${BASE_URL}/__proxy/db/tasks/${pdfTaskId}`);
    if (taskRes.ok) {
      const taskObj = await taskRes.json();
      lastTaskObj = taskObj;
      pdfState = taskObj.state;
      console.log(`  PDF Task state: ${pdfState} (progress: ${taskObj.progress}%) - msg: ${taskObj.message}`);

      if (taskObj.message?.includes('MinerU') || taskObj.metadata?.mineruExecutionProfile) {
         if (!enteredMinerUPipeline) {
           console.log(`  ✅ Successfully entered MinerU pipeline! Internal Task ID: ${taskObj.metadata?.mineruTaskId || 'Waiting...'}`);
           if (taskObj.metadata?.mineruTaskId) enteredMinerUPipeline = true;
         }
      }

      if (pdfState === 'confirmed' || pdfState === 'review-pending' || pdfState === 'failed') {
         if (taskObj.metadata?.aiClassificationProvider) {
            aiCompleted = true;
         }
         break;
      }
    }
    await sleep(3000);
    pollAttempts++;
  }

  const summary = lastTaskObj ? {
    state: lastTaskObj.state,
    message: lastTaskObj.message,
    metadata: lastTaskObj.metadata
  } : 'Task not found or fetch failed';

  if (!enteredMinerUPipeline) {
    throw new Error(`Test Failed: PDF did not enter MinerU pipeline. Last task info: ${JSON.stringify(summary, null, 2)}`);
  }

  if (pdfState === 'failed') {
    throw new Error(`Test Failed: Task failed during processing. Last task info: ${JSON.stringify(summary, null, 2)}`);
  }

  if (!aiCompleted) {
    throw new Error(`Test Failed: AI classification did not complete in time. Last task info: ${JSON.stringify(summary, null, 2)}`);
  }

  if (lastTaskObj.metadata?.aiClassificationProvider === 'skeleton') {
    throw new Error(`Test Failed: AI fallback to skeleton detected. Last task info: ${JSON.stringify(summary, null, 2)}`);
  }

  console.log(`\n✅ Tier 2 Standard Smoke Test Passed! (MinerU Pipeline + AI Non-skeleton completed)`);
  process.exit(0);
}

runTest().catch(err => {
  console.error(`\n❌ Test Failed:`, err);
  process.exit(1);
});
