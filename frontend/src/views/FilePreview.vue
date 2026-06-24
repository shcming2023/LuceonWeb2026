<template>
  <div class="preview-wrapper">
    <!-- 侧边文件列表 -->
    <aside class="preview-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="sidebar-title" v-show="!sidebarCollapsed">
          <el-icon><FolderOpened /></el-icon>
          <span>文件列表</span>
        </div>
        <el-button 
          class="collapse-btn" 
          link 
          @click="sidebarCollapsed = !sidebarCollapsed"
        >
          <el-icon :size="18">
            <component :is="sidebarCollapsed ? Expand : Fold" />
          </el-icon>
        </el-button>
      </div>
      
      <template v-if="!sidebarCollapsed">
        <el-input 
          v-model="fileSearch" 
          placeholder="搜索文件..." 
          size="small" 
          class="sidebar-search" 
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-scrollbar class="sidebar-list">
          <div 
            v-for="file in filteredFiles" 
            :key="file.id" 
            class="sidebar-file"
            :class="{ active: currentFile && file.id === currentFile.id }"
            @click="selectFile(file)"
          >
            <el-icon class="file-icon"><Document /></el-icon>
            <span class="file-name">{{ file.filename }}</span>
          </div>
        </el-scrollbar>
        
        <div class="sidebar-pagination">
          <el-pagination
            v-model:current-page="sidebarPage"
            v-model:page-size="sidebarPageSize"
            :total="sidebarTotal"
            :page-sizes="[10, 20, 50]"
            layout="prev, pager, next"
            size="small"
            :pager-count="3"
          />
        </div>
      </template>
    </aside>

    <!-- 主内容区 -->
    <main class="preview-main">
      <!-- 顶部工具栏 -->
      <header class="preview-header">
        <div class="header-left">
          <span class="current-file-name">{{ currentFile?.input_filename || currentFile?.filename || '未选择文件' }}</span>
        </div>
        <div class="header-center">
          <div class="view-toggle">
            <button
              class="toggle-btn"
              :class="{ active: viewMode === 'origin' }"
              @click="setViewMode('origin')"
            >
              <el-icon><Document /></el-icon>
              <span>原文件</span>
            </button>
            <button 
              class="toggle-btn" 
              :class="{ active: viewMode === 'both' }"
              @click="setViewMode('both')"
            >
              <el-icon><Document /></el-icon>
              <span>左右对照</span>
            </button>
            <button 
              class="toggle-btn" 
              :class="{ active: viewMode === 'markdown' }"
              @click="setViewMode('markdown')"
            >
              <el-icon><EditPen /></el-icon>
              <span>Markdown</span>
            </button>
          </div>
        </div>
        <div class="header-right">
          <el-button v-if="isReviewMode" @click="openReviewDrawer">
            <el-icon><EditPen /></el-icon>
            <span>审查记录</span>
          </el-button>
          <el-dropdown @command="handleExport">
            <el-button type="primary">
              <el-icon><Download /></el-icon>
              <span>下载</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="(name, format) in ExportFormatNames" :key="format" :command="format">
                  {{ name }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 预览内容区 -->
      <div class="preview-content">
        <!-- 原文件预览 -->
        <div 
          v-if="viewMode !== 'markdown' && markdownVariant !== 'compare'"
          class="preview-panel origin-panel"
          :class="{ 'full-width': viewMode === 'origin' }"
        >
          <div class="panel-content">
            <div v-if="loadingOrigin" class="loading-state">
              <el-icon class="is-loading" :size="32"><Loading /></el-icon>
              <span>正在加载原文件...</span>
            </div>
            <el-empty v-else-if="originLoadError" :description="originLoadError" :image-size="100">
              <el-button type="primary" @click="reloadOriginPreview">重试</el-button>
            </el-empty>
            <template v-else-if="showOrigin && currentFile">
              <template v-if="isPdf(currentFile.filename)">
                <PdfSourceViewer
                  v-if="fileUrl"
                  ref="pdfViewerRef"
                  :url="fileUrl"
                  :source-map="filteredSourceMap"
                  :active-page="activeSourcePage"
                  :active-block-id="activeSourceBlockId"
                  @page-change="handlePdfPageChange"
                  @block-select="handlePdfBlockSelect"
                />
                <el-empty v-else description="原文件暂不可预览" :image-size="100" />
              </template>
              <template v-else-if="isOffice(currentFile.filename)">
                <div v-if="loadingOffice" class="loading-state">
                  <el-icon class="is-loading" :size="32"><Loading /></el-icon>
                  <span>正在加载预览...</span>
                </div>
                <div v-else class="office-preview" v-html="officeContent"></div>
              </template>
              <template v-else-if="isImage(currentFile.filename)">
                <img v-if="fileUrl" :src="fileUrl" class="image-preview" />
                <el-empty v-else description="原文件暂不可预览" :image-size="100" />
              </template>
              <template v-else-if="isText(currentFile.filename)">
                <el-scrollbar>
                  <pre class="text-preview">{{ textContent }}</pre>
                </el-scrollbar>
              </template>
              <template v-else>
                <el-empty description="暂不支持该类型文件预览" :image-size="100" />
              </template>
            </template>
          </div>
        </div>

        <!-- Markdown预览 -->
        <div 
          v-if="viewMode !== 'origin'" 
          class="preview-panel markdown-panel"
          :class="{ 'full-width': viewMode === 'markdown' || markdownVariant === 'compare' }"
        >
          <div class="panel-content">
            <div v-if="isPdf(currentFile?.filename)" class="pdf-review-bar">
              <div class="pdf-review-title">
                <span>{{ markdownVariant === 'compare' ? 'OCR / Popo 对照' : markdownVariant === 'outline' ? '目录审查' : 'Markdown 预览' }}</span>
                <small>
                  {{ markdownVariant === 'compare' ? '原始 OCR 结果 / Popo 增强结果' : markdownVariant === 'outline' ? `目录单元 ${directoryUnits.length}` : `Page ${activeSourcePage} / ${pageSections.length || 0}` }}
                </small>
              </div>
              <div class="pdf-review-actions">
                <button
                  v-for="(name, variant) in pdfMarkdownVariantNames"
                  :key="variant"
                  class="pdf-review-mode"
                  :class="{ active: markdownVariant === variant }"
                  @click="handleMarkdownVariant(variant)"
                >
                  {{ name }}
                </button>
                <span v-if="markdownVariant !== 'compare'" class="source-trace-chip">{{ sourceTraceLabel }}</span>
              </div>
              <div v-if="markdownVariant !== 'compare' && sourceBlockTotal" class="source-type-filters">
                <button
                  v-for="option in sourceTypeFilterOptions"
                  :key="option.key"
                  class="source-type-filter"
                  :class="{ active: activeSourceTypeFilter === option.key }"
                  type="button"
                  @click="setSourceTypeFilter(option.key)"
                >
                  <span>{{ option.label }}</span>
                  <small>{{ sourceTypeFilterCount(option.key) }}</small>
                </button>
              </div>
            </div>
            <div v-else class="markdown-toolbar">
              <button
                v-for="(name, variant) in markdownVariantNames"
                :key="variant"
                class="markdown-tab"
                :class="{ active: markdownVariant === variant }"
                @click="handleMarkdownVariant(variant as MarkdownViewVariant)"
              >
                {{ name }}
              </button>
            </div>
            <div v-if="loading" class="loading-state">
              <el-icon class="is-loading" :size="32"><Loading /></el-icon>
              <span>加载中...</span>
            </div>
            <el-empty v-else-if="markdownLoadError" :description="markdownLoadError" :image-size="100">
              <el-button type="primary" @click="fetchParsedContent">重试</el-button>
            </el-empty>
            <div v-else-if="markdownVariant === 'outline'" class="outline-review">
              <div class="outline-summary">
                <div class="outline-metric">
                  <span>PDF 目录线索</span>
                  <strong>{{ outlineReview?.summary?.pdf_outline_count || 0 }}</strong>
                </div>
                <div class="outline-metric">
                  <span>目录单元</span>
                  <strong>{{ outlineReview?.summary?.directory_unit_count || 0 }}</strong>
                </div>
                <div class="outline-metric">
                  <span>Raw 可审</span>
                  <strong>{{ outlineReview?.summary?.raw_markdown_available ? '是' : '否' }}</strong>
                </div>
                <div class="outline-metric">
                  <span>Clean 可审</span>
                  <strong>{{ outlineReview?.summary?.clean_markdown_available ? '是' : '否' }}</strong>
                </div>
              </div>
              <div v-if="outlineReview?.summary?.findings?.length" class="outline-findings">
                <el-tag v-for="finding in outlineReview.summary.findings" :key="finding" type="warning">
                  {{ finding }}
                </el-tag>
              </div>
              <div class="directory-review-layout">
                <section class="directory-tree-panel">
                  <header>
                    <span>目录单元</span>
                    <small>按 Raw 标题切分，点击后联动左侧 PDF</small>
                  </header>
                  <div v-if="directoryUnits.length" class="directory-unit-list">
                    <button
                      v-for="unit in directoryUnits"
                      :key="unit.id"
                      type="button"
                      class="directory-unit"
                      :class="{ active: selectedOutlineUnit?.id === unit.id }"
                      :style="{ paddingLeft: `${Math.min(unit.level || 1, 5) * 10}px` }"
                      @click="selectOutlineUnit(unit)"
                    >
                      <span>{{ unit.title }}</span>
                      <small>{{ pageRangeLabel(unit) }}</small>
                      <em :class="`status-${unit.clean_status || 'pending'}`">{{ outlineUnitStatusLabel(unit) }}</em>
                    </button>
                  </div>
                  <el-empty v-else description="Raw 目录单元暂不可用" :image-size="80" />
                </section>

                <section class="directory-detail-panel">
                  <template v-if="selectedOutlineUnit">
                    <header class="directory-detail-header">
                      <div>
                        <span>{{ selectedOutlineUnit.title }}</span>
                        <small>{{ selectedOutlineUnit.path_label }}</small>
                      </div>
                      <button
                        v-if="selectedOutlineUnit.page_start"
                        type="button"
                        class="outline-jump-btn"
                        @click="handleOutlinePageClick(selectedOutlineUnit.page_start)"
                      >
                        PDF {{ pageRangeLabel(selectedOutlineUnit) }}
                      </button>
                    </header>
                    <div class="directory-evidence-strip">
                      <span>Raw {{ selectedOutlineUnit.raw_char_count || 0 }} 字符</span>
                      <span>Clean {{ selectedOutlineUnit.clean_char_count || 0 }} 字符</span>
                      <span>{{ outlineUnitStatusLabel(selectedOutlineUnit) }}</span>
                    </div>
                    <div class="directory-code-columns">
                      <article class="directory-code-pane">
                        <header>
                          <span>Raw 代码</span>
                          <small>{{ stageObjectLabel(outlineReview?.stage_refs?.raw_markdown) }}</small>
                        </header>
                        <pre>{{ selectedOutlineUnit.raw_text || '该目录节点暂无 Raw 内容' }}</pre>
                      </article>
                      <article class="directory-code-pane">
                        <header>
                          <span>Clean 代码</span>
                          <small>{{ stageObjectLabel(outlineReview?.stage_refs?.clean_markdown) }}</small>
                        </header>
                        <pre>{{ selectedOutlineUnit.clean_text || 'Clean 阶段暂未产出或未匹配该目录节点' }}</pre>
                      </article>
                    </div>
                  </template>
                  <el-empty v-else description="请选择目录单元" :image-size="80" />
                </section>
              </div>
              <section class="pdf-outline-panel">
                <header>
                  <span>PDF 目录线索</span>
                  <small>用于核对原书目录页是否被 Popo2Raw 正确继承</small>
                </header>
                <div v-if="outlineReview?.pdf_outline?.length" class="pdf-outline-list">
                  <button
                    v-for="(item, index) in outlineReview.pdf_outline"
                    :key="`pdf-${index}`"
                    type="button"
                    class="pdf-outline-item"
                    @click="item.page && handleOutlinePageClick(item.page)"
                  >
                    <span>{{ item.title }}</span>
                    <small v-if="item.page">P{{ item.page }}</small>
                  </button>
                </div>
                <el-empty v-else description="未识别到 PDF 目录线索" :image-size="80" />
              </section>
              <section v-if="outlineReview?.stage_refs" class="stage-ref-panel">
                <span>Raw: {{ stageObjectLabel(outlineReview.stage_refs.raw_markdown || outlineReview.stage_refs.raw_manifest) }}</span>
                <span>Clean: {{ stageObjectLabel(outlineReview.stage_refs.clean_markdown || outlineReview.stage_refs.clean_manifest) }}</span>
              </section>
            </div>
            <div v-else-if="markdownVariant === 'compare'" class="markdown-compare">
              <section class="compare-column">
                <div class="compare-header">
                  <span>原始 OCR Markdown</span>
                  <small>MinerU 原始解析结果</small>
                </div>
                <div
                  v-if="compareMarkdownContent"
                  class="markdown-content compare-content"
                  v-html="compareRenderedMarkdown"
                ></div>
                <el-empty v-else description="Markdown 结果暂不可用" :image-size="100" />
              </section>
              <section class="compare-column">
                <div class="compare-header">
                  <span>Popo 增强 Markdown</span>
                  <small>{{ comparePopoStatusLabel }}</small>
                </div>
                <div
                  v-if="comparePopoContent"
                  class="markdown-content compare-content"
                  v-html="compareRenderedPopo"
                ></div>
                <el-empty v-else :description="comparePopoEmptyDescription" :image-size="100" />
              </section>
            </div>
            <el-empty
              v-else-if="markdownVariant === 'popo' && !parsedContent"
              :description="popoEmptyDescription"
              :image-size="100"
            />
            <div
              v-else-if="showPageLinkedMarkdown"
              ref="markdownScrollRef"
              class="markdown-pages markdown-reader-pages"
            >
              <section
                v-for="section in pageTraceSections"
                :key="section.page"
                class="markdown-page-section"
                :class="{ active: section.page === activeSourcePage }"
                :data-page="section.page"
              >
                <button
                  class="markdown-page-meta reader-page-marker"
                  type="button"
                  @click="handleMarkdownPageClick(section)"
                >
                  <span>Page {{ section.page }}</span>
                  <small>{{ sourceStatusForPage(section.page) }}</small>
                </button>
                <div v-if="section.traceBlocks.length" class="markdown-source-list">
                  <article
                    v-for="trace in section.traceBlocks"
                    :key="trace.block.id"
                    class="markdown-reader-block"
                    :class="{
                      active: trace.block.id === activeSourceBlockId,
                      'no-source-pill': trace.block.type === 'page_number'
                    }"
                    :data-source-block-id="trace.block.id"
                    tabindex="0"
                    role="button"
                    @click="handleMarkdownBlockClick(section, trace)"
                    @keydown.enter.prevent="handleMarkdownBlockClick(section, trace)"
                    @keydown.space.prevent="handleMarkdownBlockClick(section, trace)"
                  >
                    <div class="markdown-content trace-content" v-html="trace.html"></div>
                    <span
                      v-if="trace.block.type !== 'page_number'"
                      class="reader-source-pill"
                      :class="`type-${sourceTypeFilterFor(trace.block.type)}`"
                    >
                      P{{ section.page }} · {{ sourceTypeLabel(trace.block.type) }}
                    </span>
                  </article>
                </div>
                <div v-else-if="isSourceTypeFilterActive" class="markdown-filter-empty">当前类型无内容</div>
                <div v-else class="markdown-content page-content" v-html="section.html"></div>
              </section>
            </div>
            <div v-else class="markdown-content" v-html="renderedContent"></div>
          </div>
        </div>
      </div>
    </main>
    <el-drawer
      v-if="isReviewMode"
      v-model="reviewDrawerVisible"
      title="审查记录"
      size="360px"
      append-to-body
    >
      <div class="review-drawer">
        <el-form label-position="top">
          <el-form-item label="审查状态">
            <el-segmented v-model="reviewForm.review_status" :options="reviewStatusOptions" />
          </el-form-item>
          <el-form-item label="审查标签">
            <el-select
              v-model="reviewForm.review_tags"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入后回车新增标签"
            >
              <el-option v-for="tag in commonReviewTags" :key="tag" :label="tag" :value="tag" />
            </el-select>
          </el-form-item>
          <el-form-item label="审查备注">
            <el-input
              v-model="reviewForm.review_note"
              type="textarea"
              :rows="8"
              placeholder="记录缺页、表格错位、图片缺失、Popo 需复核等问题"
            />
          </el-form-item>
        </el-form>
        <div class="review-drawer-actions">
          <el-button type="primary" :loading="savingReview" @click="saveReviewMetadata">保存</el-button>
          <el-button :loading="generatingReport" @click="generateReviewReport">生成报告</el-button>
          <el-button :disabled="!currentFile?.has_report" @click="downloadReviewReport">下载报告</el-button>
        </div>
        <el-alert
          v-if="currentFile?.report_generated_at"
          type="success"
          :closable="false"
          show-icon
          :title="`报告已生成：${currentFile.report_generated_at}`"
        />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  FolderOpened, Document, Search, Download, ArrowDown, 
  EditPen, Expand, Fold, Loading 
} from '@element-plus/icons-vue'
import axios from 'axios'
import MarkdownIt from 'markdown-it'
import mk from 'markdown-it-katex'
import 'katex/dist/katex.min.css'
import mammoth from 'mammoth'
import * as XLSX from 'xlsx'
import { filesApi } from '@/api/files'
import { reviewApi } from '@/api/review'
import PdfSourceViewer from '@/components/PdfSourceViewer.vue'
import {
  ExportFormatNames,
  type ExportFormat,
  type FileItem,
  type MarkdownVariant,
  type PopoStatus,
  type PopoStatusValue,
  type SourceBlock,
  type SourceMap
} from '@/types/file'
import {
  SOURCE_TYPE_FILTER_OPTIONS,
  sourceTypeFilterFor,
  sourceTypeFilterMatches,
  sourceTypeLabel,
  type SourceTypeFilter
} from '@/utils/sourceTypes'
import {
  normalizeTraceText,
  shouldRenderTraceExcerpt,
  splitMarkdownChunks,
  traceExcerptForBlock
} from '@/utils/markdownTrace'

