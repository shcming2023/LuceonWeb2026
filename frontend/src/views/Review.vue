<template>
  <div class="review-page" @wheel.capture="handleReviewWheel">
    <section class="review-header">
      <div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ pageDescription }}</p>
      </div>
    </section>

    <section v-if="reviewMode === 'page'" class="pdf-trace-workbench">
      <div class="trace-toolbar">
        <el-input v-model="search" clearable :placeholder="searchPlaceholder" @keyup.enter="loadAssets">
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="selectedAssetId"
          filterable
          placeholder="选择 PDF"
          class="asset-select"
          @change="handleSelectedAssetChange"
        >
          <el-option
            v-for="row in assets"
            :key="row.id"
            :label="displayFilename(row)"
            :value="row.id"
          />
        </el-select>
        <el-button :loading="loading" @click="loadAssets">
          <el-icon><Refresh /></el-icon>
          <span>刷新</span>
        </el-button>
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          small
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          class="trace-pagination"
        />
      </div>

      <div class="selected-asset-strip">
        <strong>{{ selectedAsset ? displayFilename(selectedAsset) : '请选择 PDF' }}</strong>
        <span>{{ selectedAsset?.material_id || selectedAsset?.run_id || '' }}</span>
        <el-tag v-if="selectedAsset" size="small" type="primary">Page {{ activeSourcePage }}</el-tag>
      </div>
      <div v-if="selectedAsset" class="review-decision-bar">
        <el-select v-model="reviewStatusDraft" size="small" class="review-status-select">
          <el-option label="待审查" value="pending" />
          <el-option label="通过" value="pass" />
          <el-option label="需修正" value="needs_fix" />
          <el-option label="退回" value="reject" />
        </el-select>
        <el-input
          v-model="reviewNoteDraft"
          size="small"
          clearable
          placeholder="审查备注"
          class="review-note-input"
          @keyup.enter="saveReviewMetadata"
        />
        <el-button size="small" type="primary" :loading="reviewSaving" @click="saveReviewMetadata">保存结论</el-button>
      </div>

      <div class="trace-grid">
        <article class="trace-panel pdf-panel">
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

        <article class="trace-panel markdown-panel">
          <header>
            <strong>MinerU 输出</strong>
            <el-tag size="small" type="primary">Page {{ activeSourcePage }}</el-tag>
          </header>
          <div ref="mineruScrollRef" class="markdown-scroll">
            <el-skeleton v-if="contentLoading" :rows="12" animated />
            <template v-else-if="mineruPageSections.length">
              <section
                v-for="section in mineruPageSections"
                :key="`mineru-${section.page}`"
                class="markdown-page-section"
                :class="{ active: section.page === activeSourcePage }"
                :data-page="section.page"
              >
                <div class="markdown-page-marker">Page {{ section.page }}</div>
                <div class="markdown-content" v-html="renderReviewMarkdown(section.markdown, 'mineru')"></div>
              </section>
            </template>
            <div v-else-if="mineruContent" class="markdown-content" v-html="renderReviewMarkdown(mineruContent, 'mineru')"></div>
            <el-empty v-else :description="mineruError || '暂无 MinerU Markdown'" />
          </div>
        </article>

        <article class="trace-panel markdown-panel">
          <header>
            <strong>MinerU-Popo 输出</strong>
            <div class="panel-header-actions">
              <button
                class="panel-mode"
                :class="{ active: popoViewMode === 'page' }"
                type="button"
                @click="setPopoViewMode('page')"
              >
                按页
              </button>
              <button
                class="panel-mode"
                :class="{ active: popoViewMode === 'tree' }"
                type="button"
                @click="setPopoViewMode('tree')"
              >
                文档树
              </button>
              <el-tag size="small" type="success">{{ popoViewMode === 'page' ? `Page ${activeSourcePage}` : 'Tree' }}</el-tag>
            </div>
          </header>
          <div ref="popoScrollRef" class="markdown-scroll">
            <el-skeleton v-if="contentLoading" :rows="12" animated />
            <template v-else-if="popoViewMode === 'page' && popoPageSections.length">
              <section
                v-for="section in popoPageSections"
                :key="`popo-${section.page}`"
                class="markdown-page-section"
                :class="{ active: section.page === activeSourcePage }"
                :data-page="section.page"
              >
                <div class="markdown-page-marker">Page {{ section.page }}</div>
                <div class="markdown-content" v-html="renderReviewMarkdown(section.markdown, 'popo')"></div>
              </section>
            </template>
            <div
              v-else-if="popoViewMode === 'tree' && popoTreeContent"
              class="markdown-content"
              v-html="renderReviewMarkdown(popoTreeContent, 'popo')"
            ></div>
            <el-empty v-else :description="popoError || '暂无 Popo 按页结果'" />
          </div>
        </article>
      </div>
    </section>

    <section v-else class="outline-workbench">
      <div class="trace-toolbar outline-toolbar">
        <el-input v-model="search" clearable :placeholder="searchPlaceholder" @keyup.enter="loadAssets">
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="selectedAssetId"
          filterable
          placeholder="选择已到 Raw/Clean 的材料"
          class="asset-select"
          @change="handleSelectedAssetChange"
        >
          <el-option
            v-for="row in assets"
            :key="row.id"
            :label="displayFilename(row)"
            :value="row.id"
          />
        </el-select>
        <el-button :loading="loading" @click="loadAssets">
          <el-icon><Refresh /></el-icon>
          <span>刷新</span>
        </el-button>
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          small
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          class="trace-pagination"
        />
      </div>

      <div class="selected-asset-strip outline-strip">
        <strong>{{ selectedAsset ? displayFilename(selectedAsset) : '请选择材料' }}</strong>
        <span>{{ selectedAsset?.material_id || selectedAsset?.run_id || '' }}</span>
        <el-tag v-if="selectedAsset" size="small" :type="stageMeta(selectedAsset.material_stage || selectedAsset.review_stage).type">
          {{ stageMeta(selectedAsset.material_stage || selectedAsset.review_stage).label }}
        </el-tag>
        <el-tag v-if="selectedAsset?.has_raw" size="small" type="warning">Raw</el-tag>
        <el-tag v-if="selectedAsset?.has_raw_dry_run" size="small" type="info">Raw预演</el-tag>
        <el-tag v-if="selectedAsset?.has_clean" size="small" type="success">Clean</el-tag>
        <el-tag v-if="selectedAsset" size="small" :type="statusMeta(selectedAsset.review_status).type">
          {{ statusMeta(selectedAsset.review_status).label }}
        </el-tag>
      </div>
      <div v-if="selectedAsset" class="review-decision-bar outline-decision-bar">
        <el-select v-model="reviewStatusDraft" size="small" class="review-status-select">
          <el-option label="待审查" value="pending" />
          <el-option label="通过" value="pass" />
          <el-option label="需修正" value="needs_fix" />
          <el-option label="退回" value="reject" />
        </el-select>
        <el-input
          v-model="reviewNoteDraft"
          size="small"
          clearable
          placeholder="审查备注"
          class="review-note-input"
          @keyup.enter="saveReviewMetadata"
        />
        <el-button size="small" type="primary" :loading="reviewSaving" @click="saveReviewMetadata">保存结论</el-button>
      </div>

      <div class="outline-grid">
        <aside class="outline-panel directory-panel">
          <header>
            <strong>目录</strong>
            <el-tag size="small" type="warning">{{ outlineUnits.length }}</el-tag>
          </header>
          <div class="outline-scroll">
            <el-skeleton v-if="outlineLoading" :rows="14" animated />
            <el-empty v-else-if="outlineError" :description="outlineError" />
            <template v-else-if="outlineUnits.length">
              <button
                v-for="unit in outlineUnits"
                :key="unit.id"
                class="outline-unit"
                :class="{ active: unit.id === activeOutlineUnitId }"
                :style="{ paddingLeft: `${Math.min(unit.level || 1, 6) * 10 + 8}px` }"
                type="button"
                @click="selectOutlineUnit(unit.id)"
              >
                <span class="outline-unit-title">{{ unit.title || '未命名目录' }}</span>
                <small>
                  <span v-if="outlineUnitPageNumber(unit)">P{{ outlineUnitPageNumber(unit) }}</span>
                  <span>{{ cleanStatusMeta(unit.clean_status).label }}</span>
                </small>
              </button>
            </template>
            <el-empty v-else description="暂无可审查目录" />
          </div>
        </aside>

        <article class="outline-panel code-review-panel">
          <header>
            <strong>Raw</strong>
            <div class="panel-header-actions">
              <el-tag size="small" type="warning">{{ outlineUnits.length }} 段</el-tag>
              <el-tag size="small">当前 {{ selectedOutlineUnit?.raw_char_count || 0 }} 字</el-tag>
            </div>
          </header>
          <div class="unit-meta">
            <strong>{{ selectedOutlineUnit?.path_label || selectedOutlineUnit?.title || '未选择目录' }}</strong>
            <button
              v-if="selectedOutlineUnitPage"
              class="pdf-page-link"
              type="button"
              @click="openSelectedOutlinePdfPage"
            >
              PDF P{{ selectedOutlineUnitPage }}
            </button>
          </div>
          <div ref="rawOutlineScrollRef" class="code-scroll">
            <el-skeleton v-if="outlineLoading" :rows="14" animated />
            <template v-else-if="outlineUnits.length">
              <section
                v-for="unit in outlineUnits"
                :key="`raw-${unit.id}`"
                class="outline-code-section"
                :class="{ active: unit.id === activeOutlineUnitId }"
                :data-unit-id="unit.id"
              >
                <div class="outline-code-marker">
                  <strong>{{ unit.path_label || unit.title || '未命名目录' }}</strong>
                  <span v-if="outlineUnitPageNumber(unit)">PDF Page {{ outlineUnitPageNumber(unit) }}</span>
                </div>
                <div
                  v-if="unit.raw_text"
                  class="markdown-content"
                  v-html="renderReviewMarkdown(unit.raw_text, 'raw')"
                ></div>
                <div v-else class="outline-empty-section">暂无 Raw 内容</div>
              </section>
            </template>
            <el-empty v-else description="暂无 Raw 内容" />
          </div>
        </article>

        <article class="outline-panel code-review-panel">
          <header>
            <strong>Clean</strong>
            <div class="panel-header-actions">
              <el-tag size="small" type="success">{{ outlineUnits.length }} 段</el-tag>
              <el-tag size="small" :type="cleanStatusMeta(selectedOutlineUnit?.clean_status).type">
                {{ cleanStatusMeta(selectedOutlineUnit?.clean_status).label }}
              </el-tag>
              <el-tag v-if="selectedOutlineUnit?.clean_char_count" size="small" type="success">
                {{ selectedOutlineUnit.clean_char_count }} 字
              </el-tag>
            </div>
          </header>
          <div class="unit-meta">
            <strong>{{ selectedOutlineUnit?.path_label || selectedOutlineUnit?.title || '未选择目录' }}</strong>
            <span v-if="selectedOutlineUnit?.heading_match">已匹配 Raw 标题</span>
            <button
              v-if="selectedOutlineUnitPage"
              class="pdf-page-link"
              type="button"
              @click="openSelectedOutlinePdfPage"
            >
              PDF P{{ selectedOutlineUnitPage }}
            </button>
          </div>
          <div ref="cleanOutlineScrollRef" class="code-scroll">
            <el-skeleton v-if="outlineLoading" :rows="14" animated />
            <template v-else-if="outlineUnits.length">
              <section
                v-for="unit in outlineUnits"
                :key="`clean-${unit.id}`"
                class="outline-code-section"
                :class="{ active: unit.id === activeOutlineUnitId }"
                :data-unit-id="unit.id"
              >
                <div class="outline-code-marker">
                  <strong>{{ unit.path_label || unit.title || '未命名目录' }}</strong>
                  <span>{{ cleanStatusMeta(unit.clean_status).label }}</span>
                </div>
                <div
                  v-if="unit.clean_text"
                  class="markdown-content"
                  v-html="renderReviewMarkdown(unit.clean_text, 'clean')"
                ></div>
                <div v-else class="outline-empty-section">
                  {{ unit.clean_status === 'missing' ? 'Clean 中未匹配到该 Raw 目录' : 'Clean 暂未产出' }}
                </div>
              </section>
            </template>
            <el-empty v-else :description="cleanEmptyDescription" />
          </div>
        </article>
      </div>
    </section>

    <el-dialog
      v-model="pdfEvidenceVisible"
      class="pdf-evidence-dialog"
      width="min(1080px, 92vw)"
      append-to-body
    >
      <template #header>
        <div class="pdf-evidence-title">
          <strong>{{ selectedOutlineUnit?.path_label || selectedOutlineUnit?.title || 'PDF 页图证据' }}</strong>
          <span>PDF P{{ pdfEvidencePage }}</span>
        </div>
      </template>
      <div class="pdf-evidence-toolbar">
        <el-button size="small" :disabled="pdfEvidencePage <= 1" @click="setPdfEvidencePage(pdfEvidencePage - 1)">上一页</el-button>
        <div class="pdf-evidence-pages">
          <button
            v-for="pageNumber in pdfEvidencePageCandidates"
            :key="pageNumber"
            class="pdf-evidence-page"
            :class="{ active: pageNumber === pdfEvidencePage }"
            type="button"
            @click="setPdfEvidencePage(pageNumber)"
          >
            P{{ pageNumber }}
          </button>
        </div>
        <el-button size="small" @click="setPdfEvidencePage(pdfEvidencePage + 1)">下一页</el-button>
      </div>
      <div class="pdf-evidence-body">
        <el-skeleton v-if="pdfEvidenceLoading" :rows="8" animated />
        <div v-if="pdfEvidenceError" class="pdf-evidence-error">{{ pdfEvidenceError }}</div>
        <img
          v-if="pdfEvidenceImageUrl"
          v-show="!pdfEvidenceLoading && !pdfEvidenceError"
          class="pdf-evidence-image"
          :src="pdfEvidenceImageUrl"
          :alt="`PDF page ${pdfEvidencePage}`"
          @load="handlePdfEvidenceLoad"
          @error="handlePdfEvidenceError"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import mk from 'markdown-it-katex'
