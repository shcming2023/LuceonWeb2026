<template>
  <div class="materials-root">
    <header class="page-header">
      <div class="page-heading">
        <h1 class="page-title">材料生产台</h1>
        <div class="page-meta">
          <span>共 {{ total }} 份材料</span>
          <span v-if="summary?.latest_run">最近任务：{{ pipelineStatusText(summary.latest_run.status) }}</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button :icon="Upload" type="primary" @click="uploadDialogVisible = true">上传 PDF</el-button>
        <el-tooltip content="扫描 MinIO 资产桶并刷新本地索引，不提交 GPU 任务" placement="bottom">
          <el-button :icon="Refresh" :loading="syncing" @click="syncMaterials(true)">同步资产</el-button>
        </el-tooltip>
        <el-dropdown trigger="click" @command="handleHeaderCommand">
          <el-button :icon="Cpu" :disabled="preflighting || pipelineBusy">
            GPU 解析
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="preflight" :icon="VideoPlay">解析预检</el-dropdown-item>
              <el-dropdown-item command="pipeline" :icon="Cpu">启动 GPU 解析</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <section class="summary-band" aria-label="阶段概览">
      <button
        v-for="tile in summaryTiles"
        :key="tile.key"
        type="button"
        class="summary-tile"
        :class="{ active: params.stage === tile.stage }"
        @click="applyStageFilter(tile.stage)"
      >
        <strong>{{ tile.value }}</strong>
        <span>{{ tile.label }}</span>
      </button>
    </section>

    <section :class="['workspace-status', `tone-${taskTickerTone}`]">
      <div class="workspace-state">
        <span class="state-icon">
          <el-icon><component :is="pipelineStateIcon" /></el-icon>
        </span>
        <div class="state-copy">
          <span class="state-label">{{ pipelineStateLabel }}</span>
          <strong>{{ pipelineHeadline }}</strong>
          <span>{{ pipelineDetail }}</span>
        </div>
      </div>
      <div v-if="recentOperation" :class="['recent-work', recentOperation.status]">
        <span>最近</span>
        <strong>{{ recentOperation.filename }}</strong>
        <em>{{ recentOperation.action }} · {{ operationStatusText(recentOperation.status) }}</em>
      </div>
      <div class="workspace-actions">
        <el-button v-if="recentOperation" size="small" @click="locateRecentOperation">定位</el-button>
        <el-button v-if="recentOperation" size="small" text @click="clearRecentOperation">清除</el-button>
      </div>
    </section>

    <section class="filter-bar">
      <el-input v-model="params.search" class="search-input" clearable placeholder="搜索书名、文件名、系列、ISBN、material_id">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="params.stage" clearable class="stage-select" placeholder="全部阶段">
        <el-option v-for="stage in stageOptions" :key="stage.value" :label="stage.label" :value="stage.value" />
      </el-select>
    </section>

    <section class="metadata-filter-bar" aria-label="教材元数据筛选">
      <el-select v-model="params.metadata_status" clearable placeholder="元数据状态">
        <el-option label="待提取" value="missing" />
        <el-option label="AI 已提取" value="ai_extracted" />
        <el-option label="人工已修改" value="manual" />
        <el-option label="提取失败" value="failed" />
      </el-select>
      <el-select v-model="params.subject" clearable filterable placeholder="学科">
        <el-option v-for="item in metadataOptions.subjects" :key="item" :label="item" :value="item" />
      </el-select>
      <el-select v-model="params.country" clearable filterable placeholder="出版国家">
        <el-option v-for="item in metadataOptions.countries" :key="item" :label="item" :value="item" />
      </el-select>
      <el-autocomplete
        v-model="params.series"
        clearable
        value-key="value"
        placeholder="系列名"
        :fetch-suggestions="suggestSeries"
        :trigger-on-focus="true"
      />
      <div class="year-filter">
        <el-input-number v-model="params.year_from" :min="0" :max="2200" controls-position="right" placeholder="起始年" />
        <span>至</span>
        <el-input-number v-model="params.year_to" :min="0" :max="2200" controls-position="right" placeholder="结束年" />
      </div>
    </section>

    <section v-if="selectedRows.length || batchState.running" class="batch-bar">
      <div class="batch-summary">
        <strong>{{ batchState.running ? '批量任务执行中' : `已选择 ${selectedRows.length} 条` }}</strong>
        <span v-if="!batchState.running">可批量补全元数据 {{ selectedRows.length }}</span>
        <span v-else>
          {{ batchState.done }}/{{ batchState.total }} · 成功 {{ batchState.success }} · 失败 {{ batchState.failed }} · {{ batchState.currentName }}
        </span>
      </div>
      <div class="batch-actions">
        <el-button v-if="batchState.running" size="small" @click="stopBatchAfterCurrent">停止后续</el-button>
        <el-button
          size="small"
          :loading="metadataBatchExtracting"
          :disabled="batchState.running || metadataBatchExtracting || !selectedRows.length"
          @click="extractSelectedMetadata"
        >
          AI 补全元数据
        </el-button>
        <el-button
          size="small"
          type="warning"
          :icon="Cpu"
          :loading="codexBatchStarting"
          :disabled="batchState.running || codexBatchStarting || !selectedCodexStartableRows.length"
          @click="startSelectedCodexJobs"
        >
          批量 Codex 重扫
        </el-button>
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
        :header-cell-style="{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)', fontWeight: 600 }"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="44" fixed="left" />
        <el-table-column prop="filename" label="材料" min-width="330">
          <template #default="{ row }">
            <div class="material-cell">
              <div class="material-title-row">
                <span class="file-name">{{ displayTitle(row) }}</span>
                <el-tag v-if="isActiveTaskRow(row)" size="small" type="primary" effect="plain">当前任务</el-tag>
                <el-tag v-else-if="isRecentOperationRow(row)" size="small" type="warning" effect="plain">最近</el-tag>
                <el-tag size="small" :type="metadataStatusType(row.book_metadata)" effect="plain">
                  {{ metadataStatusLabel(row.book_metadata) }}
                </el-tag>
              </div>
              <div v-if="metadataSubtitle(row)" class="book-subtitle">{{ metadataSubtitle(row) }}</div>
              <div class="material-meta">
                <span>{{ formatFileSize(row.size) }}</span>
                <span>{{ formatDateTime(row.last_synced_at || row.created_at) || '未同步' }}</span>
                <el-tooltip :content="row.input_object || row.material_id || row.id" placement="top">
                  <span>{{ compactMaterialId(row) }}</span>
                </el-tooltip>
              </div>
              <div v-if="metadataChips(row).length" class="metadata-chips">
                <span v-for="chip in metadataChips(row)" :key="chip">{{ chip }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="阶段" min-width="320">
          <template #default="{ row }">
            <div class="pipeline-cell">
              <div class="stage-summary">
                <span :class="['pipeline-status', `stage-${row.stage_status}`]">{{ rowStageMeta(row).label }}</span>
                <span class="stage-note">{{ rowStageNote(row) }}</span>
              </div>
              <div class="stage-track">
                <span
                  v-for="stage in artifactStages"
                  :key="stage.key"
                  :class="['stage-step', { done: stage.done(row), active: currentStageKey(row) === stage.key }]"
                >
                  <span class="stage-dot"></span>
                  <span class="stage-step-label">{{ stage.label }}</span>
                </span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="下一步" width="190" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button
                size="small"
                :icon="primaryAction(row).icon"
                :type="primaryAction(row).type"
                :loading="codexStartingIds.has(row.id)"
                :disabled="!primaryAction(row).enabled"
                @click="runPrimaryAction(row)"
              >
                {{ primaryAction(row).label }}
              </el-button>
              <el-dropdown trigger="click" @command="handleDropdownCommand(row, $event)">
                <el-button class="more-button" size="small" :icon="MoreFilled" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="metadata-edit" :icon="DocumentChecked">编辑元数据</el-dropdown-item>
                    <el-dropdown-item command="metadata-extract" :icon="Cpu">AI 提取元数据</el-dropdown-item>
                    <el-dropdown-item command="compare-review" :disabled="!hasLatexAsset(row)" :icon="View">PDF 比对</el-dropdown-item>
                    <el-dropdown-item command="start-codex" :disabled="!canStartCodex(row)" :icon="Cpu">
                      {{ hasLatexAsset(row) ? 'Codex 重扫' : '启动 Codex 精修' }}
                    </el-dropdown-item>
                    <el-dropdown-item divided command="preview-pdf" :disabled="!row.input_object" :icon="Document">打开 PDF</el-dropdown-item>
                    <el-dropdown-item command="download-pdf" :disabled="!row.input_object" :icon="Download">下载 PDF</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
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

    <el-drawer
      v-model="metadataDrawerVisible"
      class="metadata-drawer"
      size="520px"
      append-to-body
      :title="activeMetadataRow ? displayTitle(activeMetadataRow) : '教材元数据'"
    >
      <div v-if="activeMetadataRow" class="metadata-editor">
        <div class="metadata-editor-head">
          <div>
            <span>原始文件</span>
            <strong>{{ activeMetadataRow.filename }}</strong>
          </div>
          <el-tag :type="metadataStatusType(activeMetadataRow.book_metadata)" effect="plain">
            {{ metadataStatusLabel(activeMetadataRow.book_metadata) }}
          </el-tag>
        </div>

        <el-form label-position="top" class="metadata-form">
          <el-form-item label="原书名">
            <el-input v-model="metadataForm.original_title" placeholder="例如 Cambridge Primary Mathematics Learner's Book 1" />
          </el-form-item>
          <div class="metadata-form-grid">
            <el-form-item label="出版年份">
              <el-input-number v-model="metadataForm.publication_year" :min="0" :max="2200" controls-position="right" />
            </el-form-item>
            <el-form-item label="出版日期">
              <el-input v-model="metadataForm.publication_date" placeholder="原文日期或年份" />
            </el-form-item>
          </div>
          <div class="metadata-form-grid">
            <el-form-item label="版别">
              <el-input v-model="metadataForm.edition" placeholder="2nd Edition / 第二版" />
            </el-form-item>
            <el-form-item label="学科">
              <el-input v-model="metadataForm.subject" placeholder="Mathematics / English" />
            </el-form-item>
          </div>
          <div class="metadata-form-grid">
            <el-form-item label="出版国家">
              <el-input v-model="metadataForm.publication_country" placeholder="United Kingdom / 中国" />
            </el-form-item>
            <el-form-item label="系列名">
              <el-input v-model="metadataForm.series_name" placeholder="Cambridge Primary Mathematics" />
            </el-form-item>
          </div>
          <div class="metadata-form-grid">
            <el-form-item label="出版社">
              <el-input v-model="metadataForm.publisher" />
            </el-form-item>
            <el-form-item label="ISBN">
              <el-input v-model="metadataForm.isbn" />
            </el-form-item>
          </div>
          <div class="metadata-form-grid">
            <el-form-item label="语言">
              <el-input v-model="metadataForm.language" />
            </el-form-item>
            <el-form-item label="年级/阶段">
              <el-input v-model="metadataForm.grade_level" />
            </el-form-item>
          </div>
        </el-form>

        <section class="metadata-evidence">
          <header>
            <span>AI 证据</span>
            <small>{{ metadataSampleLabel }}</small>
          </header>
          <div v-if="metadataEvidenceRows.length" class="evidence-list">
            <article v-for="(item, index) in metadataEvidenceRows" :key="index">
              <span>{{ item.field }}</span>
              <p>{{ item.quote }}</p>
              <small>{{ item.source }}</small>
            </article>
          </div>
          <el-empty v-else description="暂无证据片段，可先执行 AI 提取" :image-size="76" />
        </section>

        <div v-if="metadataForm.extraction_error" class="metadata-error">
          {{ metadataForm.extraction_error }}
        </div>
      </div>

      <template #footer>
        <div class="metadata-drawer-footer">
          <el-checkbox v-model="metadataForceExtract">覆盖人工修改</el-checkbox>
          <div>
            <el-button :loading="metadataExtracting" @click="extractActiveMetadata">AI 提取</el-button>
            <el-button type="primary" :loading="metadataSaving" @click="saveActiveMetadata">保存修改</el-button>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onBeforeUnmount, onMounted, reactive, ref, watch, type Component } from 'vue'
