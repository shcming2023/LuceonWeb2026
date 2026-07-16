<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Refresh, Search, UploadFilled } from '@element-plus/icons-vue'
import { materialsApi } from '@/api/materials'
import type { MaterialArtifactCatalog, MaterialItem, MaterialLineage, MaterialUploadResponse, PipelinePreflightResponse } from '@/types/material'
import { formatFileSize } from '@/utils/format'
import { formatDateTime } from '@/utils/status'
import { ensureCurrentUser, useCurrentUser } from '@/utils/user'
import MaterialIdentity from '@/components/MaterialIdentity.vue'
import StageStatusBadge from '@/components/StageStatusBadge.vue'
import ArtifactDownloadPanel from '@/components/ArtifactDownloadPanel.vue'
import LineageTimeline from '@/components/LineageTimeline.vue'
import './workspace.css'

const route = useRoute()
const router = useRouter()
const currentUser = useCurrentUser()
const isAdmin = computed(() => Boolean(currentUser.value?.capabilities?.pipeline_admin))
const loading = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadResults = ref<MaterialUploadResponse['files']>([])
const rows = ref<MaterialItem[]>([])
const total = ref(0)
const page = ref(Number(route.query.page) || 1)
const pageSize = ref(20)
const search = ref(String(route.query.search || ''))
const stage = ref(String(route.query.stage || ''))
const selected = ref<MaterialItem[]>([])
const fileInput = ref<HTMLInputElement | null>(null)

const batchDialog = ref(false)
const preflightLoading = ref(false)
const submitting = ref(false)
const preflight = ref<PipelinePreflightResponse | null>(null)
const reprocessCompleted = ref(false)

const detailOpen = ref(false)
const detailLoading = ref(false)
const detailMaterial = ref<MaterialItem | null>(null)
const catalog = ref<MaterialArtifactCatalog | null>(null)
const lineage = ref<MaterialLineage | null>(null)

const selectionValid = computed(() => selected.value.length > 0 && selected.value.length <= 5)

function metadataDisplayStatus(material: MaterialItem) {
  const status = material.book_metadata?.status || 'missing'
  return material.book_metadata?.manual_override || status === 'manual' || status === 'ai_extracted' ? 'succeeded' : status
}

function metadataDisplayLabel(material: MaterialItem) {
  const status = material.book_metadata?.status || 'missing'
  if (material.book_metadata?.manual_override || status === 'manual') return '人工已编目'
  if (status === 'ai_extracted') return 'AI 已编目'
  return '待编目'
}

function updateQuery() {
  router.replace({ query: { ...(search.value ? { search: search.value } : {}), ...(stage.value ? { stage: stage.value } : {}), ...(page.value > 1 ? { page: String(page.value) } : {}), ...(detailOpen.value && detailMaterial.value ? { material_pk: detailMaterial.value.id } : {}) } })
}

async function load() {
  loading.value = true
  try {
    const requestedMaterialPk = String(route.query.material_pk || '')
    const result = await materialsApi.getMaterials({ page: page.value, page_size: pageSize.value, search: search.value, stage: stage.value })
    rows.value = result.materials
    total.value = result.total
    updateQuery()
    const requested = rows.value.find(row => row.id === requestedMaterialPk)
    if (requested && (!detailOpen.value || detailMaterial.value?.id !== requested.id)) await openDetail(requested)
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || 'PDF 资产加载失败')
  } finally {
    loading.value = false
  }
}

function applyFilter() {
  page.value = 1
  load()
}