import 'katex/dist/katex.min.css'
import { reviewApi } from '@/api/review'
import PdfSourceViewer from '@/components/PdfSourceViewer.vue'
import type { SourceMap } from '@/types/file'

const route = useRoute()
const md = MarkdownIt({ html: true, linkify: true, typographer: true }).use(mk)
const defaultImageRenderer = md.renderer.rules.image
md.renderer.rules.image = (tokens: any, idx: number, options: any, env: any, self: any) => {
  const token = tokens[idx]
  token.attrSet('loading', 'lazy')
  token.attrSet('decoding', 'async')
  token.attrSet('fetchpriority', 'low')
  return defaultImageRenderer
    ? defaultImageRenderer(tokens, idx, options, env, self)
    : self.renderToken(tokens, idx, options)
}
type ReviewMode = 'page' | 'outline'
type PopoViewMode = 'page' | 'tree'
type ReviewAssetStage = 'mineru' | 'popo' | 'raw' | 'clean'
const reviewMode = computed<ReviewMode>(() => route.meta.reviewMode === 'outline' ? 'outline' : 'page')
const routeAssetId = computed(() => {
  const value = route.query.asset_id || route.query.asset
  if (Array.isArray(value)) return value[0] || ''
  return value ? String(value) : ''
})
const pageTitle = computed(() => reviewMode.value === 'outline' ? '目录重建审查' : 'PDF解析审查')
const pageDescription = computed(() => reviewMode.value === 'outline'
  ? '根据重建目录联动 Raw 与 Clean，按需打开 PDF 页图证据，审查目录完整性、切分准确性和清洗继承。'
  : '基于 PDF 页面审查 MinerU 与 MinerU-Popo 输出，保留原仓库的页面溯源与对照视角。')
