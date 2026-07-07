<template>
  <div class="pdf-source-viewer">
    <div class="pdf-source-toolbar">
      <div class="pdf-source-title">
        <span>PDF</span>
        <small>{{ pageLabel }}</small>
      </div>
      <div class="pdf-source-actions">
        <button class="icon-btn" type="button" title="缩小" :disabled="zoom <= 0.75" @click="setZoom(zoom - 0.1)">
          <el-icon><ZoomOut /></el-icon>
        </button>
        <button class="icon-btn" type="button" title="适合宽度" @click="setZoom(1)">
          <el-icon><Aim /></el-icon>
        </button>
        <button class="icon-btn" type="button" title="放大" :disabled="zoom >= 1.6" @click="setZoom(zoom + 0.1)">
          <el-icon><ZoomIn /></el-icon>
        </button>
        <button class="icon-btn" type="button" title="重新加载" @click="loadDocument">
          <el-icon><Refresh /></el-icon>
        </button>
      </div>
    </div>

    <div ref="scrollRef" class="pdf-source-scroll" @scroll="handleScroll" @wheel.prevent.stop="handleWheel">
      <div v-if="loading" class="pdf-source-state">正在加载 PDF...</div>
      <div v-else-if="error" class="pdf-source-state error">{{ error }}</div>
      <template v-else>
        <div v-if="topSpacerHeight" class="pdf-page-spacer" :style="{ height: `${topSpacerHeight}px` }" />
        <section
          v-for="page in visiblePages"
          :key="page.pageNumber"
          :ref="(el) => setPageRef(el, page.pageNumber)"
          class="pdf-page-shell"
          :class="{ active: page.pageNumber === activePage, rendered: page.renderState === 'rendered' }"
        >
          <div class="pdf-page-number">Page {{ page.pageNumber }}</div>
          <div class="pdf-page-canvas-wrap" :style="{ width: `${page.width}px`, height: `${page.height}px` }">
            <canvas :ref="(el) => setCanvasRef(el, page.pageNumber)" class="pdf-page-canvas" />
            <div v-if="page.renderState !== 'rendered'" class="pdf-page-placeholder">
              {{ page.renderState === 'loading' ? '正在渲染...' : '等待渲染' }}
            </div>
            <div class="pdf-source-layer">
              <button
                v-for="block in blocksForRenderedPage(page.pageNumber)"
                :key="block.id"
                :ref="(el) => setBlockRef(el, block.id)"
                class="source-box"
                type="button"
                :data-source-block-id="block.id"
                :class="{
                  visible: page.pageNumber === activePage || block.id === activeBlockId,
                  active: block.id === activeBlockId
                }"
                :style="blockStyle(block, page)"
                :title="blockTitle(block)"
                @click.stop="handleSourceBlockClick(page.pageNumber, block)"
              />
            </div>
          </div>
        </section>
        <div v-if="bottomSpacerHeight" class="pdf-page-spacer" :style="{ height: `${bottomSpacerHeight}px` }" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { Aim, Refresh, ZoomIn, ZoomOut } from '@element-plus/icons-vue'
import * as pdfjsLib from 'pdfjs-dist'
import type { PDFDocumentProxy, PDFPageProxy, RenderTask } from 'pdfjs-dist/types/src/display/api'
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.mjs?url'
import type { SourceBlock, SourceMap, SourcePage } from '@/types/file'
import { sourceTypeLabel } from '@/utils/sourceTypes'

pdfjsLib.GlobalWorkerOptions.workerSrc = `${pdfWorkerUrl}?module=1`

const pdfAssetBase = import.meta.env.DEV ? '/node_modules/pdfjs-dist' : '/pdfjs'

interface RenderedPage {
  pageNumber: number
  width: number
  height: number
  sourceWidth: number
  sourceHeight: number
  renderState: 'idle' | 'loading' | 'rendered' | 'error'
}

interface PageGeometry {
  pageNumber: number
  sourceWidth: number
  sourceHeight: number
}

const props = defineProps<{
  url: string
  sourceMap?: SourceMap | null
  activePage?: number
  activeBlockId?: string
}>()

