import assert from 'node:assert/strict'
import fs from 'node:fs'

const filesView = fs.readFileSync(new URL('../src/views/Files.vue', import.meta.url), 'utf8')
const materialsApi = fs.readFileSync(new URL('../src/api/materials.ts', import.meta.url), 'utf8')

assert.match(materialsApi, /pipeline\/resume-popo\/preflight/)
assert.match(materialsApi, /pipeline\/resume-popo\/start/)
assert.match(filesView, /恢复 Popo/)
assert.match(filesView, /resumePopoFromFrozenMineru/)
assert.match(filesView, /!hasMineruAsset\(row\) \|\| hasPopoAsset\(row\)/)
assert.match(filesView, /仅复用已冻结的 MinerU 产物/)
assert.match(filesView, /currentUser\.value\?\.capabilities\?\.pipeline_admin/)
assert.doesNotMatch(filesView, /label: '恢复 Popo'[\s\S]{0,120}command: 'resume-popo'/)
assert.match(filesView, /v-if="isPipelineAdmin"[^>]*command="resume-popo"/)

console.log('Admin-only frozen MinerU to Popo recovery contract passed')