const searchPlaceholder = computed(() => reviewMode.value === 'outline'
  ? '搜索已到 Raw/Clean 的 material_id / 文件名'
  : '搜索已完成 MinerU+MinerU-Popo 的 material_id / manifest')
const assets = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')
const loading = ref(false)
const selectedAssetId = ref('')
const mineruContent = ref('')
const popoContent = ref('')
const popoTreeContent = ref('')
const mineruError = ref('')
const popoError = ref('')
const contentLoading = ref(false)
const fileUrl = ref('')
const sourceMap = ref<SourceMap>({ pages: [] })
const activeSourcePage = ref(1)
const activeSourceBlockId = ref('')
const mineruScrollRef = ref<HTMLElement | null>(null)
const popoScrollRef = ref<HTMLElement | null>(null)
const rawOutlineScrollRef = ref<HTMLElement | null>(null)
const cleanOutlineScrollRef = ref<HTMLElement | null>(null)
const popoViewMode = ref<PopoViewMode>('page')
const reviewStatusDraft = ref('pending')
const reviewNoteDraft = ref('')
const reviewSaving = ref(false)
const pdfEvidenceVisible = ref(false)
const pdfEvidencePage = ref(1)
const pdfEvidenceAnchorPage = ref(1)
const pdfEvidenceLoading = ref(false)
const pdfEvidenceError = ref('')
let contentLoadSeq = 0
let outlineLoadSeq = 0

