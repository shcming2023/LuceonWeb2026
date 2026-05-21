import fs from 'fs';
import { execSync } from 'child_process';
import { buildCleanServiceJobRequest } from '../server/services/cleanservice/cleanservice-worker.mjs';
import { loadCleanServiceConfig } from '../server/services/cleanservice/config.mjs';

async function main() {
  console.log('=== Task 233 Preflight and Storage Endpoint Allowlist Gate Audit ===\n');

  const reportData = {
    branch: 'lucode/task-233-dispatch-retry',
    headSha: '',
    postSent: 'no',
    postCount: 0,
    jobId: 'none',
    gates: {
      containerRunning: false,
      loopbackBinding: false,
      healthOk: false,
      credentialsEmpty: false,
      schemaGatePass: false,
      storageAllowlistPass: false,
    },
    evidence: {
      containerInspect: {},
      healthResponse: null,
      schemaMissingFields: [],
      candidateEndpoints: {},
      allowedEndpoints: [],
      jobsJsonBaseline: {},
      jobsJsonPost: {},
    }
  };

  // 0. Get current HEAD SHA
  try {
    reportData.headSha = execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
    console.log(`Current Branch HEAD SHA: ${reportData.headSha}`);
  } catch (err) {
    console.error('Failed to get HEAD SHA:', err.message);
  }

  // 1. Gate 1: Check mineru2table-api container status
  console.log('[Gate 1] Checking mineru2table-api container...');
  let inspectData;
  try {
    const stdout = execSync('docker inspect mineru2table-api', { encoding: 'utf8' });
    inspectData = JSON.parse(stdout)[0];
    reportData.gates.containerRunning = inspectData.State.Running && inspectData.State.Health?.Status === 'healthy';
    console.log(`  Container Running & Healthy: ${reportData.gates.containerRunning}`);
  } catch (err) {
    console.error('  Container check failed:', err.message);
  }

  if (!reportData.gates.containerRunning) {
    console.log('\n[BLOCKED] Gate 1 Failed: mineru2table-api is not running or not healthy.');
    console.stringify(reportData);
    process.exit(0);
  }

  // 2. Gate 2: Check loopback-only port binding
  console.log('\n[Gate 2] Checking loopback binding (127.0.0.1:8000)...');
  try {
    const ports = inspectData.NetworkSettings.Ports['8000/tcp'] || [];
    const binding = ports.find(p => p.HostIp === '127.0.0.1' && p.HostPort === '8000');
    reportData.gates.loopbackBinding = !!binding && ports.length === 1;
    reportData.evidence.containerInspect.ports = ports;
    console.log(`  HostIp: ${binding?.HostIp}, HostPort: ${binding?.HostPort}`);
    console.log(`  Loopback binding strictly enforced: ${reportData.gates.loopbackBinding}`);
  } catch (err) {
    console.error('  Loopback check failed:', err.message);
  }

  // 3. Gate 3: Check health API endpoint
  console.log('\n[Gate 3] Checking /health API...');
  try {
    const stdout = execSync('curl -s http://host.docker.internal:8000/health', { encoding: 'utf8' });
    const health = JSON.parse(stdout);
    reportData.evidence.healthResponse = health;
    console.log('  Health response:', stdout.trim());
    reportData.gates.healthOk = health.status === 'unhealthy' &&
                               health.checks?.minio === 'unconfigured' &&
                               health.checks?.llm === 'not_configured';
    console.log(`  Health Check Status OK (unconfigured dependencies): ${reportData.gates.healthOk}`);
  } catch (err) {
    console.error('  Health API check failed:', err.message);
  }

  // 4. Gate 4: Masked env credentials check
  console.log('\n[Gate 4] Checking credentials are empty...');
  try {
    const envVars = inspectData.Config.Env || [];
    const sensitiveKeys = ['MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'DEEPSEEK_API_KEY', 'TOC_REBUILD_CALLBACK_SECRET'];
    const matched = {};
    let allEmpty = true;
    for (const key of sensitiveKeys) {
      const match = envVars.find(e => e.startsWith(`${key}=`));
      if (match) {
        const val = match.split('=')[1];
        matched[key] = val ? '[PRESENT]' : '[EMPTY]';
        if (val) allEmpty = false;
      } else {
        matched[key] = '[ABSENT]';
      }
    }
    reportData.gates.credentialsEmpty = allEmpty;
    reportData.evidence.containerInspect.sensitiveEnv = matched;
    console.log('  Credentials Matrix:', JSON.stringify(matched, null, 2));
    console.log(`  All empty/absent: ${reportData.gates.credentialsEmpty}`);
  } catch (err) {
    console.error('  Env credentials check failed:', err.message);
  }

  // 5. Gate 5: OpenAPI Schema Gate
  console.log('\n[Gate 5] Running OpenAPI Schema Gate...');
  const mockTask = {
    id: 'optionb-mock-parse-task',
    materialId: 'optionb-mock-material',
    state: 'review-pending',
    metadata: {
      cleanOutputBucket: 'eduassets-clean',
      rawMaterial: {
        version: 'v1',
        mineru: {
          contentListV2: {
            bucket: 'eduassets-raw',
            object: 'mineru/optionb-mock-material/v1/content_list_v2.json',
            sha256: 'mock-sha256-hash-value-1234567890abcdef'
          }
        }
      }
    }
  };

  const config = loadCleanServiceConfig();
  const payload = buildCleanServiceJobRequest(mockTask, config);
  console.log('  Generated Candidate Payload:\n', JSON.stringify(payload, null, 2));

  let isRequestSchemaValid = false;
  try {
    const openapi = JSON.parse(fs.readFileSync('scratch/openapi.json', 'utf8'));
    const schemas = openapi.components?.schemas || {};

    const missingFields = [];
    function validateSchema(obj, schemaName, path = '') {
      const schema = schemas[schemaName];
      if (!schema) return false;

      let valid = true;
      const required = schema.required || [];
      
      for (const field of required) {
        const value = obj?.[field];
        if (value === undefined || value === null) {
          missingFields.push(`${path || 'root'}${field}`);
          valid = false;
        }
      }

      for (const [propName, prop] of Object.entries(schema.properties || {})) {
        const val = obj?.[propName];
        if (val === undefined || val === null) continue;

        let subSchemaRef = prop.$ref;
        if (prop.anyOf) {
          const refObj = prop.anyOf.find(item => item.$ref);
          if (refObj) subSchemaRef = refObj.$ref;
        }

        if (subSchemaRef) {
          const subSchemaName = subSchemaRef.split('/').pop();
          const subValid = validateSchema(val, subSchemaName, `${path}${propName}.`);
          if (!subValid) valid = false;
        } else if (prop.type === 'array' && prop.items?.$ref) {
          const subSchemaName = prop.items.$ref.split('/').pop();
          if (Array.isArray(val)) {
            val.forEach((item, index) => {
              const subValid = validateSchema(item, subSchemaName, `${path}${propName}[${index}].`);
              if (!subValid) valid = false;
            });
          }
        }
      }
      return valid;
    }

    isRequestSchemaValid = validateSchema(payload, 'JobSubmitRequest');
    reportData.gates.schemaGatePass = isRequestSchemaValid;
    reportData.evidence.schemaMissingFields = missingFields;
    console.log(`  Schema Gate Pass: ${isRequestSchemaValid}`);
    if (!isRequestSchemaValid) {
      console.log('  Missing fields:', missingFields);
    }
  } catch (err) {
    console.error('  Schema validation error:', err.message);
  }

  // 6. Gate 6: Storage Endpoint Allowlist Gate
  console.log('\n[Gate 6] Running Storage Endpoint Allowlist Gate...');
  try {
    const envVars = inspectData.Config.Env || [];
    const allowlistMatch = envVars.find(e => e.startsWith('ALLOWED_MINIO_ENDPOINTS='));
    const allowedStr = allowlistMatch ? allowlistMatch.split('=')[1] : '';
    const allowedList = allowedStr.split(',').map(s => s.trim()).filter(Boolean);
    reportData.evidence.allowedEndpoints = allowedList;

    const sourceEndpoint = payload.inputs[0].source.endpoint;
    const sinkEndpoint = payload.sink.endpoint;
    reportData.evidence.candidateEndpoints = { sourceEndpoint, sinkEndpoint };

    const sourceOk = allowedList.includes(sourceEndpoint);
    const sinkOk = allowedList.includes(sinkEndpoint);
    reportData.gates.storageAllowlistPass = sourceOk && sinkOk;

    console.log(`  Allowed minio endpoints in mineru2table-api env:`, allowedList);
    console.log(`  Candidate source endpoint: "${sourceEndpoint}"`);
    console.log(`  Candidate sink endpoint:   "${sinkEndpoint}"`);
    console.log(`  Source endpoint match allowlist: ${sourceOk}`);
    console.log(`  Sink endpoint match allowlist:   ${sinkOk}`);
    console.log(`  Allowlist Gate Pass: ${reportData.gates.storageAllowlistPass}`);
  } catch (err) {
    console.error('  Allowlist check error:', err.message);
  }

  // 7. Get jobs.json baseline stats
  const jobsJsonPath = '/workspace/ops/Mineru2Tables/data/jobs.json';
  console.log('\n[Jobs Store] Gathering jobs.json baseline stats...');
  try {
    const stat = fs.statSync(jobsJsonPath);
    const content = fs.readFileSync(jobsJsonPath, 'utf8');
    const records = JSON.parse(content);
    const hash = execSync(`sha256sum ${jobsJsonPath}`, { encoding: 'utf8' }).split(' ')[0];

    reportData.evidence.jobsJsonBaseline = {
      sizeBytes: stat.size,
      hash: hash,
      recordCount: Object.keys(records).length,
      contentExcerpt: content.substring(0, 100),
    };
    console.log('  Baseline stats:', JSON.stringify(reportData.evidence.jobsJsonBaseline, null, 2));
  } catch (err) {
    console.error('  Failed to get jobs.json baseline:', err.message);
  }

  // 8. Decide and Classification
  console.log('\n=== Final Handoff Decision ===');
  const allPreflightGatesPass = reportData.gates.containerRunning &&
                                reportData.gates.loopbackBinding &&
                                reportData.gates.healthOk &&
                                reportData.gates.credentialsEmpty &&
                                reportData.gates.schemaGatePass;

  if (!allPreflightGatesPass) {
    reportData.classification = 'BLOCKED_BEFORE_POST_WITH_EVIDENCE';
    console.log('[BLOCKED] Classification: BLOCKED_BEFORE_POST_WITH_EVIDENCE (Preflight Gate failed)');
  } else if (!reportData.gates.storageAllowlistPass) {
    reportData.classification = 'BLOCKED_STORAGE_ENDPOINT_ALLOWLIST_GAP';
    console.log('[BLOCKED] Classification: BLOCKED_STORAGE_ENDPOINT_ALLOWLIST_GAP (Storage Endpoint Allowlist Gate failed)');
    console.log('  >> PROHIBITED: Do not send POST. Do not edit config. Do not edit source code.');
  } else {
    reportData.classification = 'CONTROLLED_FAILURE_DISPATCH_OBSERVED';
    console.log('[ALLOWED] All gates pass! Real POST is authorized.');
    // Under Task 233 rules, since storage endpoint allowlist failed, we should NOT reach here.
  }

  // 9. Post jobs.json check (sanity check)
  console.log('\n[Jobs Store] Gathering jobs.json post-state stats...');
  try {
    const stat = fs.statSync(jobsJsonPath);
    const content = fs.readFileSync(jobsJsonPath, 'utf8');
    const records = JSON.parse(content);
    const hash = execSync(`sha256sum ${jobsJsonPath}`, { encoding: 'utf8' }).split(' ')[0];

    reportData.evidence.jobsJsonPost = {
      sizeBytes: stat.size,
      hash: hash,
      recordCount: Object.keys(records).length,
      contentExcerpt: content.substring(0, 100),
    };
    console.log('  Post-state stats:', JSON.stringify(reportData.evidence.jobsJsonPost, null, 2));
  } catch (err) {
    console.error('  Failed to get jobs.json post-state:', err.message);
  }

  // Print raw JSON reportData for documentation use
  console.log('\n=== JSON REPORT DATA FOR ARTIFACT ===');
  console.log(JSON.stringify(reportData, null, 2));
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
