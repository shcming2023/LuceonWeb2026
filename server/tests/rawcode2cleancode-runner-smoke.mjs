import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { convertCleanlatexPacksToRawCode } from '../../scripts/cleanlatex-pack-to-rawcode.mjs';
import { buildFixtureRawCode, parseLooseJson, validateCleanCode } from '../../scripts/rawcode2cleancode-pilot.mjs';
import { runRawCode2CleanCodeUatRunner } from '../../scripts/rawcode2cleancode-runner.mjs';

async function makeFixtureSample(root, n) {
  const fixtureRoot = join(root, `fixture-${n}`);
  const rawBundleDir = await buildFixtureRawCode(fixtureRoot);
  return {
    sampleId: `fixture-${n}-chapter-001`,
    rawBundleDir,
    chapterId: 'chapter_001',
    title: `Fixture ${n}`,
  };
}

function fakeProcessSample({ failAt = null, calls = [] } = {}) {
  return async ({ sample, index, mode, phaseLabel }) => {
    calls.push({ sampleId: sample.sampleId, index, mode, phaseLabel });
    if (failAt && failAt.index === index && failAt.mode === mode && (!failAt.phaseLabel || failAt.phaseLabel === phaseLabel)) {
      return {
        ok: false,
        stage: failAt.stage || 'rawcode2cleancode-local-clean',
        code: failAt.code || 'INJECTED_FAILURE',
        reason: failAt.reason || 'injected failure',
        operationCounts: {},
        readinessClaimed: false,
      };
    }
    return {
      ok: true,
      stage: 'rawcode2cleancode-fixture-processor',
      status: 'PASS',
      evidence: {
        input: { rawBundleDir: sample.rawBundleDir, chapterId: sample.chapterId },
        output: { simulated: true },
        sideEffects: { db_writes: 0, minio_writes: 0, runtime_worker_posts: 0 },
      },
      operationCounts: {
        localRawBundleRead: 1,
        localCleanBundleWrite: 1,
        llmApiCall: 0,
        dbWrite: 0,
        minioWrite: 0,
        runtimeWorkerPost: 0,
      },
      readinessClaimed: false,
    };
  };
}

const tmpRoot = await mkdtemp(join(tmpdir(), 'rawcode2cleancode-smoke-'));

