<template>
  <div class="final-review-page">
    <section class="review-header">
      <div>
        <h1>Standard 质检</h1>
        <p>人工判断质量；系统沉淀问题证据、批量核查归因，并输出下一轮 Raw/Clean/Standard 改进依据。</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" :loading="loading" @click="loadAssets">刷新</el-button>
        <el-button :icon="Plus" :disabled="!selectedAsset || !session" @click="openManualAnnotation">
          记录问题
        </el-button>
        <el-button type="primary" :disabled="!session" @click="generateQualityReport">
          生成质检报告
        </el-button>
      </div>
    </section>

    <section class="trace-toolbar">
      <el-input v-model="search" clearable placeholder="搜索已生成 Standard 的 material_id / 文件名" @keyup.enter="loadAssets">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="selectedAssetId" filterable placeholder="选择已生成 Standard 的材料" class="asset-select" @change="handleSelectedAssetChange">
        <el-option v-for="row in assets" :key="row.id" :label="displayFilename(row)" :value="row.id" />
      </el-select>
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        small
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        class="trace-pagination"
      />
    </section>

    <section class="selected-asset-strip">
      <strong>{{ selectedAsset ? displayFilename(selectedAsset) : '请选择材料' }}</strong>
      <span>{{ selectedAsset?.material_id || selectedAsset?.run_id || '' }}</span>
      <el-tag v-if="selectedAsset" size="small" type="success">Standard</el-tag>
      <el-tag v-if="selectedAsset?.standard_quality_score !== null && selectedAsset?.standard_quality_score !== undefined" size="small" type="primary">
        {{ selectedAsset.standard_quality_score }}分
      </el-tag>
      <el-tag v-if="session" size="small" type="info">{{ reviewProgressText }}</el-tag>
      <el-tag v-if="problemCount" size="small" type="danger">{{ problemCount }} 个问题</el-tag>
      <el-tag v-if="session" size="small" :type="acceptanceMeta.type">{{ acceptanceMeta.label }}</el-tag>
    </section>

    <section class="final-review-grid">
      <article class="final-panel final-pdf-panel">
        <header>
          <strong>源 PDF</strong>
          <el-tag v-if="selectedAsset" size="small" type="primary">P{{ activeSourcePage }}</el-tag>
        </header>
        <PdfSourceViewer
          v-if="fileUrl"
          :url="fileUrl"
          :source-map="sourceMap"
          :active-page="activeSourcePage"
          :active-block-id="activeSourceBlockId"
          @page-change="handlePdfPageChange"
          @block-select="handlePdfBlockSelect"
        />
        <el-empty v-else description="暂无 PDF 可预览" />
      </article>

      <aside class="final-panel final-middle-panel">
        <header class="queue-header">
          <div>
            <strong>审查队列</strong>
            <span>{{ reviewProgressText }}</span>
          </div>
          <el-button size="small" type="primary" :disabled="!session" @click="generateQualityReport">生成报告</el-button>
        </header>

        <section class="current-review-card">
          <div>
            <small>当前审查单元</small>
            <strong>{{ selectedOutlineUnit?.path_label || selectedOutlineUnit?.title || '未选择目录' }}</strong>
            <span>PDF P{{ selectedOutlineUnitPage || activeSourcePage }}</span>
          </div>
          <div class="quick-actions">
            <el-button size="small" type="success" :disabled="!selectedOutlineUnit" @click="passCurrentUnit">通过本节</el-button>
            <el-button size="small" type="primary" :disabled="!selectedOutlineUnit || !session" @click="openManualAnnotation">记录问题</el-button>
            <el-button size="small" :disabled="!selectedOutlineUnit" @click="skipCurrentUnit">跳过</el-button>
          </div>
        </section>

        <section class="quality-summary">
          <strong>{{ acceptanceMeta.label }}</strong>
          <p>{{ qualitySummaryText }}</p>
        </section>

        <div ref="outlineScrollRef" class="review-queue">
          <el-skeleton v-if="outlineLoading" :rows="14" animated />
          <el-empty v-else-if="outlineError" :description="outlineError" />
          <template v-else-if="reviewQueueRows.length">
            <button
              v-for="row in reviewQueueRows"
              :key="row.unit.id"
              class="queue-unit"
              :class="{ active: row.unit.id === activeOutlineUnitId, problem: row.issueCount > 0 }"
              :data-unit-id="row.unit.id"
              :style="{ paddingLeft: `${Math.min(row.unit.level || 1, 6) * 10 + 8}px` }"
              type="button"
              @click="selectOutlineUnit(row.unit.id)"
            >
              <span class="queue-title">{{ row.unit.title || '未命名目录' }}</span>
              <small>
                <span v-if="outlineUnitPageNumber(row.unit)">P{{ outlineUnitPageNumber(row.unit) }}</span>
                <el-tag size="small" :type="queueStatusMeta(row.status).type">{{ queueStatusMeta(row.status).label }}</el-tag>
                <el-tag v-if="row.issueCount" size="small" type="danger">{{ row.issueCount }}</el-tag>
              </small>
            </button>
          </template>
          <el-empty v-else description="暂无可审查目录" />
        </div>

        <section v-if="annotations.length" class="issue-digest">
          <div class="issue-digest-title">
            <strong>已记录问题</strong>
            <span>{{ annotations.length }} 条</span>
          </div>
          <article v-for="annotation in annotations.slice(0, 5)" :key="annotation.id" class="digest-item">
            <strong>{{ issueTypeLabel(annotation.issue_type) }}</strong>
            <span>{{ annotation.human_note || '未填写备注' }}</span>
          </article>
        </section>
      </aside>

      <article class="final-panel final-html-panel">
        <header>
          <strong>Standard HTML</strong>
          <div class="panel-header-actions">
            <el-tag v-if="selectedOutlineUnitPage" size="small">PDF P{{ selectedOutlineUnitPage }}</el-tag>
            <el-button v-if="standardHtmlUrl" link size="small" type="primary" @click="openStandardHtml">新窗口</el-button>
          </div>
        </header>
        <div class="unit-meta">
          <strong>{{ selectedOutlineUnit?.path_label || selectedOutlineUnit?.title || '未选择目录' }}</strong>
          <span>点击 HTML 内容块可记录问题；通过/跳过请使用中间质检队列。</span>
        </div>
        <div class="standard-frame-wrap">
          <el-skeleton v-if="outlineLoading" :rows="14" animated />
          <iframe
            v-else-if="standardHtmlUrl"
            ref="standardFrameRef"
            class="standard-frame"
            :src="standardHtmlUrl"
            title="Standard Quality Check HTML Preview"
            @load="handleStandardFrameLoad"
          ></iframe>
          <el-empty v-else description="暂无 Standard HTML" />
        </div>
      </article>
    </section>

    <el-dialog v-model="reportDialogVisible" title="Standard 质检报告" width="560px">
      <div class="report-dialog-body">
        <strong>{{ acceptanceMeta.label }}</strong>
        <p>{{ qualitySummaryText }}</p>
        <div class="report-grid">
          <span>审查覆盖</span><strong>{{ reviewedCount }}/{{ outlineUnits.length }}</strong>
          <span>通过</span><strong>{{ passedCount }}</strong>
          <span>跳过</span><strong>{{ skippedCount }}</strong>
          <span>问题</span><strong>{{ problemCount }}</strong>
          <span>阻断</span><strong>{{ blockerCount }}</strong>
          <span>已归因/建议</span><strong>{{ decidedAnnotations.length }}</strong>
        </div>
        <div class="stage-backlog">
          <strong>下一轮改进方向</strong>
          <div v-for="row in stageBacklogRows" :key="row.key">
            <span>{{ row.label }}</span>
            <strong>{{ row.count }}</strong>
          </div>
        </div>
        <div class="next-action-box">
          <strong>建议下一步</strong>
          <p>{{ nextActionText }}</p>
        </div>
        <p v-if="lastExportRef">已导出：{{ lastExportRef }}</p>
      </div>
      <template #footer>
        <el-button @click="reportDialogVisible = false">继续质检</el-button>
        <el-button type="primary" :disabled="!session" @click="exportSession">导出审查包</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="annotationDrawerVisible" size="420px" title="记录问题" append-to-body>
      <el-form label-position="top" class="annotation-form">
        <el-form-item label="问题类型">
          <el-select v-model="annotationForm.issue_type" filterable>
            <el-option v-for="item in issueTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度">
          <el-segmented v-model="annotationForm.severity" :options="severityOptions" />
        </el-form-item>
        <el-form-item label="一句话说明">
          <el-input v-model="annotationForm.human_note" type="textarea" :rows="4" placeholder="例如：这张图和上下文无关，应删除；或：公式没有渲染。" />
        </el-form-item>
        <div class="anchor-box">
          <strong>系统已自动记录定位</strong>
          <img
            v-if="annotationForm.anchors.standard_image_src"
            class="anchor-thumb"
            :src="annotationForm.anchors.standard_image_src"
            :alt="annotationForm.anchors.standard_image_alt || '问题图片'"
          />
          <span>对象：{{ annotationForm.anchors.standard_element_label || '当前审查单元' }}</span>
          <span>Standard：{{ annotationForm.anchors.standard_block_id || '当前单元' }}</span>
          <span>PDF：P{{ annotationForm.anchors.pdf_page || activeSourcePage }}</span>
          <span v-if="annotationForm.anchors.heading_path?.length">目录：{{ annotationForm.anchors.heading_path.join(' > ') }}</span>
          <span v-if="annotationForm.anchors.selected_text">选中文本：{{ annotationForm.anchors.selected_text }}</span>
          <span v-else-if="annotationForm.anchors.standard_text_preview">预览：{{ annotationForm.anchors.standard_text_preview }}</span>
        </div>
        <div class="drawer-actions">
          <el-button @click="useCurrentPdfAnchor">使用当前 PDF 定位</el-button>
          <el-button @click="annotationDrawerVisible = false">取消</el-button>
          <el-button type="primary" @click="saveAnnotation('submitted')">记录问题</el-button>
        </div>
      </el-form>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { reviewApi } from '@/api/review'