async function uploadFiles(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (!files.length) return
  if (files.some(file => file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf'))) {
    ElMessage.error('只能上传 PDF 文件')
    input.value = ''
    return
  }
  uploading.value = true
  uploadProgress.value = 0
  uploadResults.value = []
  try {
    const result = await materialsApi.upload(files, value => { uploadProgress.value = value })
    uploadResults.value = result.files || []
    const duplicateText = result.duplicates ? `，${result.duplicates} 个已存在并去重` : ''
    ElMessage.success(`上传处理完成：${result.success} 个成功${duplicateText}`)
    await load()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

function onSelectionChange(value: MaterialItem[]) {
  if (value.length > 5) {
    ElMessage.warning('一个解析批次最多选择 5 本教材')
    return
  }
  selected.value = value
  preflight.value = null
}

function openBatch() {
  if (!selectionValid.value) return
  preflight.value = null
  reprocessCompleted.value = false
  batchDialog.value = true
}

async function runPreflight() {
  preflightLoading.value = true
  try {
    preflight.value = await materialsApi.preflightPipeline(selected.value.length, {
      material_pks: selected.value.map(row => Number(row.id)),
      reprocess_completed: reprocessCompleted.value
    })
    if (preflight.value.ready) ElMessage.success('预检通过，可提交解析批次')
    else ElMessage.warning(`预检未通过：${preflight.value.status || preflight.value.plan_status || '请检查运行状态'}`)
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '预检失败')
  } finally {
    preflightLoading.value = false
  }
}

async function submitBatch() {
  if (!preflight.value?.ready) return
  await ElMessageBox.confirm('提交后将按快照执行 MinerU 批量 → 逐本冻结 → Popo 批量 → 逐本冻结。是否继续？', '提交解析批次', { type: 'warning' })
  submitting.value = true
  try {
    const run = await materialsApi.startPipeline(true, selected.value.length, {
      material_pks: selected.value.map(row => Number(row.id)),
      reprocess_completed: reprocessCompleted.value
    })
    ElMessage.success(`解析批次 #${run.id} 已进入持久队列`)
    batchDialog.value = false
    router.push(`/pipeline/runs?run_id=${run.id}`)
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

async function openDetail(material: MaterialItem) {
  detailMaterial.value = material
  detailOpen.value = true
  updateQuery()
  detailLoading.value = true
  catalog.value = null
  lineage.value = null
  try {
    const [artifactResult, lineageResult] = await Promise.all([
      materialsApi.getArtifactCatalog(material.id),
      materialsApi.getLineage(material.id)
    ])
    catalog.value = artifactResult
    lineage.value = lineageResult
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '资产详情加载失败')
  } finally {
    detailLoading.value = false
  }
}

function closeDetail() {
  detailMaterial.value = null
  catalog.value = null
  lineage.value = null
  updateQuery()
}

async function createMetadataJob(material: MaterialItem) {
  try {
    const job = await materialsApi.createMetadataJob(material.id)
    ElMessage.success(`AI 元数据任务 #${job.id} 已排队`)
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '元数据任务创建失败')
  }
}

function openReview(material: MaterialItem) {
  if (material.review_asset_id) router.push({ path: '/review/compare', query: { asset_id: material.review_asset_id } })
}

function openRefinement(material: MaterialItem) {
  router.push({ path: '/workflow/jobs', query: { material_pk: material.id, material_id: material.material_id } })
}

watch(page, load)
onMounted(async () => {
  try { await ensureCurrentUser() } catch { /* API will enforce authorization */ }
  await load()
})
</script>

<template>
  <div class="workspace-page">
    <header class="workspace-header">
      <div>
        <span class="workspace-kicker">Stage 1 · digital assets</span>
        <h1>PDF 资产</h1>
        <p>上传、去重、检索与下载原始或阶段性数字资产；任务执行在独立工作台追踪。</p>
      </div>
      <div class="workspace-actions">
        <input ref="fileInput" hidden type="file" accept="application/pdf,.pdf" multiple @change="uploadFiles" />
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
        <el-button type="primary" :icon="UploadFilled" :loading="uploading" @click="fileInput?.click()">上传 PDF</el-button>
      </div>
    </header>

    <el-progress v-if="uploading" :percentage="uploadProgress" :stroke-width="5" />

    <section v-if="uploadResults.length" class="workspace-panel">
      <div class="workspace-toolbar">
        <div>
          <strong>本次上传结果</strong>
          <p class="mono-note">逐文件显示本次提交名与系统规范资产；“已去重”表示复用既有数字资产，没有重复创建材料。</p>
        </div>
      </div>
      <el-table :data="uploadResults" size="small" max-height="240">
        <el-table-column prop="filename" label="本次提交文件名" min-width="220" />
        <el-table-column label="处理结果" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'failed' ? 'danger' : row.status === 'duplicate' ? 'warning' : 'success'">
              {{ row.status === 'duplicate' ? '已去重' : row.status === 'success' ? '已新建' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="系统规范资产" min-width="330">
          <template #default="{ row }">
            <MaterialIdentity
              v-if="row.material"
              :filename="row.material.filename"
              :material-id="row.material.material_id"
              :material-pk="row.material.id"
              :sha256="row.material.input_sha256"
            />
            <span v-else class="error-note">{{ row.error_message || '未生成资产' }}</span>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="workspace-panel">
      <div class="workspace-toolbar">
        <div class="workspace-filters">
          <el-input v-model="search" clearable placeholder="文件名、material_id、SHA 或元数据" style="width: 300px" @keyup.enter="applyFilter"><template #prefix><el-icon><Search /></el-icon></template></el-input>
          <el-select v-model="stage" clearable placeholder="资产阶段" style="width: 150px" @change="applyFilter">
            <el-option label="仅 PDF" value="input" />
            <el-option label="MinerU" value="mineru" />
            <el-option label="解析就绪" value="popo" />
            <el-option label="已有输出" value="latex" />
          </el-select>
          <el-button @click="applyFilter">查询</el-button>
        </div>
        <div class="inline-actions">
          <span class="mono-note">已选 {{ selected.length }}/5</span>
          <el-button type="primary" :disabled="!selectionValid" @click="openBatch">创建解析批次</el-button>
        </div>
      </div>

      <div class="workspace-table">
        <el-table v-loading="loading" :data="rows" row-key="id" height="calc(100vh - 284px)" @selection-change="onSelectionChange">
          <el-table-column type="selection" width="46" />
          <el-table-column label="PDF / 身份" min-width="310">
            <template #default="{ row }"><MaterialIdentity :filename="row.filename" :material-id="row.material_id" :material-pk="row.id" :sha256="row.input_sha256" /></template>
          </el-table-column>
          <el-table-column label="规格" width="135"><template #default="{ row }"><span>{{ formatFileSize(row.size) }}</span><span class="identity-meta">{{ row.page_count || '—' }} 页</span></template></el-table-column>
          <el-table-column label="解析就绪" width="120"><template #default="{ row }"><StageStatusBadge :status="row.popo_available ? 'succeeded' : row.stage_status" :label="row.popo_available ? '已就绪' : '未就绪'" /></template></el-table-column>
          <el-table-column label="编目状态" width="130"><template #default="{ row }"><StageStatusBadge :status="metadataDisplayStatus(row)" :label="metadataDisplayLabel(row)" /></template></el-table-column>
          <el-table-column label="精修状态" width="130"><template #default="{ row }"><StageStatusBadge :status="row.refinement_status" /></template></el-table-column>
          <el-table-column label="更新时间" width="166"><template #default="{ row }">{{ formatDateTime(row.last_synced_at || row.created_at || '') }}</template></el-table-column>
          <el-table-column label="操作" width="260" fixed="right">
            <template #default="{ row }">
              <el-button link @click="openDetail(row)">资产与追溯</el-button>
              <el-button link @click="createMetadataJob(row)">AI 编目</el-button>
              <el-button v-if="row.popo_available" link @click="openRefinement(row)">进入精修</el-button>
              <el-button v-if="row.review_asset_id" link @click="openReview(row)">比对审阅</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="workspace-pagination"><el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" /></div>
    </section>

    <el-dialog v-model="batchDialog" title="创建解析批次" width="720px">
      <el-alert type="info" :closable="false" show-icon title="所选教材会固化为不可变任务快照；执行顺序为 MinerU 批量、逐本冻结、Popo 批量、逐本冻结。" />
      <ul class="snapshot-list">
        <li v-for="row in selected" :key="row.id"><MaterialIdentity :filename="row.filename" :material-id="row.material_id" :material-pk="row.id" :sha256="row.input_sha256" /></li>
      </ul>
      <el-alert
        v-if="selected.some(row => row.popo_available)"
        type="warning"
        :closable="false"
        show-icon
        title="所选资产已有冻结解析结果。普通提交会保持幂等且不重刷；只有管理员明确创建新版本时才会重新运行 MinerU 与 Popo，历史版本不会删除。"
      />
      <el-checkbox v-if="isAdmin" v-model="reprocessCompleted" @change="preflight = null">管理员：为已完成资产创建新的不可变解析版本</el-checkbox>
      <el-alert v-if="preflight" :type="preflight.ready ? 'success' : 'warning'" :closable="false" :title="preflight.ready ? '预检通过' : `预检未通过：${preflight.status || preflight.plan_status}`" />
      <template #footer>
        <el-button @click="batchDialog = false">取消</el-button>
        <el-button :loading="preflightLoading" @click="runPreflight">执行预检</el-button>
        <el-button type="primary" :disabled="!preflight?.ready" :loading="submitting" @click="submitBatch">提交解析</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailOpen" size="720px" :title="detailMaterial?.filename || '资产详情'" @closed="closeDetail">
      <div v-loading="detailLoading">
        <section class="detail-section"><h3><el-icon><Download /></el-icon> 可下载资产</h3><ArtifactDownloadPanel v-if="detailMaterial && catalog" :material-pk="detailMaterial.id" :artifacts="catalog.artifacts" /></section>
        <section class="detail-section"><h3>跨域追溯</h3><LineageTimeline v-if="lineage" :lineage="lineage" /></section>
      </div>
    </el-drawer>
  </div>
</template>