interface MarkdownPageSection {
  page: number
  markdown: string
}

interface OutlineSummary {
  pdf_outline_count?: number
  raw_outline_count?: number
  raw_text_count?: number
  clean_outline_count?: number
  directory_unit_count?: number
  raw_markdown_available?: boolean
  clean_markdown_available?: boolean
  clean_extra_heading_count?: number
  outline_candidate_count?: number
  outline_decision_method?: string
  outline_llm?: Record<string, any>
  visual_candidate_count?: number
  visual_enabled?: boolean
  assigned_block_count?: number
  unassigned_block_count?: number
  missing_image_count?: number
  findings?: string[]
}

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
  raw_text?: string
  clean_text?: string
  raw_char_count?: number
  clean_char_count?: number
  raw_truncated?: boolean
  clean_truncated?: boolean
  clean_status?: string
  heading_match?: boolean
}

interface OutlineReviewData {
  summary?: OutlineSummary
  directory_units?: OutlineUnit[]
  raw_text?: Array<{ title?: string; page?: number; level?: number; text?: string }>
  clean_text?: Array<{ title?: string; page?: number; level?: number; text?: string }>
  stage_refs?: Record<string, { bucket?: string; object?: string }>
  debug_artifacts?: {
    outline_candidates_summary?: Record<string, any>
    outline_candidates_preview?: any[]
    outline_decision_summary?: Record<string, any>
    visual_decisions_summary?: Record<string, any>
    chunk_boundary_report?: Record<string, any>
    outline_apply_report?: Record<string, any>
    image_closure_report?: Record<string, any>
    by_title?: Record<string, { decisions: any[]; visual: any[]; candidates: any[]; rejected: any[] }>
  }
}

const outlineUnitPageNumber = (unit: OutlineUnit | null, fallback = 0) => {
  const pageNumber = Number(unit?.page || unit?.page_start || 0)
  return Number.isFinite(pageNumber) && pageNumber > 0 ? pageNumber : fallback
}

const selectedAsset = computed(() => assets.value.find(row => row.id === selectedAssetId.value) || null)
const mineruPageSections = computed(() => parseMarkdownPages(mineruContent.value))
const popoPageSections = computed(() => parseMarkdownPages(popoContent.value))
const outlineData = ref<OutlineReviewData | null>(null)
const outlineLoading = ref(false)
const outlineError = ref('')
const activeOutlineUnitId = ref('')
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
    raw_text: row.text || '',
    clean_text: '',
    raw_char_count: (row.text || '').length,
    clean_char_count: 0,
    clean_status: 'pending',
    heading_match: false
  }))
})
const selectedOutlineUnit = computed(() => {
  return outlineUnits.value.find(unit => unit.id === activeOutlineUnitId.value) || outlineUnits.value[0] || null
})
const selectedOutlineUnitPage = computed(() => outlineUnitPageNumber(selectedOutlineUnit.value))
const pdfEvidencePageCandidates = computed(() => {
  const anchor = Math.max(1, pdfEvidenceAnchorPage.value || pdfEvidencePage.value || 1)
  const pages = [anchor - 1, anchor, anchor + 1].filter(pageNumber => pageNumber > 0)
  if (!pages.includes(pdfEvidencePage.value)) pages.push(pdfEvidencePage.value)
  return Array.from(new Set(pages)).sort((a, b) => a - b)
})
const pdfEvidenceImageUrl = computed(() => {
  const assetId = selectedAssetId.value
  if (!pdfEvidenceVisible.value || !assetId || !pdfEvidencePage.value) return ''
  return reviewApi.getPageImageUrl(assetId, pdfEvidencePage.value, 1200)
})
const cleanEmptyDescription = computed(() => {
  const status = selectedOutlineUnit.value?.clean_status
  if (status === 'missing') return 'Clean 中未匹配到该 Raw 目录'
  if (status === 'pending') return 'Clean 暂未产出'
  return '暂无 Clean 内容'
})

const syncReviewDraftFromSelected = () => {
  const asset = selectedAsset.value
  reviewStatusDraft.value = asset?.review_status || 'pending'
  reviewNoteDraft.value = asset?.review_note || ''
}

const saveReviewMetadata = async () => {
  const asset = selectedAsset.value
  if (!asset?.id) return
  reviewSaving.value = true
  try {
    const updated = await reviewApi.updateMetadata(asset.id, {
      review_status: reviewStatusDraft.value,
      review_tags: [],
      review_note: reviewNoteDraft.value
    })
    assets.value = assets.value.map(row => row.id === updated.id ? { ...row, ...updated } : row)
    ElMessage.success('审查结论已保存')
  } catch {
    ElMessage.error('保存审查结论失败')
  } finally {
    reviewSaving.value = false
  }
}

const reviewScrollLockClass = 'luceon-review-scroll-lock'
const reviewWheelTargetSelector = '.pdf-source-scroll, .markdown-scroll, .outline-scroll, .code-scroll'
let reviewScrollResetTimer: number | undefined

const resetReviewPageScroll = () => {
  window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
  document.documentElement.scrollTop = 0
  document.body.scrollTop = 0
  const layout = document.querySelector('.mineru-layout')
  if (layout instanceof HTMLElement) layout.scrollTop = 0
}

const lockReviewPageScroll = () => {
  resetReviewPageScroll()
  document.documentElement.classList.add(reviewScrollLockClass)
  document.body.classList.add(reviewScrollLockClass)
  window.requestAnimationFrame(resetReviewPageScroll)
  if (reviewScrollResetTimer) window.clearInterval(reviewScrollResetTimer)
  const startedAt = Date.now()
  reviewScrollResetTimer = window.setInterval(() => {
    resetReviewPageScroll()
    if (Date.now() - startedAt > 2500 && reviewScrollResetTimer) {
      window.clearInterval(reviewScrollResetTimer)
      reviewScrollResetTimer = undefined
    }
  }, 100)
}