import PdfSourceViewer from '@/components/PdfSourceViewer.vue'
import type { SourceBlock, SourceMap } from '@/types/file'

interface OutlineUnit {
  id: string
  index?: number
  title?: string
  level?: number
  path?: string[]
  path_label?: string
  page?: number
  page_start?: number
  page_end?: number
  clean_status?: string
}

interface OutlineReviewData {
  directory_units?: OutlineUnit[]
  raw_text?: Array<{ title?: string; page?: number; level?: number; text?: string }>
  standard_navigation?: {
    available?: boolean
    outline?: Array<{ block_id?: string; title?: string; level?: number; path?: string[]; heading_path?: string[] }>
    blocks?: Array<{ block_id?: string; type?: string; line_start?: number; heading_path?: string[] }>
  }
}

interface FinalReviewAnnotation {
  id: string
  issue_type: string
  severity: string
  status: string
  human_note: string
  anchors: Record<string, any>
  evidence: Record<string, any>
  verification?: {
    root_cause_stage: string
    root_cause_label: string
    confidence: number
    proposed_action?: Record<string, any>
  } | null
  decisions?: Array<Record<string, any>>
}

interface FinalReviewSession {
  id: string
  status: string
  material_id: string
  standard_run_id: string
  counts?: Record<string, number>
  annotations?: FinalReviewAnnotation[]
}

type ReviewUnitStatus = 'unreviewed' | 'passed' | 'problem' | 'skipped'
type TagType = 'primary' | 'success' | 'warning' | 'danger' | 'info'

const route = useRoute()
const routeAssetId = computed(() => {
  const value = route.query.asset_id || route.query.asset
  if (Array.isArray(value)) return value[0] || ''
  return value ? String(value) : ''
})

const assets = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')
const loading = ref(false)
const selectedAssetId = ref('')
const session = ref<FinalReviewSession | null>(null)
const fileUrl = ref('')
const sourceMap = ref<SourceMap>({ pages: [] })
const outlineData = ref<OutlineReviewData | null>(null)
const outlineLoading = ref(false)
const outlineError = ref('')
const activeSourcePage = ref(1)
const activeSourceBlockId = ref('')
const activeOutlineUnitId = ref('')
const outlineScrollRef = ref<HTMLElement | null>(null)
const standardFrameRef = ref<HTMLIFrameElement | null>(null)
const annotationDrawerVisible = ref(false)
const reportDialogVisible = ref(false)
const lastExportRef = ref('')
const unitReviewState = ref<Record<string, ReviewUnitStatus>>({})
const currentPdfAnchor = ref<Record<string, any>>({})
const annotationForm = reactive({
  issue_type: 'needs_ai_check',
  severity: 'major',
  human_note: '',
  anchors: {} as Record<string, any>,
  evidence: {} as Record<string, any>
})