const emit = defineEmits<{
  'page-change': [page: number]
  'block-select': [page: number, blockId: string]
}>()

const scrollRef = ref<HTMLElement | null>(null)
const pages = shallowRef<RenderedPage[]>([])
const loading = ref(false)
const error = ref('')
const zoom = ref(1)
const currentPage = ref(1)
const pdfPageTotal = ref(0)
const pdfDoc = shallowRef<PDFDocumentProxy | null>(null)
const canvasRefs = new Map<number, HTMLCanvasElement>()
const pageRefs = new Map<number, HTMLElement>()
const blockRefs = new Map<string, HTMLElement>()
const renderTasks = new Map<number, RenderTask>()
const VIRTUALIZE_PAGE_THRESHOLD = 80
const VIRTUAL_WINDOW_RADIUS = 8
const PAGE_VERTICAL_CHROME = 44
let loadToken = 0
let pendingScrollPage: number | undefined
let visibleRenderFrame: number | undefined

const activePage = computed(() => props.activePage || currentPage.value)
const useVirtualPages = computed(() => pages.value.length > VIRTUALIZE_PAGE_THRESHOLD)
const sourcePages = computed(() => props.sourceMap?.pages || [])
const sourcePageMap = computed(() => new Map(sourcePages.value.map((page) => [page.page, page])))
const sourceBlockCount = computed(() => sourcePages.value.reduce((total, page) => total + page.blocks.length, 0))
const pageLabel = computed(() => {
  const total = pdfPageTotal.value || pages.value.length
  const trace = sourceBlockCount.value ? `${sourceBlockCount.value} 个溯源框` : '无溯源数据'
  return total ? `第 ${activePage.value} / ${total} 页 · ${trace}` : trace
})

const pageSource = (pageNumber: number): SourcePage | undefined => {
  return sourcePageMap.value.get(pageNumber)
}

const blocksForPage = (pageNumber: number): SourceBlock[] => {
  return pageSource(pageNumber)?.blocks || []
}

const shouldRenderSourceBlocks = (pageNumber: number) => {
  return Math.abs(pageNumber - activePage.value) <= 1 || Math.abs(pageNumber - currentPage.value) <= 1
}

const blocksForRenderedPage = (pageNumber: number): SourceBlock[] => {
  return shouldRenderSourceBlocks(pageNumber) ? blocksForPage(pageNumber) : []
}

const clampPageNumber = (pageNumber: number) => {
  const total = pdfPageTotal.value || pages.value.length || pageNumber
  return Math.max(1, Math.min(total, pageNumber))
}

const pageOuterHeight = (page: RenderedPage) => page.height + PAGE_VERTICAL_CHROME

const pageOffsetBefore = (pageNumber: number) => {
  const target = clampPageNumber(pageNumber)
  let offset = 0
  for (const page of pages.value) {
    if (page.pageNumber >= target) break
    offset += pageOuterHeight(page)
  }
  return offset
}

const totalScrollHeight = computed(() => pages.value.reduce((total, page) => total + pageOuterHeight(page), 0))

const pageFromScrollOffset = (offset: number) => {
  if (!pages.value.length) return currentPage.value
  let cursor = 0
  for (const page of pages.value) {
    cursor += pageOuterHeight(page)
    if (offset <= cursor) return page.pageNumber
  }
  return pages.value[pages.value.length - 1]?.pageNumber || currentPage.value
}

const visiblePages = computed(() => {
  if (!useVirtualPages.value) return pages.value
  const total = pdfPageTotal.value || pages.value.length
  const anchors = new Set([clampPageNumber(currentPage.value), clampPageNumber(activePage.value)])
  let start = total
  let end = 1
  anchors.forEach((anchor) => {
    start = Math.min(start, Math.max(1, anchor - VIRTUAL_WINDOW_RADIUS))
    end = Math.max(end, Math.min(total, anchor + VIRTUAL_WINDOW_RADIUS))
  })
  return pages.value.filter((page) => page.pageNumber >= start && page.pageNumber <= end)
})

const topSpacerHeight = computed(() => {
  if (!useVirtualPages.value || !visiblePages.value.length) return 0
  return pageOffsetBefore(visiblePages.value[0].pageNumber)
})

