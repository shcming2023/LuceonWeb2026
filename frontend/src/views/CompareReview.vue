<template>
  <div class="compare-page">
    <header class="compare-header">
      <div>
        <h1>PDF 比对审查</h1>
        <p>原 PDF · ElegantBook 编译 PDF</p>
      </div>
      <div class="compare-actions">
        <el-button :icon="Refresh" :loading="loading" @click="refreshCurrent">刷新</el-button>
      </div>
    </header>

    <section class="compare-toolbar">
      <el-input v-model="search" clearable placeholder="搜索 material_id / 文件名" @keyup.enter="loadAssets">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select
        v-model="selectedAssetId"
        filterable
        placeholder="选择已有 ElegantBook 输出的材料"
        class="asset-select"
        @change="handleAssetChange"
      >
        <el-option
          v-for="row in assets"
          :key="row.id"
          :label="displayFilename(row)"
          :value="row.id"
        />
      </el-select>
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        small
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
      />
    </section>

    <section v-if="selectedAsset" class="selected-strip">
      <div>
        <strong>{{ displayFilename(selectedAsset) }}</strong>
        <span>{{ selectedAsset.material_id || selectedAsset.run_id || '' }}</span>
      </div>
      <div class="selected-tags">
        <el-tag size="small" :type="outputOriginTagType">{{ outputOriginLabel }}</el-tag>
        <el-tag v-if="compileStatus" size="small" :type="compileTagType">{{ compileStatus }}</el-tag>
      </div>
      <el-select
        v-if="availableOutputs.length > 1"
        v-model="selectedOutputId"
        size="small"
        class="output-select"
        placeholder="输出版本"
        @change="loadSelectedCompare"
      >
        <el-option
          v-for="row in availableOutputs"
          :key="outputOptionValue(row)"
          :label="outputOptionLabel(row)"
          :value="outputOptionValue(row)"
        />
      </el-select>
      <div class="download-actions">
        <el-button v-if="downloadUrls.package_zip" type="primary" :icon="Download" @click="openUrl(downloadUrls.package_zip)">
          {{ zipButtonText }}
        </el-button>
        <el-button v-if="downloadUrls.compiled_pdf" :icon="Document" @click="openUrl(downloadUrls.compiled_pdf)">下载 PDF</el-button>
        <el-button v-if="downloadUrls.compile_report" link type="primary" @click="openUrl(downloadUrls.compile_report)">编译报告</el-button>
      </div>
    </section>

    <section class="compare-grid">
      <article class="compare-panel source-panel">
        <header>
          <strong>原 PDF</strong>
          <el-tag v-if="sourcePdfUrl" size="small" type="primary">Source</el-tag>
        </header>
        <PdfSourceViewer
          v-if="sourcePdfUrl"
          :url="sourcePdfUrl"
          :source-map="{ pages: [] }"
          :active-page="sourceActivePage"
          @page-change="sourceActivePage = $event"
        />
        <el-empty v-else :description="emptyText" />
      </article>

      <article class="compare-panel latex-panel">
        <header>
          <strong>ElegantBook 编译 PDF</strong>
          <el-tag v-if="latexPdfUrl" size="small" type="success">Compiled</el-tag>
        </header>
        <PdfSourceViewer
          v-if="latexPdfUrl"
          :url="latexPdfUrl"
          :source-map="{ pages: [] }"
          :active-page="latexActivePage"
          @page-change="latexActivePage = $event"
        />
        <el-empty v-else :description="compareError || '暂无编译 PDF'" />
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Download, Refresh, Search } from '@element-plus/icons-vue'
import { reviewApi, type LatexCompareResponse } from '@/api/review'
import PdfSourceViewer from '@/components/PdfSourceViewer.vue'
import type { FileItem } from '@/types/file'

const route = useRoute()
const router = useRouter()

const assets = ref<FileItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')
const loading = ref(false)
const selectedAssetId = ref('')
const selectedOutputId = ref('')
const compare = ref<LatexCompareResponse | null>(null)
const compareError = ref('')
const sourceActivePage = ref(1)
const latexActivePage = ref(1)