let standardScrollTimer: number | undefined
let pdfStandardSyncTimer: number | undefined
let standardFrameCleanup: (() => void) | null = null
let suppressNextStandardSync = false
let suppressPdfToStandardSync = false
let loadSeq = 0

const issueLabels: Record<string, string> = {
  missing_content: '内容缺失',
  extra_noise: '多余噪音',
  wrong_order: '顺序错误',
  heading_hierarchy: '目录层级',
  question_grouping: '题组成组',
  option_answer_blank: '选项/空格',
  image_missing: '图片缺失',
  image_wrong_parent: '图片归属错误',
  image_should_keep: '误删图片',
  image_should_drop: '应删图片',
  table_broken: '表格错误',
  formula_broken: '公式错误',
  ocr_text_error: 'OCR 文本错误',
  print_layout: '打印排版',
  needs_ai_check: '需要核查'
}
const issueTypeOptions = Object.entries(issueLabels).map(([value, label]) => ({ value, label }))
const severityOptions = [
  { value: 'minor', label: '轻微' },
  { value: 'major', label: '重要' },
  { value: 'blocker', label: '阻断' }
]
const selectedAsset = computed(() => assets.value.find(row => row.id === selectedAssetId.value) || null)
const annotations = computed(() => session.value?.annotations || [])
const annotationsByUnitId = computed(() => {
  const map = new Map<string, FinalReviewAnnotation[]>()
  for (const annotation of annotations.value) {
    const unitId = String(annotation.anchors?.outline_unit_id || '')
    if (!unitId) continue
    map.set(unitId, [...(map.get(unitId) || []), annotation])
  }
  return map
})
const verifiedAnnotations = computed(() => annotations.value.filter(row => isVerificationActive(row) && !isAnnotationDecided(row)))
const actionableVerifiedAnnotations = computed(() => verifiedAnnotations.value.filter(row => canAcceptSuggestion(row)))
const decidedAnnotations = computed(() => annotations.value.filter(row => isAnnotationDecided(row)))
const reviewQueueRows = computed(() => outlineUnits.value.map(unit => {
  const issueCount = annotationsByUnitId.value.get(unit.id)?.length || 0
  const status = issueCount > 0 ? 'problem' : (unitReviewState.value[unit.id] || 'unreviewed')
  return { unit, status, issueCount }
}))
const passedCount = computed(() => reviewQueueRows.value.filter(row => row.status === 'passed').length)
const skippedCount = computed(() => reviewQueueRows.value.filter(row => row.status === 'skipped').length)
const problemCount = computed(() => annotations.value.length)
const problemUnitCount = computed(() => reviewQueueRows.value.filter(row => row.status === 'problem').length)
const blockerCount = computed(() => annotations.value.filter(row => row.severity === 'blocker').length)
const reviewedCount = computed(() => reviewQueueRows.value.filter(row => row.status !== 'unreviewed').length)
const reviewProgressText = computed(() => `已审 ${reviewedCount.value}/${outlineUnits.value.length}`)
const acceptanceMeta = computed<{ label: string; type: TagType }>(() => {
  if (!outlineUnits.value.length) return { label: '暂无质检对象', type: 'info' }
  if (blockerCount.value > 0) return { label: '阻断：不可交付', type: 'danger' }
  if (problemCount.value > 0) return { label: '有问题：需迭代', type: 'warning' }
  if (reviewedCount.value < outlineUnits.value.length) return { label: '质检中', type: 'primary' }
  return { label: '可进入交付候选', type: 'success' }
})
const qualitySummaryText = computed(() => {
  if (!outlineUnits.value.length) return '当前材料尚未加载出可审查目录。'
  if (blockerCount.value > 0) return `发现 ${blockerCount.value} 个阻断问题，应先生成报告并进入下一轮修订。`
  if (problemCount.value > 0) return `已记录 ${problemCount.value} 个问题，覆盖 ${problemUnitCount.value} 个审查单元；生成报告后系统会批量核查归因。`
  if (reviewedCount.value < outlineUnits.value.length) return '继续按队列通过、记录问题或跳过，直到覆盖足够审查范围。'
  return '未记录问题且审查队列已覆盖，可作为 Standard 交付候选。'
})
const stageBacklogCounts = computed(() => {
  const counts: Record<string, number> = {
    rerun_raw: 0,
    rerun_clean: 0,
    rerun_standard: 0,
    upstream_limited: 0,
    needs_more_evidence: 0
  }
  for (const annotation of annotations.value) {
    const decision = suggestedDecision(annotation)
    if (decision in counts) counts[decision] += 1
  }
  return counts
})
const stageBacklogRows = computed(() => {
  const counts = stageBacklogCounts.value
  return [
    { key: 'rerun_raw', label: 'Raw：目录/块归属', count: counts.rerun_raw },
    { key: 'rerun_clean', label: 'Clean：清洗/保守性', count: counts.rerun_clean },
    { key: 'rerun_standard', label: 'Standard：分组/渲染/版面', count: counts.rerun_standard },
    { key: 'upstream_limited', label: '上游限制：PDF/MinerU', count: counts.upstream_limited },
    { key: 'needs_more_evidence', label: '待补证据/人工复核', count: counts.needs_more_evidence }
  ]
})
const nextActionText = computed(() => {
  const counts = stageBacklogCounts.value
  if (counts.needs_more_evidence > 0) {
    return `先不要进入规则修订。还有 ${counts.needs_more_evidence} 条问题缺少可执行证据，请回到审查队列，把它们重新记录为更具体的问题类型和一句话事实，再重新生成报告。`
  }
  if (blockerCount.value > 0) {
    return '存在阻断问题。请使用审查包进入下一轮修订，优先处理阻断项，再重新生成 Standard 并复检。'
  }
  if (counts.rerun_clean > 0 || counts.rerun_standard > 0 || counts.rerun_raw > 0) {
    const priorities = [
      counts.rerun_clean ? `Clean ${counts.rerun_clean}` : '',
      counts.rerun_standard ? `Standard ${counts.rerun_standard}` : '',
      counts.rerun_raw ? `Raw ${counts.rerun_raw}` : ''
    ].filter(Boolean).join('，')
    return `可以进入下一轮迭代。优先处理：${priorities}。修订后重跑对应阶段，再回到本页复检。`
  }
  if (reviewedCount.value < outlineUnits.value.length) {
    return '继续完成剩余审查队列；覆盖足够后再生成报告判断是否可交付。'
  }
  return '当前未发现问题且审查覆盖完成，可以作为 Standard 交付候选。'
})
const outlineUnits = computed<OutlineUnit[]>(() => {
  const units = outlineData.value?.directory_units || []
  if (units.length) return units
  const rawRows = outlineData.value?.raw_text || []
  return rawRows.map((row, index) => ({
    id: `raw-${index + 1}`,
    index: index + 1,
    title: row.title || `目录 ${index + 1}`,
    level: row.level || 1,
    path: [row.title || `目录 ${index + 1}`],
    path_label: row.title || `目录 ${index + 1}`,
    page: row.page,
    page_start: row.page,
    page_end: row.page,
    clean_status: 'pending'
  }))
})
const selectedOutlineUnit = computed(() => outlineUnits.value.find(unit => unit.id === activeOutlineUnitId.value) || outlineUnits.value[0] || null)
const selectedOutlineUnitPage = computed(() => outlineUnitPageNumber(selectedOutlineUnit.value))
const standardHtmlUrl = computed(() => selectedAssetId.value ? `/api/review/assets/${selectedAssetId.value}/artifact?stage=standard&path=standard.html` : '')
const standardOutlineTargets = computed(() => outlineData.value?.standard_navigation?.outline || [])
const standardTargetByUnitId = computed(() => {
  const targets = standardOutlineTargets.value
  const byPath = new Map<string, any>()
  const byTitle = new Map<string, any>()
  for (const target of targets) {
    const pathKey = standardPathKey(target.path || target.heading_path || [])
    if (pathKey && !byPath.has(pathKey)) byPath.set(pathKey, target)
    const titleKey = standardTitleKey(target.title || '', target.level)
    if (titleKey && !byTitle.has(titleKey)) byTitle.set(titleKey, target)
  }
  const map = new Map<string, any>()
  for (const unit of outlineUnits.value) {
    const target =
      byPath.get(standardPathKey(unit.path || [])) ||
      byPath.get(standardPathKey(unit.path_label ? unit.path_label.split(' > ') : [])) ||
      byTitle.get(standardTitleKey(unit.title || '', unit.level))
    if (target?.block_id) map.set(unit.id, target)
  }
  return map
})
const unitIdByStandardBlockId = computed(() => {
  const map = new Map<string, string>()
  for (const [unitId, target] of standardTargetByUnitId.value.entries()) {
    if (target?.block_id) map.set(String(target.block_id), unitId)
  }
  return map
})
const standardClickableBlockIds = computed(() => {
  const ids = new Set<string>()
  for (const target of outlineData.value?.standard_navigation?.outline || []) {
    if (target.block_id) ids.add(String(target.block_id))
  }
  for (const block of outlineData.value?.standard_navigation?.blocks || []) {
    if (block.block_id) ids.add(String(block.block_id))
  }
  return ids
})
const sourceBlockMap = computed(() => {
  const map = new Map<string, { page: number; block: SourceBlock }>()
  for (const pageRow of sourceMap.value.pages || []) {
    for (const block of pageRow.blocks || []) {
      map.set(block.id, { page: pageRow.page, block })
    }
  }
  return map
})

