<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { materialsApi, type WorkflowV2JobSummary } from '@/api/materials'
import type { MaterialItem } from '@/types/material'
import { formatDateTime } from '@/utils/status'
import MaterialIdentity from '@/components/MaterialIdentity.vue'
import StageStatusBadge from '@/components/StageStatusBadge.vue'
import './workspace.css'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const rows = ref<WorkflowV2JobSummary[]>([])
const total = ref(0)
const page = ref(Number(route.query.page) || 1)
const pageSize = ref(20)
const status = ref(String(route.query.status || ''))

const createOpen = ref(false)
const materialLoading = ref(false)
const eligibleMaterials = ref<MaterialItem[]>([])
const selectedMaterials = ref<MaterialItem[]>([])
const materialSearch = ref('')
const creating = ref(false)

const detailOpen = ref(false)
const detailLoading = ref(false)
const selectedJob = ref<Record<string, any> | null>(null)
const candidate = ref<Record<string, any> | null>(null)

function updateQuery() {
  router.replace({ query: { ...(status.value ? { status: status.value } : {}), ...(page.value > 1 ? { page: String(page.value) } : {}), ...(selectedJob.value ? { job_id: selectedJob.value.id } : {}) } })
}

async function load() {
  loading.value = true
  try {
    const result = await materialsApi.getWorkflowV2JobSummaryPage({ page: page.value, page_size: pageSize.value, status: status.value })
    rows.value = result.jobs
    total.value = result.total
    const requested = String(route.query.job_id || '')
    if (requested) await openDetail(requested)
    updateQuery()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '精修任务加载失败')
  } finally {
    loading.value = false
  }
}

function applyFilter() {
  page.value = 1
  load()
}

async function openCreate() {
  createOpen.value = true
  selectedMaterials.value = []
  await loadEligibleMaterials()
}

async function loadEligibleMaterials() {
  materialLoading.value = true
  try {
    const result = await materialsApi.getMaterials({ page: 1, page_size: 100, stage: 'popo', search: materialSearch.value })
    eligibleMaterials.value = result.materials
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '解析就绪材料加载失败')
  } finally {
    materialLoading.value = false
  }
}

function onMaterialSelection(value: MaterialItem[]) {
  selectedMaterials.value = value
}

async function createJobs() {
  if (!selectedMaterials.value.length) return
  creating.value = true
  try {
    const result = await materialsApi.createWorkflowV2JobsBatch(selectedMaterials.value.map(row => Number(row.id)))
    ElMessage.success(`已创建 ${result.created || 0} 个任务，复用 ${result.existing || 0} 个现有任务，失败 ${result.failed || 0} 个`)
    createOpen.value = false
    await load()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '精修任务创建失败')
  } finally {
    creating.value = false
  }
}

async function runJob(job: WorkflowV2JobSummary) {
  await ElMessageBox.confirm(`开始执行 ${job.id}？Worker 会异步运行，页面可随时退出。`, '运行精修任务', { type: 'info' })
  try {
    await materialsApi.runWorkflowV2Job(job.id)
    ElMessage.success('任务已进入 Worker 队列')
    await load()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '任务入队失败')
  }
}

async function retryJob(job: WorkflowV2JobSummary) {
  try {
    await materialsApi.retryWorkflowV2Job(job.id)
    ElMessage.success('已从失败阶段重试')
    await load()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '重试失败')
  }
}

async function openDetail(jobId: string) {
  detailOpen.value = true
  detailLoading.value = true
  candidate.value = null
  try {
    selectedJob.value = await materialsApi.getWorkflowV2Job(jobId)
    if (selectedJob.value.status === 'needs_review') {
      candidate.value = await materialsApi.getWorkflowV2ReviewCandidate(jobId)
    }
    updateQuery()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '任务详情加载失败')
  } finally {
    detailLoading.value = false
  }
}

function closeDetail() {
  selectedJob.value = null
  candidate.value = null
  const query = { ...route.query }
  delete query.job_id
  router.replace({ query })
}

async function handoff() {
  if (!selectedJob.value) return
  try {
    await materialsApi.handoffWorkflowV2ReviewCandidate(selectedJob.value.id)
    ElMessage.success('人工接手已登记；请下载候选 PDF、问题证据和待修复 ZIP')
    await openDetail(selectedJob.value.id)
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '人工交接登记失败')
  }
}

async function revalidate() {
  if (!selectedJob.value) return
  try {
    await materialsApi.revalidateWorkflowV2ReviewCandidate(selectedJob.value.id)
    ElMessage.success('已从最小失败阶段重新验证')
    detailOpen.value = false
    await load()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '重新验证失败')
  }
}

