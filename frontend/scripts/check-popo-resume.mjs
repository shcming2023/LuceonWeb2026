import assert from 'node:assert/strict'
import fs from 'node:fs'

const pipelineView = fs.readFileSync(new URL('../src/views/PipelineTasks.vue', import.meta.url), 'utf8')
const assetView = fs.readFileSync(new URL('../src/views/PdfAssets.vue', import.meta.url), 'utf8')
const refinementView = fs.readFileSync(new URL('../src/views/RefinementTasks.vue', import.meta.url), 'utf8')
const runItems = fs.readFileSync(new URL('../src/components/PipelineRunItems.vue', import.meta.url), 'utf8')
const materialsApi = fs.readFileSync(new URL('../src/api/materials.ts', import.meta.url), 'utf8')

assert.match(materialsApi, /pipeline\/resume-popo\/preflight/)
assert.match(materialsApi, /pipeline\/resume-popo\/start/)
assert.match(pipelineView, /恢复 Popo/)
assert.match(runItems, /mineru_manifest\?\.object && !row\.popo_manifest\?\.object/)
assert.match(pipelineView, /仅重跑.*Popo，复用已冻结 MinerU 资产/)
assert.match(pipelineView, /currentUser\.value\?\.capabilities\?\.pipeline_admin/)
assert.match(pipelineView, /:show-recovery="isAdmin"/)
assert.doesNotMatch(assetView, /startPopoResume|preflightPopoResume|恢复 Popo/)
assert.doesNotMatch(refinementView, /startPopoResume|preflightPopoResume|恢复 Popo/)

console.log('Admin-only frozen MinerU to Popo recovery contract passed')