const bottomSpacerHeight = computed(() => {
  if (!useVirtualPages.value || !visiblePages.value.length) return 0
  const last = visiblePages.value[visiblePages.value.length - 1]
  return Math.max(0, totalScrollHeight.value - pageOffsetBefore(last.pageNumber) - pageOuterHeight(last))
})

const setCanvasRef = (el: unknown, pageNumber: number) => {
  if (el instanceof HTMLCanvasElement) {
    canvasRefs.set(pageNumber, el)
  } else {
    canvasRefs.delete(pageNumber)
  }
}

const setPageRef = (el: unknown, pageNumber: number) => {
  if (el instanceof HTMLElement) {
    pageRefs.set(pageNumber, el)
    if (!useVirtualPages.value && pendingScrollPage === pageNumber) {
      void scrollToPage(pageNumber)
    }
  } else {
    pageRefs.delete(pageNumber)
  }
}

const setBlockRef = (el: unknown, blockId: string) => {
  if (el instanceof HTMLElement) {
    blockRefs.set(blockId, el)
  } else {
    blockRefs.delete(blockId)
  }
}

const cleanupRenderTasks = () => {
  renderTasks.forEach((task) => task.cancel())
  renderTasks.clear()
}

const destroyDocument = async () => {
  cleanupRenderTasks()
  if (visibleRenderFrame) {
    window.cancelAnimationFrame(visibleRenderFrame)
    visibleRenderFrame = undefined
  }
  const doc = pdfDoc.value
  pdfDoc.value = null
  if (doc) await doc.destroy()
}

const targetPageWidth = () => {
  const containerWidth = scrollRef.value?.clientWidth || 760
  return Math.max(320, Math.min(980, containerWidth - 48)) * zoom.value
}

const estimatedPageGeometry = (pageNumber: number, width: number) => {
  const source = pageSource(pageNumber)
  const sourceWidth = Number(source?.width) > 0 ? Number(source?.width) : 612
  const sourceHeight = Number(source?.height) > 0 ? Number(source?.height) : Math.round(sourceWidth * 1.414)
  const scale = width / sourceWidth
  return {
    width,
    height: Math.round(sourceHeight * scale),
    sourceWidth,
    sourceHeight
  }
}

const patchPage = (pageNumber: number, patch: Partial<RenderedPage>) => {
  pages.value = pages.value.map((page) => page.pageNumber === pageNumber ? { ...page, ...patch } : page)
}

const pageState = (pageNumber: number) => {
  return pages.value.find((page) => page.pageNumber === pageNumber)
}

const renderPage = async (pageNumber: number, token: number) => {
  const page = pageState(pageNumber)
  const doc = pdfDoc.value
  if (!page || !doc || token !== loadToken || page.renderState === 'loading' || page.renderState === 'rendered') return
  patchPage(pageNumber, { renderState: 'loading' })
  await nextTick()

  let canvas = canvasRefs.get(pageNumber)
  if (!canvas || token !== loadToken) {
    patchPage(pageNumber, { renderState: 'idle' })
    return
  }
  const context = canvas.getContext('2d', { alpha: false })
  if (!context) {
    patchPage(pageNumber, { renderState: 'error' })
    return
  }

  let pdfPage: PDFPageProxy | null = null
  try {
    pdfPage = await doc.getPage(pageNumber)
    if (token !== loadToken) return
    const baseViewport = pdfPage.getViewport({ scale: 1 })
    const width = targetPageWidth()
    const scale = width / baseViewport.width
    const viewport = pdfPage.getViewport({ scale })
    patchPage(pageNumber, {
      width: viewport.width,
      height: viewport.height,
      sourceWidth: baseViewport.width,
      sourceHeight: baseViewport.height,
      renderState: 'loading'
    })
    await nextTick()

    canvas = canvasRefs.get(pageNumber)
    if (!canvas || token !== loadToken) return
    const freshContext = canvas.getContext('2d', { alpha: false })
    if (!freshContext) return
    const ratio = Math.min(window.devicePixelRatio || 1, 1.5)
    canvas.width = Math.floor(viewport.width * ratio)
    canvas.height = Math.floor(viewport.height * ratio)
    canvas.style.width = `${viewport.width}px`
    canvas.style.height = `${viewport.height}px`
    freshContext.setTransform(ratio, 0, 0, ratio, 0, 0)
    freshContext.fillStyle = '#fff'
    freshContext.fillRect(0, 0, viewport.width, viewport.height)

    const renderTask = pdfPage.render({ canvasContext: freshContext, viewport })
    renderTasks.set(pageNumber, renderTask)
    await renderTask.promise
    if (token === loadToken) {
      patchPage(pageNumber, { renderState: 'rendered' })
    }
  } catch (e) {
    if (String((e as Error).name) !== 'RenderingCancelledException' && token === loadToken) {
      patchPage(pageNumber, { renderState: 'error' })
    }
  } finally {
    renderTasks.delete(pageNumber)
    pdfPage?.cleanup()
  }
}