const route = useRoute()
const md = MarkdownIt({ html: true, linkify: true, typographer: true }).use(mk)
const isReviewMode = computed(() => route.name === 'ReviewPreview')

interface MarkdownPageSection {
  page: number
  markdown: string
  html: string
}

interface MarkdownTraceBlock {
  block: SourceBlock
  excerpt: string
  html: string
  index: number
  score: number
}

interface MarkdownTraceSection extends MarkdownPageSection {
  traceBlocks: MarkdownTraceBlock[]
}

interface StageObjectRef {
  bucket?: string
  object?: string
}

interface DirectoryUnit {
  id: string
  index: number
  title: string
  level: number
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
  clean_status?: 'matched' | 'missing' | 'pending' | string
  heading_match?: boolean
}

interface OutlineReviewPayload {
  summary?: Record<string, any>
  stage_refs?: Record<string, StageObjectRef>
  pdf_outline?: any[]
  raw_outline?: any[]
  clean_outline?: any[]
  directory_units?: DirectoryUnit[]
}

interface PdfSourceViewerRef {
  scrollToPage: (pageNumber: number) => Promise<void> | void
  scrollToBlock: (pageNumber: number, blockId: string) => Promise<void> | void
}

type MarkdownViewVariant = MarkdownVariant | 'compare' | 'outline'