const unlockReviewPageScroll = () => {
  if (reviewScrollResetTimer) {
    window.clearInterval(reviewScrollResetTimer)
    reviewScrollResetTimer = undefined
  }
  document.documentElement.classList.remove(reviewScrollLockClass)
  document.body.classList.remove(reviewScrollLockClass)
}

const normalizeWheelDelta = (delta: number, mode: number) => {
  if (mode === WheelEvent.DOM_DELTA_LINE) return delta * 16
  if (mode === WheelEvent.DOM_DELTA_PAGE) return delta * window.innerHeight
  return delta
}

const handleReviewWheel = (event: WheelEvent) => {
  const target = event.target instanceof Element
    ? event.target.closest(reviewWheelTargetSelector)
    : null

  if (!(target instanceof HTMLElement)) return

  const deltaY = normalizeWheelDelta(event.deltaY, event.deltaMode)
  const deltaX = normalizeWheelDelta(event.deltaX, event.deltaMode)
  const canScrollY = deltaY > 0
    ? target.scrollTop + target.clientHeight < target.scrollHeight - 1
    : deltaY < 0 && target.scrollTop > 0
  const canScrollX = deltaX > 0
    ? target.scrollLeft + target.clientWidth < target.scrollWidth - 1
    : deltaX < 0 && target.scrollLeft > 0

  if (!canScrollY && !canScrollX) return

  event.preventDefault()
  event.stopPropagation()
  event.stopImmediatePropagation()

  target.scrollTop += deltaY
  target.scrollLeft += deltaX
}

const displayFilename = (row: any) => row?.input_filename || row?.filename || row?.title || '未命名 PDF'

const rewriteReviewImageUrls = (markdown: string, stage: ReviewAssetStage) => {
  const assetId = selectedAssetId.value
  if (!assetId || !markdown) return markdown
  return markdown.replace(/!\[([^\]]*)\]\(([^)\n]+)\)/g, (match, alt: string, rawUrl: string) => {
    const url = rawUrl.trim().replace(/^<|>$/g, '')
    if (/^(https?:|data:|blob:|\/api\/)/i.test(url)) return match
    const proxied = `/api/review/assets/${assetId}/artifact?stage=${stage}&path=${encodeURIComponent(url)}`
    return `![${alt}](${proxied})`
  })
}

const renderReviewMarkdown = (markdown: string, stage: ReviewAssetStage) => {
  return md.render(rewriteReviewImageUrls(markdown || '', stage))
}

const assetMatchesReviewMode = (row: any) => {
  if (!row) return false
  if (reviewMode.value === 'outline') return Boolean(row.has_raw || row.has_clean || row.has_raw_dry_run)
  return Boolean(row.has_manifest && !['raw', 'clean'].includes(row.review_stage))
}

const statusMeta = (status = 'pending') => {
  const map: Record<string, { label: string; type: 'primary' | 'success' | 'warning' | 'danger' | 'info' }> = {
    pending: { label: '待审查', type: 'info' },
    pass: { label: '通过', type: 'success' },
    needs_fix: { label: '需修正', type: 'warning' },
    reject: { label: '退回', type: 'danger' }
  }
  return map[status] || map.pending
}

const stageMeta = (stage = 'parse') => {
  const map: Record<string, { label: string; type: 'primary' | 'success' | 'warning' | 'danger' | 'info' }> = {
    parse: { label: '解析', type: 'primary' },
    input: { label: 'Input', type: 'info' },
    mineru_done: { label: 'MinerU', type: 'primary' },
    popo_done: { label: 'Popo', type: 'primary' },
    raw_done: { label: 'Raw', type: 'warning' },
    clean_stale: { label: 'Clean 失效', type: 'warning' },
    clean_done: { label: 'Clean', type: 'success' },
    raw: { label: 'Raw', type: 'warning' },
    clean: { label: 'Clean', type: 'success' }
  }
  return map[stage] || { label: stage, type: 'info' }
}

const cleanStatusMeta = (status = 'pending') => {
  const map: Record<string, { label: string; type: 'primary' | 'success' | 'warning' | 'danger' | 'info' }> = {
    matched: { label: '已匹配', type: 'success' },
    missing: { label: '缺失', type: 'danger' },
    pending: { label: '待 Clean', type: 'info' }
  }
  return map[status] || map.pending
}

const loadAssets = async () => {
  loading.value = true
  try {
    const res = await reviewApi.getAssets({
      page: page.value,
      page_size: pageSize.value,
      search: search.value,
      view: reviewMode.value
    })
    assets.value = res.files
    total.value = res.total
    const requestedAssetId = routeAssetId.value
    let nextSelected = requestedAssetId ? assets.value.find(row => row.id === requestedAssetId) : null
    if (requestedAssetId && !nextSelected) {
      try {
        const requestedAsset = await reviewApi.getAsset(requestedAssetId)
        if (assetMatchesReviewMode(requestedAsset)) {
          assets.value = [requestedAsset, ...assets.value.filter(row => row.id !== requestedAsset.id)]
          nextSelected = requestedAsset
        }
      } catch {
        // The list can still fall back to the first reviewable asset.
      }
    }
    if (!nextSelected) {
      nextSelected = assets.value.find(row => row.id === selectedAssetId.value) || assets.value[0]
    }
    if (nextSelected) {
      selectedAssetId.value = nextSelected.id
      if (reviewMode.value === 'page') {
        void loadSelectedContent(nextSelected.id)
      } else {
        void loadSelectedOutline(nextSelected.id)
      }
    } else {
      clearSelectedContent()
    }
  } catch {
    ElMessage.error('获取审查列表失败')
  } finally {
    loading.value = false
  }
}