const renderAroundPage = (pageNumber: number, radius = 1) => {
  const total = pdfPageTotal.value || pages.value.length
  if (!total) return
  const start = Math.max(1, pageNumber - radius)
  const end = Math.min(total, pageNumber + radius)
  const token = loadToken
  const targets = Array.from({ length: end - start + 1 }, (_, index) => start + index)
    .sort((a, b) => Math.abs(a - pageNumber) - Math.abs(b - pageNumber))
  void (async () => {
    const [target, ...nearby] = targets
    if (!target) return
    await renderPage(target, token)
    nearby.forEach((nearbyPage) => {
      void renderPage(nearbyPage, token)
    })
  })()
}

const renderVisiblePages = () => {
  const scroller = scrollRef.value
  if (!scroller || !pages.value.length) return
  const scrollerRect = scroller.getBoundingClientRect()
  const top = scrollerRect.top - scroller.clientHeight * 0.8
  const bottom = scrollerRect.bottom + scroller.clientHeight * 0.8
  const token = loadToken
  const candidates: Array<{ pageNumber: number; distance: number }> = []
  pageRefs.forEach((el, pageNumber) => {
    const rect = el.getBoundingClientRect()
    if (rect.bottom >= top && rect.top <= bottom) {
      candidates.push({
        pageNumber,
        distance: Math.abs(rect.top - scrollerRect.top)
      })
    }
  })
  candidates
    .sort((a, b) => a.distance - b.distance)
    .slice(0, 6)
    .forEach(({ pageNumber }) => {
      void renderPage(pageNumber, token)
    })
}

const scheduleVisibleRender = () => {
  if (visibleRenderFrame) return
  visibleRenderFrame = window.requestAnimationFrame(() => {
    visibleRenderFrame = undefined
    renderVisiblePages()
  })
}

const loadDocument = async () => {
  if (!props.url) return
  const token = ++loadToken
  loading.value = true
  error.value = ''
  pages.value = []
  pdfPageTotal.value = 0
  canvasRefs.clear()
  pageRefs.clear()
  blockRefs.clear()
  await destroyDocument()

  try {
    const sourceUrl = new URL(props.url, window.location.href).toString()
    const doc = await pdfjsLib.getDocument({
      url: sourceUrl,
      withCredentials: true,
      cMapUrl: `${pdfAssetBase}/cmaps/`,
      cMapPacked: true,
      standardFontDataUrl: `${pdfAssetBase}/standard_fonts/`,
      rangeChunkSize: 1024 * 1024,
      disableRange: false,
      disableStream: true,
      disableAutoFetch: true
    }).promise
    if (token !== loadToken) {
      await doc.destroy()
      return
    }
    pdfDoc.value = doc
    pdfPageTotal.value = doc.numPages
    const requestedPage = props.activePage || 1
    const width = targetPageWidth()
    pages.value = Array.from({ length: doc.numPages }, (_, index) => {
      const pageNumber = index + 1
      return {
        pageNumber,
        ...estimatedPageGeometry(pageNumber, width),
        renderState: 'idle' as const
      }
    })
    currentPage.value = requestedPage
    loading.value = false
    await nextTick()
    await scrollToPage(requestedPage)
  } catch (e) {
    if (token === loadToken) {
      const message = e instanceof Error && e.message ? `：${e.message}` : ''
      error.value = `PDF 加载失败${message}`
    }
  } finally {
    if (token === loadToken) {
      loading.value = false
    }
  }
}