import {
  ArrowDown,
  CircleCheckFilled,
  Cpu,
  Document,
  DocumentChecked,
  Download,
  MoreFilled,
  Refresh,
  Search,
  Timer,
  Upload,
  UploadFilled,
  VideoPlay,
  View,
  WarningFilled
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadUserFile } from 'element-plus'
import { useRouter } from 'vue-router'
import { materialsApi } from '@/api/materials'
import type {
  MaterialItem,
  MaterialBookMetadata,
  MaterialMetadataOptions,
  MaterialSummary,
  ObjectRef,
  PipelinePreflightResponse,
  PipelineRun,
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
const metadataOptions = ref<MaterialMetadataOptions>({
  subjects: [],
  countries: [],
  series: [],
  publishers: [],
  languages: [],
  editions: []
})
const metadataDrawerVisible = ref(false)
const metadataSaving = ref(false)
const metadataExtracting = ref(false)
const metadataBatchExtracting = ref(false)
const codexBatchStarting = ref(false)
const codexStartingIds = ref(new Set<string>())
const metadataForceExtract = ref(false)
const activeMetadataRow = ref<MaterialItem | null>(null)
const metadataForm = reactive<MaterialBookMetadata>({
  id: '',
  material_pk: '',
  original_title: '',
  publication_date: '',
  publication_year: null,
  edition: '',
  subject: '',
  publication_country: '',
  series_name: '',
  publisher: '',
  isbn: '',
  language: '',
  grade_level: '',
  status: 'missing',
  source: 'manual',
  confidence: null,
  manual_override: false,
  evidence: [],
  sample: {},
  extraction_model: '',
  extraction_error: '',
  extracted_at: null,
  created_at: null,
  updated_at: null
})

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

type HeaderCommand = 'preflight' | 'pipeline'
type RowCommand =
  | 'metadata-edit'
  | 'metadata-extract'
  | 'compare-review'
  | 'start-codex'
  | 'preview-pdf'
  | 'download-pdf'

type PrimaryRowAction = {
  label: string
  command: RowCommand | null
  enabled: boolean
  type: 'primary' | 'success' | 'warning' | 'info'
  icon: Component
}

type PipelineTarget = {
  material_id?: string
  input_object?: string
}

const RECENT_OPERATION_STORAGE_KEY = 'luceon.files.recentOperation'
const recentOperation = ref<RecentOperation | null>(loadRecentOperation())
const batchState = reactive({
  running: false,
  stopping: false,
  mode: '',
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
  stage: '',
  metadata_status: '',
  subject: '',
  country: '',
  series: '',
  year_from: null as number | null,
  year_to: null as number | null
})

const stageMeta: Record<string, { label: string; type: 'primary' | 'success' | 'warning' | 'danger' | 'info' }> = {
  input: { label: 'PDF', type: 'info' },
  mineru_done: { label: 'MinerU', type: 'warning' },
  popo_done: { label: 'Popo', type: 'primary' },
  latex_done: { label: 'LaTeX', type: 'success' },
  raw_done: { label: '旧节点', type: 'info' },
  clean_stale: { label: '旧节点', type: 'info' },
  clean_done: { label: '旧节点', type: 'info' },
  standard_done: { label: '旧节点', type: 'info' },
  failed: { label: '失败', type: 'danger' }
}

function rowStageMeta(row: MaterialItem) {
  if (row.pipeline_status === 'running' && row.stage_status === 'clean_stale') {
    return { label: '旧节点任务中', type: 'primary' as const }
  }
  if (row.pipeline_status === 'queued' && row.stage_status === 'clean_stale') {
    return { label: '旧节点排队中', type: 'primary' as const }
  }
  return stageMeta[row.stage_status] || { label: row.stage_status || '未知', type: 'info' as const }
}

function currentStageKey(row: MaterialItem) {
  const map: Record<string, string> = {
    input: 'pdf',
    mineru_done: 'mineru',
    popo_done: 'popo',
    latex_done: 'latex',
    raw_done: 'popo',
    clean_stale: 'popo',
    clean_done: 'popo',
    standard_done: 'popo',
    failed: 'pdf'
  }
  return map[row.stage_status] || 'pdf'
}

function rowStageNote(row: MaterialItem) {
  if (row.pipeline_status === 'running') return '任务运行中'
  if (row.pipeline_status === 'queued') return '任务排队中'
  if (hasLatexAsset(row)) return '可进行 PDF 比对'
  if (row.codex_job) return codexJobStatusText(row.codex_job.status)
  if (hasPopoAsset(row)) return '可启动 Codex 精修任务'
  if (hasMineruAsset(row)) return '等待 Popo 或继续 GPU 解析'
  if (row.input_object) return '等待上游解析'
  return '缺少源 PDF'
}

function codexJobStatusText(status: string) {
  const map: Record<string, string> = {
    queued: 'Codex 任务排队中',
    running: 'Codex 任务运行中',
    dry_run_succeeded: 'Codex dry-run 已完成',
    validating: 'Codex 输出验证中',
    published: 'Codex 输出已发布',
    failed: 'Codex 精修失败',
    cancelled: 'Codex 精修已取消'
  }
  return map[status] || `Codex ${status || '未知状态'}`
}

const stageOptions = [
  { label: 'PDF', value: 'pdf' },
  { label: 'MinerU', value: 'mineru' },
  { label: 'Popo', value: 'popo' },
  { label: 'LaTeX', value: 'latex' },
  { label: '失败', value: 'failed' }
]

const hasRef = (ref: ObjectRef) => Boolean(ref?.bucket && ref?.object)

const artifactStages = [
  { key: 'pdf', label: 'PDF', done: (row: MaterialItem) => Boolean(row.input_object) },
  { key: 'mineru', label: 'MinerU', done: (row: MaterialItem) => row.mineru_available || hasRef(row.mineru_manifest) },
  { key: 'popo', label: 'Popo', done: (row: MaterialItem) => row.popo_available || hasRef(row.popo_manifest) },
  { key: 'latex', label: 'LaTeX', done: (row: MaterialItem) => row.latex_available || hasRef(row.latex_manifest) }
]

const availabilityLine = computed(() => {
  const stages = summary.value?.availability || summary.value?.stages || {}
  const rows = [
    ['PDF', stages.input || 0],
    ['Popo', stages.popo_done || 0],
    ['LaTeX', stages.latex_done || 0]
  ]
  return rows.map(([label, value]) => `${label} ${value}`).join(' · ')
})
const summaryTiles = computed(() => {
  const stages = summary.value?.availability || summary.value?.stages || {}
  return [
    { key: 'all', label: '全部', value: total.value, stage: '' },
    { key: 'pdf', label: 'PDF', value: stages.input || 0, stage: 'pdf' },
    { key: 'popo', label: 'Popo', value: stages.popo_done || 0, stage: 'popo' },
    { key: 'latex', label: 'LaTeX', value: stages.latex_done || 0, stage: 'latex' }
  ]
})

const emptyText = computed(() => {
  if (
    params.search ||
    params.stage ||
    params.metadata_status ||
    params.subject ||
    params.country ||
    params.series ||
    params.year_from ||
    params.year_to
  ) return '没有匹配的材料'
  return '暂无材料'
})

const uploadableFiles = computed(() => uploadFileList.value.map(item => item.raw).filter(Boolean) as File[])
const pipelineBusy = computed(() => pipeline.run?.status === 'queued' || pipeline.run?.status === 'running')
const pipelineSummary = computed(() => asRecord(pipeline.run?.summary))
const pipelinePreflight = computed(() => asRecord(pipelineSummary.value.preflight))
const activeMaterialId = computed(() => textValue(pipelineSummary.value.material_id || pipelinePreflight.value.material_id, ''))
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
const pipelineStateIcon = computed(() => {
  if (pipeline.run?.status === 'failed' || (preflight.value && !preflight.value.ready)) return WarningFilled
  if (pipelineBusy.value) return Timer
  if (pipeline.run?.status === 'succeeded' || preflight.value?.ready) return CircleCheckFilled
  return Timer
})
const pipelineStateLabel = computed(() => {
  if (pipeline.run) return '当前任务'
  if (preflight.value) return '预检结果'
  return '任务状态'
})
const pipelineHeadline = computed(() => {
  if (pipeline.run) return `${pipelineModeText(pipeline.run.mode)} · ${pipelineStatusText(pipeline.run.status)}`
  if (preflight.value) return preflight.value.ready ? '解析预检通过' : '解析预检未通过'
  if (summary.value?.latest_run) {
    const run = summary.value.latest_run
    return `${pipelineModeText(run.mode)} · ${pipelineStatusText(run.status)}`
  }
  return '空闲'
})
const pipelineDetail = computed(() => {
  if (pipeline.run) {
    const progress = `${pipeline.run.processed}/${pipeline.run.total || '?'} · ${pipelineProgress.value}%`
    if (pipeline.run.error_message) return `${progress} · ${pipeline.run.error_message}`
    if (latestPipelineEvent.value) return `${progress} · ${latestPipelineEvent.value.message}`
    return progress
  }
  if (preflight.value) {
    return preflight.value.ready ? `待提交 ${preflight.value.selected_count} 个 PDF` : preflightFailureText(preflight.value)
  }
  if (summary.value?.latest_run) return formatDateTime(summary.value.latest_run.created_at)
  return availabilityLine.value || '等待材料'
})
const metadataEvidenceRows = computed(() => {
  return (metadataForm.evidence || []).slice(0, 8).map(item => ({
    field: String(item.field || '证据'),
    quote: String(item.quote || ''),
    source: String(item.source || 'sample')
  })).filter(item => item.quote)
})
const metadataSampleLabel = computed(() => {
  const chars = typeof metadataForm.sample?.sampled_chars === 'number' ? metadataForm.sample.sampled_chars : 0
  const strategy = typeof metadataForm.sample?.strategy === 'string' ? metadataForm.sample.strategy : ''
  if (!chars && !strategy) return '文件名 + 前部文本 + 关键词窗口'
  return `${chars ? `${chars.toLocaleString('zh-CN')} 字符样本` : '文本样本'}`
})
const orderedMaterials = computed(() => {
  const active = activeMaterialId.value
  const recent = recentOperation.value
  return [...materials.value].sort((a, b) => rowPriority(a, active, recent) - rowPriority(b, active, recent))
})
const selectedCodexStartableRows = computed(() => selectedRows.value.filter(canStartCodex))

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
}

