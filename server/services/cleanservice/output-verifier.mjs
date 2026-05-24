import { CLEAN_STAGE_STATES } from './states.mjs';

export const REQUIRED_CLEAN_ARTIFACTS = Object.freeze([
  'flooded_content',
  'logic_tree',
  'readable_tree',
  'skeleton',
  'unresolved_anchors',
  'metrics',
  'provenance',
]);

function isObjectRef(value) {
  return Boolean(value) &&
    typeof value === 'object' &&
    typeof value.bucket === 'string' &&
    value.bucket.length > 0 &&
    typeof value.object === 'string' &&
    value.object.length > 0;
}

function verifyProvenanceShape(provenance, expected = {}) {
  if (!provenance || typeof provenance !== 'object') {
    return {
      errors: ['missing-provenance-shape'],
      warnings: [],
      provenanceJobId: null,
      canonicalJobId: expected.jobId || null,
      provenanceJobIdPolicy: null,
    };
  }

  const errors = [];
  const warnings = [];
  let provenanceJobIdPolicy = null;
  if (provenance.schema !== 'luceon-provenance/v1') errors.push('invalid-provenance-schema');
  if (expected.serviceName && provenance.service?.name !== expected.serviceName) errors.push('service-name-mismatch');
  if (expected.protocolVersion && provenance.service?.protocol_version !== expected.protocolVersion) errors.push('protocol-version-mismatch');
  if (expected.materialId && provenance.asset?.material_id !== expected.materialId) errors.push('material-id-mismatch');
  if (expected.assetVersion && provenance.asset?.asset_version !== expected.assetVersion) errors.push('asset-version-mismatch');
  const provenanceJobId = provenance.job?.job_id || null;
  if (expected.jobId && provenanceJobId !== expected.jobId) {
    if (provenanceJobId === `${expected.jobId}-probe` && expected.allowProbeJobIdSuffix === true) {
      warnings.push('provenance-job-id-probe-suffix-accepted');
      provenanceJobIdPolicy = 'accepted-probe-suffix';
    } else {
      errors.push('job-id-mismatch');
    }
  }
  return {
    errors,
    warnings,
    provenanceJobId,
    canonicalJobId: expected.jobId || null,
    provenanceJobIdPolicy,
  };
}

export function verifyCleanServiceOutput(job = {}, options = {}) {
  const artifacts = job.artifacts || {};
  const errors = [];

  for (const key of REQUIRED_CLEAN_ARTIFACTS) {
    if (!isObjectRef(artifacts[key])) {
      // 向后兼容：旧的 smoke tests 不含 unresolved_anchors 与 metrics，此处在同步传统校验时豁免
      if (key === 'unresolved_anchors' || key === 'metrics') {
        continue;
      }
      errors.push(`missing-artifact:${key}`);
    }
  }

  if (artifacts.raw_mineru || artifacts.rawMineru || job.rawMineruOutput === true) {
    errors.push('raw-mineru-output-not-clean-success');
  }
  if (job.placeholderOutput === true || job.skeletonOnly === true) {
    errors.push('placeholder-or-skeleton-output-not-clean-success');
  }

  const provenanceCheck = verifyProvenanceShape(job.provenance, {
    serviceName: options.serviceName || job.service_name,
    protocolVersion: options.protocolVersion || job.protocol_version,
    materialId: job.material_id,
    assetVersion: job.asset_version,
    jobId: job.job_id,
    allowProbeJobIdSuffix: options.allowProbeJobIdSuffix,
  });
  errors.push(...provenanceCheck.errors);

  const unresolvedAnchorCount = Number(job.stats?.unresolved_anchor_count || 0);
  if (errors.length > 0) {
    return {
      ok: false,
      cleanState: CLEAN_STAGE_STATES.PROTOCOL_FAILURE,
      errors,
      unresolvedAnchorCount,
    };
  }

  if (unresolvedAnchorCount > 0) {
    return {
      ok: true,
      cleanState: CLEAN_STAGE_STATES.REVIEW_PENDING_PARTIAL,
      errors: [],
      unresolvedAnchorCount,
    };
  }

  return {
    ok: true,
    cleanState: CLEAN_STAGE_STATES.COMPLETED,
    errors: [],
    unresolvedAnchorCount,
  };
}