function displayFilename(row: any) {
  return row?.input_filename || row?.filename || row?.title || '未命名 PDF'
}

function issueTypeLabel(value: string) {
  return issueLabels[value] || value
}

function queueStatusMeta(value: ReviewUnitStatus) {
  const map: Record<ReviewUnitStatus, { label: string; type: TagType }> = {
    unreviewed: { label: '未审', type: 'info' },
    passed: { label: '通过', type: 'success' },
    problem: { label: '有问题', type: 'danger' },
    skipped: { label: '跳过', type: 'warning' }
  }
  return map[value] || map.unreviewed
}

function reviewStateStorageKey(assetId = selectedAssetId.value) {
  return assetId ? `luceon-standard-quality:${assetId}` : ''
}

function loadReviewState(assetId: string) {
  const key = reviewStateStorageKey(assetId)
  if (!key) {
    unitReviewState.value = {}
    return
  }
  try {
    const parsed = JSON.parse(window.localStorage.getItem(key) || '{}')
    unitReviewState.value = parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    unitReviewState.value = {}
  }
}

function saveReviewState() {
  const key = reviewStateStorageKey()
  if (!key) return
  window.localStorage.setItem(key, JSON.stringify(unitReviewState.value))
}

function setCurrentUnitReviewState(status: ReviewUnitStatus) {
  const unitId = selectedOutlineUnit.value?.id
  if (!unitId) return
  unitReviewState.value = {
    ...unitReviewState.value,
    [unitId]: status
  }
  saveReviewState()
}

function passCurrentUnit() {
  setCurrentUnitReviewState('passed')
  ElMessage.success('当前审查单元已标记通过')
}

function skipCurrentUnit() {
  setCurrentUnitReviewState('skipped')
  ElMessage.info('当前审查单元已跳过')
}

function isAnnotationDecided(annotation: FinalReviewAnnotation) {
  return ['fix_proposed', 'project_accepted', 'project_rejected', 'resolved'].includes(annotation.status)
}

function isVerificationActive(annotation: FinalReviewAnnotation) {
  return Boolean(annotation.verification) && !['draft', 'submitted'].includes(annotation.status)
}

function suggestedDecision(annotation: FinalReviewAnnotation) {
  if (!isVerificationActive(annotation)) return 'needs_more_evidence'
  const verification = annotation.verification
  if (!verification) return 'needs_more_evidence'
  if (verification.root_cause_stage === 'pdf_source_limit') return 'upstream_limited'
  if (verification.root_cause_stage === 'human_false_positive') return 'reject'
  const issueType = annotation.issue_type
  if (['wrong_order', 'heading_hierarchy'].includes(issueType)) return 'rerun_raw'
  if (['formula_broken', 'table_broken', 'question_grouping', 'option_answer_blank', 'image_wrong_parent', 'print_layout'].includes(issueType)) {
    return 'rerun_standard'
  }
  if (['missing_content', 'extra_noise', 'image_missing', 'image_should_keep', 'image_should_drop', 'ocr_text_error'].includes(issueType)) {
    return 'rerun_clean'
  }
  return 'needs_more_evidence'
}