const sidebarCollapsed = ref(false)
const allFiles = ref<FileItem[]>([])
const sidebarPage = ref(1)
const sidebarPageSize = ref(10)
const sidebarTotal = ref(0)
const fileSearch = ref('')
const currentFile = ref<FileItem | null>(null)
const reviewDrawerVisible = ref(false)
const savingReview = ref(false)
const generatingReport = ref(false)
const reviewForm = ref({
  review_status: 'pending',
  review_tags: [] as string[],
  review_note: ''
})
const reviewStatusOptions = [
  { label: '待审查', value: 'pending' },
  { label: '通过', value: 'pass' },
  { label: '需修正', value: 'needs_fix' },
  { label: '退回', value: 'reject' }
]
const commonReviewTags = ['表格需复核', '图片需复核', 'OCR 噪声', '缺页风险', '目录错位', '可入库']
const isReady = ref(false)
const pdfViewerRef = ref<PdfSourceViewerRef | null>(null)
const markdownScrollRef = ref<HTMLElement | null>(null)
const sourceMap = ref<SourceMap>({ pages: [] })
const sourceMapLoading = ref(false)
const sourceTypeFilterOptions = SOURCE_TYPE_FILTER_OPTIONS
const activeSourceTypeFilter = ref<SourceTypeFilter>('all')
const activeSourcePage = ref(1)
const activeSourceBlockId = ref('')
const currentPdfPage = ref(1)
let sourceMapRequestSeq = 0

// 获取侧边栏文件列表
const fetchSidebarFiles = async () => {
  try {
    const res = isReviewMode.value
      ? await reviewApi.getAssets({ page: sidebarPage.value, page_size: sidebarPageSize.value, search: fileSearch.value })
      : await filesApi.getFiles({ page: sidebarPage.value, page_size: sidebarPageSize.value, search: fileSearch.value })
    allFiles.value = res.files
    sidebarTotal.value = res.total
  } catch (e) {
    ElMessage.error(isReviewMode.value ? '获取审查列表失败' : '获取文件列表失败')
    allFiles.value = []
    sidebarTotal.value = 0
  }
}

const getPreviewApi = () => {
  return isReviewMode.value ? reviewApi : filesApi
}

const syncReviewForm = () => {
  reviewForm.value = {
    review_status: currentFile.value?.review_status || 'pending',
    review_tags: [...(currentFile.value?.review_tags || [])],
    review_note: currentFile.value?.review_note || ''
  }
}

// 根据ID获取单个文件信息
const loadFileById = async (fileId: string) => {
  try {
    const data = isReviewMode.value
      ? await reviewApi.getAsset(fileId)
      : await filesApi.getFile(fileId)
    if (data) {
      currentFile.value = data
      syncReviewForm()
    }
  } catch (e) {
    ElMessage.error(isReviewMode.value ? '获取审查资产失败' : '获取文件信息失败')
  }
}

// 监听分页变化
watch(sidebarPage, () => {
  if (isReady.value) {
    fetchSidebarFiles()
  }
})

watch([sidebarPageSize, fileSearch], () => {
  if (isReady.value) {
    sidebarPage.value = 1
    fetchSidebarFiles()
  }
})

onMounted(async () => {
  const fileId = route.params.id as string
  const pageFromQuery = Number(route.query.page) || 1
  
  // 设置初始页码
  sidebarPage.value = pageFromQuery
  
  if (fileId) {
    // 加载指定文件
    await loadFileById(fileId)
  }
  
  // 加载对应页的文件列表
  await fetchSidebarFiles()
  
  // 如果没有指定文件，选中第一个
  if (!currentFile.value && allFiles.value.length > 0) {
    currentFile.value = allFiles.value[0]
    syncReviewForm()
  }

  if (currentFile.value) {
    markdownVariant.value = preferredMarkdownVariant(currentFile.value)
  }

  // 初始化完成
  await nextTick()
  isReady.value = true

  // 如果初始视图模式需要显示 markdown，立即加载内容
  if (viewMode.value !== 'origin' && currentFile.value) {
    await fetchParsedContent()
  }
})

const filteredFiles = computed(() => allFiles.value)

const selectFile = (file: FileItem) => {
  currentFile.value = file
  syncReviewForm()
  page.value = 1
  markdownVariant.value = preferredMarkdownVariant(file)
  popoStatus.value = null
  parsedContent.value = ''
  outlineReview.value = null
  selectedOutlineUnitId.value = ''
  markdownLoadError.value = ''
  originLoadError.value = ''
  loading.value = false
  hasMore.value = true
  sourceMap.value = { pages: [] }
  activeSourceTypeFilter.value = 'all'
  activeSourcePage.value = 1
  activeSourceBlockId.value = ''
  currentPdfPage.value = 1
  if (viewMode.value !== 'origin') {
    fetchParsedContent()
  }
}

const openReviewDrawer = () => {
  syncReviewForm()
  reviewDrawerVisible.value = true
}