const setZoom = (nextZoom: number) => {
  zoom.value = Math.min(1.6, Math.max(0.75, Number(nextZoom.toFixed(2))))
}

const blockStyle = (block: SourceBlock, page: PageGeometry) => {
  const sourcePage = pageSource(page.pageNumber)
  const sourceWidth = sourcePage?.width || page.sourceWidth
  const sourceHeight = sourcePage?.height || page.sourceHeight
  const [x0, y0, x1, y1] = block.bbox
  const left = Math.min(x0, x1)
  const top = Math.min(y0, y1)
  const width = Math.abs(x1 - x0)
  const height = Math.abs(y1 - y0)

  return {
    left: `${(left / sourceWidth) * 100}%`,
    top: `${(top / sourceHeight) * 100}%`,
    width: `${(width / sourceWidth) * 100}%`,
    height: `${(height / sourceHeight) * 100}%`
  }
}

const blockTitle = (block: SourceBlock) => {
  const text = block.text.length > 80 ? `${block.text.slice(0, 80)}...` : block.text
  return `${sourceTypeLabel(block.type)}: ${text}`
}

const scrollToPage = async (pageNumber: number, behavior: ScrollBehavior = 'auto') => {
  await nextTick()
  const scroller = scrollRef.value
  const targetPage = clampPageNumber(pageNumber)
  if (!scroller) {
    pendingScrollPage = targetPage
    return
  }
  pendingScrollPage = undefined
  currentPage.value = targetPage
  if (useVirtualPages.value) {
    scroller.scrollTo({
      top: Math.max(0, pageOffsetBefore(targetPage) - 8),
      behavior
    })
    await nextTick()
  }
  const page = pageRefs.get(targetPage)
  if (!page) {
    pendingScrollPage = targetPage
    renderAroundPage(targetPage, 2)
    return
  }
  renderAroundPage(targetPage, 2)
  const scrollerRect = scroller.getBoundingClientRect()
  const pageRect = page.getBoundingClientRect()
  scroller.scrollTo({
    top: Math.max(0, scroller.scrollTop + pageRect.top - scrollerRect.top - 8),
    behavior
  })
}

const scrollToBlock = async (pageNumber: number, blockId: string) => {
  await nextTick()
  const scroller = scrollRef.value
  const block = blockRefs.get(blockId)
  if (!scroller || !block) {
    await scrollToPage(pageNumber)
    await nextTick()
    const retryBlock = blockRefs.get(blockId)
    if (!scroller || !retryBlock) return
    const scrollerRect = scroller.getBoundingClientRect()
    const blockRect = retryBlock.getBoundingClientRect()
    scroller.scrollTo({
      top: Math.max(0, scroller.scrollTop + blockRect.top - scrollerRect.top - scroller.clientHeight * 0.35),
      behavior: 'auto'
    })
    return
  }
  const scrollerRect = scroller.getBoundingClientRect()
  const blockRect = block.getBoundingClientRect()
  scroller.scrollTo({
    top: Math.max(0, scroller.scrollTop + blockRect.top - scrollerRect.top - scroller.clientHeight * 0.35),
    behavior: 'auto'
  })
}

const handleSourceBlockClick = (pageNumber: number, block: SourceBlock) => {
  currentPage.value = pageNumber
  emit('block-select', pageNumber, block.id)
}

const handleScroll = () => {
  const scroller = scrollRef.value
  if (!scroller || !pages.value.length) return
  let nextPage = currentPage.value
  if (useVirtualPages.value) {
    nextPage = pageFromScrollOffset(scroller.scrollTop + scroller.clientHeight * 0.35)
  } else {
    const scrollerTop = scroller.getBoundingClientRect().top
    const probeTop = scrollerTop + scroller.clientHeight * 0.35
    let nearestDistance = Number.POSITIVE_INFINITY
    pageRefs.forEach((el, pageNumber) => {
      const distance = Math.abs(el.getBoundingClientRect().top - probeTop)
      if (distance < nearestDistance) {
        nearestDistance = distance
        nextPage = pageNumber
      }
    })
  }

  if (nextPage !== currentPage.value) {
    currentPage.value = nextPage
    emit('page-change', nextPage)
    renderAroundPage(nextPage, 1)
  }
  scheduleVisibleRender()
}

