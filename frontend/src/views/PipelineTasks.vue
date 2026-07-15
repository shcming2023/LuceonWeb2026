<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { materialsApi } from '@/api/materials'
import type { PipelineRun, PipelineRunItem } from '@/types/material'
import { ensureCurrentUser, useCurrentUser } from '@/utils/user'
import { formatDateTime } from '@/utils/status'
import StageStatusBadge from '@/components/StageStatusBadge.vue'
import PipelineRunItems from '@/components/PipelineRunItems.vue'
import './workspace.css'

const route = useRoute()
const router = useRouter()
const currentUser = useCurrentUser()
const isAdmin = computed(() => Boolean(currentUser.value?.capabilities?.pipeline_admin))
const loading = ref(false)
const rows = ref<PipelineRun[]>([])
const total = ref(0)
const page = ref(Number(route.query.page) || 1)
const pageSize = ref(20)
const status = ref(String(route.query.status || ''))
const selectedRun = ref<PipelineRun | null>(null)
const detailOpen = ref(false)
const detailLoading = ref(false)
const recovering = ref(false)

function updateQuery() {
  router.replace({ query: { ...(status.value ? { status: status.value } : {}), ...(page.value > 1 ? { page: String(page.value) } : {}), ...(selectedRun.value ? { run_id: selectedRun.value.id } : {}) } })
}

async function load() {
  loading.value = true
  try {
    const result = await materialsApi.getPipelineRuns({ page: page.value, page_size: pageSize.value, status: status.value })
    rows.value = result.runs
    total.value = result.total
    const requested = String(route.query.run_id || '')
    if (requested) {
      const listed = rows.value.find(run => run.id === requested)
      if (listed) await openDetail(listed)
      else {
        const detail = await materialsApi.getPipelineRun(requested)
        selectedRun.value = detail
        detailOpen.value = true
      }
    }
    updateQuery()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '解析任务加载失败')
  } finally {
    loading.value = false
  }
}

function applyFilter() {
  page.value = 1
  load()
}

async function openDetail(run: PipelineRun) {
  detailOpen.value = true
  detailLoading.value = true
  try {
    selectedRun.value = await materialsApi.getPipelineRun(run.id)
    updateQuery()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '任务详情加载失败')
  } finally {
    detailLoading.value = false
  }
}

function closeDetail() {
  selectedRun.value = null
  const query = { ...route.query }
  delete query.run_id
  router.replace({ query })
}

async function recoverPopo(item: PipelineRunItem) {
  if (!isAdmin.value) return
  await ElMessageBox.confirm(`仅重跑《${item.filename}》的 Popo，复用已冻结 MinerU 资产。该入口只用于异常恢复。`, '管理员异常恢复', { type: 'warning' })
  recovering.value = true
  try {
    const check = await materialsApi.preflightPopoResume(item.material_pk)
    if (!check.ready) throw new Error(`恢复预检未通过：${check.status || check.plan_status}`)
    const run = await materialsApi.startPopoResume(item.material_pk)
    ElMessage.success(`异常恢复任务 #${run.id} 已排队`)
    await load()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '恢复 Popo 失败')
  } finally {
    recovering.value = false
  }
}