const saveReviewMetadata = async () => {
  if (!currentFile.value || !isReviewMode.value) return
  savingReview.value = true
  try {
    const updated = await reviewApi.updateMetadata(currentFile.value.id, reviewForm.value)
    currentFile.value = updated
    syncReviewForm()
    await fetchSidebarFiles()
    ElMessage.success('审查记录已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存审查记录失败')
  } finally {
    savingReview.value = false
  }
}

const generateReviewReport = async () => {
  if (!currentFile.value || !isReviewMode.value) return
  generatingReport.value = true
  try {
    const res = await reviewApi.generateReport(currentFile.value.id)
    currentFile.value = res.asset
    syncReviewForm()
    await fetchSidebarFiles()
    ElMessage.success('审查报告已生成')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '生成审查报告失败')
  } finally {
    generatingReport.value = false
  }
}

const downloadReviewReport = () => {
  if (!currentFile.value || !isReviewMode.value) return
  const link = document.createElement('a')
  link.href = reviewApi.getReportUrl(currentFile.value.id)
  link.download = `${currentFile.value.title || currentFile.value.filename}-review-report.md`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const showOrigin = ref(true)
const isImage = (name?: string) => name ? /\.(png|jpe?g|gif|bmp|webp)$/i.test(name) : false
const isText = (name?: string) => name ? /\.(txt|md|json|log)$/i.test(name) : false
const isWord = (name?: string) => name ? /\.(doc|docx)$/i.test(name) : false
const isExcel = (name?: string) => name ? /\.(xls|xlsx)$/i.test(name) : false
const isOffice = (name?: string) => name ? /\.(doc|docx|xls|xlsx)$/i.test(name) : false
const isPdf = (name?: string) => name ? /\.pdf$/i.test(name) : false
const preferredMarkdownVariant = (file: FileItem): MarkdownViewVariant => {
  if (isReviewMode.value && route.query.outline === '1' && file.has_manifest !== false) return 'outline'
  if (isReviewMode.value && file.has_manifest === false) return 'popo'
  if (isReviewMode.value && isPdf(file.filename)) return 'popo'
  return isPdf(file.filename) ? 'markdown_page' : 'markdown'
}

const page = ref(1)
const parsedContent = ref('')
const loading = ref(false)
const markdownLoadError = ref('')
const hasMore = ref(true)
let markdownRequestSeq = 0
const markdownVariant = ref<MarkdownViewVariant>('markdown')
const popoStatus = ref<PopoStatus | null>(null)
const compareMarkdownContent = ref('')
const comparePopoContent = ref('')
const comparePopoStatus = ref<PopoStatus | null>(null)
const outlineReview = ref<OutlineReviewPayload | null>(null)
const selectedOutlineUnitId = ref('')
const markdownVariantNames: Record<MarkdownViewVariant, string> = {
  markdown: '原始 Markdown',
  markdown_page: '按页 Markdown',
  popo: 'Popo 增强',
  compare: '对比',
  outline: '目录审查'
}
const pdfMarkdownVariantNames: Record<'markdown_page' | 'popo' | 'compare' | 'outline', string> = {
  markdown_page: '溯源阅读',
  popo: 'Popo 文本',
  compare: 'OCR-Popo 对照',
  outline: '目录审查'
}
const popoStatusNames: Record<PopoStatusValue, string> = {
  not_available: 'Popo 结果暂不可用',
  processing: 'Popo 结果生成中',
  success: 'Popo 结果可用',
  failed: 'Popo 处理失败',
  skipped: 'Popo 已跳过'
}
const popoEmptyDescription = computed(() => {
  if (!popoStatus.value) return 'Popo 结果暂不可用'
  return popoStatus.value.message || popoStatusNames[popoStatus.value.status]
})
const comparePopoEmptyDescription = computed(() => {
  if (!comparePopoStatus.value) return 'Popo 结果暂不可用'
  return comparePopoStatus.value.message || popoStatusNames[comparePopoStatus.value.status]
})
const comparePopoStatusLabel = computed(() => {
  if (comparePopoContent.value) return '可对比'
  if (!comparePopoStatus.value) return '未加载'
  return popoStatusNames[comparePopoStatus.value.status]
})
const directoryUnits = computed<DirectoryUnit[]>(() => outlineReview.value?.directory_units || [])
const selectedOutlineUnit = computed<DirectoryUnit | null>(() => {
  if (!directoryUnits.value.length) return null
  return directoryUnits.value.find((unit) => unit.id === selectedOutlineUnitId.value) || directoryUnits.value[0]
})
const pageRangeLabel = (unit: DirectoryUnit) => {
  const start = unit.page_start || unit.page
  const end = unit.page_end
  if (!start) return '无页码'
  if (end && end > start) return `P${start}-${end}`
  return `P${start}`
}
const outlineUnitStatusLabel = (unit: DirectoryUnit) => {
  if (unit.clean_status === 'matched') return 'Clean 已匹配'
  if (unit.clean_status === 'missing') return 'Clean 缺失'
  return '待 Clean'
}
const stageObjectLabel = (ref?: StageObjectRef | null) => {
  if (!ref?.object) return '未接入'
  const name = ref.object.split('/').filter(Boolean).pop()
  return name || ref.object
}
const sourceBlockTotal = computed(() => {
  return sourceMap.value.pages.reduce((total, item) => total + item.blocks.length, 0)
})
const isSourceTypeFilterActive = computed(() => activeSourceTypeFilter.value !== 'all')
const filterSourceBlocks = (blocks: SourceBlock[]) => {
  return blocks.filter((block) => sourceTypeFilterMatches(block.type, activeSourceTypeFilter.value))
}
const filteredSourceMap = computed<SourceMap>(() => {
  if (!isSourceTypeFilterActive.value) return sourceMap.value
  return {
    pages: sourceMap.value.pages.map((pageItem) => ({
      ...pageItem,
      blocks: filterSourceBlocks(pageItem.blocks)
    }))
  }
})
const filteredSourceBlockTotal = computed(() => {
  return filteredSourceMap.value.pages.reduce((total, item) => total + item.blocks.length, 0)
})
const sourceTraceLabel = computed(() => {
  if (sourceMapLoading.value) return '溯源加载中'
  if (sourceBlockTotal.value && isSourceTypeFilterActive.value) {
    return `${filteredSourceBlockTotal.value} / ${sourceBlockTotal.value} 个 bbox`
  }
  if (sourceBlockTotal.value) return `${sourceBlockTotal.value} 个 bbox`
  return '暂无 bbox'
})
const sourcePageFor = (page: number) => {
  return sourceMap.value.pages.find((item) => item.page === page)
}
const filteredSourcePageFor = (page: number) => {
  return filteredSourceMap.value.pages.find((item) => item.page === page)
}
const sourceStatusForPage = (page: number) => {
  const count = filteredSourcePageFor(page)?.blocks.length || 0
  const total = sourcePageFor(page)?.blocks.length || 0
  if (isSourceTypeFilterActive.value && total) return count ? `${count} / ${total} 个 bbox` : '无匹配'
  return total ? `${total} 个 bbox` : '无 bbox'
}
const sourceTypeFilterCount = (filter: SourceTypeFilter) => {
  if (filter === 'all') return sourceBlockTotal.value
  return sourceMap.value.pages.reduce((total, pageItem) => {
    return total + pageItem.blocks.filter((block) => sourceTypeFilterMatches(block.type, filter)).length
  }, 0)
}
const firstVisibleSourceBlock = () => {
  for (const pageItem of filteredSourceMap.value.pages) {
    const block = pageItem.blocks[0]
    if (block) return { page: pageItem.page, block }
  }
  return null
}
const activeSourceBlockVisible = () => {
  if (!activeSourceBlockId.value) return false
  return filteredSourceMap.value.pages.some((pageItem) => {
    return pageItem.blocks.some((block) => block.id === activeSourceBlockId.value)
  })
}
const setSourceTypeFilter = async (filter: SourceTypeFilter) => {
  activeSourceTypeFilter.value = filter
  await nextTick()
  if (activeSourceBlockVisible()) return

  const nextBlock = filteredSourcePageFor(activeSourcePage.value)?.blocks[0] || firstVisibleSourceBlock()?.block
  const nextPage = filteredSourcePageFor(activeSourcePage.value)?.blocks[0]
    ? activeSourcePage.value
    : firstVisibleSourceBlock()?.page
  activeSourcePage.value = nextPage || activeSourcePage.value
  currentPdfPage.value = activeSourcePage.value
  activeSourceBlockId.value = nextBlock?.id || ''
  if (nextBlock) {
    await pdfViewerRef.value?.scrollToBlock(activeSourcePage.value, nextBlock.id)
    await scrollMarkdownBlockIntoView(nextBlock.id)
  }
}
const parseMarkdownPages = (content: string): MarkdownPageSection[] => {
  const matches = Array.from(content.matchAll(/^#\s+Page\s+(\d+)\s*$/gim))
  if (!matches.length) return []

  return matches
    .map((match, index) => {
      const page = Number(match[1])
      const start = match.index ?? 0
      const bodyStart = start + match[0].length
      const nextStart = matches[index + 1]?.index ?? content.length
      const markdown = content.slice(bodyStart, nextStart).trim()
      return {
        page,
        markdown,
        html: md.render(markdown || ' ')
      }
    })
    .filter((section) => Number.isFinite(section.page))
}
const pageSections = computed(() => parseMarkdownPages(parsedContent.value || ''))
const showPageLinkedMarkdown = computed(() => {
  return markdownVariant.value === 'markdown_page' && pageSections.value.length > 0
})
const traceBlocksForSection = (section: MarkdownPageSection): MarkdownTraceBlock[] => {
  const blocks = filteredSourcePageFor(section.page)?.blocks || []
  const chunks = splitMarkdownChunks(section.markdown)
  const usedChunks = new Set<number>()
  const seenExcerpts = new Set<string>()
  const traces: MarkdownTraceBlock[] = []
  blocks.forEach((block, index) => {
    const trace = traceExcerptForBlock(block, chunks, usedChunks, {
      includeNearbyTable: sourceTypeFilterFor(block.type) === 'table'
    })
    const traceBlock = {
      block,
      excerpt: trace.excerpt,
      html: md.render(trace.excerpt || block.text || ' '),
      index: index + 1,
      score: trace.score
    }
    if (shouldRenderTraceExcerpt(traceBlock.excerpt, seenExcerpts)) {
      traces.push(traceBlock)
    }
  })
  return traces
}
const pageTraceSections = computed<MarkdownTraceSection[]>(() => {
  return pageSections.value.map((section) => ({
    ...section,
    traceBlocks: traceBlocksForSection(section)
  }))
})
const traceSectionForPage = (page: number) => {
  return pageTraceSections.value.find((section) => section.page === page)
}
const findBestBlockForSection = (section: MarkdownPageSection): SourceBlock | null => {
  const tracedBlock = traceSectionForPage(section.page)?.traceBlocks[0]?.block
  if (tracedBlock) return tracedBlock
  const blocks = filteredSourcePageFor(section.page)?.blocks || []
  if (!blocks.length) return null
  const sectionText = normalizeTraceText(section.markdown)
  if (!sectionText) return blocks[0]

  let bestBlock: SourceBlock | null = null
  let bestScore = 0
  for (const block of blocks) {
    const blockText = normalizeTraceText(block.text)
    if (!blockText) continue
    const sample = blockText.slice(0, Math.min(80, blockText.length))
    const head = sectionText.slice(0, Math.min(80, sectionText.length))
    let score = 0
    if (sample && sectionText.includes(sample)) {
      score = sample.length
    } else if (head && blockText.includes(head)) {
      score = head.length
    } else {
      score = blockText
        .split(' ')
        .filter((word) => word.length > 2 && sectionText.includes(word))
        .length
    }
    if (score > bestScore) {
      bestScore = score
      bestBlock = block
    }
  }
  return bestBlock || blocks[0]
}
const scrollMarkdownPageIntoView = async (page: number) => {
  if (!showPageLinkedMarkdown.value) return
  await nextTick()
  const target = markdownScrollRef.value?.querySelector(`[data-page="${page}"]`) as HTMLElement | null
  target?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}
const scrollMarkdownBlockIntoView = async (blockId: string) => {
  if (!showPageLinkedMarkdown.value || !blockId) return
  await nextTick()
  const target = markdownScrollRef.value?.querySelector(`[data-source-block-id="${blockId}"]`) as HTMLElement | null
  target?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
const handleMarkdownPageClick = async (section: MarkdownPageSection) => {
  const block = findBestBlockForSection(section)
  currentPdfPage.value = section.page
  activeSourcePage.value = section.page
  activeSourceBlockId.value = block?.id || ''
  if (block) {
    await pdfViewerRef.value?.scrollToBlock(section.page, block.id)
  } else {
    await pdfViewerRef.value?.scrollToPage(section.page)
  }
}
const handleMarkdownBlockClick = async (section: MarkdownTraceSection, trace: MarkdownTraceBlock) => {
  currentPdfPage.value = section.page
  activeSourcePage.value = section.page
  activeSourceBlockId.value = trace.block.id
  await pdfViewerRef.value?.scrollToBlock(section.page, trace.block.id)
}
const handlePdfBlockSelect = (page: number, blockId: string) => {
  currentPdfPage.value = page
  activeSourcePage.value = page
  activeSourceBlockId.value = blockId
  void scrollMarkdownBlockIntoView(blockId)
}
const handlePdfPageChange = (page: number) => {
  const pageChanged = activeSourcePage.value !== page
  currentPdfPage.value = page
  activeSourcePage.value = page
  if (pageChanged) {
    activeSourceBlockId.value = filteredSourcePageFor(page)?.blocks[0]?.id || ''
  }
  if (activeSourceBlockId.value) {
    void scrollMarkdownBlockIntoView(activeSourceBlockId.value)
  } else {
    void scrollMarkdownPageIntoView(page)
  }
}

const isLatestMarkdownRequest = (seq: number, fileId: string, variant: MarkdownViewVariant) => {
  return seq === markdownRequestSeq
    && currentFile.value?.id === fileId
    && markdownVariant.value === variant
}

const fetchParsedContent = async () => {
  if (!currentFile.value) return
  if (isReviewMode.value && currentFile.value.has_manifest === false) {
    parsedContent.value = ''
    markdownLoadError.value = '该 input PDF 尚未产出 manifest，暂不可溯源审查'
    return
  }
  if (markdownVariant.value === 'outline') {
    await fetchOutlineReview()
    return
  }
  if (markdownVariant.value === 'compare') {
    await fetchCompareContent()
    return
  }
  const fileId = currentFile.value.id
  const variant = markdownVariant.value as MarkdownVariant
  const seq = ++markdownRequestSeq
  loading.value = true
  markdownLoadError.value = ''
  try {
    const data = await getPreviewApi().getParsedContent(fileId, variant)
    if (!isLatestMarkdownRequest(seq, fileId, variant)) return
    parsedContent.value = data || ''
    popoStatus.value = null
  } catch (e) {
    if (!isLatestMarkdownRequest(seq, fileId, variant)) return
    parsedContent.value = ''
    if (variant === 'popo') {
      await fetchPopoStatus(fileId, seq, variant)
    } else if (isReviewMode.value) {
      try {
        const fallback = await getPreviewApi().getParsedContent(fileId, 'popo')
        if (!isLatestMarkdownRequest(seq, fileId, variant)) return
        parsedContent.value = fallback || ''
        markdownVariant.value = 'popo'
        popoStatus.value = null
        markdownLoadError.value = ''
        loading.value = false
      } catch {
        if (!isLatestMarkdownRequest(seq, fileId, variant)) return
        markdownLoadError.value = '解析内容暂不可用或加载失败'
      }
    } else {
      markdownLoadError.value = '解析内容暂不可用或加载失败'
      ElMessage.error('获取解析内容失败')
    }
  } finally {
    if (isLatestMarkdownRequest(seq, fileId, variant)) {
      loading.value = false
    }
  }
}

const fetchOutlineReview = async () => {
  if (!currentFile.value || !isReviewMode.value) return
  const fileId = currentFile.value.id
  const variant: MarkdownViewVariant = 'outline'
  const seq = ++markdownRequestSeq
  loading.value = true
  markdownLoadError.value = ''
  try {
    const data = await reviewApi.getOutlineReview(fileId)
    if (!isLatestMarkdownRequest(seq, fileId, variant)) return
    outlineReview.value = data
    const units = data?.directory_units || []
    if (!units.some((unit: DirectoryUnit) => unit.id === selectedOutlineUnitId.value)) {
      selectedOutlineUnitId.value = units[0]?.id || ''
    }
  } catch (e) {
    if (!isLatestMarkdownRequest(seq, fileId, variant)) return
    outlineReview.value = null
    markdownLoadError.value = '目录审查数据暂不可用'
  } finally {
    if (isLatestMarkdownRequest(seq, fileId, variant)) {
      loading.value = false
    }
  }
}

const selectOutlineUnit = async (unit: DirectoryUnit) => {
  selectedOutlineUnitId.value = unit.id
  const targetPage = unit.page_start || unit.page
  if (targetPage) {
    await handleOutlinePageClick(targetPage)
  }
}

const handleOutlinePageClick = async (pageNumber: number) => {
  activeSourcePage.value = pageNumber
  currentPdfPage.value = pageNumber
  await pdfViewerRef.value?.scrollToPage(pageNumber)
}

const fetchPopoStatus = async (
  fileId = currentFile.value?.id,
  seq = markdownRequestSeq,
  variant: MarkdownViewVariant = markdownVariant.value
) => {
  if (!fileId) {
    popoStatus.value = { status: 'not_available', message: '' }
    return
  }
  try {
    const res = await getPreviewApi().getPopoStatus(fileId)
    if (!isLatestMarkdownRequest(seq, fileId, variant)) return
    popoStatus.value = res || { status: 'not_available', message: '' }
  } catch (e) {
    if (!isLatestMarkdownRequest(seq, fileId, variant)) return
    popoStatus.value = { status: 'not_available', message: '' }
  }
}

const fetchVariantContent = async (fileId: string, variant: MarkdownVariant) => {
  return await getPreviewApi().getParsedContent(fileId, variant)
}

const fetchCompareContent = async () => {
  if (!currentFile.value) return
  const fileId = currentFile.value.id
  const variant: MarkdownViewVariant = 'compare'
  const seq = ++markdownRequestSeq
  loading.value = true
  markdownLoadError.value = ''
  compareMarkdownContent.value = ''
  comparePopoContent.value = ''
  comparePopoStatus.value = null
  outlineReview.value = null
  try {
    const [markdownResult, popoResult] = await Promise.allSettled([
      fetchVariantContent(fileId, 'markdown'),
      fetchVariantContent(fileId, 'popo')
    ])
    if (!isLatestMarkdownRequest(seq, fileId, variant)) return

    compareMarkdownContent.value = markdownResult.status === 'fulfilled' ? markdownResult.value : ''
    if (popoResult.status === 'fulfilled') {
      comparePopoContent.value = popoResult.value
    } else {
      try {
        const statusRes = await getPreviewApi().getPopoStatus(fileId)
        if (!isLatestMarkdownRequest(seq, fileId, variant)) return
        comparePopoStatus.value = statusRes || { status: 'not_available', message: '' }
      } catch (e) {
        if (!isLatestMarkdownRequest(seq, fileId, variant)) return
        comparePopoStatus.value = { status: 'not_available', message: '' }
      }
    }
  } finally {
    if (isLatestMarkdownRequest(seq, fileId, variant)) {
      loading.value = false
    }
  }
}

const handleMarkdownVariant = async (variant: MarkdownViewVariant) => {
  if (markdownVariant.value === variant) return
  markdownVariant.value = variant
  await fetchParsedContent()
}

const viewMode = ref<'both' | 'origin' | 'markdown'>('both')

const setViewMode = (mode: 'both' | 'origin' | 'markdown') => {
  viewMode.value = mode
}

watch(viewMode, (newMode) => {
  if (newMode !== 'origin') fetchParsedContent()
})

const handleExport = async (format: ExportFormat) => {
  if (!currentFile.value) return
  if (isReviewMode.value) {
    try {
      const res = await reviewApi.getDownloadUrl(currentFile.value.id)
      const link = document.createElement('a')
      link.href = res.url
      link.download = currentFile.value.filename
      link.target = '_blank'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch {
      ElMessage.error('下载源 PDF 失败')
    }
    return
  }
  if (currentFile.value.status !== 'parsed') {
    ElMessage.warning('解析完成后才能导出')
    return
  }
  try {
    const res = await filesApi.exportFile(currentFile.value.id, format)
    if (res.status === 'success') {
      const response = await fetch(res.download_url)
      if (!response.ok) throw new Error('download failed')
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = res.filename
      document.body.appendChild(link)
      link.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(link)
      ElMessage.success(`导出${ExportFormatNames[format]}成功`)
    } else {
      ElMessage.error(`导出失败`)
    }
  } catch (e) {
    ElMessage.error(`导出失败`)
  }
}

const fileUrl = ref('')
const textContent = ref('')
const officeContent = ref('')
const loadingOrigin = ref(false)
const loadingOffice = ref(false)
const originLoadError = ref('')

const fetchFileUrl = async () => {
  if (!currentFile.value) return
  loadingOrigin.value = true
  originLoadError.value = ''
  try {
    const res = await getPreviewApi().getDownloadUrl(currentFile.value.id)
    fileUrl.value = res.url
  } catch (e) {
    fileUrl.value = ''
    textContent.value = ''
    officeContent.value = ''
    originLoadError.value = '获取原文件地址失败'
  } finally {
    loadingOrigin.value = false
  }
}

const fetchSourceMap = async () => {
  const file = currentFile.value
  const seq = ++sourceMapRequestSeq
  if (!file || !isPdf(file.filename)) {
    sourceMap.value = { pages: [] }
    activeSourceTypeFilter.value = 'all'
    sourceMapLoading.value = false
    return
  }

  sourceMapLoading.value = true
  try {
    const data = await getPreviewApi().getSourceMap(file.id)
    if (seq !== sourceMapRequestSeq || currentFile.value?.id !== file.id) return
    sourceMap.value = data || { pages: [] }
    if (!activeSourceBlockId.value) {
      const activePageSource = filteredSourcePageFor(activeSourcePage.value)
      activeSourceBlockId.value = activePageSource?.blocks[0]?.id || filteredSourceMap.value.pages[0]?.blocks[0]?.id || ''
    }
  } catch (e) {
    if (seq !== sourceMapRequestSeq || currentFile.value?.id !== file.id) return
    sourceMap.value = { pages: [] }
  } finally {
    if (seq === sourceMapRequestSeq && currentFile.value?.id === file.id) {
      sourceMapLoading.value = false
    }
  }
}

const previewOfficeFile = async () => {
  if (!currentFile.value || !fileUrl.value) return
  loadingOffice.value = true
  try {
    const response = await fetch(fileUrl.value)
    const blob = await response.blob()
    if (isWord(currentFile.value.filename)) {
      const arrayBuffer = await blob.arrayBuffer()
      const result = await mammoth.convertToHtml({ arrayBuffer })
      officeContent.value = result.value
    } else if (isExcel(currentFile.value.filename)) {
      const arrayBuffer = await blob.arrayBuffer()
      const workbook = XLSX.read(arrayBuffer, { type: 'array' })
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
      officeContent.value = XLSX.utils.sheet_to_html(firstSheet)
    }
  } catch (e) {
    originLoadError.value = '预览 Office 文件失败，可下载原文件后查看'
    ElMessage.error('预览 Office 文件失败')
    officeContent.value = ''
  } finally {
    loadingOffice.value = false
  }
}

const fetchTextContent = async () => {
  if (!fileUrl.value) return
  try {
    const res = await axios.get(fileUrl.value)
    textContent.value = res.data
  } catch (e) {
    textContent.value = ''
    originLoadError.value = '文本预览加载失败'
  }
}

const reloadOriginPreview = async () => {
  if (!currentFile.value) return
  fileUrl.value = ''
  textContent.value = ''
  officeContent.value = ''
  originLoadError.value = ''
  activeSourcePage.value = 1
  activeSourceBlockId.value = ''
  currentPdfPage.value = 1
  if (isPdf(currentFile.value.filename)) {
    loadingOrigin.value = true
    fileUrl.value = getPreviewApi().getContentUrl(currentFile.value.id)
    await fetchSourceMap()
    loadingOrigin.value = false
  } else {
    sourceMap.value = { pages: [] }
    await fetchFileUrl()
  }
  if (isText(currentFile.value.filename)) await fetchTextContent()
  else if (isOffice(currentFile.value.filename)) await previewOfficeFile()
}

watch(currentFile, async (newFile) => {
  if (!newFile) return
  if (isReviewMode.value && newFile.has_manifest === false) {
    viewMode.value = 'origin'
  }
  fileUrl.value = ''
  textContent.value = ''
  officeContent.value = ''
  originLoadError.value = ''
  await reloadOriginPreview()
})

const renderedContent = computed(() => md.render(parsedContent.value || ''))
const compareRenderedMarkdown = computed(() => md.render(compareMarkdownContent.value || ''))
const compareRenderedPopo = computed(() => md.render(comparePopoContent.value || ''))
</script>

<style scoped>
.preview-wrapper {
  display: flex;
  min-height: 100vh;
  background: var(--bg-secondary);
}

/* 侧边栏 */
.preview-sidebar {
  width: 260px;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-normal);
  flex-shrink: 0;
}

.preview-sidebar.collapsed {
  width: 48px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--border-light);
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--text-primary);
}

.collapse-btn {
  color: var(--text-muted);
}

.sidebar-search {
  width: calc(100% - 32px);
  margin: 12px 16px;
  box-sizing: border-box;
}

.sidebar-list {
  flex: 1;
  padding: 0 8px;
}

.sidebar-file {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-bottom: 4px;
}

.sidebar-file:hover {
  background: var(--bg-tertiary);
}

.sidebar-file.active {
  background: var(--primary-tint);
  color: var(--primary-color);
}

.file-icon {
  color: var(--text-muted);
  flex-shrink: 0;
}

.sidebar-file.active .file-icon {
  color: var(--primary-color);
}

.file-name {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-pagination {
  padding: 12px 16px;
  border-top: 1px solid var(--border-light);
}

/* 主内容区 */
.preview-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
  gap: 16px;
}

.header-left {
  flex: 1;
  min-width: 0;
}

.current-file-name {
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.view-toggle {
  display: flex;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 4px;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-muted);
  transition: all var(--transition-fast);
}

.toggle-btn:hover {
  color: var(--text-primary);
}

.toggle-btn.active {
  background: var(--bg-primary);
  color: var(--primary-color);
  box-shadow: var(--shadow-sm);
}

/* 预览内容 */
.preview-content {
  flex: 1;
  display: flex;
  gap: 1px;
  background: var(--border-light);
  overflow: hidden;
}

.preview-panel {
  flex: 1;
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
  min-width: 0;
  transition: flex var(--transition-normal);
}

.preview-panel.full-width {
  flex: 1 0 100%;
}

.panel-content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

.image-preview {
  max-width: 100%;
  height: auto;
  border-radius: var(--radius-md);
}

.text-preview {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
  margin: 0;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
  color: var(--text-muted);
}

/* Markdown样式 */
.markdown-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px;
  padding: 3px;
  margin-bottom: 16px;
  max-width: 100%;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.pdf-review-bar {
  position: sticky;
  top: -24px;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin: -24px -24px 18px;
  padding: 14px 24px 12px;
  border-bottom: 1px solid var(--border-light);
  background: color-mix(in srgb, var(--bg-primary) 94%, transparent);
  backdrop-filter: blur(14px);
}

.pdf-review-title {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pdf-review-title span {
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 700;
}

.pdf-review-title small {
  color: var(--text-muted);
  font-size: 12px;
}

.pdf-review-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-left: auto;
}

.pdf-review-mode {
  height: 28px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  transition: background var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast);
}

.pdf-review-mode:hover {
  color: var(--text-primary);
  background: color-mix(in srgb, var(--bg-tertiary) 72%, transparent);
}

.pdf-review-mode.active {
  border-color: var(--border-light);
  background: var(--bg-primary);
  color: var(--primary-color);
}

.review-drawer {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.review-drawer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.outline-review {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.outline-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.outline-metric {
  min-width: 0;
  padding: 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
}

.outline-metric span {
  display: block;
  color: var(--text-muted);
  font-size: 12px;
}

.outline-metric strong {
  display: block;
  margin-top: 4px;
  color: var(--text-primary);
  font-size: 20px;
}

.outline-findings {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.directory-review-layout {
  min-height: 560px;
  display: grid;
  grid-template-columns: minmax(220px, 31%) minmax(0, 1fr);
  gap: 12px;
}

.directory-tree-panel,
.directory-detail-panel,
.pdf-outline-panel,
.stage-ref-panel {
  min-width: 0;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
}

.directory-tree-panel,
.directory-detail-panel {
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.directory-tree-panel header,
.pdf-outline-panel header {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-light);
}

.directory-tree-panel header span,
.pdf-outline-panel header span,
.directory-code-pane header span {
  display: block;
  color: var(--text-primary);
  font-weight: 700;
  font-size: 13px;
}

.directory-tree-panel header small,
.pdf-outline-panel header small,
.directory-code-pane header small,
.directory-detail-header small {
  color: var(--text-muted);
  font-size: 11px;
}

.directory-unit-list {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 6px;
}

.directory-unit {
  width: 100%;
  min-height: 40px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 3px 8px;
  padding: 7px 8px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
}

.directory-unit:hover,
.directory-unit.active {
  background: var(--bg-tertiary);
}

.directory-unit.active {
  color: var(--primary-color);
}

.directory-unit span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 600;
}

.directory-unit small,
.directory-unit em {
  flex: 0 0 auto;
  color: var(--text-muted);
  font-size: 11px;
  font-style: normal;
}

.directory-unit em {
  grid-column: 1 / -1;
}

.directory-unit em.status-matched {
  color: var(--success-color);
}

.directory-unit em.status-missing {
  color: var(--warning-color);
}

.directory-detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid var(--border-light);
}

.directory-detail-header span {
  display: block;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 700;
}

.outline-jump-btn {
  flex: 0 0 auto;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.outline-jump-btn:hover {
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.directory-evidence-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-secondary);
}

.directory-evidence-strip span,
.stage-ref-panel span {
  color: var(--text-secondary);
  font-size: 12px;
}

.directory-code-columns {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  background: var(--border-light);
}

.directory-code-pane {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.directory-code-pane header {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-light);
}

.directory-code-pane pre {
  flex: 1;
  min-height: 380px;
  margin: 0;
  padding: 12px;
  overflow: auto;
  color: var(--text-primary);
  background: var(--bg-secondary);
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}

.pdf-outline-list {
  max-height: 180px;
  overflow: auto;
  padding: 6px;
}

.pdf-outline-item {
  width: 100%;
  min-height: 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 8px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
}

.pdf-outline-item:hover {
  background: var(--bg-tertiary);
}

.pdf-outline-item span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}

.pdf-outline-item small {
  flex: 0 0 auto;
  color: var(--text-muted);
  font-size: 11px;
}

.stage-ref-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 8px 10px;
  background: var(--bg-secondary);
}

