<template>
  <div class="materials-root">
    <header class="page-header">
      <div>
        <h1 class="page-title">文件管理</h1>
        <div class="page-meta">
          <span>共 {{ total }} 份材料</span>
          <span v-if="availabilityLine">{{ availabilityLine }}</span>
          <span v-if="summary?.latest_run">最近任务：{{ pipelineStatusText(summary.latest_run.status) }}</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button :icon="Upload" type="primary" @click="uploadDialogVisible = true">上传 PDF</el-button>
        <el-tooltip content="扫描 MinIO 资产桶并刷新本地索引，不提交 GPU 任务" placement="bottom">
          <el-button :icon="Refresh" :loading="syncing" @click="syncMaterials(true)">同步资产</el-button>
        </el-tooltip>
        <el-tooltip content="检查 GPU 服务、分段接口、待处理 PDF 和 active marker，不提交 GPU 任务" placement="bottom">
          <el-button :icon="VideoPlay" :loading="preflighting" :disabled="pipelineBusy" @click="runPreflight">解析预检</el-button>
        </el-tooltip>
        <el-tooltip content="提交最多 5 个待处理 PDF 到 GPU，执行 MinerU 后再跑 Popo" placement="bottom">
          <el-button :icon="Cpu" type="warning" :loading="pipelineBusy" :disabled="preflighting" @click="startPipeline">启动GPU解析</el-button>
        </el-tooltip>
      </div>
    </header>

    <section :class="['task-ticker', `tone-${taskTickerTone}`]">
      <span class="task-ticker-label">任务</span>
      <div class="task-ticker-viewport">
        <div class="task-ticker-track">
          <span>{{ taskTickerText }}</span>
          <span aria-hidden="true">{{ taskTickerText }}</span>
        </div>
      </div>
      <el-button
        v-if="canPublishPopoToRawDryRun"
        size="small"
        type="primary"
        :loading="publishingRawDryRun"
        @click="publishPopoToRawDryRun"
      >
        发布未入库Raw
      </el-button>
    </section>

    <section v-if="recentOperation" :class="['operation-focus', recentOperation.status]">
      <div class="operation-main">
        <span class="operation-label">最近操作</span>
        <strong>{{ recentOperation.filename }}</strong>
        <span>{{ recentOperation.action }} · {{ operationStatusText(recentOperation.status) }}</span>
        <span class="operation-id">{{ recentOperation.materialId || recentOperation.materialPk }}</span>
      </div>
      <div class="operation-actions">
        <el-button size="small" @click="locateRecentOperation">定位</el-button>
        <el-button size="small" text @click="clearRecentOperation">清除</el-button>
      </div>
    </section>

    <section class="filter-bar">
      <el-input v-model="params.search" class="search-input" clearable placeholder="搜索文件名、material_id、MinIO 对象">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="params.stage" clearable class="stage-select" placeholder="全部阶段">
        <el-option v-for="stage in stageOptions" :key="stage.value" :label="stage.label" :value="stage.value" />
      </el-select>
      <div class="quick-selects">
        <el-button size="small" @click="selectCurrentPage('clean-missing')">选本页待Clean</el-button>
        <el-button size="small" @click="selectCurrentPage('raw-existing')">选本页已有Raw</el-button>
      </div>
    </section>

    <section v-if="selectedRows.length || batchState.running" class="batch-bar">
      <div class="batch-summary">
        <strong>{{ batchState.running ? '批量任务执行中' : `已选择 ${selectedRows.length} 条` }}</strong>
        <span v-if="!batchState.running">
          待Clean {{ selectedCleanMissingRows.length }} · 可重建Clean {{ selectedCleanRows.length }} · 可重建Raw {{ selectedRawRows.length }}
        </span>
        <span v-else>
          {{ batchState.done }}/{{ batchState.total }} · 成功 {{ batchState.success }} · 失败 {{ batchState.failed }} · {{ batchState.currentName }}
        </span>
      </div>
      <div class="batch-actions">
        <el-button
          size="small"
          type="success"
          :disabled="batchState.running || !selectedCleanMissingRows.length"
          @click="startBatch('clean-missing')"
        >
          批量生成Clean
        </el-button>
        <el-button
          size="small"
          type="warning"
          :disabled="batchState.running || !selectedCleanRows.length"
          @click="startBatch('clean-rebuild')"
        >
          批量重建Clean
        </el-button>
        <el-button
          size="small"
          type="danger"
          :disabled="batchState.running || !selectedRawRows.length"
          @click="startBatch('raw-rebuild')"
        >
          批量重建Raw
        </el-button>
        <el-button v-if="batchState.running" size="small" @click="stopBatchAfterCurrent">停止后续</el-button>
      </div>
      <div v-if="batchState.logs.length" class="batch-log">最近失败：{{ batchState.logs[0] }}</div>
    </section>

    <section class="table-shell">
      <el-table
        v-if="!loading"
        ref="materialTable"
        :data="orderedMaterials"
        height="100%"
        row-key="id"
        :row-class-name="materialRowClassName"
        :header-cell-style="{ background: 'var(--bg-tertiary)', color: 'var(--text-primary)', fontWeight: 600 }"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="44" fixed="left" />
        <el-table-column prop="filename" label="材料" min-width="260">
          <template #default="{ row }">
            <div class="material-cell">
              <span class="file-name">
                {{ row.filename }}
                <el-tag v-if="isActiveTaskRow(row)" size="small" type="primary" effect="plain">当前任务</el-tag>
                <el-tag v-else-if="isRecentOperationRow(row)" size="small" type="warning" effect="plain">最近操作</el-tag>
              </span>
              <span class="object-path">{{ row.input_object || row.material_id || '未绑定源 PDF' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="进度" min-width="300">
          <template #default="{ row }">
            <div class="pipeline-cell">
              <el-tag class="pipeline-status" :type="stageMeta[row.stage_status]?.type || 'info'" effect="plain">
                {{ stageMeta[row.stage_status]?.label || row.stage_status }}
              </el-tag>
              <div class="stage-chain">
                <span v-for="stage in artifactStages" :key="stage.key" :class="['stage-pill', { done: stage.done(row) }]">
                  {{ stage.label }}
                </span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="96">
          <template #default="{ row }">{{ formatFileSize(row.size) }}</template>
        </el-table-column>
        <el-table-column prop="last_synced_at" label="同步时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.last_synced_at || row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="430" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-tooltip :content="reviewUnavailableReason(row, 'pdf')" :disabled="Boolean(pdfReviewRoute(row))" placement="top">
                <span class="action-wrap">
                  <el-button link type="primary" @click="openPdfReview(row)" :disabled="!pdfReviewRoute(row)">PDF审查</el-button>
                </span>
              </el-tooltip>
              <el-tooltip :content="reviewUnavailableReason(row, 'outline')" :disabled="Boolean(outlineReviewRoute(row))" placement="top">
                <span class="action-wrap">
                  <el-button link type="warning" @click="openOutlineReview(row)" :disabled="!outlineReviewRoute(row)">目录审查</el-button>
                </span>
              </el-tooltip>
              <el-button
                v-if="canRunPopoToRaw(row)"
                link
                :type="hasRawAsset(row) ? 'danger' : 'success'"
                @click="startPopoToRawDryRun(row)"
              >
                {{ hasRawAsset(row) ? '重建Raw' : '生成Raw' }}
              </el-button>
              <el-button
                v-if="canRunRawToClean(row)"
                link
                :type="hasCleanAsset(row) ? 'danger' : 'success'"
                @click="startRawToClean(row, hasCleanAsset(row))"
              >
                {{ hasCleanAsset(row) ? '重建Clean' : '生成Clean' }}
              </el-button>
              <el-button link @click="previewPdf(row)" :disabled="!row.input_object">PDF</el-button>
              <el-button link @click="downloadPdf(row)" :disabled="!row.input_object">下载</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-skeleton v-else :rows="8" animated />
      <el-empty v-if="!loading && !materials.length" :description="emptyText">
        <el-button type="primary" :icon="Upload" @click="uploadDialogVisible = true">上传 PDF</el-button>
        <el-button :loading="syncing" @click="syncMaterials(true)">同步资产</el-button>
      </el-empty>
    </section>

    <footer class="pagination-row">
      <el-pagination
        v-model:current-page="params.page"
        v-model:page-size="params.page_size"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next"
      />
    </footer>

    <el-dialog v-model="uploadDialogVisible" title="上传 PDF" width="520px">
      <el-upload
        v-model:file-list="uploadFileList"
        drag
        multiple
        accept=".pdf,application/pdf"
        :auto-upload="false"
        :limit="20"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖入 PDF 或点击选择</div>
      </el-upload>
      <el-progress v-if="uploading" :percentage="uploadProgress" class="upload-progress" />
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" :disabled="!uploadableFiles.length" @click="submitUpload">
          上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Cpu, Refresh, Search, Upload, UploadFilled, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadUserFile } from 'element-plus'
import { useRouter } from 'vue-router'
import { materialsApi } from '@/api/materials'
import type {
  MaterialItem,
  MaterialSummary,
  ObjectRef,
  PipelinePreflightResponse,
  PipelineRun,
  PopoToRawPreflightResponse,
  RawToCleanPreflightResponse,
  PipelineStatusResponse
} from '@/types/material'
import { formatFileSize } from '@/utils/format'
import { formatDateTime as formatDate } from '@/utils/status'

const router = useRouter()
const materials = ref<MaterialItem[]>([])
const total = ref(0)
const loading = ref(false)
const syncing = ref(false)
const uploadDialogVisible = ref(false)
const uploading = ref(false)
const publishingRawDryRun = ref(false)
const uploadProgress = ref(0)
const uploadFileList = ref<UploadUserFile[]>([])
const summary = ref<MaterialSummary | null>(null)
const pipeline = reactive<PipelineStatusResponse>({ run: null, events: [] })
const preflight = ref<PipelinePreflightResponse | null>(null)
const searchTimer = ref<number | null>(null)
const pollingTimer = ref<number | null>(null)
const initialSyncChecked = ref(false)
const preflighting = ref(false)
const materialTable = ref()
const selectedRows = ref<MaterialItem[]>([])

type RecentOperationStatus = 'started' | 'running' | 'succeeded' | 'failed' | 'opened'
type RecentOperation = {
  materialPk: string
  materialId: string
  filename: string
  action: string
  status: RecentOperationStatus
  runId?: string
  updatedAt: string
}

type BatchMode = 'clean-missing' | 'clean-rebuild' | 'raw-rebuild'

const RECENT_OPERATION_STORAGE_KEY = 'luceon.files.recentOperation'
const recentOperation = ref<RecentOperation | null>(loadRecentOperation())
const batchState = reactive({
  running: false,
  stopping: false,
  mode: '' as BatchMode | '',
  total: 0,
  done: 0,
  success: 0,
  failed: 0,
  currentName: '',
  logs: [] as string[]
})

const params = reactive({
  page: 1,
  page_size: 20,
  search: '',
  stage: ''
})

const stageMeta: Record<string, { label: string; type: 'primary' | 'success' | 'warning' | 'danger' | 'info' }> = {
  input: { label: 'PDF', type: 'info' },
  mineru_done: { label: 'MinerU', type: 'warning' },
  popo_done: { label: 'Popo', type: 'primary' },
  raw_done: { label: 'Raw', type: 'success' },
  clean_stale: { label: 'Clean 失效', type: 'warning' },
  clean_done: { label: 'Clean', type: 'success' },
  failed: { label: '失败', type: 'danger' }
}

const stageOptions = [
  { label: 'PDF', value: 'pdf' },
  { label: 'MinerU', value: 'mineru' },
  { label: 'Popo', value: 'popo' },
  { label: 'Raw', value: 'raw' },
  { label: 'Clean 失效', value: 'clean_stale' },
  { label: 'Clean', value: 'clean' },
  { label: '失败', value: 'failed' }
]

const hasRef = (ref: ObjectRef) => Boolean(ref?.bucket && ref?.object)

const artifactStages = [
  { key: 'pdf', label: 'PDF', done: (row: MaterialItem) => Boolean(row.input_object) },
  { key: 'mineru', label: 'MinerU', done: (row: MaterialItem) => row.mineru_available || hasRef(row.mineru_manifest) },
  { key: 'popo', label: 'Popo', done: (row: MaterialItem) => row.popo_available || hasRef(row.popo_manifest) },
  { key: 'raw', label: 'Raw', done: (row: MaterialItem) => row.raw_available || hasRef(row.raw_manifest) },
  { key: 'clean', label: 'Clean', done: (row: MaterialItem) => row.clean_available || hasRef(row.clean_manifest) }
]

const availabilityLine = computed(() => {
  const stages = summary.value?.availability || summary.value?.stages || {}
  const rows = [
    ['PDF', stages.input || 0],
    ['Popo', stages.popo_done || 0],
    ['Raw', stages.raw_done || 0],
    ['Clean', stages.clean_done || 0]
  ]
  return rows.map(([label, value]) => `${label} ${value}`).join(' · ')
})

const emptyText = computed(() => {
  if (params.search || params.stage) return '没有匹配的材料'
  return '暂无材料'
})

const uploadableFiles = computed(() => uploadFileList.value.map(item => item.raw).filter(Boolean) as File[])
const pipelineBusy = computed(() => pipeline.run?.status === 'queued' || pipeline.run?.status === 'running')
const pipelineSummary = computed(() => asRecord(pipeline.run?.summary))
const pipelinePreflight = computed(() => asRecord(pipelineSummary.value.preflight))
const activeMaterialId = computed(() => textValue(pipelineSummary.value.material_id || pipelinePreflight.value.material_id, ''))
const outlineArtifacts = computed(() => asRecord(pipelineSummary.value.outline_artifacts))
const outlineDecision = computed(() => asRecord(outlineArtifacts.value?.outline_decision))
const visualDecisions = computed(() => asRecord(outlineArtifacts.value?.visual_decisions))
const llmInfo = computed(() => asRecord(outlineDecision.value.llm))
const llmUsage = computed(() => asRecord(llmInfo.value.raw_usage || llmInfo.value.usage))
const canPublishPopoToRawDryRun = computed(() => {
  if (pipeline.run?.mode !== 'popo2raw' || pipeline.run.status !== 'succeeded') return false
  if (pipelineSummary.value.published === true) return false
  if (!pipelineSummary.value.body_final) return false
  return Boolean(pipelinePreflight.value.material_pk)
})
const pipelineProgress = computed(() => {
  if (!pipeline.run) return 0
  if (pipeline.run.status === 'succeeded') return 100
  if (pipeline.run.status === 'failed') return 100
  if (pipeline.run.total > 0) return Math.min(95, Math.round((pipeline.run.processed / pipeline.run.total) * 100))
  return pipeline.run.status === 'running' ? 35 : 10
})
const latestPipelineEvent = computed(() => pipeline.events[0] || null)
const taskTickerTone = computed(() => {
  if (pipeline.run?.status === 'failed') return 'danger'
  if (preflight.value && !preflight.value.ready) return 'warning'
  if (pipelineBusy.value) return 'active'
  if (pipeline.run?.status === 'succeeded' || preflight.value?.ready) return 'success'
  return 'idle'
})
const taskTickerText = computed(() => {
  if (pipeline.run) {
    const parts = [
      pipelineStatusText(pipeline.run.status),
      pipelineModeText(pipeline.run.mode),
      `${pipeline.run.processed}/${pipeline.run.total || '?'} · ${pipelineProgress.value}%`
    ]
    if (pipeline.run.error_message) parts.push(`错误：${pipeline.run.error_message}`)
    if (latestPipelineEvent.value) {
      parts.push(`${latestPipelineEvent.value.stage}：${latestPipelineEvent.value.message}`)
      const time = formatDateTime(latestPipelineEvent.value.created_at)
      if (time) parts.push(time)
    }
    if (canPublishPopoToRawDryRun.value) parts.push('Raw 预演待发布')
    return parts.filter(Boolean).join(' ｜ ')
  }
  if (preflight.value) {
    const result = preflight.value
    const base = [
      result.ready ? '预检通过' : '预检未通过',
      `GPU ${result.gpu_ok ? '正常' : '异常'}`,
      `分段接口 ${result.staged_api_ok ? '可用' : '不可用'}`,
      `待提交 ${result.selected_count}`,
      `Active Marker ${result.active_marker_count}`,
      formatDateTime(result.checked_at)
    ]
    if (!result.ready) base.push(preflightFailureText(result))
    return base.filter(Boolean).join(' ｜ ')
  }
  if (summary.value?.latest_run) {
    const run = summary.value.latest_run
    return [
      '任务空闲',
      `最近任务 ${pipelineStatusText(run.status)}`,
      pipelineModeText(run.mode),
      formatDateTime(run.created_at)
    ].filter(Boolean).join(' ｜ ')
  }
  return '任务空闲 ｜ 可以上传 PDF、同步资产或先执行解析预检'
})
const llmSummaryText = computed(() => {
  const provider = textValue(llmInfo.value.provider)
  const model = textValue(llmInfo.value.model)
  const tokens = numberValue(llmInfo.value.total_tokens || llmUsage.value.total_tokens)
  const cost = numberValue(llmInfo.value.estimated_cost_usd ?? llmInfo.value.estimated_cost)
  const tokenText = tokens ? `${formatCount(tokens)} tokens` : 'tokens待记录'
  const costText = cost ? `约 $${cost.toFixed(4)}` : '费用待记录'
  return `${provider}/${model} · ${tokenText} · ${costText}`
})
const visualSummaryText = computed(() => {
  if (visualDecisions.value.enabled === false) return '未启用'
  const validated = numberValue(visualDecisions.value.validated_count)
  const total = numberValue(visualDecisions.value.candidate_count)
  const errors = numberValue(visualDecisions.value.error_count)
  return `${formatCount(validated)}/${formatCount(total)} 已核实${errors ? `，${errors} 个错误` : ''}`
})
const selectedCleanMissingRows = computed(() => selectedRows.value.filter(row => hasRawAsset(row) && !hasCleanAsset(row)))
const selectedCleanRows = computed(() => selectedRows.value.filter(row => hasRawAsset(row)))
const selectedRawRows = computed(() => selectedRows.value.filter(row => hasPopoAsset(row) && hasRawAsset(row)))
const orderedMaterials = computed(() => {
  const active = activeMaterialId.value
  const recent = recentOperation.value
  return [...materials.value].sort((a, b) => rowPriority(a, active, recent) - rowPriority(b, active, recent))
})

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
}