const selectedAsset = computed(() => assets.value.find(row => row.id === selectedAssetId.value) || null)
const sourcePdfUrl = computed(() => compare.value?.source_pdf_url || (selectedAssetId.value ? reviewApi.getContentUrl(selectedAssetId.value) : ''))
const latexPdfUrl = computed(() => compare.value?.latex_pdf_url || '')
const downloadUrls = computed(() => compare.value?.download_urls || {})
const availableOutputs = computed(() => compare.value?.available_outputs || [])
const outputOrigin = computed(() => String(compare.value?.output_origin || 'legacy_selfloop'))
type AvailableOutput = NonNullable<LatexCompareResponse['available_outputs']>[number]
const selectedOutputRow = computed<AvailableOutput | null>(() => {
  const target = String(compare.value?.output_id || selectedOutputId.value || '')
  return availableOutputs.value.find(row => outputOptionValue(row) === target) || null
})
const selectedQualityStatus = computed(() => {
  const manifest = compare.value?.manifest_json || {}
  const qa = manifest.qa && typeof manifest.qa === 'object' ? manifest.qa as Record<string, unknown> : {}
  return String(selectedOutputRow.value?.quality_status || qa.status || '')
})
const outputOriginLabel = computed(() => {
  return outputOriginText(outputOrigin.value, selectedQualityStatus.value)
})
const zipButtonText = computed(() => {
  if (outputOrigin.value === 'legacy_selfloop') return '导出 LaTeX ZIP'
  return selectedQualityStatus.value === 'passed' ? '导出精修 LaTeX ZIP' : '导出候选 LaTeX ZIP'
})
const outputOriginTagType = computed(() => {
  if (outputOrigin.value === 'codex_refined' && selectedQualityStatus.value === 'passed') return 'success'
  if (outputOrigin.value === 'codex_refined') return 'warning'
  if (outputOrigin.value === 'codex_elegantbook') return 'primary'
  return 'info'
})
const compileStatus = computed(() => {
  const report = compare.value?.compile_report || {}
  const manifest = compare.value?.manifest_json || {}
  const compile = manifest.compile && typeof manifest.compile === 'object' ? manifest.compile as Record<string, unknown> : {}
  return String(report.status || compile.status || '')
})
const compileTagType = computed(() => {
  if (compileStatus.value === 'succeeded') return 'success'
  if (compileStatus.value === 'fallback_pdf' || compileStatus.value === 'skipped') return 'warning'
  if (compileStatus.value === 'failed') return 'danger'
  return 'info'
})
const emptyText = computed(() => loading.value ? '正在加载' : '请选择材料')

function displayFilename(row: FileItem) {
  return row.title || row.input_filename || row.filename || row.material_id || `#${row.id}`
}

function outputOptionValue(row: NonNullable<LatexCompareResponse['available_outputs']>[number]) {
  return String(row.id || row.manifest?.object || row.output_run_id || '')
}

function outputOriginText(origin: string, qualityStatus = '') {
  if (origin === 'codex_refined') {
    if (qualityStatus === 'passed') return 'Codex 精修'
    if (qualityStatus === 'needs_fix') return 'Codex 候选（待修复）'
    return 'Codex 候选'
  }
  if (origin === 'codex_elegantbook') return 'Codex ElegantBook'
  return 'Legacy baseline'
}

function outputOptionLabel(row: NonNullable<LatexCompareResponse['available_outputs']>[number]) {
  const origin = outputOriginText(row.origin, row.quality_status || '')
  const quality = row.quality_status && row.quality_status !== 'passed' ? ` · ${row.quality_status}` : ''
  const suffix = row.is_current ? ' · 当前' : ''
  return `${origin}${quality} · ${row.version_label || row.output_run_id || row.created_at || row.manifest?.object || '未命名'}${suffix}`
}

function apiUrl(url: string) {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  return url.startsWith('/api/') ? url : `/api${url.startsWith('/') ? url : `/${url}`}`
}