.source-trace-chip {
  margin-left: auto;
  padding: 0 10px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: color-mix(in srgb, var(--bg-primary) 86%, transparent);
  color: var(--text-muted);
  font-size: 12px;
  white-space: nowrap;
}

.pdf-review-actions .source-trace-chip {
  margin-left: 2px;
}

.source-type-filters {
  flex: 1 0 100%;
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  padding: 2px 0 1px;
  scrollbar-width: none;
}

.source-type-filters::-webkit-scrollbar {
  display: none;
}

.source-type-filter {
  height: 28px;
  padding: 0 9px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  transition: background var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast);
}

.source-type-filter:hover {
  color: var(--text-primary);
  background: color-mix(in srgb, var(--bg-tertiary) 78%, transparent);
}

.source-type-filter.active {
  border-color: color-mix(in srgb, var(--primary-color) 26%, var(--border-light));
  background: color-mix(in srgb, var(--primary-tint) 36%, var(--bg-primary));
  color: var(--primary-color);
}

.source-type-filter small {
  min-width: 16px;
  height: 16px;
  padding: 0 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: color-mix(in srgb, currentColor 8%, transparent);
  font-size: 10px;
  line-height: 1;
}

.markdown-tab {
  flex: 0 1 auto;
  min-width: 88px;
  height: 30px;
  padding: 0 12px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  font-size: 13px;
  transition: all var(--transition-fast);
}