function canAcceptSuggestion(annotation: FinalReviewAnnotation) {
  if (!isVerificationActive(annotation) || isAnnotationDecided(annotation)) return false
  return !['needs_more_evidence', 'reject'].includes(suggestedDecision(annotation))
}

function outlineUnitPageNumber(unit: OutlineUnit | null, fallback = 0) {
  const pageNumber = Number(unit?.page || unit?.page_start || 0)
  return Number.isFinite(pageNumber) && pageNumber > 0 ? pageNumber : fallback
}

function standardPathKey(path: unknown) {
  const rows = Array.isArray(path) ? path : []
  return rows.map(item => String(item || '').trim().toLowerCase()).filter(Boolean).join(' > ')
}

function standardTitleKey(title: string, level?: number) {
  const normalized = String(title || '').trim().toLowerCase()
  return normalized ? `${Number(level || 0)}:${normalized}` : ''
}

function standardFrameDocument() {
  try {
    return standardFrameRef.value?.contentDocument || standardFrameRef.value?.contentWindow?.document || null
  } catch {
    return null
  }
}

async function loadAssets() {
  loading.value = true
  try {
    const res = await reviewApi.getFinalReviewAssets({
      page: page.value,
      page_size: pageSize.value,
      search: search.value
    })
    assets.value = res.files
    total.value = res.total
    const requestedAssetId = routeAssetId.value
    let nextSelected = requestedAssetId ? assets.value.find(row => row.id === requestedAssetId) : null
    if (requestedAssetId && !nextSelected) {
      try {
        const requestedAsset = await reviewApi.getAsset(requestedAssetId)
        if (requestedAsset?.has_standard) {
          assets.value = [requestedAsset, ...assets.value.filter(row => row.id !== requestedAsset.id)]
          nextSelected = requestedAsset
        }
      } catch {
        // Fall through to the first available final-review asset.
      }
    }
    if (!nextSelected) nextSelected = assets.value.find(row => row.id === selectedAssetId.value) || assets.value[0]
    if (nextSelected) {
      selectedAssetId.value = nextSelected.id
      await loadSelectedAsset(nextSelected.id)
    } else {
      clearSelectedAsset()
    }
  } catch {
    ElMessage.error('获取终审列表失败')
  } finally {
    loading.value = false
  }
}

function clearSelectedAsset() {
  cleanupStandardFrameListener()
  selectedAssetId.value = ''
  session.value = null
  unitReviewState.value = {}
  fileUrl.value = ''
  sourceMap.value = { pages: [] }
  outlineData.value = null
  outlineError.value = ''
  activeSourcePage.value = 1
  activeSourceBlockId.value = ''
  activeOutlineUnitId.value = ''
}

async function loadSelectedAsset(assetId: string) {
  cleanupStandardFrameListener()
  const seq = ++loadSeq
  outlineLoading.value = true
  outlineError.value = ''
  session.value = null
  fileUrl.value = reviewApi.getContentUrl(assetId)
  sourceMap.value = { pages: [] }
  outlineData.value = null
  activeSourcePage.value = 1
  activeSourceBlockId.value = ''
  try {
    const [outlineResult, sourceMapResult, sessionResult] = await Promise.all([
      reviewApi.getOutlineReview(assetId),
      reviewApi.getSourceMap(assetId),
      reviewApi.createFinalReviewSession({ asset_id: Number(assetId), reuse_open: true })
    ])
    if (seq !== loadSeq || selectedAssetId.value !== assetId) return
    outlineData.value = outlineResult
    sourceMap.value = sourceMapResult || { pages: [] }
    session.value = sessionResult
    loadReviewState(assetId)
    await nextTick()
    activeOutlineUnitId.value = outlineUnits.value[0]?.id || ''
    syncOutlineUnitPage(selectedOutlineUnit.value)
  } catch (e: any) {
    if (seq !== loadSeq || selectedAssetId.value !== assetId) return
    outlineError.value = e?.response?.data?.detail || '终审数据不可用'
  } finally {
    if (seq === loadSeq && selectedAssetId.value === assetId) outlineLoading.value = false
  }
}

function handleSelectedAssetChange(assetId: string) {
  if (!assetId) return
  void loadSelectedAsset(assetId)
}

async function refreshSession() {
  if (!session.value?.id) return
  session.value = await reviewApi.getFinalReviewSession(session.value.id)
}

function outlineUnitForPdfPage(pageNumber: number) {
  const pageNo = Math.max(1, Number(pageNumber) || 1)
  const candidates = outlineUnits.value
    .map((unit, index) => ({
      unit,
      index,
      start: outlineUnitPageNumber(unit, 0),
      end: Number(unit.page_end || unit.page || unit.page_start || 0)
    }))
    .filter(row => row.start > 0 && row.start <= pageNo)
  if (!candidates.length) return outlineUnits.value[0] || null
  const containing = candidates.filter(row => !row.end || row.end >= pageNo)
  const pool = containing.length ? containing : candidates
  return pool.sort((a, b) => (b.start - a.start) || (b.index - a.index))[0]?.unit || null
}

function syncOutlineUnitPage(unit: OutlineUnit | null) {
  const pageNumber = outlineUnitPageNumber(unit, 1)
  suppressPdfToStandardSync = true
  window.setTimeout(() => {
    suppressPdfToStandardSync = false
  }, 240)
  activeSourcePage.value = pageNumber
  activeSourceBlockId.value = ''
  currentPdfAnchor.value = { pdf_page: pageNumber }
}

function scrollOutlinePaneToUnit(unitId: string) {
  const container = outlineScrollRef.value
  if (!container || !unitId) return
  const target = Array.from(container.querySelectorAll<HTMLElement>('[data-unit-id]'))
    .find(section => section.dataset.unitId === unitId)
  if (!target) return
  const containerRect = container.getBoundingClientRect()
  const targetRect = target.getBoundingClientRect()
  container.scrollTo({
    top: Math.max(0, container.scrollTop + targetRect.top - containerRect.top - container.clientHeight / 2 + target.clientHeight / 2),
    behavior: 'auto'
  })
}

function scrollStandardToUnit(unitId: string) {
  const target = standardTargetByUnitId.value.get(unitId)
  const doc = standardFrameDocument()
  if (!target?.block_id || !doc) return
  const element = doc.getElementById(String(target.block_id))
  if (!element) return
  suppressNextStandardSync = true
  element.scrollIntoView({ block: 'start', behavior: 'auto' })
  window.setTimeout(() => {
    suppressNextStandardSync = false
  }, 180)
}

