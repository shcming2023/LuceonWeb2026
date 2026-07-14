import assert from 'node:assert/strict'
import fs from 'node:fs'

const filesView = fs.readFileSync(new URL('../src/views/Files.vue', import.meta.url), 'utf8')
const materialsApi = fs.readFileSync(new URL('../src/api/materials.ts', import.meta.url), 'utf8')

assert.match(filesView, /error\?\.response\?\.status !== 404/)
assert.match(filesView, /v-else-if="activeWorkflowV2Job\.status === 'needs_review'"/)
assert.match(filesView, /restartWorkflowV2Job\(jobId, stageKey\)/)
assert.match(filesView, /处理 V2\.3 质量阻断/)
assert.match(filesView, /补全审阅闭环/)
assert.match(filesView, /workflowV2ReviewClosureMissing/)
assert.match(filesView, /从排版构建重新运行/)
assert.match(filesView, /restartActiveWorkflowV2LatexBuild/)
assert.doesNotMatch(
  filesView,
  /retryWorkflowV2Job\(job\.id\)[\s\S]{0,120}runWorkflowV2Job\(job\.id\)/,
  'retry endpoint already enqueues the new attempt and must not be followed by a second run request'
)
assert.match(materialsApi, /\/restart\/\$\{stageKey\}/)

console.log('Worker V2 non-layout quality-block recovery contract passed')