async function retryMetadata(item: PipelineRunItem) {
  const job = item.metadata_jobs?.[0]
  if (!job) return
  try {
    await materialsApi.retryMetadataJob(item.material_pk, job.id)
    ElMessage.success('AI 元数据任务已重新排队；不会覆盖人工确认内容')
    if (selectedRun.value) await openDetail(selectedRun.value)
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '编目任务重试失败')
  }
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
        <span class="workspace-kicker">Stage 2 · asynchronous pipeline</span>
        <h1>解析任务</h1>
        <p>每个批次固定教材快照；MinerU 与 Popo 按模型批量串行，结果按教材独立冻结与失败隔离。</p>
      </div>
      <div class="workspace-actions">
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
        <el-button type="primary" @click="router.push('/assets')">从 PDF 资产创建批次</el-button>
      </div>
    </header>

    <el-alert type="info" :closable="false" show-icon>
      <template #title>标准执行链：MinerU 批量 → 每本拉回并冻结 → 卸载 MinerU → Popo 批量 → 每本拉回并冻结 → AI 元数据任务。失败只影响对应教材。</template>
    </el-alert>

    <section class="workspace-panel">
      <div class="workspace-toolbar">
        <div class="workspace-filters">
          <el-select v-model="status" clearable placeholder="任务状态" style="width: 170px" @change="applyFilter">
            <el-option label="排队中" value="queued" />
            <el-option label="运行中" value="running" />
            <el-option label="已完成" value="succeeded" />
            <el-option label="部分失败" value="partial" />
            <el-option label="失败" value="failed" />
          </el-select>
        </div>
        <span class="mono-note">GPU 重任务全局串行 · 批次上限 5</span>
      </div>
      <el-table v-loading="loading" :data="rows" height="calc(100vh - 330px)" empty-text="暂无解析任务">
        <el-table-column label="批次" width="105"><template #default="{ row }"><el-button link @click="openDetail(row)">#{{ row.id }}</el-button></template></el-table-column>
        <el-table-column label="模式" width="130"><template #default="{ row }">{{ row.mode === 'popo_resume' ? '异常恢复' : '完整解析' }}</template></el-table-column>
        <el-table-column label="状态" width="120"><template #default="{ row }"><StageStatusBadge :status="row.status" /></template></el-table-column>
        <el-table-column prop="current_stage" label="当前阶段" min-width="145" />
        <el-table-column label="逐本结果" width="190"><template #default="{ row }">共 {{ row.total }} · 成功 {{ row.success }} · 失败 {{ row.failed }}</template></el-table-column>
        <el-table-column label="Worker / 租约" min-width="185"><template #default="{ row }"><span class="mono-note">{{ row.worker_id || '尚未领取' }}</span><span class="identity-meta">尝试 {{ row.attempt_count }}</span></template></el-table-column>
        <el-table-column label="创建时间" width="170"><template #default="{ row }">{{ formatDateTime(row.created_at || '') }}</template></el-table-column>
        <el-table-column label="操作" width="100" fixed="right"><template #default="{ row }"><el-button link @click="openDetail(row)">查看</el-button></template></el-table-column>
      </el-table>
      <div class="workspace-pagination"><el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" /></div>
    </section>

    <el-drawer v-model="detailOpen" size="86%" :title="selectedRun ? `解析批次 #${selectedRun.id}` : '解析任务详情'" @closed="closeDetail">
      <div v-loading="detailLoading || recovering">
        <el-descriptions v-if="selectedRun" :column="3" border class="detail-section">
          <el-descriptions-item label="状态"><StageStatusBadge :status="selectedRun.status" /></el-descriptions-item>
          <el-descriptions-item label="模式">{{ selectedRun.mode }}</el-descriptions-item>
          <el-descriptions-item label="当前阶段">{{ selectedRun.current_stage || '—' }}</el-descriptions-item>
          <el-descriptions-item label="幂等键"><span class="mono-note">{{ selectedRun.idempotency_key || '历史任务未登记' }}</span></el-descriptions-item>
          <el-descriptions-item label="心跳">{{ formatDateTime(selectedRun.heartbeat_at || '') || '—' }}</el-descriptions-item>
          <el-descriptions-item label="错误"><span class="error-note">{{ selectedRun.error_message }}</span></el-descriptions-item>
        </el-descriptions>
        <section v-if="selectedRun" class="detail-section">
          <h3>逐本状态与阶段证据</h3>
          <PipelineRunItems :items="selectedRun.items || []" :show-recovery="isAdmin" @recover-popo="recoverPopo" @retry-metadata="retryMetadata" />
        </section>
        <el-alert v-if="!isAdmin" type="info" :closable="false" title="“恢复 Popo”仅向具备 pipeline_admin 权限的管理员显示，普通流程不会要求用户手动提交 Popo。" />
      </div>
    </el-drawer>
  </div>
</template>