async function selectOutlineUnit(unitId: string) {
  activeOutlineUnitId.value = unitId
  await nextTick()
  syncOutlineUnitPage(selectedOutlineUnit.value)
  scrollOutlinePaneToUnit(unitId)
  scrollStandardToUnit(unitId)
}

function activeStandardBlockId() {
  const doc = standardFrameDocument()
  if (!doc) return ''
  const win = standardFrameRef.value?.contentWindow
  const scrollY = win?.scrollY ?? doc.documentElement.scrollTop ?? doc.body.scrollTop ?? 0
  const candidates = Array.from(doc.querySelectorAll<HTMLElement>('[id]'))
    .filter(element => unitIdByStandardBlockId.value.has(element.id))
    .sort((a, b) => a.offsetTop - b.offsetTop)
  let active = candidates[0]?.id || ''
  for (const element of candidates) {
    if (element.offsetTop <= scrollY + 96) active = element.id
    else break
  }
  return active
}

async function syncFromStandardScroll() {
  if (suppressNextStandardSync) return
  const blockId = activeStandardBlockId()
  const unitId = blockId ? unitIdByStandardBlockId.value.get(blockId) : ''
  if (!unitId || unitId === activeOutlineUnitId.value) return
  activeOutlineUnitId.value = unitId
  syncOutlineUnitPage(selectedOutlineUnit.value)
  await nextTick()
  scrollOutlinePaneToUnit(unitId)
}

function scheduleStandardScrollSync() {
  if (standardScrollTimer) window.clearTimeout(standardScrollTimer)
  standardScrollTimer = window.setTimeout(syncFromStandardScroll, 120)
}

function isFrameElement(target: EventTarget | null): target is Element {
  return Boolean(target && typeof (target as Element).closest === 'function')
}

function findStandardBlockElement(target: EventTarget | null) {
  const doc = standardFrameDocument()
  if (!doc || !isFrameElement(target)) return null
  let element: Element | null = target.closest('[id]')
  while (element) {
    if (standardClickableBlockIds.value.has((element as HTMLElement).id)) return element as HTMLElement
    element = element.parentElement?.closest('[id]') || null
  }
  return target.closest('[id]') as HTMLElement | null
}

function handleStandardClick(event: MouseEvent) {
  const element = findStandardBlockElement(event.target)
  if (!element) return
  const blockId = element.id
  const unitId = unitIdByStandardBlockId.value.get(blockId) || activeOutlineUnitId.value
  if (unitId) activeOutlineUnitId.value = unitId
  const selection = standardFrameRef.value?.contentWindow?.getSelection()?.toString().trim() || ''
  const anchors = standardElementAnchors(element, selection)
  openAnnotationDrawer({
    ...anchors,
    standard_block_id: blockId,
    html_selector: `#${CSS.escape(blockId)}`,
    selected_text: selection.slice(0, 500)
  }, defaultIssueTypeForElement(anchors.standard_element_kind))
}

function cleanupStandardFrameListener() {
  if (standardFrameCleanup) {
    standardFrameCleanup()
    standardFrameCleanup = null
  }
  if (standardScrollTimer) window.clearTimeout(standardScrollTimer)
  if (pdfStandardSyncTimer) window.clearTimeout(pdfStandardSyncTimer)
}

function installStandardClickHints(doc: Document) {
  const styleId = 'luceon-final-review-click-hints'
  if (!doc.getElementById(styleId)) {
    const style = doc.createElement('style')
    style.id = styleId
    style.textContent = `
      .luceon-final-review-clickable {
        cursor: copy !important;
        outline-offset: 3px;
        transition: outline-color 120ms ease, background-color 120ms ease;
      }
      .luceon-final-review-clickable:hover {
        outline: 2px solid #2563eb !important;
        background-color: rgba(37, 99, 235, 0.06) !important;
      }
    `
    doc.head.appendChild(style)
  }
  for (const blockId of standardClickableBlockIds.value) {
    doc.getElementById(blockId)?.classList.add('luceon-final-review-clickable')
  }
}

function handleStandardFrameLoad() {
  cleanupStandardFrameListener()
  const win = standardFrameRef.value?.contentWindow
  const doc = standardFrameDocument()
  if (!win || !doc) return
  installStandardClickHints(doc)
  win.addEventListener('scroll', scheduleStandardScrollSync, { passive: true })
  doc.addEventListener('click', handleStandardClick, true)
  standardFrameCleanup = () => {
    win.removeEventListener('scroll', scheduleStandardScrollSync)
    doc.removeEventListener('click', handleStandardClick, true)
  }
  if (activeOutlineUnitId.value) void nextTick(() => scrollStandardToUnit(activeOutlineUnitId.value))
}

async function syncStandardFromPdfPage(pageNumber: number) {
  if (suppressPdfToStandardSync) return
  const unit = outlineUnitForPdfPage(pageNumber)
  if (!unit?.id) return
  if (activeOutlineUnitId.value !== unit.id) activeOutlineUnitId.value = unit.id
  await nextTick()
  scrollOutlinePaneToUnit(unit.id)
  scrollStandardToUnit(unit.id)
}

function schedulePdfToStandardSync(pageNumber: number) {
  if (pdfStandardSyncTimer) window.clearTimeout(pdfStandardSyncTimer)
  pdfStandardSyncTimer = window.setTimeout(() => {
    pdfStandardSyncTimer = undefined
    void syncStandardFromPdfPage(pageNumber)
  }, 180)
}

function handlePdfPageChange(pageNumber: number) {
  activeSourcePage.value = pageNumber
  activeSourceBlockId.value = ''
  currentPdfAnchor.value = { pdf_page: pageNumber }
  schedulePdfToStandardSync(pageNumber)
}

function handlePdfBlockSelect(pageNumber: number, blockId: string) {
  activeSourcePage.value = pageNumber
  activeSourceBlockId.value = blockId
  const hit = sourceBlockMap.value.get(blockId)
  currentPdfAnchor.value = {
    pdf_page: pageNumber,
    source_block_id: blockId,
    pdf_bbox: hit?.block.bbox || null,
    source_text_preview: hit?.block.text?.slice(0, 500) || ''
  }
  schedulePdfToStandardSync(pageNumber)
}

