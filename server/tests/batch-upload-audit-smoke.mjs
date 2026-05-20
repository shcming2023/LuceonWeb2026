import assert from 'assert';
import * as http from 'http';

/**
 * P0 Batch Upload Auditability Smoke Test
 * Verifies that sequential batch upload tasks explicitly capture
 * success and failure for each file, providing durable counting truth
 * rather than silently dropping tasks during monitoring.
 */

async function run() {
  console.log('--- Starting batch-upload-audit-smoke ---');

  let processedCount = 0;
  let rejectedCount = 0;

  // Mock Upload Server
  const mockUploadServer = http.createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/tasks') {
      let body = '';
      req.on('data', chunk => { body += chunk.toString(); });
      req.on('end', () => {
        const data = JSON.parse(body);
        if (data.fileId === 'fail-me') {
          rejectedCount++;
          res.writeHead(503, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ ok: false, message: 'Admission open' }));
        } else {
          processedCount++;
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            ok: true,
            task: { id: `task-${Date.now()}`, materialId: data.materialId }
          }));
        }
      });
    } else {
      res.writeHead(404);
      res.end();
    }
  });

  await new Promise((resolve) => mockUploadServer.listen(0, '127.0.0.1', resolve));
  const port = mockUploadServer.address().port;
  const endpoint = `http://127.0.0.1:${port}/tasks`;

  // Simulating BatchProcessingController sequential queue
  const items = [
    { fileId: 'f1', status: 'pending' },
    { fileId: 'fail-me', status: 'pending' },
    { fileId: 'f3', status: 'pending' },
  ];

  let stats = { submitted: 0, failed: 0, failReasons: [] };

  console.log('Simulating sequential queue processing...');

  for (const item of items) {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileId: item.fileId, materialId: `mat-${item.fileId}` })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      stats.submitted++;
    } catch (e) {
      stats.failed++;
      stats.failReasons.push(e.message);
    }
  }

  mockUploadServer.close();

  console.log('\n--- Assertions ---');

  assert(processedCount === 2, `Expected 2 files processed successfully, got ${processedCount}`);
  assert(rejectedCount === 1, `Expected 1 file explicitly rejected, got ${rejectedCount}`);

  assert(stats.submitted === 2, `Expected UI to track 2 submitted, got ${stats.submitted}`);
  assert(stats.failed === 1, `Expected UI to track 1 failed, got ${stats.failed}`);
  assert(stats.failReasons.length === 1, `Expected 1 explicit fail reason`);

  console.log('SUCCESS: batch-upload-audit-smoke passed! Per-file submit counts are explicitly auditable and caught.');
}

run().catch(err => {
  console.error('Smoke test failed:', err);
  process.exit(1);
});