.markdown-tab:hover {
  color: var(--text-primary);
}

.markdown-tab.active {
  background: var(--bg-primary);
  color: var(--primary-color);
  box-shadow: var(--shadow-sm);
}

.markdown-content {
  font-size: 14px;
  line-height: 1.64;
  color: var(--text-primary);
}

.markdown-pages {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.markdown-reader-pages {
  max-width: 720px;
  margin: 0 auto;
}

.markdown-page-section {
  position: relative;
  padding-left: 14px;
  border-left: 1px solid var(--border-light);
  transition: border-color var(--transition-fast);
}

.markdown-page-section.active {
  border-left-color: color-mix(in srgb, var(--primary-color) 58%, var(--border-light));
}

.markdown-page-meta {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  padding: 0 2px;
  border: none;
  background: transparent;
  cursor: pointer;
}

.markdown-page-meta span {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
}

.reader-page-marker {
  position: sticky;
  top: -24px;
  z-index: 1;
  min-height: 30px;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
}

.reader-page-marker:hover {
  color: var(--text-primary);
}

.markdown-page-meta small {
  min-width: 0;
  color: var(--text-muted);
  font-size: 12px;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.markdown-source-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.markdown-reader-block {
  position: relative;
  display: block;
  width: 100%;
  padding: 6px 72px 6px 12px;
  border: 1px solid transparent;
  border-left: 2px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  outline: none;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast);
}

.markdown-reader-block:hover,
.markdown-reader-block:focus-visible {
  border-color: color-mix(in srgb, var(--primary-color) 22%, transparent);
  border-left-color: color-mix(in srgb, var(--primary-color) 42%, var(--border-light));
  background: color-mix(in srgb, var(--primary-tint) 18%, transparent);
}

.markdown-reader-block.active {
  border-color: color-mix(in srgb, var(--primary-color) 30%, var(--border-light));
  border-left-color: color-mix(in srgb, var(--primary-color) 82%, var(--border-light));
  background: color-mix(in srgb, var(--primary-tint) 30%, var(--bg-primary));
  box-shadow: 0 8px 22px rgb(0 0 0 / 4%);
}

.markdown-reader-block.no-source-pill {
  padding-right: 12px;
}

.reader-source-pill {
  position: absolute;
  top: 10px;
  right: 10px;
  max-width: 58px;
  height: 20px;
  padding: 0 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid var(--border-light);
  border-radius: 999px;
  background: color-mix(in srgb, var(--bg-primary) 82%, transparent);
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.markdown-reader-block.active .reader-source-pill {
  border-color: color-mix(in srgb, var(--primary-color) 36%, var(--border-light));
  color: var(--primary-color);
  background: var(--bg-primary);
}

.reader-source-pill.type-title {
  color: var(--primary-color);
}

.reader-source-pill.type-table {
  color: #8a5b16;
}

.reader-source-pill.type-image {
  color: #0f766e;
}

.reader-source-pill.type-formula {
  color: #7c3aed;
}

.reader-source-pill.type-assist {
  color: var(--text-muted);
}

.markdown-filter-empty {
  padding: 8px 12px;
  color: var(--text-muted);
  font-size: 13px;
}

.trace-content {
  font-size: 13px;
  line-height: 1.56;
}

.trace-content :deep(h1),
.trace-content :deep(h2),
.trace-content :deep(h3) {
  margin-top: 0.25em;
  font-size: 1.04em;
}

.trace-content :deep(p),
.trace-content :deep(ul),
.trace-content :deep(ol) {
  margin: 0.38em 0;
}

.trace-content :deep(:first-child) {
  margin-top: 0;
}

.trace-content :deep(:last-child) {
  margin-bottom: 0;
}

.page-content {
  padding: 6px 16px 16px;
}

.markdown-compare {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
  height: calc(100vh - 190px);
  min-height: 420px;
  overflow: hidden;
}

.compare-column {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  overflow: hidden;
}

.compare-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-secondary);
}