function numberValue(value: unknown) {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

function textValue(value: unknown, fallback = '未记录') {
  return typeof value === 'string' && value.trim() ? value : fallback
}

function formatCount(value: unknown) {
  const count = numberValue(value)
  return count.toLocaleString('zh-CN')
}

function loadRecentOperation(): RecentOperation | null {
  try {
    const raw = window.localStorage.getItem(RECENT_OPERATION_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as RecentOperation
    return parsed?.materialPk || parsed?.materialId ? parsed : null
  } catch {
    return null
  }
}

function saveRecentOperation(operation: RecentOperation | null) {
  recentOperation.value = operation
  if (!operation) {
    window.localStorage.removeItem(RECENT_OPERATION_STORAGE_KEY)
    return
  }
  window.localStorage.setItem(RECENT_OPERATION_STORAGE_KEY, JSON.stringify(operation))
}

function rememberOperation(row: MaterialItem, action: string, status: RecentOperationStatus = 'started', run?: PipelineRun) {
  saveRecentOperation({
    materialPk: row.id,
    materialId: row.material_id || '',
    filename: row.filename || row.title || row.material_id || row.id,
    action,
    status,
    runId: run?.id,
    updatedAt: new Date().toISOString()
  })
}

function clearRecentOperation() {
  saveRecentOperation(null)
}

async function locateRecentOperation() {
  const recent = recentOperation.value
  if (!recent) return
  params.search = recent.materialId || recent.filename || recent.materialPk
  params.page = 1
  await fetchMaterials()
}

function operationStatusText(status: RecentOperationStatus) {
  const map: Record<RecentOperationStatus, string> = {
    opened: '已打开',
    started: '已启动',
    running: '执行中',
    succeeded: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

function isActiveTaskRow(row: MaterialItem) {
  return Boolean(activeMaterialId.value && row.material_id === activeMaterialId.value)
}

function isRecentOperationRow(row: MaterialItem) {
  const recent = recentOperation.value
  return Boolean(recent && (row.id === recent.materialPk || (!!recent.materialId && row.material_id === recent.materialId)))
}

function rowPriority(row: MaterialItem, active: string, recent: RecentOperation | null) {
  if (active && row.material_id === active) return 0
  if (recent && (row.id === recent.materialPk || (!!recent.materialId && row.material_id === recent.materialId))) return 1
  return 2
}

function materialRowClassName({ row }: { row: MaterialItem }) {
  if (isActiveTaskRow(row)) return 'is-active-task-row'
  if (isRecentOperationRow(row)) return 'is-recent-operation-row'
  return ''
}

function pipelineStatusText(status: string) {
  const map: Record<string, string> = {
    queued: '排队中',
    running: '运行中',
    succeeded: '已完成',
    failed: '失败',
    idle: '空闲'
  }
  return map[status] || status
}

function pipelineModeText(mode: string) {
  const map: Record<string, string> = {
    apply: 'PDF解析',
    dry_run: '预检',
    popo2raw: 'Popo→Raw',
    raw2clean: 'Raw→Clean'
  }
  return map[mode] || mode
}

function formatDateTime(value?: string | null) {
  return value ? formatDate(value) : ''
}

async function fetchMaterials() {
  loading.value = true
  try {
    const data = await materialsApi.getMaterials(params)
    materials.value = data.materials
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function fetchSummary() {
  summary.value = await materialsApi.getSummary()
}

async function fetchPipeline() {
  const data = await materialsApi.getPipelineStatus()
  pipeline.run = data.run
  pipeline.events = data.events
  syncRecentOperationFromPipeline()
  updatePipelinePolling()
}

function syncRecentOperationFromPipeline() {
  const recent = recentOperation.value
  const run = pipeline.run
  if (!recent || !run) return
  const runMaterialId = textValue(asRecord(run.summary).material_id || asRecord(asRecord(run.summary).preflight).material_id, '')
  const sameMaterial = runMaterialId && recent.materialId === runMaterialId
  const sameRun = recent.runId && String(recent.runId) === String(run.id)
  if (!sameMaterial && !sameRun) return
  const nextStatus: RecentOperationStatus =
    run.status === 'succeeded' ? 'succeeded' : run.status === 'failed' ? 'failed' : pipelineBusy.value ? 'running' : recent.status
  if (nextStatus !== recent.status || recent.runId !== run.id) {
    saveRecentOperation({ ...recent, status: nextStatus, runId: run.id, updatedAt: new Date().toISOString() })
  }
}

async function loadDashboard() {
  await Promise.all([fetchMaterials(), fetchSummary(), fetchPipeline()])
  if (!initialSyncChecked.value && total.value === 0) {
    initialSyncChecked.value = true
    await syncMaterials(false)
  }
}

async function syncMaterials(showMessage = true) {
  syncing.value = true
  try {
    const data = await materialsApi.sync()
    await Promise.all([fetchMaterials(), fetchSummary(), fetchPipeline()])
    if (showMessage) {
      ElMessage.success(`同步完成：${data.total} 份材料`)
    }
  } finally {
    syncing.value = false
  }
}

async function submitUpload() {
  if (!uploadableFiles.value.length) return
  uploading.value = true
  uploadProgress.value = 0
  try {
    const data = await materialsApi.upload(uploadableFiles.value, progress => {
      uploadProgress.value = progress
    })
    uploadDialogVisible.value = false
    uploadFileList.value = []
    await Promise.all([fetchMaterials(), fetchSummary()])
    ElMessage.success(`上传完成：${data.success} 个成功`)
  } finally {
    uploading.value = false
  }
}

function preflightFailureText(result: PipelinePreflightResponse) {
  const reasons: string[] = []
  if (!result.gpu_ok) reasons.push('GPU 服务未就绪')
  if (!result.staged_api_ok) reasons.push('分段 MinerU/Popo API 不可用')
  if (result.active_marker_count > 0) reasons.push(`存在 ${result.active_marker_count} 个 active marker`)
  if (result.selected_count <= 0) reasons.push('没有可提交 PDF')
  return reasons.join('；') || `状态：${result.status}`
}

function preflightSummaryRows(result: PipelinePreflightResponse) {
  return [
    `GPU服务：${result.gpu_ok ? '正常' : '异常'}`,
    `分段接口：${result.staged_api_ok ? '可用' : '不可用'}`,
    `待提交PDF：${result.selected_count} 个`,
    `Active Marker：${result.active_marker_count} 个`,
    `预检状态：${result.status}`
  ]
}

function preflightConfirmContent(result: PipelinePreflightResponse) {
  return h(
    'div',
    { class: 'preflight-confirm' },
    preflightSummaryRows(result).map(row => h('p', { style: 'margin: 0 0 6px;' }, row))
  )
}

function popoToRawFailureText(result: PopoToRawPreflightResponse) {
  const map: Record<string, string> = {
    missing_material_id: '缺少 material_id',
    missing_popo_asset: '缺少 Popo 产物',
    missing_mineru_asset: '缺少 MinerU 上游产物',
    missing_skill_script: '后端未挂载 Popo→Raw 技能脚本',
    missing_deepseek_api_key: '缺少 DeepSeek 模型密钥，无法执行 LLM 目录推理',
    missing_vision_api_key: '缺少视觉模型密钥，无法执行目录视觉核实',
    raw_already_exists: 'Raw 已存在，请使用“重建Raw”入口'
  }
  return result.blockers.map(item => map[item] || item).join('；') || '预检未通过'
}

function popoToRawDryRunConfirmContent(result: PopoToRawPreflightResponse) {
  return h('div', { class: 'preflight-confirm' }, [
    h('p', { style: 'margin: 0 0 6px;' }, `材料：${result.filename || result.material_id}`),
    h('p', { style: 'margin: 0 0 6px;' }, `Material ID：${result.material_id}`),
    h('p', { style: 'margin: 0 0 6px;' }, `Popo Run：${result.popo_run_id}`),
    h('p', { style: 'margin: 0 0 6px;' }, `MinerU Run：${result.mineru_run_id}`),
    h('p', { style: 'margin: 0 0 6px;' }, `写入：${result.raw_bucket}/${result.raw_prefix}`),
    h(
      'p',
      { style: 'margin: 10px 0 0; color: var(--el-color-danger);' },
      '确认后会重建 Raw 并写入 eduassets-raw；如果已有 Raw 会覆盖，下游 Clean 会标记为失效，等待重新 Clean。'
    )
  ])
}

function popoToRawDryRunPublishConfirmContent() {
  const materialId = textValue(pipelineSummary.value.material_id || pipelinePreflight.value.material_id)
  const filename = textValue(pipelinePreflight.value.filename)
  const rawBucket = textValue(pipelinePreflight.value.raw_bucket || pipelineSummary.value.raw_bucket)
  const rawPrefix = textValue(pipelinePreflight.value.raw_prefix || pipelineSummary.value.raw_prefix)
  const finalOutline = formatCount(outlineDecision.value.final_outline_count)
  const llmText = llmSummaryText.value
  const visualText = visualSummaryText.value
  return h('div', { class: 'preflight-confirm' }, [
    h('p', { style: 'margin: 0 0 6px;' }, `材料：${filename}`),
    h('p', { style: 'margin: 0 0 6px;' }, `Material ID：${materialId}`),
    h('p', { style: 'margin: 0 0 6px;' }, `目录节点：${finalOutline}`),
    h('p', { style: 'margin: 0 0 6px;' }, `LLM：${llmText}`),
    h('p', { style: 'margin: 0 0 6px;' }, `视觉核实：${visualText}`),
    h('p', { style: 'margin: 0 0 6px;' }, `写入：${rawBucket}/${rawPrefix}`),
    h(
      'p',
      { style: 'margin: 10px 0 0; color: var(--el-color-danger);' },
      '确认后会把这个 dry-run 产物发布为正式 Raw；如果已有 Raw 会覆盖，下游 Clean 会标记为失效，等待重新 Clean。'
    )
  ])
}

function rawToCleanFailureText(result: RawToCleanPreflightResponse) {
  const map: Record<string, string> = {
    missing_material_id: '缺少 material_id',
    missing_raw_asset: '缺少 Raw 产物',
    missing_skill_script: '后端未挂载 Raw→Clean 技能脚本',
    clean_already_exists: 'Clean 已存在，请使用“重建Clean”入口'
  }
  return result.blockers.map(item => map[item] || item).join('；') || '预检未通过'
}

function rawToCleanConfirmContent(result: RawToCleanPreflightResponse, force: boolean) {
  const rows = [
    h('p', { style: 'margin: 0 0 6px;' }, `材料：${result.filename || result.material_id}`),
    h('p', { style: 'margin: 0 0 6px;' }, `Material ID：${result.material_id}`),
    h('p', { style: 'margin: 0 0 6px;' }, `Raw Run：${result.raw_run_id}`),
    h('p', { style: 'margin: 0 0 6px;' }, `LLM 模式：${result.llm_mode || 'auto'}`),
    h('p', { style: 'margin: 0 0 6px;' }, `读取：${result.raw_bucket}/${result.raw_prefix}`),
    h('p', { style: 'margin: 0;' }, `写入：${result.clean_bucket}/${result.clean_prefix}`)
  ]
  rows.push(
    h(
      'p',
      { style: `margin: 10px 0 0; color: ${force ? 'var(--el-color-danger)' : 'var(--el-color-warning)'};` },
      force
        ? '将基于当前 Raw 重建并覆盖 Clean；Clean 会严格继承 Raw 目录，不会重建、改名或重排标题。'
        : 'Clean 会严格继承 Raw 目录，只清洗目录节点内的文本、图表和公式呈现。'
    )
  )
  return h('div', { class: 'preflight-confirm' }, rows)
}

async function runPreflightCheck(showMessage: boolean) {
  preflighting.value = true
  try {
    const result = await materialsApi.preflightPipeline(5)
    preflight.value = result
    if (showMessage) {
      if (result.ready) {
        ElMessage.success(`预检通过：待提交 ${result.selected_count} 个 PDF`)
      } else {
        ElMessage.warning(`预检未通过：${preflightFailureText(result)}`)
      }
    }
    return result
  } finally {
    preflighting.value = false
  }
}

async function runPreflight() {
  await runPreflightCheck(true)
}

async function startPipeline() {
  const result = await runPreflightCheck(false)
  if (!result.ready) {
    ElMessage.warning(`启动已拦截：${preflightFailureText(result)}`)
    return
  }
  await ElMessageBox.confirm(
    preflightConfirmContent(result),
    '启动GPU解析',
    { type: 'warning', confirmButtonText: '启动', cancelButtonText: '取消' }
  )
  await materialsApi.startPipeline(true, 5)
  await fetchPipeline()
  ElMessage.success('解析任务已启动')
}

function hasPopoAsset(row: MaterialItem) {
  return Boolean(row.popo_available || hasRef(row.popo_manifest))
}

function hasRawAsset(row: MaterialItem) {
  return Boolean(row.raw_available || hasRef(row.raw_manifest))
}

function hasCleanAsset(row: MaterialItem) {
  return Boolean(row.clean_available || hasRef(row.clean_manifest))
}

function canRunPopoToRaw(row: MaterialItem) {
  return !pipelineBusy.value && hasPopoAsset(row)
}

function canRunRawToClean(row: MaterialItem) {
  return !pipelineBusy.value && hasRawAsset(row)
}

function handleSelectionChange(rows: MaterialItem[]) {
  selectedRows.value = rows
}

function selectCurrentPage(kind: 'clean-missing' | 'raw-existing') {
  const table = materialTable.value
  if (!table) return
  table.clearSelection()
  const rows = orderedMaterials.value.filter(row => {
    if (kind === 'clean-missing') return hasRawAsset(row) && !hasCleanAsset(row)
    return hasPopoAsset(row) && hasRawAsset(row)
  })
  rows.forEach(row => table.toggleRowSelection(row, true))
  if (!rows.length) {
    ElMessage.info(kind === 'clean-missing' ? '本页没有待生成 Clean 的材料' : '本页没有已生成 Raw 的材料')
  }
}

function sleep(ms: number) {
  return new Promise(resolve => window.setTimeout(resolve, ms))
}

async function waitForPipelineIdle() {
  while (pipelineBusy.value) {
    await sleep(3000)
    await fetchPipeline()
  }
}

function batchModeText(mode: BatchMode) {
  const map: Record<BatchMode, string> = {
    'clean-missing': '批量生成Clean',
    'clean-rebuild': '批量重建Clean',
    'raw-rebuild': '批量重建Raw'
  }
  return map[mode]
}

function batchRows(mode: BatchMode) {
  if (mode === 'clean-missing') return selectedCleanMissingRows.value
  if (mode === 'clean-rebuild') return selectedCleanRows.value
  return selectedRawRows.value
}

async function startBatch(mode: BatchMode) {
  const rows = [...batchRows(mode)]
  if (!rows.length) {
    ElMessage.warning('没有符合条件的已选材料')
    return
  }
  await ElMessageBox.confirm(
    `${batchModeText(mode)}：共 ${rows.length} 条。任务会按顺序执行，每条完成后再启动下一条。`,
    batchModeText(mode),
    { type: mode === 'clean-missing' ? 'warning' : 'error', confirmButtonText: '开始执行', cancelButtonText: '取消' }
  )
  batchState.running = true
  batchState.stopping = false
  batchState.mode = mode
  batchState.total = rows.length
  batchState.done = 0
  batchState.success = 0
  batchState.failed = 0
  batchState.currentName = ''
  batchState.logs = []

  for (const row of rows) {
    if (batchState.stopping) break
    batchState.currentName = row.filename || row.material_id || row.id
    try {
      await waitForPipelineIdle()
      if (mode === 'raw-rebuild') {
        const result = await materialsApi.preflightPopoToRaw(row.id, true, true)
        if (!result.ready) throw new Error(popoToRawFailureText(result))
        const run = await materialsApi.startPopoToRaw(row.id, true, true)
        rememberOperation(row, batchModeText(mode), 'running', run)
      } else {
        const force = mode === 'clean-rebuild' || hasCleanAsset(row)
        const result = await materialsApi.preflightRawToClean(row.id, force)
        if (!result.ready) throw new Error(rawToCleanFailureText(result))
        const run = await materialsApi.startRawToClean(row.id, true, force)
        rememberOperation(row, batchModeText(mode), 'running', run)
      }
      await fetchPipeline()
      await waitForPipelineIdle()
      await Promise.all([fetchPipeline(), fetchMaterials(), fetchSummary()])
      if (pipeline.run?.status === 'failed') {
        throw new Error(pipeline.run.error_message || '任务失败')
      }
      batchState.success += 1
      rememberOperation(row, batchModeText(mode), 'succeeded', pipeline.run || undefined)
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      batchState.failed += 1
      batchState.logs.unshift(`${row.filename || row.material_id || row.id}：${message}`)
      rememberOperation(row, batchModeText(mode), 'failed')
    } finally {
      batchState.done += 1
    }
  }

  batchState.running = false
  batchState.currentName = ''
  await Promise.all([fetchMaterials(), fetchSummary(), fetchPipeline()])
  if (batchState.failed) {
    ElMessage.warning(`${batchModeText(mode)}结束：成功 ${batchState.success}，失败 ${batchState.failed}`)
  } else if (batchState.stopping) {
    ElMessage.info(`${batchModeText(mode)}已停止：已完成 ${batchState.done}/${batchState.total}`)
  } else {
    ElMessage.success(`${batchModeText(mode)}完成：${batchState.success} 条`)
  }
}

function stopBatchAfterCurrent() {
  batchState.stopping = true
  ElMessage.info('已设置为当前任务完成后停止')
}

async function startPopoToRawDryRun(row: MaterialItem) {
  const result = await materialsApi.preflightPopoToRaw(row.id, true, true)
  if (!result.ready) {
    ElMessage.warning(`Raw 重建已拦截：${popoToRawFailureText(result)}`)
    return
  }
  await ElMessageBox.confirm(
    popoToRawDryRunConfirmContent(result),
    hasRawAsset(row) ? '重建Raw' : '生成Raw',
    { type: 'warning', confirmButtonText: hasRawAsset(row) ? '确认重建' : '确认生成', cancelButtonText: '取消' }
  )
  const run = await materialsApi.startPopoToRaw(row.id, true, true)
  rememberOperation(row, hasRawAsset(row) ? '重建Raw' : '生成Raw', 'running', run)
  await fetchPipeline()
  ElMessage.success('Popo→Raw 任务已启动，成功后会写入 Raw 篮子')
}

async function publishPopoToRawDryRun() {
  if (!pipeline.run || !canPublishPopoToRawDryRun.value) return
  const materialPk = String(pipelinePreflight.value.material_pk || '')
  if (!materialPk) {
    ElMessage.warning('缺少材料 ID，无法发布此预演')
    return
  }
  await ElMessageBox.confirm(
    popoToRawDryRunPublishConfirmContent(),
    '发布Raw预演结果',
    { type: 'warning', confirmButtonText: '确认发布Raw', cancelButtonText: '取消' }
  )
  publishingRawDryRun.value = true
  try {
    await materialsApi.publishPopoToRawDryRun(materialPk, pipeline.run.id, true)
    await Promise.all([fetchPipeline(), fetchMaterials(), fetchSummary()])
    ElMessage.success('Raw 预演已发布，Clean 已标记为失效')
  } finally {
    publishingRawDryRun.value = false
  }
}

async function startRawToClean(row: MaterialItem, force: boolean) {
  const result = await materialsApi.preflightRawToClean(row.id, force)
  if (!result.ready) {
    ElMessage.warning(`Clean 生成已拦截：${rawToCleanFailureText(result)}`)
    return
  }
  await ElMessageBox.confirm(
    rawToCleanConfirmContent(result, force),
    force ? '重建Clean' : '生成Clean',
    { type: 'warning', confirmButtonText: force ? '重建并发布Clean' : '发布到Clean', cancelButtonText: '取消' }
  )
  const run = await materialsApi.startRawToClean(row.id, true, force)
  rememberOperation(row, force ? '重建Clean' : '生成Clean', 'running', run)
  await fetchPipeline()
  ElMessage.success(force ? 'Raw→Clean 重建任务已启动' : 'Raw→Clean 任务已启动')
}

function updatePipelinePolling() {
  if (pipelineBusy.value && !pollingTimer.value) {
    pollingTimer.value = window.setInterval(async () => {
      await fetchPipeline()
      await fetchSummary()
      if (!pipelineBusy.value) {
        await fetchMaterials()
      }
    }, 5000)
  }
  if (!pipelineBusy.value && pollingTimer.value) {
    window.clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

function openPdfReview(row: MaterialItem) {
  const route = pdfReviewRoute(row)
  if (!route) return
  rememberOperation(row, 'PDF审查', 'opened')
  router.push(route)
}

function openOutlineReview(row: MaterialItem) {
  const route = outlineReviewRoute(row)
  if (!route) return
  rememberOperation(row, '目录审查', 'opened')
  router.push(route)
}

function pdfReviewRoute(row: MaterialItem) {
  if (!row.review_asset_id) return null
  if (hasPopoAsset(row)) {
    return { path: '/review/pdf', query: { asset_id: row.review_asset_id } }
  }
  return null
}

function outlineReviewRoute(row: MaterialItem) {
  if (!row.review_asset_id) return null
  if (hasRawAsset(row) || hasCleanAsset(row) || row.raw_dry_run_available) {
    return { path: '/review/outline', query: { asset_id: row.review_asset_id } }
  }
  return null
}

function reviewUnavailableReason(row: MaterialItem, mode: 'pdf' | 'outline') {
  if (!row.review_asset_id) return '尚未建立审查索引，请先同步资产'
  if (mode === 'pdf') return 'PDF审查需完成 MinerU + MinerU-Popo'
  return '目录审查需先生成 Raw、Raw 预演或 Clean'
}

function previewPdf(row: MaterialItem) {
  window.open(materialsApi.getContentUrl(row.id), '_blank')
}

async function downloadPdf(row: MaterialItem) {
  const { url } = await materialsApi.getDownloadUrl(row.id)
  window.open(url, '_blank')
}

watch(
  () => [params.page, params.page_size, params.stage],
  () => fetchMaterials()
)

watch(
  () => params.search,
  () => {
    if (searchTimer.value) window.clearTimeout(searchTimer.value)
    searchTimer.value = window.setTimeout(() => {
      params.page = 1
      fetchMaterials()
    }, 300)
  }
)

onMounted(loadDashboard)

onBeforeUnmount(() => {
  if (searchTimer.value) window.clearTimeout(searchTimer.value)
  if (pollingTimer.value) window.clearInterval(pollingTimer.value)
})
</script>

<style scoped>
.materials-root {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
  overflow: hidden;
}

.page-header {
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 24px;
  font-weight: 700;
}

.page-meta {
  display: flex;
  gap: 14px;
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 13px;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.task-ticker,
.operation-focus,
.filter-bar,
.batch-bar,
.table-shell {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
}

.task-ticker {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 42px;
  padding: 0 12px;
  overflow: hidden;
}

.task-ticker.tone-active {
  border-color: var(--primary-light);
  background: var(--primary-faint);
}

.task-ticker.tone-success {
  border-color: color-mix(in srgb, var(--success-color) 28%, var(--border-light));
}

.task-ticker.tone-warning {
  border-color: color-mix(in srgb, var(--warning-color) 42%, var(--border-light));
}

.task-ticker.tone-danger {
  border-color: color-mix(in srgb, var(--danger-color) 48%, var(--border-light));
}

.task-ticker-label {
  flex-shrink: 0;
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 700;
}

.task-ticker-viewport {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
}

.task-ticker-track {
  display: inline-flex;
  align-items: center;
  gap: 56px;
  min-width: max-content;
  color: var(--text-secondary);
  font-size: 13px;
  animation: task-ticker-scroll 32s linear infinite;
}

.task-ticker:hover .task-ticker-track {
  animation-play-state: paused;
}

@keyframes task-ticker-scroll {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(calc(-50% - 28px));
  }
}

.operation-focus {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
}

.operation-focus.running,
.operation-focus.started {
  border-color: var(--primary-light);
  background: var(--primary-faint);
}

.operation-focus.succeeded {
  border-color: color-mix(in srgb, var(--success-color) 34%, var(--border-light));
}

.operation-focus.failed {
  border-color: color-mix(in srgb, var(--danger-color) 46%, var(--border-light));
}

.operation-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.operation-main strong {
  max-width: 420px;
  overflow: hidden;
  color: var(--text-primary);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.operation-label {
  flex-shrink: 0;
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 700;
}

.operation-id {
  max-width: 180px;
  overflow: hidden;
  color: var(--text-muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.operation-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.filter-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
}

.search-input {
  max-width: 420px;
}

.stage-select {
  width: 160px;
}

.quick-selects {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.batch-bar {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
}

.batch-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.batch-summary strong {
  color: var(--text-primary);
}

.batch-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.batch-log {
  width: 100%;
  overflow: hidden;
  color: var(--danger-color);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.table-shell :deep(.el-table) {
  flex: 1;
  min-height: 0;
}

.table-shell :deep(.el-table__inner-wrapper) {
  height: 100%;
}

.table-shell :deep(.el-table-fixed-column--left),
.table-shell :deep(.el-table-fixed-column--right) {
  background: var(--bg-primary);
}

.table-shell :deep(.is-active-task-row td) {
  background: var(--primary-faint) !important;
}

.table-shell :deep(.is-recent-operation-row td) {
  background: color-mix(in srgb, var(--warning-color) 8%, var(--bg-primary)) !important;
}

.material-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.file-name {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  color: var(--text-primary);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.object-path {
  color: var(--text-muted);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pipeline-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.pipeline-status {
  flex-shrink: 0;
}

.stage-chain {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  min-width: 0;
}

.stage-pill {
  flex-shrink: 0;
  padding: 3px 7px;
  border: 1px solid var(--border-light);
  border-radius: 6px;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.3;
}

.stage-pill.done {
  border-color: var(--primary-light);
  background: var(--primary-faint);
  color: var(--primary-color);
  font-weight: 600;
}

.row-actions {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8px;
  white-space: nowrap;
}

.row-actions :deep(.el-button) {
  margin-left: 0 !important;
  padding: 0;
}

.action-wrap {
  display: inline-flex;
}

.pagination-row {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
}

.upload-icon {
  color: var(--primary-color);
  font-size: 42px;
}

.upload-progress {
  margin-top: 14px;
}

@media (max-width: 900px) {
  .page-header,
  .operation-focus,
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input,
  .stage-select {
    width: 100%;
    max-width: none;
  }
}
</style>