try {
  const samples = [
    await makeFixtureSample(tmpRoot, 1),
    await makeFixtureSample(tmpRoot, 2),
    await makeFixtureSample(tmpRoot, 3),
  ];

  console.log('=== RawCode2CleanCode UAT Runner Smoke ===');

  {
    console.log('  [1] fixture dry-run produces PASS CleanCode and zero production side effects...');
    const outDir = join(tmpRoot, 'dry-run-out');
    const result = await runRawCode2CleanCodeUatRunner({
      samples: [samples[0]],
      mode: 'dry-run',
      operatorId: 'local-operator',
      outDir,
      cleaner: 'deterministic',
      deps: { now: () => '2026-06-04T00:00:00.000Z', manifestSha: 'a'.repeat(64) },
    });
    assert.equal(result.ok, true, JSON.stringify(result, null, 2));
    assert.equal(result.realRunExecuted, false);
    assert.equal(result.completedSampleCount, 1);
    assert.equal(result.samples[0].status, 'PASS');
    assert.equal(result.operationCounts.dbWrite, 0);
    assert.equal(result.operationCounts.minioWrite, 0);
    assert.equal(result.operationCounts.runtimeWorkerPost, 0);
    assert.equal(result.readinessClaimed, false);
    assert.equal(result.samples[0].readinessClaimed, false);
    assert.equal(existsSync(result.samples[0].evidence.output.cleanMd), true);
  }

  {
    console.log('  [2] llm-dry-run generates audit evidence and NEEDS_REVIEW without LLM API calls...');
    const outDir = join(tmpRoot, 'llm-dry-run-out');
    const result = await runRawCode2CleanCodeUatRunner({
      samples: [samples[1]],
      mode: 'dry-run',
      operatorId: 'local-operator',
      outDir,
      cleaner: 'llm-dry-run',
      deps: { now: () => '2026-06-04T00:01:00.000Z', manifestSha: 'b'.repeat(64) },
    });
    assert.equal(result.ok, true, JSON.stringify(result, null, 2));
    assert.equal(result.samples[0].status, 'NEEDS_REVIEW');
    assert.equal(result.samples[0].evidence.cleaner.effective, 'llm-dry-run');
    assert.equal(result.operationCounts.llmApiCall, 0);
    assert.equal(existsSync(join(result.samples[0].evidence.output.auditDir, 'llm_prompt.txt')), true);
    assert.equal(result.readinessClaimed, false);
  }

  {
    console.log('  [3] rejects empty list, hard-cap overflow, duplicates, missing operator, unconfirmed real, and missing raw bundle...');
    const deps = { processSample: fakeProcessSample() };
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples: [], mode: 'dry-run', operatorId: 'op', deps })).code, 'EMPTY_SAMPLE_LIST');
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples, mode: 'dry-run', operatorId: 'op', hardCap: 2, deps })).code, 'HARD_CAP_EXCEEDED');
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples: [...samples, await makeFixtureSample(tmpRoot, 4)], mode: 'dry-run', operatorId: 'op', hardCap: 4, deps })).code, 'ENTRY_HARD_CAP_EXCEEDED');
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples: [samples[0], samples[0]], mode: 'dry-run', operatorId: 'op', deps })).code, 'DUPLICATE_SAMPLE');
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples: [samples[0]], mode: 'dry-run', deps })).code, 'MISSING_OPERATOR');
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples: [samples[0]], mode: 'real', operatorId: 'op', deps })).code, 'REAL_RUN_NOT_CONFIRMED');
    assert.equal((await runRawCode2CleanCodeUatRunner({ samples: [{ ...samples[0], rawBundleDir: join(tmpRoot, 'not-found') }], mode: 'dry-run', operatorId: 'op', deps })).code, 'RAW_BUNDLE_NOT_FOUND');
  }

  {
    console.log('  [4] rejects non-approved LLM model before any sample processing...');
    const calls = [];
    const result = await runRawCode2CleanCodeUatRunner({
      samples: [samples[0]],
      mode: 'real',
      operatorId: 'local-operator',
      confirmRealRun: true,
      cleaner: 'llm',
      model: 'gpt-4o-mini',
      deps: { processSample: fakeProcessSample({ calls }) },
    });
    assert.equal(result.ok, false);
    assert.equal(result.code, 'LLM_MODEL_NOT_ALLOWED');
    assert.equal(calls.length, 0);
  }

  {
    console.log('  [5] stop-on-first-failure blocks later samples...');
    const calls = [];
    const result = await runRawCode2CleanCodeUatRunner({
      samples,
      mode: 'dry-run',
      operatorId: 'local-operator',
      deps: {
        processSample: fakeProcessSample({
          calls,
          failAt: { index: 1, mode: 'dry-run', stage: 'validator', code: 'QUALITY_BLOCKED' },
        }),
        now: () => '2026-06-04T00:02:00.000Z',
        manifestSha: 'c'.repeat(64),
      },
    });
    assert.equal(result.ok, false);
    assert.equal(result.stopped.order, 2);
    assert.equal(result.stopped.code, 'QUALITY_BLOCKED');
    assert.deepEqual(calls.map((call) => call.sampleId), [samples[0].sampleId, samples[1].sampleId]);
    assert.equal(result.readinessClaimed, false);
  }

  {
    console.log('  [6] failed real-mode preflight prevents real execution...');
    const calls = [];
    const result = await runRawCode2CleanCodeUatRunner({
      samples,
      mode: 'real',
      operatorId: 'local-operator',
      confirmRealRun: true,
      deps: {
        processSample: fakeProcessSample({
          calls,
          failAt: { index: 0, mode: 'dry-run', phaseLabel: 'preflight', stage: 'preflight', code: 'PREFLIGHT_STOP' },
        }),
        now: () => '2026-06-04T00:03:00.000Z',
        manifestSha: 'd'.repeat(64),
      },
    });
    assert.equal(result.ok, false);
    assert.equal(result.code, 'PREFLIGHT_FAILED');
    assert.equal(result.realRunExecuted, false);
    assert.deepEqual(calls.map((call) => call.mode), ['dry-run']);
    assert.equal(result.readinessClaimed, false);
  }

  {
    console.log('  [7] real mode runs preflight then local real phase with zero production side effects...');
    const calls = [];
    const result = await runRawCode2CleanCodeUatRunner({
      samples: [samples[0], samples[1]],
      mode: 'real',
      operatorId: 'local-operator',
      confirmRealRun: true,
      deps: {
        processSample: fakeProcessSample({ calls }),
        now: () => '2026-06-04T00:04:00.000Z',
        manifestSha: 'e'.repeat(64),
      },
    });
    assert.equal(result.ok, true, JSON.stringify(result, null, 2));
    assert.equal(result.realRunExecuted, true);
    assert.equal(result.preflight.operationCounts.dbWrite, 0);
    assert.equal(result.operationCounts.dbWrite, 0);
    assert.deepEqual(calls.map((call) => call.mode), ['dry-run', 'dry-run', 'real', 'real']);
    assert.equal(result.readinessClaimed, false);
  }

  {
    console.log('  [8] Task329 cleaning_unit_pack artifacts adapt into RawCode and run through CleanCode dry-run...');
    const packsPath = join(tmpRoot, 'cleaning_unit_packs.json');
    await writeFile(packsPath, JSON.stringify([
      {
        schema: 'luceon-cleanlatex-cleaning-unit-pack/v1',
        pack_id: 'cleaning-unit:toc-0003',
        material_id: 'fixture-material',
        asset_version: 'v329',
        node: {
          node_id: 'toc-0003',
          canonical_kind: 'section',
          title: '1.1 Different types of numbers',
          number: '1.1',
          parent_id: 'toc-0002',
          parent_title: '1 Review of number concepts',
        },
        pack_boundary: {
          pack_level: 3,
          boundary_basis: 'structure-level',
          semantic_kind_is_boundary_driver: false,
        },
        source_span: {
          source_page_range: [16, 17],
          source_block_ids: ['b1', 'b2'],
          unresolved_source_block_ids: [],
        },
        content_blocks: [
          { block_id: 'b1', source_block_ids: ['b1'], source_order: 1, page: 16, type: 'text', raw_text: '1.1 Different types of numbers' },
          { block_id: 'b2', source_block_ids: ['b2'], source_order: 2, page: 16, type: 'text', raw_text: 'Real numbers include rational and irrational numbers.' },
        ],
        assets: { images: [], formulas: [], tables: [], audio: [] },
        warnings: [],
      },
      {
        schema: 'luceon-cleanlatex-cleaning-unit-pack/v1',
        pack_id: 'cleaning-unit:toc-0024',
        material_id: 'fixture-material',
        asset_version: 'v329',
        node: {
          node_id: 'toc-0024',
          canonical_kind: 'section',
          title: '4.1 Collecting and classifying data',
          number: '4.1',
          parent_id: 'toc-0023',
          parent_title: '4 Collecting, organising and displaying data',
        },
        pack_boundary: {
          pack_level: 3,
          boundary_basis: 'structure-level',
          semantic_kind_is_boundary_driver: false,
        },
        source_span: {
          source_page_range: [122, 123],
          source_block_ids: ['c1'],
          unresolved_source_block_ids: [],
        },
        content_blocks: [
          { block_id: 'c1', source_block_ids: ['c1'], source_order: 10, page: 122, type: 'text', raw_text: 'Data is a set of facts, numbers or other information.' },
          {
            block_id: 'c-table-1',
            source_block_ids: ['c-table-1'],
            source_order: 11,
            page: 122,
            type: 'table',
            raw_text: '',
            bbox: [0.1, 0.2, 0.7, 0.4],
            asset_hash_names: ['flow-table-hash.jpg'],
            asset_refs: [{
              kind: 'table',
              asset_hash_name: 'flow-table-hash.jpg',
              raw_ref: 'images/flow-table-hash.jpg',
              source_page: 122,
              bbox: [0.1, 0.2, 0.7, 0.4],
            }],
          },
        ],
        assets: {
          images: [],
          formulas: [],
          tables: [{
            asset_hash_name: 'flow-table-hash.jpg',
            source_page: 122,
            bbox: [0.1, 0.2, 0.7, 0.4],
            raw_ref: 'images/flow-table-hash.jpg',
            source_block_ids: ['c-table-1'],
          }],
          audio: [],
        },
        warnings: [],
      },
    ], null, 2));

    const packAssetRoot = join(tmpRoot, 'pack-assets');
    await mkdir(join(packAssetRoot, 'images'), { recursive: true });
    await writeFile(join(packAssetRoot, 'images', 'flow-table-hash.jpg'), 'fixture table image');

    const adapted = await convertCleanlatexPacksToRawCode({
      packsPath,
      outDir: join(tmpRoot, 'pack-adapter-out'),
      operatorId: 'local-operator',
      versionOverride: 'rawcode-from-v329',
      assetRoot: packAssetRoot,
    });
    assert.equal(adapted.ok, true);
    assert.equal(adapted.packCount, 2);
    assert.equal(existsSync(join(adapted.rawBundleDir, 'chapters', 'toc-0003', 'source_map.json')), true);
    const sectionRaw = await readFile(join(adapted.rawBundleDir, 'chapters', 'toc-0024', 'raw.md'), 'utf8');
    const sectionUnit = await readFile(join(adapted.rawBundleDir, 'chapters', 'toc-0024', 'unit.md'), 'utf8');
    const sectionSourceMap = JSON.parse(await readFile(join(adapted.rawBundleDir, 'chapters', 'toc-0024', 'source_map.json'), 'utf8'));
    const sectionImageMap = JSON.parse(await readFile(join(adapted.rawBundleDir, 'chapters', 'toc-0024', 'image_map.json'), 'utf8'));
    assert.match(sectionRaw, /luceon:visual_block type=table source_block_ids=c-table-1 page=122/);
    assert.match(sectionRaw, /!\[table source_block=c-table-1 page=122\]\(images\/flow-table-hash\.jpg\)/);
    assert.match(sectionUnit, /luceon:visual_block type=table source_block_ids=c-table-1 page=122/);
    const mappedTableBlock = sectionSourceMap.source_blocks.find((block) => block.block_id === 'c-table-1');
    assert.equal(mappedTableBlock.markdown_placeholders[0].asset_hash_name, 'flow-table-hash.jpg');
    assert.deepEqual(mappedTableBlock.markdown_placeholders[0].bbox, [0.1, 0.2, 0.7, 0.4]);
    const mappedTableImage = sectionImageMap.images.find((image) => image.asset_hash_name === 'flow-table-hash.jpg');
    assert.equal(mappedTableImage.required, true);
    assert.equal(mappedTableImage.asset_kind, 'table');

    const result = await runRawCode2CleanCodeUatRunner({
      samples: [
        {
          sampleId: 'pack-toc-0003',
          rawBundleDir: adapted.rawBundleDir,
          chapterId: 'toc-0003',
          title: '1.1 Different types of numbers',
        },
        {
          sampleId: 'pack-toc-0024',
          rawBundleDir: adapted.rawBundleDir,
          chapterId: 'toc-0024',
          title: '4.1 Collecting and classifying data',
        },
      ],
      mode: 'dry-run',
      operatorId: 'local-operator',
      outDir: join(tmpRoot, 'pack-runner-out'),
      cleaner: 'deterministic',
      deps: { now: () => '2026-06-04T00:05:00.000Z', manifestSha: 'f'.repeat(64) },
    });
    assert.equal(result.ok, true, JSON.stringify(result, null, 2));
    assert.equal(result.completedSampleCount, 2);
    assert.equal(result.operationCounts.dbWrite, 0);
    assert.equal(result.operationCounts.minioWrite, 0);
    assert.equal(result.operationCounts.runtimeWorkerPost, 0);
    const cleanTableMarkdown = await readFile(result.samples[1].evidence.output.cleanMd, 'utf8');
    assert.match(cleanTableMarkdown, /luceon:visual_block type=table source_block_ids=c-table-1 page=122 bbox=\[0\.1,0\.2,0\.7,0\.4\] asset_hash=flow-table-hash\.jpg/);
  }

  {
    console.log('  [9] raw split markers and repeated large text downgrade CleanCode candidate to NEEDS_REVIEW...');
    const packsPath = join(tmpRoot, 'dirty_cleaning_unit_packs.json');
    const repeatedText = 'This paragraph is intentionally long enough to be detected as a repeated source segment for validation. It should not be silently accepted.';
    await writeFile(packsPath, JSON.stringify([
      {
        schema: 'luceon-cleanlatex-cleaning-unit-pack/v1',
        pack_id: 'cleaning-unit:toc-dirty',
        material_id: 'fixture-material',
        asset_version: 'v329',
        node: {
          node_id: 'toc-dirty',
          canonical_kind: 'section',
          title: 'Dirty section',
          number: 'D.1',
        },
        pack_boundary: {
          pack_level: 3,
          boundary_basis: 'structure-level',
          semantic_kind_is_boundary_driver: false,
        },
        source_span: {
          source_page_range: [1, 2],
          source_block_ids: ['d1', 'd2'],
          unresolved_source_block_ids: [],
        },
        content_blocks: [
          { block_id: 'd1', source_block_ids: ['d1'], source_order: 1, page: 1, type: 'text', raw_text: `${repeatedText}<|txt_split|>Question one.` },
          { block_id: 'd2', source_block_ids: ['d2'], source_order: 2, page: 1, type: 'text', raw_text: repeatedText },
        ],
        assets: { images: [], formulas: [], tables: [], audio: [] },
        warnings: [],
      },
    ], null, 2));

    const adapted = await convertCleanlatexPacksToRawCode({
      packsPath,
      outDir: join(tmpRoot, 'dirty-pack-adapter-out'),
      operatorId: 'local-operator',
      versionOverride: 'rawcode-from-v329',
    });
    const result = await runRawCode2CleanCodeUatRunner({
      samples: [{ sampleId: 'dirty-pack', rawBundleDir: adapted.rawBundleDir, chapterId: 'toc-dirty', title: 'Dirty section' }],
      mode: 'dry-run',
      operatorId: 'local-operator',
      outDir: join(tmpRoot, 'dirty-pack-runner-out'),
      cleaner: 'deterministic',
      deps: { now: () => '2026-06-04T00:06:00.000Z', manifestSha: '1'.repeat(64) },
    });
    assert.equal(result.ok, true, JSON.stringify(result, null, 2));
    assert.equal(result.samples[0].status, 'NEEDS_REVIEW');
    const qualityReport = JSON.parse(await readFile(result.samples[0].evidence.output.qualityReport, 'utf8'));
    assert.equal(qualityReport.risks.includes('raw_split_markers_remaining'), true);
    assert.equal(qualityReport.risks.includes('duplicate_large_text_segments'), true);
  }

  {
    console.log('  [10] sample processing errors redact API keys from evidence...');
    const result = await runRawCode2CleanCodeUatRunner({
      samples: [samples[0]],
      mode: 'dry-run',
      operatorId: 'local-operator',
      deps: {
        processSample: async () => {
          throw new Error('LLM API request failed with 401: Incorrect API key provided: sk-test********************************tail');
        },
      },
    });
    assert.equal(result.ok, false);
    assert.equal(result.samples[0].reason.includes('sk-test'), false);
    assert.equal(result.samples[0].reason.includes('[REDACTED_API_KEY]'), true);
    assert.equal(JSON.stringify(result.samples[0].evidence).includes('sk-test'), false);
  }

  {
    console.log('  [11] duplicate-aware coverage accepts faithful de-duplicated LLM output...');
    const repeatedText = 'This duplicated source paragraph contains all unique educational content for the section and should count once after cleaning.';
    const qualityReport = validateCleanCode({
      cleanMarkdown: `# Dedup section\n\n${repeatedText}\n`,
      chapterTitle: 'Dedup section',
      imageMap: { images: [] },
      cleanChapterDir: tmpRoot,
      copiedImages: [],
      missingImages: [],
      unresolvedItems: [],
      rawMarkdown: `# Dedup section\n\n${[repeatedText, repeatedText, repeatedText, repeatedText].join('\n\n')}\n`,
      cleanerMode: 'llm',
      llmResponse: {
        clean_markdown: `# Dedup section\n\n${repeatedText}\n`,
        kept_images: [],
        removed_noise: [],
        unresolved_items: [],
        change_summary: ['removed exact duplicate source paragraphs'],
        risk_flags: [],
      },
    });
    const coverageCheck = qualityReport.checks.find((check) => check.id === 'content_coverage_ratio');
    assert.equal(qualityReport.status, 'PASS', JSON.stringify(qualityReport, null, 2));
    assert.equal(coverageCheck.status, 'PASS');
    assert.equal(coverageCheck.detail.duplicateAwarePass, true);
  }

  {
    console.log('  [12] visual references without assets or review items require review...');
    const qualityReport = validateCleanCode({
      cleanMarkdown: '# Section\n\nThe flow diagram shows the statistical investigation process.\n',
      chapterTitle: 'Section',
      imageMap: { images: [] },
      cleanChapterDir: tmpRoot,
      copiedImages: [],
      missingImages: [],
      unresolvedItems: [],
      rawMarkdown: '# Section\n\nThe flow diagram shows the statistical investigation process.\n',
      cleanerMode: 'llm',
      llmResponse: {
        clean_markdown: '# Section\n\nThe flow diagram shows the statistical investigation process.\n',
        kept_images: [],
        removed_noise: [],
        unresolved_items: [],
        change_summary: [],
        risk_flags: [],
      },
    });
    const visualCheck = qualityReport.checks.find((check) => check.id === 'visual_references_have_assets_or_review_items');
    assert.equal(qualityReport.status, 'NEEDS_REVIEW', JSON.stringify(qualityReport, null, 2));
    assert.equal(visualCheck.status, 'NEEDS_REVIEW');
    assert.equal(qualityReport.risks.includes('visual_reference_without_asset_or_review_item'), true);
  }

  {
    console.log('  [13] pack visual evidence requirements require asset refs or review items...');
    const imageHashName = '71ef028a11659ad184c2c55a77eec9c6447b1168a81d59e273fb945c43d6929f.jpg';
    const qualityReport = validateCleanCode({
      cleanMarkdown: '# Section\n\nStatistical investigation process.\n',
      chapterTitle: 'Section',
      imageMap: {
        images: [{
          raw_ref: `images/${imageHashName}`,
          normalized_ref: `images/${imageHashName}`,
          source_path: `../../images/${imageHashName}`,
          required: false,
          asset_hash_name: imageHashName,
        }],
        visual_evidence_requirements: [{
          terms: ['flow diagram'],
          status: 'asset-linked',
          required_action: 'preserve_asset_reference_or_report_unresolved',
          linked_asset_hash_names: [imageHashName],
          source_block_ids: ['b-4-1'],
        }],
      },
      cleanChapterDir: tmpRoot,
      copiedImages: [],
      missingImages: [],
      unresolvedItems: [],
      rawMarkdown: '# Section\n\nThe flow diagram shows the statistical investigation process.\n',
      cleanerMode: 'llm',
      llmResponse: {
        clean_markdown: '# Section\n\nStatistical investigation process.\n',
        kept_images: [],
        removed_noise: [],
        unresolved_items: [],
        change_summary: [],
        risk_flags: [],
      },
    });
    const visualCheck = qualityReport.checks.find((check) => check.id === 'visual_references_have_assets_or_review_items');
    assert.equal(qualityReport.status, 'NEEDS_REVIEW', JSON.stringify(qualityReport, null, 2));
    assert.equal(visualCheck.status, 'NEEDS_REVIEW');
    assert.equal(visualCheck.detail.visualEvidenceGaps[0].linked_asset_hash_names[0], imageHashName);
  }

  {
    console.log('  [14] LLM JSON parser tolerates unescaped LaTeX backslashes from model content...');
    const parsed = parseLooseJson([
      '{',
      '  "clean_markdown": "# Section\\n\\nAB \\parallel CD and \\sqrt{x} appear in the source.",',
      '  "kept_images": [],',
      '  "removed_noise": [],',
      '  "unresolved_items": [],',
      '  "change_summary": [],',
      '  "risk_flags": ["contains_formula"]',
      '}',
    ].join('\n'));
    assert.match(parsed.clean_markdown, /\\parallel CD/);
    assert.match(parsed.clean_markdown, /\\sqrt\{x\}/);
  }

  console.log('RawCode2CleanCode UAT runner smoke passed.');
} finally {
  await rm(tmpRoot, { recursive: true, force: true });
}