function openReview(job: WorkflowV2JobSummary) {
  if (job.review_asset_id) router.push({ path: '/review/compare', query: { asset_id: job.review_asset_id } })
}

function openMaterial(job: WorkflowV2JobSummary) {
  router.push({ path: '/assets', query: { material_pk: job.material_pk, search: job.material_id } })
}

watch(page, load)
onMounted(async () => {
  const linkedMaterialPk = String(route.query.material_pk || '')
  const linkedMaterialId = String(route.query.material_id || '')
  await load()
  if (linkedMaterialPk) {
    materialSearch.value = linkedMaterialId
    await openCreate()
    const requested = eligibleMaterials.value.find(row => row.id === linkedMaterialPk)
    if (requested) selectedMaterials.value = [requested]
  }
})
</script>

<template>
  <div class="workspace-page">
    <header class="workspace-header">
      <div>
        <span class="workspace-kicker">Stage 3 · Worker V2.3</span>
        <h1>精修任务</h1>
        <p>从已冻结 Popo 资产创建异步 Worker 任务，明确区分成功、失败与需人工接手。</p>
      </div>
      <div class="workspace-actions">
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
        <el-button type="primary" @click="openCreate">创建精修任务</el-button>
      </div>
    </header>

    <section class="workspace-panel">
      <div class="workspace-toolbar">
        <div class="workspace-filters">
          <el-select v-model="status" clearable placeholder="任务状态" style="width: 180px" @change="applyFilter">
            <el-option label="排队中" value="queued" />
            <el-option label="运行中" value="running" />
            <el-option label="需人工接手" value="needs_review" />
            <el-option label="失败" value="failed" />
            <el-option label="已完成" value="succeeded" />
          </el-select>
        </div>
        <span class="mono-note">任务记录与浏览器会话解耦，刷新或退出不会丢失进度</span>
      </div>
      <el-table v-loading="loading" :data="rows" height="calc(100vh - 286px)" empty-text="暂无精修任务">
        <el-table-column label="教材" min-width="280"><template #default="{ row }"><MaterialIdentity :filename="row.filename || row.material_id" :material-id="row.material_id" :material-pk="row.material_pk" /></template></el-table-column>
        <el-table-column label="任务" min-width="180"><template #default="{ row }"><el-button link @click="openDetail(row.id)">{{ row.id }}</el-button><span class="identity-meta">{{ row.workflow_version }}</span></template></el-table-column>
        <el-table-column label="状态" width="130"><template #default="{ row }"><StageStatusBadge :status="row.status" /></template></el-table-column>
        <el-table-column label="当前阶段 / 尝试" min-width="180"><template #default="{ row }">{{ row.current_stage_key || '—' }}<span class="identity-meta">尝试 {{ row.current_attempt || 0 }} · {{ row.current_stage_status }}</span></template></el-table-column>
        <el-table-column label="输入 / 输出" min-width="190"><template #default="{ row }"><span class="mono-note" :title="row.source_popo_manifest?.object">Popo {{ row.source_popo_manifest?.object?.split('/').at(-2) || '—' }}</span><span class="identity-meta">Output {{ row.current_output_id || '尚未接受' }}</span></template></el-table-column>
        <el-table-column label="证据" width="180"><template #default="{ row }">产物 {{ row.artifact_count }} · 发现 {{ row.open_finding_count }}<span class="identity-meta">事件 {{ row.event_count }} · 模型调用 {{ row.model_call_count }}</span></template></el-table-column>
        <el-table-column label="问题" min-width="190"><template #default="{ row }"><span class="error-note">{{ row.error?.message }}</span></template></el-table-column>
        <el-table-column label="更新时间" width="170"><template #default="{ row }">{{ formatDateTime(row.updated_at || row.created_at || '') }}</template></el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link @click="openDetail(row.id)">详情</el-button>
            <el-button link @click="openMaterial(row)">材料谱系</el-button>
            <el-button v-if="row.status === 'queued'" link @click="runJob(row)">运行</el-button>
            <el-button v-if="row.status === 'failed'" link @click="retryJob(row)">重试失败阶段</el-button>
            <el-button v-if="row.status === 'succeeded' && row.review_asset_id" link @click="openReview(row)">比对审阅</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="workspace-pagination"><el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" /></div>
    </section>

    <el-dialog v-model="createOpen" title="从解析就绪资产创建 Worker V2.3 任务" width="900px">
      <div class="workspace-filters" style="margin-bottom: 12px">
        <el-input v-model="materialSearch" placeholder="搜索教材" style="width: 300px" @keyup.enter="loadEligibleMaterials"><template #prefix><el-icon><Search /></el-icon></template></el-input>
        <el-button @click="loadEligibleMaterials">查询</el-button>
      </div>
      <el-table v-loading="materialLoading" :data="eligibleMaterials" row-key="id" max-height="460" @selection-change="onMaterialSelection">
        <el-table-column type="selection" width="46" />
        <el-table-column label="教材" min-width="330"><template #default="{ row }"><MaterialIdentity :filename="row.filename" :material-id="row.material_id" :material-pk="row.id" /></template></el-table-column>
        <el-table-column label="Popo Run" min-width="180"><template #default="{ row }"><span class="mono-note">{{ row.popo_run_id }}</span></template></el-table-column>
        <el-table-column label="现有精修" width="130"><template #default="{ row }"><StageStatusBadge :status="row.codex_job?.status || 'idle'" /></template></el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="createOpen = false">取消</el-button>
        <el-button type="primary" :disabled="!selectedMaterials.length" :loading="creating" @click="createJobs">创建 {{ selectedMaterials.length }} 个任务</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailOpen" size="82%" :title="selectedJob ? `Worker V2.3 · ${selectedJob.id}` : '精修任务详情'" @closed="closeDetail">
      <div v-loading="detailLoading">
        <el-descriptions v-if="selectedJob" :column="3" border class="detail-section">
          <el-descriptions-item label="状态"><StageStatusBadge :status="selectedJob.status" /></el-descriptions-item>
          <el-descriptions-item label="教材">#{{ selectedJob.material_pk }} · {{ selectedJob.material_id }}</el-descriptions-item>
          <el-descriptions-item label="当前阶段">{{ selectedJob.current_stage_key }} / {{ selectedJob.current_stage_status }}</el-descriptions-item>
          <el-descriptions-item label="输入 Popo" :span="3"><span class="mono-note">{{ selectedJob.source_popo_manifest?.bucket }}/{{ selectedJob.source_popo_manifest?.object }}</span></el-descriptions-item>
          <el-descriptions-item label="错误" :span="3"><span class="error-note">{{ selectedJob.error_message || '—' }}</span></el-descriptions-item>
        </el-descriptions>

        <section v-if="candidate" class="detail-section">
          <h3>needs_review 人工闭环</h3>
          <el-alert type="warning" :closable="false" title="needs_review 不是完成状态：必须检查候选 PDF 与证据、下载待修复 ZIP、登记交接并重新验证。" />
          <div class="inline-actions" style="margin-top: 12px">
            <el-button tag="a" target="_blank" :href="candidate.files?.pdf">查看候选 PDF</el-button>
            <el-button tag="a" :href="candidate.files?.latex">下载待修复 ZIP</el-button>
            <el-button tag="a" :href="candidate.files?.validation">下载问题证据</el-button>
            <el-button type="warning" @click="handoff">登记人工接手</el-button>
            <el-button type="primary" @click="revalidate">重新验证</el-button>
          </div>
          <pre class="candidate-blockers">{{ JSON.stringify(candidate.blockers, null, 2) }}</pre>
        </section>

        <section v-if="selectedJob" class="detail-section">
          <h3>阶段尝试</h3>
          <el-table :data="selectedJob.stages || []" size="small">
            <el-table-column prop="stage_key" label="阶段" min-width="190" />
            <el-table-column prop="attempt" label="尝试" width="80" />
            <el-table-column label="状态" width="130"><template #default="{ row }"><StageStatusBadge :status="row.status" /></template></el-table-column>
            <el-table-column prop="error_message" label="错误" min-width="220" />
          </el-table>
        </section>

        <section v-if="selectedJob" class="detail-section">
          <h3>产物与质量发现</h3>
          <el-tabs>
            <el-tab-pane :label="`已登记输出 ${selectedJob.outputs?.length || 0}`"><pre>{{ JSON.stringify(selectedJob.outputs || [], null, 2) }}</pre></el-tab-pane>
            <el-tab-pane :label="`产物 ${selectedJob.artifacts?.length || 0}`"><pre>{{ JSON.stringify(selectedJob.artifacts || [], null, 2) }}</pre></el-tab-pane>
            <el-tab-pane :label="`质量发现 ${selectedJob.qa_findings?.length || 0}`"><pre>{{ JSON.stringify(selectedJob.qa_findings || [], null, 2) }}</pre></el-tab-pane>
            <el-tab-pane :label="`修复记录 ${selectedJob.repair_attempts?.length || 0}`"><pre>{{ JSON.stringify(selectedJob.repair_attempts || [], null, 2) }}</pre></el-tab-pane>
          </el-tabs>
        </section>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.candidate-blockers, pre { max-height: 320px; overflow: auto; padding: 12px; border-radius: 6px; background: #111827; color: #e5e7eb; font-size: 11px; }
</style>