.compare-header span {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.compare-header small {
  min-width: 0;
  color: var(--text-muted);
  font-size: 12px;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compare-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 16px;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  margin-top: 1.05em;
  margin-bottom: 0.38em;
  font-weight: 650;
  line-height: 1.32;
  color: var(--text-primary);
}

.markdown-content :deep(h1) { font-size: 1.32em; border-bottom: 1px solid var(--border-light); padding-bottom: 0.18em; }
.markdown-content :deep(h2) { font-size: 1.18em; }
.markdown-content :deep(h3) { font-size: 1.08em; }

.markdown-content :deep(p) { margin: 0.58em 0; }

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.55em 0;
  padding-left: 1.35em;
}

.markdown-content :deep(li + li) {
  margin-top: 0.18em;
}

.markdown-content :deep(code) {
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background: var(--bg-tertiary);
  padding: 12px;
  border-radius: var(--radius-sm);
  overflow-x: auto;
}

.markdown-content :deep(pre code) {
  background: transparent;
  padding: 0;
}

.markdown-content :deep(table) {
  width: 100%;
  display: block;
  overflow-x: auto;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  border-collapse: separate;
  border-spacing: 0;
  margin: 0.62em 0;
  font-size: 0.9em;
  line-height: 1.36;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border-right: 1px solid var(--border-light);
  border-bottom: 1px solid var(--border-light);
  padding: 6px 8px;
  text-align: left;
  vertical-align: top;
}