const clearSelectedContent = () => {
  selectedAssetId.value = ''
  mineruContent.value = ''
  popoContent.value = ''
  popoTreeContent.value = ''
  mineruError.value = ''
  popoError.value = ''
  fileUrl.value = ''
  sourceMap.value = { pages: [] }
  activeSourcePage.value = 1
  activeSourceBlockId.value = ''
  popoViewMode.value = 'page'
  outlineData.value = null
  outlineError.value = ''
  outlineLoading.value = false
  activeOutlineUnitId.value = ''
}

const selectAsset = (row: any) => {
  if (!row?.id || !assetMatchesReviewMode(row)) return
  selectedAssetId.value = row.id
  if (reviewMode.value === 'page') {
    void loadSelectedContent(row.id)
  } else {
    void loadSelectedOutline(row.id)
  }
}

const handleSelectedAssetChange = (assetId: string) => {
  const row = assets.value.find(item => item.id === assetId)
  if (row) selectAsset(row)
}

const loadSelectedContent = async (assetId: string) => {
  const seq = ++contentLoadSeq
  contentLoading.value = true
  mineruContent.value = ''
  popoContent.value = ''
  popoTreeContent.value = ''
  mineruError.value = ''
  popoError.value = ''
  fileUrl.value = reviewApi.getContentUrl(assetId)
  sourceMap.value = { pages: [] }
  activeSourcePage.value = 1
  activeSourceBlockId.value = ''
  popoViewMode.value = 'page'
  const [sourceMapResult, mineruResult, popoPageResult, popoTreeResult] = await Promise.allSettled([
    reviewApi.getSourceMap(assetId),
    reviewApi.getParsedContent(assetId, 'markdown_page'),
    reviewApi.getParsedContent(assetId, 'popo_page'),
    reviewApi.getParsedContent(assetId, 'popo')
  ])
  if (seq !== contentLoadSeq) return

  if (sourceMapResult.status === 'fulfilled') {
    sourceMap.value = sourceMapResult.value || { pages: [] }
    activeSourceBlockId.value = sourceMap.value.pages[0]?.blocks[0]?.id || ''
  }
  if (mineruResult.status === 'fulfilled') {
    mineruContent.value = mineruResult.value
  } else {
    mineruError.value = mineruResult.reason?.response?.data?.detail || 'MinerU Markdown 不可用'
  }
  if (popoPageResult.status === 'fulfilled') {
    popoContent.value = popoPageResult.value
  } else {
    popoError.value = popoPageResult.reason?.response?.data?.detail || 'Popo 按页结果不可用'
  }
  if (popoTreeResult.status === 'fulfilled') {
    popoTreeContent.value = popoTreeResult.value
  }
  contentLoading.value = false
  await nextTick()
  scrollMarkdownToPage(activeSourcePage.value)
}

const loadSelectedOutline = async (assetId: string) => {
  const seq = ++outlineLoadSeq
  outlineLoading.value = true
  outlineError.value = ''
  outlineData.value = null
  activeOutlineUnitId.value = ''
  fileUrl.value = ''
  sourceMap.value = { pages: [] }
  activeSourcePage.value = 1
  activeSourceBlockId.value = ''
  try {
    const outlineResult = await reviewApi.getOutlineReview(assetId)
    if (seq !== outlineLoadSeq || selectedAssetId.value !== assetId) return
    outlineData.value = outlineResult
    await nextTick()
    activeOutlineUnitId.value = outlineUnits.value[0]?.id || ''
    syncOutlineUnitPage(selectedOutlineUnit.value)
    await nextTick()
    rawOutlineScrollRef.value?.scrollTo({ top: 0 })
    cleanOutlineScrollRef.value?.scrollTo({ top: 0 })
  } catch (e: any) {
    if (seq !== outlineLoadSeq || selectedAssetId.value !== assetId) return
    outlineError.value = e?.response?.data?.detail || '目录审查数据不可用'
  } finally {
    if (seq === outlineLoadSeq && selectedAssetId.value === assetId) {
      outlineLoading.value = false
    }
  }
}

const syncOutlineUnitPage = (unit: OutlineUnit | null) => {
  const pageNumber = outlineUnitPageNumber(unit, 1)
  activeSourcePage.value = pageNumber
  activeSourceBlockId.value = ''
}

const outlinePdfPageUrl = (pageNumber: number) => {
  const assetId = selectedAssetId.value
  if (!assetId || !pageNumber) return ''
  return reviewApi.getPageImageUrl(assetId, pageNumber, 1200)
}

const setPdfEvidencePage = (pageNumber: number) => {
  const nextPage = Math.max(1, Number(pageNumber) || 1)
  pdfEvidencePage.value = nextPage
  pdfEvidenceLoading.value = true
  pdfEvidenceError.value = ''
}

const openSelectedOutlinePdfPage = () => {
  const pageNumber = selectedOutlineUnitPage.value
  const url = outlinePdfPageUrl(pageNumber)
  if (!url) return
  pdfEvidenceAnchorPage.value = pageNumber
  setPdfEvidencePage(pageNumber)
  pdfEvidenceVisible.value = true
}

const handlePdfEvidenceLoad = () => {
  pdfEvidenceLoading.value = false
  pdfEvidenceError.value = ''
}

const handlePdfEvidenceError = () => {
  pdfEvidenceLoading.value = false
  pdfEvidenceError.value = 'PDF 页图加载失败'
}

const scrollOutlinePaneToUnit = (container: HTMLElement | null, unitId: string) => {
  if (!container || !unitId) return
  const target = Array.from(container.querySelectorAll<HTMLElement>('[data-unit-id]'))
    .find((section) => section.dataset.unitId === unitId)
  if (!target) return
  const containerRect = container.getBoundingClientRect()
  const targetRect = target.getBoundingClientRect()
  container.scrollTo({
    top: Math.max(0, container.scrollTop + targetRect.top - containerRect.top - 8),
    behavior: 'auto'
  })
}