function baseAnchors(extra: Record<string, any> = {}) {
  const unit = selectedOutlineUnit.value
  return {
    ...currentPdfAnchor.value,
    pdf_page: currentPdfAnchor.value.pdf_page || activeSourcePage.value,
    heading_path: unit?.path || (unit?.path_label ? unit.path_label.split(' > ') : []),
    outline_unit_id: unit?.id || '',
    ...extra
  }
}

function standardElementKind(element: HTMLElement) {
  const tag = element.tagName.toLowerCase()
  if (tag === 'figure' || tag === 'img' || element.querySelector('img')) return 'image'
  if (tag === 'table' || element.classList.contains('table-wrap') || element.querySelector('table')) return 'table'
  if (element.classList.contains('math-display') || Boolean(element.closest('.math-display'))) return 'formula'
  if (/^h[1-6]$/.test(tag)) return 'heading'
  if (tag === 'li' || Boolean(element.closest('li'))) return 'question'
  return 'text'
}

function standardElementLabel(kind: string) {
  const map: Record<string, string> = {
    image: '图片',
    table: '表格',
    formula: '公式',
    heading: '标题',
    question: '题目/选项',
    text: '正文'
  }
  return map[kind] || '内容块'
}

function defaultIssueTypeForElement(kind: string) {
  const map: Record<string, string> = {
    image: 'image_should_drop',
    table: 'table_broken',
    formula: 'formula_broken',
    heading: 'heading_hierarchy',
    question: 'question_grouping',
    text: 'needs_ai_check'
  }
  return map[kind] || 'needs_ai_check'
}

function standardElementAnchors(element: HTMLElement, selection: string) {
  const kind = standardElementKind(element)
  const image = kind === 'image' ? element.querySelector('img') : null
  const imageSrc = image?.getAttribute('src') || ''
  const imageAlt = image?.getAttribute('alt') || ''
  const textPreview = (selection || imageAlt || element.innerText || '').trim().slice(0, 500)
  return {
    standard_element_kind: kind,
    standard_element_label: standardElementLabel(kind),
    standard_image_src: imageSrc,
    standard_image_alt: imageAlt,
    standard_text_preview: textPreview
  }
}

function openAnnotationDrawer(extraAnchors: Record<string, any> = {}, defaultIssueType = 'needs_ai_check') {
  annotationForm.issue_type = defaultIssueType
  annotationForm.severity = 'major'
  annotationForm.human_note = ''
  annotationForm.anchors = baseAnchors(extraAnchors)
  annotationForm.evidence = {}
  annotationDrawerVisible.value = true
}

function openManualAnnotation() {
  openAnnotationDrawer()
}

function useCurrentPdfAnchor() {
  annotationForm.anchors = {
    ...annotationForm.anchors,
    ...baseAnchors()
  }
}

async function saveAnnotation(status: 'draft' | 'submitted') {
  if (!session.value?.id) return
  const payload = {
    issue_type: annotationForm.issue_type,
    severity: annotationForm.severity,
    status,
    human_note: annotationForm.human_note,
    anchors: annotationForm.anchors,
    evidence: annotationForm.evidence
  }
  await reviewApi.createFinalReviewAnnotation(session.value.id, payload)
  annotationDrawerVisible.value = false
  setCurrentUnitReviewState('problem')
  await refreshSession()
  ElMessage.success(`${issueTypeLabel(annotationForm.issue_type)}已记录`)
}

async function generateQualityReport() {
  if (!session.value?.id) return
  const sessionId = session.value.id
  const draftCount = annotations.value.filter(row => row.status === 'draft').length
  if (draftCount) await reviewApi.submitFinalReviewSession(sessionId)
  const sessionAfterSubmit = await reviewApi.getFinalReviewSession(sessionId)
  session.value = sessionAfterSubmit
  if (annotations.value.some(row => row.status === 'submitted')) {
    const result = await reviewApi.verifyFinalReviewSession(sessionId)
    session.value = result.session
  }
  const suggestions = actionableVerifiedAnnotations.value
  for (const annotation of suggestions) {
    await reviewApi.decideFinalReviewAnnotation(annotation.id, { decision: suggestedDecision(annotation) })
  }
  await refreshSession()
  const exportResult = await reviewApi.exportFinalReviewSession(sessionId)
  lastExportRef.value = `${exportResult.archive.bucket}/${exportResult.archive.prefix}`
  reportDialogVisible.value = true
  ElMessage.success('Standard 质检报告已生成')
}

async function exportSession() {
  if (!session.value?.id) return
  const result = await reviewApi.exportFinalReviewSession(session.value.id)
  lastExportRef.value = `${result.archive.bucket}/${result.archive.prefix}`
  reportDialogVisible.value = true
  ElMessage.success(`已导出：${result.archive.bucket}/${result.archive.prefix}`)
}

function openStandardHtml() {
  if (standardHtmlUrl.value) window.open(standardHtmlUrl.value, '_blank')
}

watch([page, pageSize], loadAssets)
watch(routeAssetId, async () => {
  page.value = 1
  await loadAssets()
})

onMounted(() => {
  void loadAssets()
})

onBeforeUnmount(() => {
  cleanupStandardFrameListener()
})
</script>

<style scoped>
.final-review-page {
  flex: 1;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: hidden;
}

.review-header,
.selected-asset-strip,
.trace-toolbar {
  flex-shrink: 0;
}

.review-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.review-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
}

.review-header p {
  margin: 0;
  color: var(--text-secondary);
}

.header-actions,
.panel-header-actions,
.session-actions,
.issue-toolbar,
.issue-actions,
.drawer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trace-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
}

.trace-toolbar .el-input {
  max-width: 340px;
}

.asset-select {
  min-width: 320px;
  flex: 1;
}

.trace-pagination {
  flex-shrink: 0;
}

.selected-asset-strip {
  min-height: 34px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.selected-asset-strip strong,
.selected-asset-strip span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-asset-strip strong {
  color: var(--text-primary);
  font-size: 14px;
}

.selected-asset-strip span {
  color: var(--text-muted);
  font-size: 12px;
}

.final-review-grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns:
    minmax(360px, 1.05fr)
    minmax(270px, 0.72fr)
    minmax(440px, 1.28fr);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--bg-primary);
}

.final-panel {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.final-panel + .final-panel {
  border-left: 1px solid var(--border-light);
}

.final-panel header {
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-secondary);
}

