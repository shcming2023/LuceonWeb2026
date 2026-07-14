<template>
  <div class="home-root">
    <header class="home-header">
      <div>
        <span class="page-kicker">控制台</span>
        <h1>工作概览</h1>
        <p>材料处理与产物状态</p>
      </div>
      <div class="home-actions">
        <el-button type="primary" :icon="Document" @click="$router.push('/files')">文件管理</el-button>
        <el-button :icon="View" @click="$router.push('/review/compare')">PDF 比对</el-button>
      </div>
    </header>

    <section class="overview-grid" aria-label="材料概览">
      <div class="overview-item tone-total">
        <span class="value">{{ summary?.total || 0 }}</span>
        <span class="label">材料总数</span>
      </div>
      <div class="overview-item tone-pending">
        <span class="value">{{ pendingCount }}</span>
        <span class="label">待继续解析</span>
      </div>
      <div class="overview-item tone-popo">
        <span class="value">{{ summary?.stages.popo_done || 0 }}</span>
        <span class="label">Popo</span>
      </div>
      <div class="overview-item tone-latex">
        <span class="value">{{ summary?.stages.latex_done || 0 }}</span>
        <span class="label">LaTeX</span>
      </div>
    </section>

    <div class="dashboard-grid">
      <section class="stage-panel">
        <div class="panel-head">
          <div>
            <strong>阶段分布</strong>
            <span>当前材料所处的最高完成阶段</span>
          </div>
          <el-button link :icon="Refresh" :loading="loading" @click="loadSummary">刷新</el-button>
        </div>
        <div class="stage-list">
          <div v-for="item in stageRows" :key="item.key" class="stage-row">
            <span class="stage-name">{{ item.label }}</span>
            <el-progress :percentage="item.percent" :show-text="false" :stroke-width="7" />
            <span class="stage-percent">{{ item.percent }}%</span>
            <span class="stage-count">{{ item.value }}</span>
          </div>
        </div>
      </section>

      <section class="run-panel">
        <div class="panel-head">
          <div>
            <strong>最近任务</strong>
            <span>最近一次批处理运行</span>
          </div>
          <el-tag v-if="summary?.latest_run" :type="runType(summary.latest_run.status)" effect="plain">
            {{ runText(summary.latest_run.status) }}
          </el-tag>
        </div>
        <template v-if="summary?.latest_run">
          <div class="run-state">
            <span>{{ summary.latest_run.mode === 'apply' ? '生产运行' : '预检' }}</span>
            <strong>{{ runText(summary.latest_run.status) }}</strong>
          </div>
          <div class="run-meta">
            <span>{{ formatDate(summary.latest_run.started_at || summary.latest_run.created_at) }}</span>
          </div>
          <p v-if="summary.latest_run.error_message" class="run-error">{{ summary.latest_run.error_message }}</p>
        </template>
        <div v-else class="run-empty">暂无运行记录</div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Document, Refresh, View } from '@element-plus/icons-vue'
import { materialsApi } from '@/api/materials'
import type { MaterialSummary } from '@/types/material'
import { formatDateTime } from '@/utils/status'

const loading = ref(false)
const summary = ref<MaterialSummary | null>(null)

const stageLabels = [
  { key: 'input', label: 'PDF' },
  { key: 'mineru_done', label: 'MinerU' },
  { key: 'popo_done', label: 'Popo' },
  { key: 'latex_done', label: 'LaTeX' }
]

const pendingCount = computed(() => {
  const stages = summary.value?.stages || {}
  return (stages.input || 0) + (stages.mineru_done || 0) + (stages.popo_done || 0)
})

const stageRows = computed(() => {
  const total = Math.max(summary.value?.total || 0, 1)
  const stages = summary.value?.stages || {}
  return stageLabels.map(item => {
    const value = stages[item.key] || 0
    return {
      ...item,
      value,
      percent: Math.round((value / total) * 100)
    }
  })
})

async function loadSummary() {
  loading.value = true
  try {
    summary.value = await materialsApi.getSummary()
  } finally {
    loading.value = false
  }
}

function runText(status: string) {
  const map: Record<string, string> = {
    queued: '排队中',
    running: '运行中',
    succeeded: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

function runType(status: string) {
  if (status === 'succeeded') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'running' || status === 'queued') return 'warning'
  return 'info'
}

function formatDate(value?: string | null) {
  return value ? formatDateTime(value) : ''
}

onMounted(loadSummary)
</script>

<style scoped>
.home-root {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

.home-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 18px;
  padding-bottom: 2px;
}

.page-kicker {
  display: block;
  margin-bottom: 6px;
  color: var(--primary-dark);
  font-size: 12px;
  font-weight: 650;
}

.home-header h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: 26px;
  font-weight: 720;
  line-height: 1.25;
  letter-spacing: 0;
}

.home-header p {
  margin: 5px 0 0;
  color: var(--text-muted);
  font-size: 13px;
}

.home-actions {
  display: flex;
  gap: 10px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  overflow: hidden;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
}

.overview-item {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-height: 104px;
  padding: 18px 20px;
  border-right: 1px solid var(--border-light);
}

.overview-item:last-child {
  border-right: 0;
}

.overview-item::after {
  content: '';
  position: absolute;
  right: 18px;
  bottom: 18px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--border-color);
}

.tone-pending::after {
  background: var(--warning-color);
}

.tone-popo::after {
  background: var(--primary-color);
}

.tone-latex::after {
  background: var(--success-color);
}

.value {
  color: var(--text-primary);
  font-size: 30px;
  font-weight: 720;
  line-height: 1.1;
}

.label,
.run-meta,
.run-error {
  color: var(--text-muted);
  font-size: 13px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(280px, 0.8fr);
  gap: 16px;
  align-items: stretch;
}

.stage-panel,
.run-panel {
  min-height: 310px;
  padding: 18px 20px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 24px;
  color: var(--text-primary);
}

.panel-head > div {
  display: grid;
  gap: 3px;
}

.panel-head strong {
  font-size: 15px;
  font-weight: 680;
}

.panel-head span {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 400;
}

.stage-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stage-row {
  display: grid;
  grid-template-columns: 70px minmax(0, 1fr) 42px 42px;
  align-items: center;
  gap: 10px;
}

.stage-name {
  color: var(--text-secondary);
  font-size: 13px;
}

.stage-count {
  color: var(--text-primary);
  font-weight: 650;
  text-align: right;
}

.stage-percent {
  color: var(--text-muted);
  font-size: 11px;
  text-align: right;
}

.run-state {
  display: grid;
  gap: 6px;
  padding: 18px 0;
  border-top: 1px solid var(--border-light);
  border-bottom: 1px solid var(--border-light);
}

.run-state span {
  color: var(--text-muted);
  font-size: 12px;
}

.run-state strong {
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 680;
}

.run-meta {
  margin-top: 14px;
}

.run-error {
  margin: 14px 0 0;
  padding: 10px 12px;
  border-left: 3px solid var(--danger-color);
  background: rgb(217 45 32 / 0.04);
  color: var(--danger-color);
  line-height: 1.5;
}

.run-empty {
  display: grid;
  min-height: 190px;
  place-items: center;
  border-top: 1px solid var(--border-light);
  color: var(--text-muted);
  font-size: 13px;
}

@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .home-header,
  .home-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .overview-item:nth-child(2) {
    border-right: 0;
  }

  .overview-item:nth-child(-n + 2) {
    border-bottom: 1px solid var(--border-light);
  }

  .stage-row {
    grid-template-columns: 58px minmax(0, 1fr) 36px;
  }

  .stage-percent {
    display: none;
  }
}
</style>