function textValue(value: unknown, fallback = '未记录') {
  return typeof value === 'string' && value.trim() ? value : fallback
}

type FilterSuggestion = { value: string }

function suggestSeries(query: string, cb: (items: FilterSuggestion[]) => void) {
  const keyword = query.trim().toLowerCase()
  const options = metadataOptions.value.series || []
  const matched = options
    .filter(item => !keyword || item.toLowerCase().includes(keyword))
    .slice(0, 12)
    .map(value => ({ value }))
  if (keyword && !matched.some(item => item.value.toLowerCase() === keyword)) {
    matched.unshift({ value: query.trim() })
  }
  cb(matched)
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

function pipelineTargetForRow(row: MaterialItem | null | undefined): PipelineTarget {
  if (!row) return {}
  return {
    material_id: row.material_id || undefined,
    input_object: row.input_object || undefined
  }
}

function currentPipelineTarget(): PipelineTarget {
  if (selectedRows.value.length === 1) {
    return pipelineTargetForRow(selectedRows.value[0])
  }
  const recent = recentOperation.value
  if (recent) {
    const recentRow = materials.value.find(row => row.id === recent.materialPk || (!!recent.materialId && row.material_id === recent.materialId))
    if (recentRow && (params.search === recent.materialId || params.search === recent.filename || params.search === recent.materialPk)) {
      return pipelineTargetForRow(recentRow)
    }
  }
  if (params.search && orderedMaterials.value.length === 1) {
    return pipelineTargetForRow(orderedMaterials.value[0])
  }
  return {}
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
  if (mode.startsWith('popo2latex')) return '旧 LaTeX 任务'
  const map: Record<string, string> = {
    apply: 'PDF解析',
    dry_run: '预检',
    popo2raw: '旧节点',
    raw2clean: '旧节点',
    clean2standard: '旧节点'
  }
  return map[mode] || mode
}

function formatDateTime(value?: string | null) {
  return value ? formatDate(value) : ''
}

function applyStageFilter(stage: string) {
  params.stage = stage
  params.page = 1
}

function compactMaterialId(row: MaterialItem) {
  const id = row.material_id || row.id || ''
  if (!id) return '未绑定 ID'
  return id.length > 18 ? `${id.slice(0, 10)}...${id.slice(-4)}` : id
}

function displayTitle(row: MaterialItem) {
  return row.book_metadata?.original_title || row.title || row.filename
}

function metadataSubtitle(row: MaterialItem) {
  const title = row.book_metadata?.original_title || ''
  return title && title !== row.filename ? row.filename : ''
}

function metadataChips(row: MaterialItem) {
  const meta = row.book_metadata
  if (!meta) return []
  return [
    meta.subject,
    meta.publication_year ? String(meta.publication_year) : '',
    meta.edition,
    meta.publication_country,
    meta.series_name
  ].filter(Boolean).slice(0, 4)
}

function metadataStatusLabel(meta?: MaterialBookMetadata | null) {
  if (!meta || meta.status === 'missing') return '待提取'
  if (meta.status === 'ai_extracted') return meta.confidence ? `AI ${Math.round(meta.confidence * 100)}%` : 'AI 已提取'
  if (meta.status === 'manual') return '人工已改'
  if (meta.status === 'failed') return '提取失败'
  return meta.status
}

function metadataStatusType(meta?: MaterialBookMetadata | null) {
  if (!meta || meta.status === 'missing') return 'info'
  if (meta.status === 'ai_extracted') return 'success'
  if (meta.status === 'manual') return 'warning'
  if (meta.status === 'failed') return 'danger'
  return 'info'
}

function applyMetadataToRow(row: MaterialItem, metadata: MaterialBookMetadata) {
  row.book_metadata = metadata
  if (activeMetadataRow.value?.id === row.id) {
    activeMetadataRow.value = row
  }
}

function resetMetadataForm(metadata?: MaterialBookMetadata | null) {
  const source = metadata || {
    id: '',
    material_pk: '',
    original_title: '',
    publication_date: '',
    publication_year: null,
    edition: '',
    subject: '',
    publication_country: '',
    series_name: '',
    publisher: '',
    isbn: '',
    language: '',
    grade_level: '',
    status: 'missing',
    source: 'manual',
    confidence: null,
    manual_override: false,
    evidence: [],
    sample: {},
    extraction_model: '',
    extraction_error: '',
    extracted_at: null,
    created_at: null,
    updated_at: null
  }
  Object.assign(metadataForm, JSON.parse(JSON.stringify(source)))
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

async function fetchMetadataOptions() {
  metadataOptions.value = await materialsApi.getMetadataOptions()
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
  await Promise.all([fetchMaterials(), fetchSummary(), fetchPipeline(), fetchMetadataOptions()])
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
    const uploadedMaterial = data.files.find(item => item.status === 'success' && item.material)?.material
    if (uploadedMaterial) {
      params.page = 1
      params.stage = ''
      params.search = uploadedMaterial.material_id || uploadedMaterial.filename || uploadedMaterial.id
      rememberOperation(uploadedMaterial, '上传PDF', 'succeeded')
    }
    await Promise.all([fetchMaterials(), fetchSummary()])
    ElMessage.success(uploadedMaterial ? `上传完成：${data.success} 个成功，已定位到新 PDF` : `上传完成：${data.success} 个成功`)
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

async function runPreflightCheck(showMessage: boolean) {
  preflighting.value = true
  try {
    const target = currentPipelineTarget()
    const result = await materialsApi.preflightPipeline(5, target)
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

async function handleHeaderCommand(command: HeaderCommand) {
  if (command === 'preflight') {
    await runPreflight()
    return
  }
  await startPipeline()
}

async function startPipeline() {
  const target = currentPipelineTarget()
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
  await materialsApi.startPipeline(true, 5, target)
  await fetchPipeline()
  ElMessage.success('解析任务已启动')
}

function hasPopoAsset(row: MaterialItem) {
  return Boolean(row.popo_available || hasRef(row.popo_manifest))
}

function hasMineruAsset(row: MaterialItem) {
  return Boolean(row.mineru_available || hasRef(row.mineru_manifest))
}

function hasLatexAsset(row: MaterialItem) {
  return Boolean(row.latex_available || hasRef(row.latex_manifest))
}

function canStartCodex(row: MaterialItem) {
  return hasPopoAsset(row) && !codexJobActive(row)
}

function codexJobActive(row: MaterialItem) {
  return ['queued', 'running', 'dry_run_succeeded', 'validating'].includes(row.codex_job?.status || '')
}

function primaryAction(row: MaterialItem): PrimaryRowAction {
  if (hasLatexAsset(row)) {
    return {
      label: 'PDF 比对',
      command: 'compare-review',
      enabled: true,
      type: 'primary',
      icon: View
    }
  }
  if (hasPopoAsset(row)) {
    const codexStatus = row.codex_job?.status || ''
    if (!codexStatus || codexStatus === 'failed' || codexStatus === 'cancelled') {
      return {
        label: '启动 Codex 精修',
        command: 'start-codex',
        enabled: true,
        type: 'warning',
        icon: Cpu
      }
    }
    return {
      label: codexJobStatusText(codexStatus),
      command: null,
      enabled: false,
      type: 'info',
      icon: Timer
    }
  }
  if (row.input_object) {
    return {
      label: '打开 PDF',
      command: 'preview-pdf',
      enabled: true,
      type: 'info',
      icon: Document
    }
  }
  return {
    label: '等待同步',
    command: null,
    enabled: false,
    type: 'info',
    icon: Timer
  }
}

function runPrimaryAction(row: MaterialItem) {
  const action = primaryAction(row)
  if (!action.enabled || !action.command) return
  handleRowCommand(row, action.command)
}

function handleSelectionChange(rows: MaterialItem[]) {
  selectedRows.value = rows
}

async function openMetadataDrawer(row: MaterialItem) {
  activeMetadataRow.value = row
  metadataDrawerVisible.value = true
  metadataForceExtract.value = false
  resetMetadataForm(row.book_metadata)
  try {
    const metadata = await materialsApi.getMetadata(row.id)
    applyMetadataToRow(row, metadata)
    resetMetadataForm(metadata)
  } catch (error) {
    ElMessage.warning(error instanceof Error ? error.message : '元数据加载失败')
  }
}

async function extractRowMetadata(row: MaterialItem, force = false, openAfter = false) {
  if (openAfter) {
    activeMetadataRow.value = row
    metadataDrawerVisible.value = true
    resetMetadataForm(row.book_metadata)
  }
  metadataExtracting.value = true
  try {
    const metadata = await materialsApi.extractMetadata(row.id, force)
    applyMetadataToRow(row, metadata)
    if (activeMetadataRow.value?.id === row.id) resetMetadataForm(metadata)
    await fetchMetadataOptions()
    ElMessage.success('元数据已提取')
  } catch (error: any) {
    const message = error?.response?.data?.detail || error?.message || '元数据提取失败'
    ElMessage.warning(message)
    if (openAfter) {
      try {
        const metadata = await materialsApi.getMetadata(row.id)
        applyMetadataToRow(row, metadata)
        resetMetadataForm(metadata)
      } catch {
        // keep the drawer open with existing local values
      }
    }
  } finally {
    metadataExtracting.value = false
  }
}

async function extractActiveMetadata() {
  if (!activeMetadataRow.value) return
  await extractRowMetadata(activeMetadataRow.value, metadataForceExtract.value, false)
}

async function saveActiveMetadata() {
  const row = activeMetadataRow.value
  if (!row) return
  metadataSaving.value = true
  try {
    const metadata = await materialsApi.updateMetadata(row.id, {
      original_title: metadataForm.original_title,
      publication_date: metadataForm.publication_date,
      publication_year: metadataForm.publication_year,
      edition: metadataForm.edition,
      subject: metadataForm.subject,
      publication_country: metadataForm.publication_country,
      series_name: metadataForm.series_name,
      publisher: metadataForm.publisher,
      isbn: metadataForm.isbn,
      language: metadataForm.language,
      grade_level: metadataForm.grade_level,
      confidence: metadataForm.confidence,
      evidence: metadataForm.evidence
    })
    applyMetadataToRow(row, metadata)
    resetMetadataForm(metadata)
    await fetchMetadataOptions()
    ElMessage.success('元数据已保存')
  } finally {
    metadataSaving.value = false
  }
}

async function extractSelectedMetadata() {
  const rows = [...selectedRows.value]
  if (!rows.length) return
  try {
    await ElMessageBox.confirm(
      `将对已选 ${rows.length} 份材料按顺序进行 AI 元数据提取。模型只会接收文件名、前部文本样本和关键词窗口。`,
      'AI 补全元数据',
      { type: 'warning', confirmButtonText: '开始提取', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  metadataBatchExtracting.value = true
  let success = 0
  let failed = 0
  try {
    for (const row of rows) {
      try {
        const metadata = await materialsApi.extractMetadata(row.id, false)
        applyMetadataToRow(row, metadata)
        success += 1
      } catch {
        failed += 1
      }
    }
  } finally {
    metadataBatchExtracting.value = false
  }
  await fetchMetadataOptions()
  if (failed) {
    ElMessage.warning(`元数据提取结束：成功 ${success}，失败 ${failed}`)
  } else {
    ElMessage.success(`元数据提取完成：${success} 份`)
  }
}

function stopBatchAfterCurrent() {
  batchState.stopping = true
  ElMessage.info('已设置为当前任务完成后停止')
}

function codexSkillVersion() {
  return `manual-${new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)}`
}

function codexModeForRow(row: MaterialItem) {
  return hasLatexAsset(row) ? 'refresh_legacy' : 'new_pdf'
}

function codexRunReasonForRow(row: MaterialItem, batch = false) {
  if (hasLatexAsset(row)) return batch ? 'batch_refresh_legacy' : 'manual_refresh_legacy'
  return batch ? 'batch_new_pdf' : 'manual_new_pdf'
}

async function startCodexJob(row: MaterialItem, batch = false) {
  if (!canStartCodex(row)) {
    ElMessage.warning('该材料暂不能启动 Codex 任务')
    return null
  }
  const next = new Set(codexStartingIds.value)
  next.add(row.id)
  codexStartingIds.value = next
  try {
    const job = await materialsApi.createCodexJob(row.id, {
      mode: codexModeForRow(row),
      skill_version: codexSkillVersion(),
      run_reason: codexRunReasonForRow(row, batch),
      force: true,
      payload: {
        source: batch ? 'files_batch_action' : 'files_row_action',
        previous_job_id: row.codex_job?.id || '',
        had_legacy_output: hasLatexAsset(row)
      }
    })
    row.codex_job = job
    recentOperation.value = {
      materialPk: row.id,
      materialId: row.material_id,
      filename: displayTitle(row),
      action: hasLatexAsset(row) ? 'Codex 重扫已入队' : 'Codex 精修已入队',
      status: 'started',
      runId: job.id,
      updatedAt: new Date().toISOString()
    }
    if (!batch) ElMessage.success(`Codex 任务已入队：#${job.id}`)
    return job
  } catch (error: any) {
    if (!batch) {
      const message = error?.response?.data?.detail || error?.message || '创建 Codex 任务失败'
      ElMessage.warning(message)
    }
    return null
  } finally {
    const current = new Set(codexStartingIds.value)
    current.delete(row.id)
    codexStartingIds.value = current
  }
}

async function startSelectedCodexJobs() {
  const rows = selectedCodexStartableRows.value
  if (!rows.length) return
  try {
    await ElMessageBox.confirm(
      `将为已选 ${rows.length} 份材料创建新的 Codex 异步任务。任务只入队，不会在浏览器请求中直接执行长时间精修。`,
      '批量 Codex 重扫',
      { type: 'warning', confirmButtonText: '创建任务', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  codexBatchStarting.value = true
  let success = 0
  let failed = 0
  try {
    for (const row of rows) {
      const job = await startCodexJob(row, true)
      if (job) success += 1
      else failed += 1
    }
  } finally {
    codexBatchStarting.value = false
  }
  await fetchMaterials()
  if (failed) ElMessage.warning(`Codex 任务创建结束：成功 ${success}，失败 ${failed}`)
  else ElMessage.success(`已创建 ${success} 个 Codex 任务`)
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

function handleRowCommand(row: MaterialItem, command: RowCommand) {
  if (command === 'metadata-edit') return openMetadataDrawer(row)
  if (command === 'metadata-extract') return extractRowMetadata(row, false, true)
  if (command === 'compare-review') return openCompareReview(row)
  if (command === 'start-codex') return startCodexJob(row)
  if (command === 'preview-pdf') return previewPdf(row)
  if (command === 'download-pdf') return downloadPdf(row)
}

function handleDropdownCommand(row: MaterialItem, command: string | number | object) {
  if (typeof command !== 'string') return
  handleRowCommand(row, command as RowCommand)
}

async function openCompareReview(row: MaterialItem) {
  if (!hasLatexAsset(row)) {
    ElMessage.warning('该材料还没有可比对的 ElegantBook 输出')
    return
  }
  let assetId = row.review_asset_id
  if (!assetId) {
    try {
      const target = await materialsApi.getReviewTarget(row.id)
      assetId = target.review_asset_id
    } catch {
      ElMessage.warning('尚未建立审查索引，请先同步资产')
      return
    }
  }
  rememberOperation(row, 'PDF比对', 'opened')
  router.push({ path: '/review/compare', query: { asset_id: assetId } })
}

function previewPdf(row: MaterialItem) {
  window.open(materialsApi.getContentUrl(row.id), '_blank')
}

async function downloadPdf(row: MaterialItem) {
  const { url } = await materialsApi.getDownloadUrl(row.id)
  window.open(url, '_blank')
}

watch(
  () => [
    params.page,
    params.page_size,
    params.stage,
    params.metadata_status,
    params.subject,
    params.country,
    params.series,
    params.year_from,
    params.year_to
  ],
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
  display: block;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.sort-hint {
  margin-left: auto;
  color: var(--text-muted);
  font-size: 12px;
  white-space: nowrap;
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
  background: color-mix(in srgb, var(--warning-color) 4%, var(--bg-primary)) !important;
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

.stage-pill.score {
  border-color: var(--success-color);
  color: var(--success-color);
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

  .sort-hint {
    margin-left: 0;
    white-space: normal;
  }
}

.materials-root {
  gap: 12px;
}

.page-header {
  align-items: center;
}

.page-heading {
  min-width: 0;
}

.page-title {
  font-size: 26px;
  line-height: 1.15;
  letter-spacing: 0;
}

.page-meta {
  gap: 10px;
  color: var(--text-secondary);
}

.header-actions :deep(.el-button) {
  height: 38px;
  padding: 0 14px !important;
}

.summary-band {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(6, minmax(92px, 1fr));
  overflow: hidden;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--bg-primary);
}

.summary-tile {
  min-width: 0;
  padding: 12px 14px;
  border: 0;
  border-right: 1px solid var(--border-light);
  background: transparent;
  color: var(--text-secondary);
  text-align: left;
  cursor: pointer;
}

.summary-tile:last-child {
  border-right: 0;
}

.summary-tile:hover,
.summary-tile.active {
  background: color-mix(in srgb, var(--primary-color) 5%, var(--bg-primary));
}

.summary-tile.active {
  box-shadow: inset 0 -2px 0 var(--primary-color);
}

.summary-tile strong {
  display: block;
  color: var(--text-primary);
  font-size: 20px;
  line-height: 1.1;
}

.summary-tile span {
  display: block;
  margin-top: 4px;
  font-size: 12px;
}

.workspace-status {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(220px, 0.75fr) auto;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  border: 1px solid var(--border-light);
  border-left-width: 3px;
  border-radius: 8px;
  background: var(--bg-primary);
}

.workspace-status.tone-idle {
  border-left-color: var(--border-color);
}

.workspace-status.tone-active {
  border-left-color: var(--primary-color);
}

.workspace-status.tone-success {
  border-left-color: var(--success-color);
}

.workspace-status.tone-warning {
  border-left-color: var(--warning-color);
}

.workspace-status.tone-danger {
  border-left-color: var(--danger-color);
}

.workspace-state {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 10px;
}

.state-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.tone-active .state-icon {
  background: var(--primary-faint);
  color: var(--primary-color);
}

.tone-success .state-icon {
  background: color-mix(in srgb, var(--success-color) 12%, var(--bg-primary));
  color: var(--success-dark);
}

.tone-warning .state-icon {
  background: color-mix(in srgb, var(--warning-color) 14%, var(--bg-primary));
  color: var(--warning-dark);
}

.tone-danger .state-icon {
  background: color-mix(in srgb, var(--danger-color) 12%, var(--bg-primary));
  color: var(--danger-dark);
}

.state-copy {
  display: grid;
  min-width: 0;
  gap: 2px;
}

.state-label {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
}

.state-copy strong {
  overflow: hidden;
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.state-copy span:last-child {
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-work {
  display: grid;
  min-width: 0;
  gap: 2px;
  padding-left: 14px;
  border-left: 1px solid var(--border-light);
}

.recent-work span {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
}

.recent-work strong {
  overflow: hidden;
  color: var(--text-primary);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-work em {
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 12px;
  font-style: normal;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workspace-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.filter-bar {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) 170px auto;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
}

.metadata-filter-bar {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(120px, 1fr)) minmax(230px, auto);
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: color-mix(in srgb, var(--bg-primary) 86%, var(--bg-secondary));
}

.year-filter {
  display: grid;
  grid-template-columns: minmax(92px, 1fr) auto minmax(92px, 1fr);
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 12px;
}

.year-filter :deep(.el-input-number) {
  width: 100%;
}

.search-input {
  max-width: none;
}

.quick-selects {
  justify-content: flex-end;
}

.batch-bar {
  border-radius: 8px;
}

.table-shell {
  border-radius: 8px;
  background: var(--bg-primary);
}

.table-shell :deep(.el-table) {
  --el-table-row-hover-bg-color: color-mix(in srgb, var(--primary-color) 4%, var(--bg-primary));
}

.table-shell :deep(.el-table__cell) {
  padding: 12px 0;
}

.table-shell :deep(.el-table__header .cell) {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

.table-shell :deep(.el-table-fixed-column--right) {
  box-shadow: -12px 0 18px -18px rgb(29 29 31 / 0.32);
}

.material-cell {
  gap: 7px;
}

.material-title-row {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 8px;
}

.file-name {
  display: block;
  min-width: 0;
  font-size: 14px;
  line-height: 1.35;
}

.material-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.25;
}

.material-meta span {
  min-width: 0;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-subtitle {
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metadata-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.metadata-chips span {
  max-width: 180px;
  overflow: hidden;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 1.45;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pipeline-cell {
  flex-direction: column;
  align-items: stretch;
  gap: 9px;
}

.stage-summary {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 8px;
}

.pipeline-status {
  flex: 0 0 auto;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
  line-height: 1.4;
}

.pipeline-status.stage-raw_done,
.pipeline-status.stage-clean_done,
.pipeline-status.stage-standard_done {
  background: color-mix(in srgb, var(--success-color) 12%, var(--bg-primary));
  color: var(--success-dark);
}

.pipeline-status.stage-popo_done,
.pipeline-status.stage-mineru_done {
  background: color-mix(in srgb, var(--primary-color) 8%, var(--bg-primary));
  color: var(--primary-dark);
}

.pipeline-status.stage-clean_stale {
  background: color-mix(in srgb, var(--warning-color) 14%, var(--bg-primary));
  color: var(--warning-dark);
}

.pipeline-status.stage-failed {
  background: color-mix(in srgb, var(--danger-color) 12%, var(--bg-primary));
  color: var(--danger-dark);
}

.stage-note {
  min-width: 0;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stage-track {
  display: grid;
  grid-template-columns: repeat(6, minmax(36px, 1fr));
  align-items: start;
  gap: 0;
  min-width: 0;
}

.stage-step {
  position: relative;
  display: grid;
  justify-items: center;
  gap: 4px;
  min-width: 0;
  color: var(--text-muted);
  font-size: 11px;
}

.stage-step::before {
  content: '';
  position: absolute;
  top: 5px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--border-light);
}

.stage-step:first-child::before {
  left: 50%;
}

.stage-step:last-child::before {
  right: 50%;
}

.stage-step.done::before {
  background: color-mix(in srgb, var(--success-color) 34%, var(--border-light));
}

.stage-dot {
  position: relative;
  z-index: 1;
  width: 11px;
  height: 11px;
  border: 2px solid var(--border-color);
  border-radius: 50%;
  background: var(--bg-primary);
}

.stage-step.done .stage-dot {
  border-color: var(--success-color);
  background: var(--success-color);
}

.stage-step.active .stage-dot {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary-color) 14%, transparent);
}

.stage-step-label {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quality-score {
  align-self: center;
  justify-self: end;
  padding: 2px 6px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--success-color) 12%, var(--bg-primary));
  color: var(--success-dark);
  font-size: 11px;
  font-weight: 700;
}

.row-actions {
  justify-content: flex-start;
  gap: 6px;
}

.row-actions :deep(.el-button) {
  margin-left: 0 !important;
  padding: 7px 10px !important;
  border: 1px solid var(--border-light) !important;
  box-shadow: none !important;
}

.row-actions :deep(.el-button--primary) {
  border-color: transparent !important;
}

.more-button {
  width: 32px;
  padding: 7px 0 !important;
}

.metadata-drawer :deep(.el-drawer__body) {
  padding: 0 20px 16px;
}

.metadata-drawer :deep(.el-drawer__footer) {
  padding: 12px 20px;
  border-top: 1px solid var(--border-light);
}

.metadata-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metadata-editor-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--bg-secondary);
}

.metadata-editor-head div {
  min-width: 0;
}

.metadata-editor-head span {
  display: block;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
}

.metadata-editor-head strong {
  display: block;
  overflow: hidden;
  margin-top: 3px;
  color: var(--text-primary);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metadata-form {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metadata-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.metadata-form :deep(.el-input-number) {
  width: 100%;
}

.metadata-evidence {
  display: grid;
  gap: 10px;
  padding-top: 2px;
}

.metadata-evidence header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.metadata-evidence header span {
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 700;
}

.metadata-evidence header small {
  overflow: hidden;
  color: var(--text-muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.evidence-list {
  display: grid;
  gap: 8px;
}

.evidence-list article {
  padding: 10px 11px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background: var(--bg-primary);
}

.evidence-list article span {
  color: var(--primary-color);
  font-size: 12px;
  font-weight: 700;
}

.evidence-list article p {
  margin: 5px 0 4px;
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.45;
}

.evidence-list article small {
  color: var(--text-muted);
  font-size: 11px;
}

.metadata-error {
  padding: 10px 11px;
  border: 1px solid color-mix(in srgb, var(--danger-color) 26%, var(--border-light));
  border-radius: 8px;
  background: color-mix(in srgb, var(--danger-color) 7%, var(--bg-primary));
  color: var(--danger-dark);
  font-size: 13px;
}

.metadata-drawer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

@media (max-width: 980px) {
  .workspace-status {
    grid-template-columns: 1fr;
  }

  .recent-work {
    padding-left: 0;
    border-left: 0;
  }

  .workspace-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 900px) {
  .summary-band {
    grid-template-columns: repeat(2, minmax(120px, 1fr));
  }

  .filter-bar {
    grid-template-columns: 1fr;
  }

  .metadata-filter-bar {
    grid-template-columns: 1fr 1fr;
  }

  .stage-track {
    grid-template-columns: repeat(3, minmax(56px, 1fr));
    row-gap: 8px;
  }

  .metadata-form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