.final-panel header strong {
  color: var(--text-primary);
  font-size: 14px;
}

.final-pdf-panel :deep(.pdf-source-viewer) {
  flex: 1;
  height: auto;
  min-height: 0;
  border: 0;
  border-radius: 0;
}

.queue-header {
  flex-shrink: 0;
}

.queue-header div,
.current-review-card div,
.quality-summary,
.issue-digest-title {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.queue-header span,
.current-review-card small,
.current-review-card span,
.quality-summary p,
.issue-digest-title span {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.45;
}

.current-review-card,
.quality-summary {
  flex-shrink: 0;
  display: flex;
  gap: 10px;
  padding: 12px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-primary);
}

.current-review-card {
  align-items: flex-start;
  justify-content: space-between;
}

.current-review-card strong {
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.4;
}

.quick-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.quality-summary {
  flex-direction: column;
  background: color-mix(in srgb, var(--primary-color) 6%, var(--bg-primary));
}

.quality-summary strong {
  color: var(--text-primary);
  font-size: 13px;
}

.quality-summary p {
  margin: 0;
}

.review-queue {
  flex: 1;
  min-height: 0;
  overflow: auto;
  overscroll-behavior: contain;
  padding: 8px;
}

.queue-unit {
  width: 100%;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
}

.queue-unit:hover {
  background: var(--bg-secondary);
}

.queue-unit.active {
  border-color: color-mix(in srgb, var(--primary-color) 28%, var(--border-light));
  background: var(--primary-tint);
  color: var(--primary-color);
  box-shadow: inset 3px 0 0 var(--primary-color);
}

.queue-unit.problem {
  border-left: 3px solid var(--danger-color);
}

.queue-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
}

.queue-unit small {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 11px;
}

.issue-digest {
  flex-shrink: 0;
  max-height: 210px;
  overflow: auto;
  padding: 10px;
  border-top: 1px solid var(--border-light);
  background: var(--bg-secondary);
}

.issue-digest-title {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.digest-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 8px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
}

.digest-item + .digest-item {
  margin-top: 6px;
}

.digest-item strong {
  color: var(--text-primary);
  font-size: 12px;
}

.digest-item span {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.4;
}

.report-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-dialog-body p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.5;
}

.report-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px 14px;
  padding: 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
}

.report-grid span {
  color: var(--text-secondary);
}

.stage-backlog {
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
}

.stage-backlog > strong {
  color: var(--text-primary);
  font-size: 13px;
}

.stage-backlog div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 12px;
}

.next-action-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border: 1px solid color-mix(in srgb, var(--primary-color) 24%, var(--border-light));
  border-radius: var(--radius-sm);
  background: color-mix(in srgb, var(--primary-color) 6%, var(--bg-primary));
}

.next-action-box strong {
  color: var(--text-primary);
  font-size: 13px;
}

.next-action-box p {
  margin: 0;
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.55;
}

.middle-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.middle-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
}

.middle-tabs :deep(.el-tab-pane) {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.outline-scroll,
.issue-list {
  flex: 1;
  height: auto;
  min-height: 0;
  overflow: auto;
  overscroll-behavior: contain;
  padding: 8px;
}

.outline-unit {
  width: 100%;
  min-height: 42px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
}

.outline-unit:hover {
  background: var(--bg-secondary);
}

.outline-unit.active {
  border-color: color-mix(in srgb, var(--primary-color) 28%, var(--border-light));
  background: var(--primary-tint);
  color: var(--primary-color);
  box-shadow: inset 3px 0 0 var(--primary-color);
}

.outline-unit-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
}

.outline-unit small {
  flex-shrink: 0;
  display: flex;
  gap: 6px;
  color: var(--text-muted);
  font-size: 11px;
}

.issue-toolbar,
.session-actions {
  padding: 8px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-primary);
}

.issue-toolbar .el-select {
  flex: 1;
}

.decision-panel {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px;
  border-bottom: 1px solid var(--border-light);
  background: color-mix(in srgb, var(--primary-color) 8%, var(--bg-primary));
}

.decision-panel strong {
  display: block;
  color: var(--text-primary);
  font-size: 13px;
}

.decision-panel p {
  margin: 3px 0 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.45;
}

.issue-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--border-light);
  border-left-width: 4px;
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
}

.issue-item + .issue-item {
  margin-top: 8px;
}

.issue-item.severity-minor {
  border-left-color: var(--text-muted);
}

.issue-item.severity-major {
  border-left-color: var(--warning-color);
}

.issue-item.severity-blocker {
  border-left-color: var(--danger-color);
}

.issue-main {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 4px;
  align-items: start;
}

.issue-main strong {
  font-size: 13px;
  color: var(--text-primary);
}

.issue-main strong,
.issue-main span {
  grid-column: 2;
}

.issue-thumb {
  grid-row: 1 / span 2;
  width: 56px;
  height: 56px;
  object-fit: cover;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: #fff;
}

.issue-main span,
.root-cause,
.anchor-box span {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.issue-meta,
.root-cause {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.root-cause {
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
}

.recommendation {
  padding: 7px 8px;
  border: 1px solid color-mix(in srgb, var(--primary-color) 24%, var(--border-light));
  border-radius: var(--radius-sm);
  background: color-mix(in srgb, var(--primary-color) 6%, var(--bg-primary));
  color: var(--text-primary);
  font-size: 12px;
  line-height: 1.5;
}

.unit-meta {
  min-height: 38px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-secondary);
  font-size: 12px;
}

.unit-meta strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
  font-size: 13px;
}

.standard-frame-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: #fff;
}

.standard-frame {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
  background: #fff;
}

.annotation-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.annotation-form .el-select {
  width: 100%;
}

.anchor-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
}

.anchor-thumb {
  width: 100%;
  max-height: 180px;
  object-fit: contain;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: #fff;
}

.anchor-box strong {
  color: var(--text-primary);
  font-size: 13px;
}

.drawer-actions {
  justify-content: flex-end;
  margin-top: 8px;
  flex-wrap: wrap;
}

@media (max-width: 1180px) {
  .final-review-grid {
    grid-template-columns: 1fr;
  }

  .final-panel + .final-panel {
    border-left: 0;
    border-top: 1px solid var(--border-light);
  }

  .final-pdf-panel,
  .final-middle-panel,
  .final-html-panel {
    min-height: 520px;
  }
}
</style>