const handleWheel = (event: WheelEvent) => {
  const scroller = scrollRef.value
  if (!scroller) return
  scroller.scrollTop += event.deltaY
  scroller.scrollLeft += event.deltaX
  scheduleVisibleRender()
}

watch(() => props.url, loadDocument, { immediate: true })
watch(() => props.activePage, (pageNumber) => {
  if (!pageNumber || pageNumber === currentPage.value) return
  void scrollToPage(pageNumber)
})
watch(zoom, loadDocument)

onBeforeUnmount(() => {
  loadToken += 1
  void destroyDocument()
})

defineExpose({ scrollToPage, scrollToBlock })
</script>

<style scoped>
.pdf-source-viewer {
  height: calc(100vh - 120px);
  min-height: 420px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
}

.pdf-source-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-light);
  background: color-mix(in srgb, var(--bg-primary) 88%, transparent);
}

.pdf-source-title {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pdf-source-title span {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
}

.pdf-source-title small {
  color: var(--text-muted);
  font-size: 12px;
  white-space: nowrap;
}

.pdf-source-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.icon-btn {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  background: transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.icon-btn:hover:not(:disabled) {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.icon-btn:disabled {
  cursor: default;
  opacity: 0.35;
}

.pdf-source-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
  overscroll-behavior: contain;
  overflow-anchor: none;
  padding: 18px;
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--bg-secondary) 94%, #000 6%) 1px, transparent 1px),
    linear-gradient(color-mix(in srgb, var(--bg-secondary) 94%, #000 6%) 1px, transparent 1px),
    var(--bg-secondary);
  background-size: 28px 28px;
}

.pdf-source-state {
  min-height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 14px;
}

.pdf-source-state.error {
  color: var(--danger-color);
}

.pdf-page-shell {
  width: fit-content;
  margin: 0 auto 18px;
  transition: filter var(--transition-fast), transform var(--transition-fast);
}

.pdf-page-spacer {
  width: 1px;
  margin: 0 auto;
  pointer-events: none;
}

.pdf-page-shell.active {
  filter: drop-shadow(0 10px 28px rgb(0 0 0 / 10%));
}

.pdf-page-number {
  padding: 0 2px 8px;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
}

.pdf-page-canvas-wrap {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-sm);
  background: #fff;
  box-shadow: 0 1px 2px rgb(0 0 0 / 8%), 0 16px 42px rgb(0 0 0 / 10%);
}

.pdf-page-canvas {
  display: block;
}

.pdf-page-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 12px;
  background:
    linear-gradient(90deg, rgb(248 250 252 / 92%) 25%, rgb(241 245 249 / 92%) 37%, rgb(248 250 252 / 92%) 63%);
  background-size: 360px 100%;
  animation: pdf-placeholder-shimmer 1.4s ease-in-out infinite;
  pointer-events: none;
}

.pdf-source-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.source-box {
  position: absolute;
  border: 1px solid rgb(245 158 11 / 70%);
  border-radius: 3px;
  background: rgb(245 158 11 / 16%);
  opacity: 0;
  pointer-events: auto;
  transition: opacity var(--transition-fast), background var(--transition-fast), border-color var(--transition-fast);
}

.source-box.visible {
  opacity: 0.42;
}

.source-box.active {
  z-index: 2;
  opacity: 0.95;
  border-color: rgb(217 119 6 / 90%);
  background: rgb(251 191 36 / 32%);
  box-shadow: 0 0 0 2px rgb(251 191 36 / 16%);
}

@keyframes pdf-placeholder-shimmer {
  0% {
    background-position: -360px 0;
  }

  100% {
    background-position: 360px 0;
  }
}

@media (max-width: 768px) {
  .pdf-source-viewer {
    height: 50vh;
    min-height: 360px;
  }

  .pdf-source-scroll {
    padding: 12px;
  }
}
</style>