.markdown-content :deep(th) {
  background: color-mix(in srgb, var(--bg-tertiary) 72%, var(--bg-primary));
  font-weight: 600;
}

.markdown-content :deep(tr:last-child > th),
.markdown-content :deep(tr:last-child > td) {
  border-bottom: none;
}

.markdown-content :deep(th:last-child),
.markdown-content :deep(td:last-child) {
  border-right: none;
}

.markdown-content :deep(img) {
  max-width: 100%;
  border-radius: var(--radius-md);
}

.markdown-content :deep(blockquote) {
  margin: 0.75em 0;
  padding: 0 0.8em;
  border-left: 2px solid color-mix(in srgb, var(--primary-color) 56%, var(--border-light));
  color: var(--text-secondary);
}

.markdown-content :deep(.katex-display) {
  overflow-x: auto;
  margin: 0.72em 0;
}

.markdown-content.trace-content :deep(h1),
.markdown-content.trace-content :deep(h2),
.markdown-content.trace-content :deep(h3) {
  margin: 0.38em 0 0.24em;
  border-bottom: none;
  padding-bottom: 0;
  line-height: 1.28;
}

.markdown-content.trace-content :deep(h1) { font-size: 1.08em; }
.markdown-content.trace-content :deep(h2) { font-size: 1.04em; }
.markdown-content.trace-content :deep(h3) { font-size: 1em; }

.markdown-content.trace-content :deep(table) {
  margin: 0.48em 0;
  font-size: 0.88em;
}

.markdown-content :deep(.katex-mathml) {
  display: none !important;
}

@media (max-width: 1024px) {
  .preview-content {
    flex-direction: column;
  }
  
  .preview-panel {
    min-height: 50vh;
  }

  .markdown-compare {
    grid-template-columns: 1fr;
    height: auto;
    min-height: 0;
    overflow: visible;
  }

  .compare-column {
    min-height: 360px;
  }

  .directory-review-layout,
  .directory-code-columns {
    grid-template-columns: 1fr;
  }

  .directory-tree-panel {
    max-height: 360px;
  }
}

@media (max-width: 768px) {
  .preview-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    box-shadow: var(--shadow-xl);
  }

  .preview-sidebar.collapsed {
    width: 48px;
  }

  .preview-main {
    padding-left: 48px;
  }

  .preview-header {
    flex-wrap: wrap;
    padding: 12px 16px;
  }
  
  .header-center {
    order: 3;
    width: 100%;
    margin-top: 12px;
  }
  
  .view-toggle {
    width: 100%;
    justify-content: center;
  }
  
  .panel-content {
    padding: 16px;
  }
}
</style>