const selectOutlineUnit = async (unitId: string) => {
  activeOutlineUnitId.value = unitId
  await nextTick()
  syncOutlineUnitPage(selectedOutlineUnit.value)
  scrollOutlinePaneToUnit(rawOutlineScrollRef.value, unitId)
  scrollOutlinePaneToUnit(cleanOutlineScrollRef.value, unitId)
}

const parseMarkdownPages = (content: string): MarkdownPageSection[] => {
  const matches = Array.from(content.matchAll(/^#\s+Page\s+(\d+)\s*$/gim))
  if (!matches.length) return []

  return matches
    .map((match, index) => {
      const pageNumber = Number(match[1])
      const bodyStart = (match.index ?? 0) + match[0].length
      const nextStart = matches[index + 1]?.index ?? content.length
      return {
        page: pageNumber,
        markdown: content.slice(bodyStart, nextStart).trim()
      }
    })
    .filter(section => Number.isFinite(section.page))
}

const scrollContainerToPage = (container: HTMLElement | null, pageNumber: number) => {
  if (!container) return
  const target = container.querySelector(`[data-page="${pageNumber}"]`) as HTMLElement | null
  if (target) {
    const containerRect = container.getBoundingClientRect()
    const targetRect = target.getBoundingClientRect()
    container.scrollTo({
      top: Math.max(0, container.scrollTop + targetRect.top - containerRect.top - 8),
      behavior: 'auto'
    })
  }
}

const scrollMarkdownToPage = (pageNumber: number) => {
  void nextTick(() => {
    scrollContainerToPage(mineruScrollRef.value, pageNumber)
    if (popoViewMode.value === 'page') {
      scrollContainerToPage(popoScrollRef.value, pageNumber)
    }
  })
}

const setPopoViewMode = async (mode: PopoViewMode) => {
  popoViewMode.value = mode
  await nextTick()
  if (mode === 'page') {
    scrollMarkdownToPage(activeSourcePage.value)
  } else {
    popoScrollRef.value?.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const handlePdfPageChange = (pageNumber: number) => {
  const pageChanged = activeSourcePage.value !== pageNumber
  activeSourcePage.value = pageNumber
  if (pageChanged) {
    activeSourceBlockId.value = sourceMap.value.pages.find(page => page.page === pageNumber)?.blocks[0]?.id || ''
  }
  scrollMarkdownToPage(pageNumber)
}

const handlePdfBlockSelect = (pageNumber: number, blockId: string) => {
  activeSourcePage.value = pageNumber
  activeSourceBlockId.value = blockId
  scrollMarkdownToPage(pageNumber)
}

watch([page, pageSize], loadAssets)
watch(selectedAsset, syncReviewDraftFromSelected, { immediate: true })
watch(routeAssetId, async () => {
  page.value = 1
  await loadAssets()
})
watch(reviewMode, async () => {
  lockReviewPageScroll()
  page.value = 1
  clearSelectedContent()
  await loadAssets()
})
onMounted(() => {
  lockReviewPageScroll()
  void loadAssets()
})
onBeforeUnmount(unlockReviewPageScroll)
</script>

<style scoped>
:global(html.luceon-review-scroll-lock),
:global(body.luceon-review-scroll-lock) {
  height: 100%;
  overflow: hidden;
}

:global(body.luceon-review-scroll-lock .main-area),
:global(body.luceon-review-scroll-lock .content-area),
:global(body.luceon-review-scroll-lock .content-wrapper) {
  overflow: hidden !important;
  overscroll-behavior: none;
  overflow-anchor: none;
}

:global(body.luceon-review-scroll-lock .mineru-layout) {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  overscroll-behavior: none;
  overflow-anchor: none;
}

.review-page {
  flex: 1;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
  overflow: hidden;
  overscroll-behavior: none;
  overflow-anchor: none;
}

.review-header {
  flex-shrink: 0;
}

.review-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
}

.review-header p {
  margin: 0;
  color: var(--text-secondary);
}

.review-list {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 18px;
}

.pdf-trace-workbench {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
}

.trace-toolbar {
  flex-shrink: 0;
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
  flex-shrink: 0;
  min-height: 36px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 2px;
}

.selected-asset-strip strong {
  min-width: 0;
  color: var(--text-primary);
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-asset-strip span {
  min-width: 0;
  color: var(--text-muted);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.review-decision-bar {
  flex-shrink: 0;
  min-height: 36px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
}

.review-status-select {
  width: 112px;
  flex-shrink: 0;
}

.review-note-input {
  min-width: 160px;
  flex: 1;
}

.trace-grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(320px, 1.05fr) minmax(260px, 1fr) minmax(260px, 1fr);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--bg-primary);
}

.outline-workbench {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
}

.outline-toolbar {
  flex-shrink: 0;
}

.outline-strip {
  flex-wrap: wrap;
}

.outline-grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns:
    minmax(240px, 0.72fr)
    minmax(360px, 1.14fr)
    minmax(360px, 1.14fr);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--bg-primary);
}

.outline-panel {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.outline-panel + .outline-panel {
  border-left: 1px solid var(--border-light);
}

.outline-panel header {
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-secondary);
}

.outline-panel header strong {
  color: var(--text-primary);
  font-size: 14px;
}

.outline-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 0 12px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-muted);
  font-size: 12px;
}

.outline-scroll,
.code-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
  overscroll-behavior: contain;
  overflow-anchor: none;
}

.outline-scroll {
  padding: 6px;
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
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 11px;
}

.unit-meta {
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 14px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-primary);
}