function openUrl(url: string) {
  const target = apiUrl(url)
  if (target) window.open(target, '_blank', 'noopener,noreferrer')
}

async function refreshCurrent() {
  if (!selectedAssetId.value) {
    await loadAssets()
    return
  }
  await loadSelectedCompare()
}

async function handleAssetChange() {
  selectedOutputId.value = ''
  await loadSelectedCompare()
}

async function ensureSelectedAssetVisible(assetId: string) {
  if (!assetId || assets.value.some(row => row.id === assetId)) return
  try {
    const asset = await reviewApi.getAsset(assetId) as FileItem
    assets.value = [asset, ...assets.value]
  } catch {
    // Keep the URL-selected id; the compare endpoint will surface the real error.
  }
}

async function loadAssets() {
  loading.value = true
  compareError.value = ''
  try {
    const response = await reviewApi.getAssets({
      page: page.value,
      page_size: pageSize.value,
      search: search.value,
      view: 'compare'
    })
    assets.value = response.files
    total.value = response.total
    const routeAssetId = typeof route.query.asset_id === 'string' ? route.query.asset_id : ''
    const routeOutputId = typeof route.query.output_id === 'string' ? route.query.output_id : ''
    if (routeAssetId) {
      selectedAssetId.value = routeAssetId
      selectedOutputId.value = routeOutputId
      await ensureSelectedAssetVisible(routeAssetId)
    } else if (!selectedAssetId.value || !assets.value.some(row => row.id === selectedAssetId.value)) {
      selectedAssetId.value = assets.value[0]?.id || ''
      selectedOutputId.value = ''
    }
    await loadSelectedCompare()
  } finally {
    loading.value = false
  }
}

async function loadSelectedCompare() {
  compare.value = null
  compareError.value = ''
  sourceActivePage.value = 1
  latexActivePage.value = 1
  if (!selectedAssetId.value) return
  const query: Record<string, string> = { asset_id: selectedAssetId.value }
  if (selectedOutputId.value) query.output_id = selectedOutputId.value
  void router.replace({ path: '/review/compare', query })
  try {
    compare.value = await reviewApi.getLatexCompare(selectedAssetId.value, selectedOutputId.value)
    selectedOutputId.value = compare.value.output_id || selectedOutputId.value
  } catch (error: any) {
    compareError.value = error?.response?.data?.detail || error?.message || 'LaTeX 比对信息加载失败'
    ElMessage.error(compareError.value)
  }
}

watch([page, pageSize], () => {
  void loadAssets()
})

onMounted(loadAssets)
</script>

<style scoped>
.compare-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.compare-header,
.compare-toolbar,
.selected-strip,
.compare-panel {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
}

.compare-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
}

.compare-header h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: 24px;
}

.compare-header p {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: 13px;
}

.compare-toolbar,
.selected-strip {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
}

.asset-select {
  width: min(420px, 34vw);
}

.output-select {
  width: min(320px, 26vw);
  flex-shrink: 0;
}

.selected-strip {
  justify-content: space-between;
}

.selected-strip > div:first-child {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.selected-strip strong {
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-strip span {
  color: var(--text-muted);
  font-size: 12px;
}

.selected-tags,
.download-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.compare-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 14px;
  min-height: 0;
}

.compare-panel {
  min-width: 0;
  overflow: hidden;
}

.compare-panel > header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-primary);
}

.compare-panel :deep(.pdf-source-viewer) {
  height: calc(100vh - 260px);
  min-height: 520px;
  border: none;
  border-radius: 0;
}

@media (max-width: 900px) {
  .compare-toolbar,
  .selected-strip,
  .compare-header {
    flex-direction: column;
    align-items: stretch;
  }

  .asset-select {
    width: 100%;
  }

  .output-select {
    width: 100%;
  }

  .selected-strip {
    align-items: stretch;
  }

  .selected-tags,
  .download-actions {
    flex-wrap: wrap;
  }

  .compare-grid {
    grid-template-columns: 1fr;
  }
}
</style>