export async function verifyCleanServiceOutputArtifacts(job = {}, options = {}) {
  const artifacts = job.artifacts || {};
  const errors = [];
  const warnings = [];
  const expected = options.expected || {};
  const artifactReader = options.artifactReader;

  let tokensPrompt = null;
  let tokensCompletion = null;
  let tokensTotal = null;
  let sourceInput = null;

  if (!artifactReader) {
    throw new Error('verifyCleanServiceOutputArtifacts requires options.artifactReader');
  }

  // 1. 检查 ObjectRef 齐全性
  for (const role of REQUIRED_CLEAN_ARTIFACTS) {
    if (!isObjectRef(artifacts[role])) {
      errors.push(`missing-artifact:${role}`);
    }
  }

  if (artifacts.raw_mineru || artifacts.rawMineru || job.rawMineruOutput === true) {
    errors.push('raw-mineru-output-not-clean-success');
  }
  if (job.placeholderOutput === true || job.skeletonOnly === true) {
    errors.push('placeholder-or-skeleton-output-not-clean-success');
  }

  // 路径校验：如果 expected 提供了 materialId 和 assetVersion，每一个 artifact 的 object 必须在 toc-rebuild/{materialId}/{assetVersion}/ 下。
  const materialId = expected.materialId || job.material_id;
  const assetVersion = expected.assetVersion || job.asset_version;
  if (materialId && assetVersion) {
    const requiredPrefix = `toc-rebuild/${materialId}/${assetVersion}/`;
    for (const role of REQUIRED_CLEAN_ARTIFACTS) {
      const art = artifacts[role];
      if (isObjectRef(art)) {
        if (!art.object.startsWith(requiredPrefix)) {
          errors.push(`path-prefix-mismatch:${role}`);
        }
      }
    }
  }

  // 如果 ObjectRef 或基本格式校验失败，提前返回 protocol-failure
  if (errors.length > 0) {
    return {
      ok: false,
      cleanState: CLEAN_STAGE_STATES.PROTOCOL_FAILURE,
      errors,
      warnings,
      unresolvedAnchorCount: 0,
    };
  }

  // 2. 读取七件套内容并强校验
  const contents = {};
  for (const role of REQUIRED_CLEAN_ARTIFACTS) {
    try {
      let content;
      if (typeof artifactReader.readArtifact === 'function') {
        content = await artifactReader.readArtifact(role, artifacts[role]);
      } else if (typeof artifactReader.read === 'function') {
        content = await artifactReader.read(artifacts[role].bucket, artifacts[role].object);
      } else {
        throw new Error('artifactReader must implement readArtifact or read');
      }

      if (content === undefined || content === null) {
        errors.push(`missing-object:${role}`);
        continue;
      }
      contents[role] = content;
    } catch (err) {
      errors.push(`missing-object:${role}`);
    }
  }

  if (errors.length > 0) {
    return {
      ok: false,
      cleanState: CLEAN_STAGE_STATES.PROTOCOL_FAILURE,
      errors,
      warnings,
      unresolvedAnchorCount: 0,
    };
  }

  // 3. 强内容规则校验
  // 3.1 flooded_content.json
  let flooded;
  try {
    flooded = typeof contents.flooded_content === 'string'
      ? JSON.parse(contents.flooded_content)
      : contents.flooded_content;
    if (!Array.isArray(flooded) || flooded.length === 0) {
      errors.push('invalid-flooded_content-array');
    }
  } catch (e) {
    errors.push('invalid-flooded_content-json');
  }

  // 3.2 logic_tree.json
  let logic;
  try {
    logic = typeof contents.logic_tree === 'string'
      ? JSON.parse(contents.logic_tree)
      : contents.logic_tree;
    if (!logic || typeof logic !== 'object' || (Array.isArray(logic) && logic.length === 0) || (Object.keys(logic).length === 0)) {
      errors.push('invalid-logic_tree-shape');
    }
  } catch (e) {
    errors.push('invalid-logic_tree-json');
  }

  // 3.3 readable_tree.md
  const readable = contents.readable_tree;
  if (typeof readable !== 'string' || readable.trim().length === 0) {
    errors.push('empty-readable_tree');
  }

  // 3.4 skeleton.json
  let skeleton;
  try {
    skeleton = typeof contents.skeleton === 'string'
      ? JSON.parse(contents.skeleton)
      : contents.skeleton;
    if (!skeleton || typeof skeleton !== 'object' || (Array.isArray(skeleton) && skeleton.length === 0) || (Object.keys(skeleton).length === 0)) {
      errors.push('invalid-skeleton-shape');
    }
  } catch (e) {
    errors.push('invalid-skeleton-json');
  }

  // 3.5 unresolved_anchors.json
  let unresolved;
  try {
    unresolved = typeof contents.unresolved_anchors === 'string'
      ? JSON.parse(contents.unresolved_anchors)
      : contents.unresolved_anchors;
  } catch (e) {
    errors.push('invalid-unresolved_anchors-json');
  }

  // 3.6 metrics.json
  let metrics;
  try {
    metrics = typeof contents.metrics === 'string'
      ? JSON.parse(contents.metrics)
      : contents.metrics;
    const totalTokens = metrics.stats?.tokens?.total ?? metrics.tokens?.total ?? metrics.total_tokens ?? metrics.stats?.total_tokens;
    if (!Number.isFinite(totalTokens) || totalTokens <= 0) {
      errors.push('zero-or-missing-tokens');
    } else {
      tokensTotal = totalTokens;
      tokensPrompt = metrics.stats?.tokens?.prompt ?? metrics.tokens?.prompt ?? metrics.prompt_tokens ?? metrics.stats?.prompt_tokens ?? null;
      tokensCompletion = metrics.stats?.tokens?.completion ?? metrics.tokens?.completion ?? metrics.completion_tokens ?? metrics.stats?.completion_tokens ?? null;
    }
  } catch (e) {
    errors.push('invalid-metrics-json');
  }

  // 3.7 provenance.json
  let provenanceObj;
  try {
    provenanceObj = typeof contents.provenance === 'string'
      ? JSON.parse(contents.provenance)
      : contents.provenance;

    const provCheck = verifyProvenanceShape(provenanceObj, {
      serviceName: expected.serviceName || job.service_name,
      protocolVersion: expected.protocolVersion || job.protocol_version,
      materialId: expected.materialId || job.material_id,
      assetVersion: expected.assetVersion || job.asset_version,
      jobId: expected.jobId || job.job_id,
      allowProbeJobIdSuffix: expected.allowProbeJobIdSuffix,
    });
    errors.push(...provCheck.errors);
    warnings.push(...provCheck.warnings);

    if (provCheck.canonicalJobId) {
      sourceInput = {
        canonicalJobId: provCheck.canonicalJobId,
        provenanceJobId: provCheck.provenanceJobId,
        provenanceJobIdPolicy: provCheck.provenanceJobIdPolicy,
      };
    }

    // 优先从 inputs[0] 提取，否则回退到 input
    const provInput = (provenanceObj.inputs && Array.isArray(provenanceObj.inputs) && provenanceObj.inputs[0])
      || provenanceObj.input
      || {};

    // 校验 expected.rawInput
    if (expected.rawInput) {
      if (expected.rawInput.bucket && provInput.bucket !== expected.rawInput.bucket) {
        errors.push('provenance-input-bucket-mismatch');
      }
      if (expected.rawInput.object && provInput.object !== expected.rawInput.object) {
        errors.push('provenance-input-object-mismatch');
      }
      if (expected.rawInput.sha256 && (provInput.sha256 !== expected.rawInput.sha256 && provInput.sha256_hex !== expected.rawInput.sha256)) {
        errors.push('provenance-input-sha256-mismatch');
      }
    }

    // size_bytes=0 债务补偿
    let provInputSize = provInput.size_bytes ?? provInput.sizeBytes ?? null;
    if (provInputSize === 0) {
      warnings.push('input-size-bytes-zero');
      if (expected.rawInput?.sizeBytes) {
        provInputSize = expected.rawInput.sizeBytes;
      }
    }

    sourceInput = {
      ...(sourceInput || {}),
      bucket: provInput.bucket || null,
      object: provInput.object || null,
      sha256: provInput.sha256 || provInput.sha256_hex || null,
      sizeBytes: provInputSize,
    };
  } catch (e) {
    errors.push('invalid-provenance-json');
  }

  if (errors.length > 0) {
    return {
      ok: false,
      cleanState: CLEAN_STAGE_STATES.PROTOCOL_FAILURE,
      errors,
      warnings,
      unresolvedAnchorCount: 0,
    };
  }

  // 4. 计算 unresolvedAnchorCount 与补偿 inputSizeBytes
  let unresolvedAnchorCount = 0;
  if (Array.isArray(unresolved)) {
    unresolvedAnchorCount = unresolved.length;
  } else if (unresolved && typeof unresolved === 'object') {
    const list = unresolved.anchors || unresolved.unresolved_anchors || unresolved.list;
    if (Array.isArray(list)) {
      unresolvedAnchorCount = list.length;
    } else if (typeof unresolved.count === 'number') {
      unresolvedAnchorCount = unresolved.count;
    } else {
      unresolvedAnchorCount = Object.keys(unresolved).length;
    }
  }

  const provInput = (provenanceObj.inputs && Array.isArray(provenanceObj.inputs) && provenanceObj.inputs[0])
    || provenanceObj.input
    || {};
  let inputSizeBytes = provInput.size_bytes ?? provInput.sizeBytes ?? 0;
  if (inputSizeBytes === 0 && expected.rawInput?.sizeBytes) {
    inputSizeBytes = expected.rawInput.sizeBytes;
  }

  if (unresolvedAnchorCount > 0) {
    return {
      ok: true,
      cleanState: CLEAN_STAGE_STATES.REVIEW_PENDING_PARTIAL,
      errors: [],
      warnings,
      unresolvedAnchorCount,
      inputSizeBytes,
      sourceInput,
      tokensPrompt,
      tokensCompletion,
      tokensTotal,
      canonicalJobId: sourceInput?.canonicalJobId || null,
      provenanceJobId: sourceInput?.provenanceJobId || null,
      provenanceJobIdPolicy: sourceInput?.provenanceJobIdPolicy || null,
    };
  }

  return {
    ok: true,
    cleanState: CLEAN_STAGE_STATES.COMPLETED,
    errors: [],
    warnings,
    unresolvedAnchorCount,
    inputSizeBytes,
    sourceInput,
    tokensPrompt,
    tokensCompletion,
    tokensTotal,
    canonicalJobId: sourceInput?.canonicalJobId || null,
    provenanceJobId: sourceInput?.provenanceJobId || null,
    provenanceJobIdPolicy: sourceInput?.provenanceJobIdPolicy || null,
  };
}