.unit-meta strong {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.unit-meta span {
  color: var(--text-muted);
  font-size: 12px;
}

.pdf-page-link {
  flex-shrink: 0;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 0 8px;
  color: var(--primary-color);
  background: var(--bg-primary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast);
}

.pdf-page-link:hover {
  border-color: color-mix(in srgb, var(--primary-color) 38%, var(--border-light));
  background: color-mix(in srgb, var(--primary-color) 8%, var(--bg-primary));
}

:global(.pdf-evidence-dialog .el-dialog__body) {
  padding-top: 0;
}

.pdf-evidence-title {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.pdf-evidence-title strong {
  min-width: 0;
  overflow: hidden;
  color: var(--text-primary);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pdf-evidence-title span {
  flex-shrink: 0;
  color: var(--text-muted);
  font-size: 12px;
}

.pdf-evidence-toolbar {
  min-height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid var(--border-light);
  padding: 0 0 10px;
}

.pdf-evidence-pages {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pdf-evidence-page {
  height: 28px;
  min-width: 46px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.pdf-evidence-page.active {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: color-mix(in srgb, var(--primary-color) 9%, var(--bg-primary));
}

.pdf-evidence-body {
  position: relative;
  min-height: 420px;
  max-height: min(74vh, 900px);
  overflow: auto;
  overscroll-behavior: contain;
  padding: 14px;
  background: var(--bg-secondary);
}

.pdf-evidence-image {
  display: block;
  width: min(100%, 1200px);
  height: auto;
  margin: 0 auto;
  border-radius: var(--radius-sm);
  background: #fff;
  box-shadow: 0 1px 2px rgb(0 0 0 / 8%), 0 14px 36px rgb(0 0 0 / 10%);
}

.pdf-evidence-error {
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--danger-color);
  font-size: 13px;
}

.outline-code-section {
  border-left: 3px solid transparent;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-primary);
  transition: background var(--transition-fast), border-color var(--transition-fast);
}

.outline-code-section.active {
  border-left-color: var(--primary-color);
  background: color-mix(in srgb, var(--primary-tint) 28%, var(--bg-primary));
}

.outline-code-marker {
  position: sticky;
  top: 0;
  z-index: 1;
  min-height: 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 7px 13px;
  border-bottom: 1px solid var(--border-light);
  background: color-mix(in srgb, var(--bg-primary) 94%, transparent);
  color: var(--text-muted);
  font-size: 12px;
}

.outline-code-marker strong {
  min-width: 0;
  overflow: hidden;
  color: var(--text-primary);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.outline-code-marker span {
  flex-shrink: 0;
}

.outline-empty-section {
  min-height: 92px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px;
  color: var(--text-muted);
  font-size: 13px;
}

.trace-panel {
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: var(--bg-primary);
}

.trace-panel + .trace-panel {
  border-left: 1px solid var(--border-light);
}

.pdf-panel {
  display: flex;
  min-height: 0;
}

.pdf-panel :deep(.pdf-source-viewer) {
  width: 100%;
  height: 100%;
  min-height: 0;
  border: 0;
  border-radius: 0;
}

.markdown-panel {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.markdown-panel + .markdown-panel {
  border-left: 1px solid var(--border-light);
}

.markdown-panel header {
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-secondary);
}

.markdown-panel header strong {
  color: var(--text-primary);
  font-size: 14px;
}

.panel-header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.panel-mode {
  height: 26px;
  padding: 0 9px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.panel-mode:hover {
  color: var(--text-primary);
  background: var(--bg-primary);
}

.panel-mode.active {
  border-color: var(--border-light);
  background: var(--bg-primary);
  color: var(--primary-color);
}

.markdown-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
  overscroll-behavior: contain;
  overflow-anchor: none;
  background: var(--bg-primary);
}

.markdown-page-section {
  border-left: 3px solid transparent;
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.markdown-page-section.active {
  border-left-color: var(--primary-color);
  background: var(--primary-tint);
}

.markdown-page-marker {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border-light);
  background: color-mix(in srgb, var(--bg-primary) 94%, transparent);
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 700;
}

.markdown-code {
  margin: 0;
  padding: 16px;
  color: var(--text-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.markdown-content {
  padding: 14px 16px;
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.58;
  word-break: break-word;
}

.markdown-content :deep(p) {
  margin: 0.45em 0;
}

.markdown-content :deep(img) {
  display: block;
  max-width: 100%;
  max-height: 360px;
  margin: 8px 0;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  object-fit: contain;
}

.markdown-content :deep(table) {
  width: 100%;
  display: block;
  overflow-x: auto;
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 12px;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid var(--border-light);
  padding: 5px 7px;
  vertical-align: top;
}

.markdown-content :deep(pre) {
  overflow-x: auto;
  padding: 10px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}

.markdown-content :deep(.katex-display) {
  overflow-x: auto;
}

.markdown-panel :deep(.el-empty) {
  height: 100%;
}

.review-list-toolbar {
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.review-list-toolbar .el-input {
  max-width: 420px;
}

.tag-cell {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
}

.view-cell {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
}

.muted {
  color: var(--text-muted);
  font-size: 12px;
}

.review-pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

@media (max-width: 900px) {
  .review-page {
    height: auto;
    overflow: visible;
  }

  .trace-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .trace-toolbar .el-input,
  .asset-select {
    max-width: none;
    width: 100%;
  }

  .trace-grid {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .pdf-trace-workbench,
  .outline-workbench {
    height: auto;
    overflow: visible;
  }

  .outline-grid {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .trace-panel {
    min-height: 420px;
  }

  .outline-panel {
    min-height: 360px;
  }

  .trace-panel + .trace-panel {
    border-left: 0;
    border-top: 1px solid var(--border-light);
  }

  .outline-panel + .outline-panel {
    border-left: 0;
    border-top: 1px solid var(--border-light);
  }

  .markdown-panel + .markdown-panel {
    border-left: 0;
    border-top: 1px solid var(--border-light);
  }
}
</style>
