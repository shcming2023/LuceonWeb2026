<template>
  <div class="home-root">
    <header class="home-header">
      <div>
        <h1>LuceonWeb2026</h1>
        <p>PDF · MinerU · Popo · LaTeX</p>
      </div>
      <div class="home-actions">
        <el-button type="primary" :icon="Document" @click="$router.push('/files')">文件管理</el-button>
        <el-button :icon="View" @click="$router.push('/review/compare')">PDF 比对</el-button>
      </div>
    </header>

    <section class="overview-grid">
      <div class="overview-item">
        <span class="value">{{ summary?.total || 0 }}</span>
        <span class="label">材料总数</span>
      </div>
      <div class="overview-item">
        <span class="value">{{ pendingCount }}</span>
        <span class="label">待继续解析</span>
      </div>
      <div class="overview-item">
        <span class="value">{{ summary?.stages.popo_done || 0 }}</span>
        <span class="label">Popo</span>
      </div>
      <div class="overview-item">
        <span class="value">{{ summary?.stages.latex_done || 0 }}</span>
        <span class="label">LaTeX</span>
      </div>
    </section>

    <section class="stage-panel">
      <div class="panel-head">
        <strong>阶段分布</strong>
        <el-button link :icon="Refresh" :loading="loading" @click="loadSummary">刷新</el-button>
      </div>
      <div class="stage-list">
        <div v-for="item in stageRows" :key="item.key" class="stage-row">
          <span class="stage-name">{{ item.label }}</span>
          <el-progress :percentage="item.percent" :show-text="false" :stroke-width="8" />
          <span class="stage-count">{{ item.value }}</span>
        </div>
      </div>
    </section>

    <section v-if="summary?.latest_run" class="run-panel">
      <div class="panel-head">
        <strong>最近任务</strong>
        <el-tag :type="runType(summary.latest_run.status)" effect="plain">{{ runText(summary.latest_run.status) }}</el-tag>
      </div>
      <div class="run-meta">
        <span>{{ summary.latest_run.mode === 'apply' ? '生产运行' : '预检' }}</span>
        <span>{{ formatDate(summary.latest_run.started_at || summary.latest_run.created_at) }}</span>
      </div>
      <p v-if="summary.latest_run.error_message" class="run-error">{{ summary.latest_run.error_message }}</p>
    </section>
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
  gap: 18px;
  max-width: 980px;
  margin: 0 auto;
}

.home-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
}

.home-header h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: 28px;
  line-height: 1.2;
}

.home-header p {
  margin: 8px 0 0;
  color: var(--text-muted);
}

.home-actions {
  display: flex;
  gap: 10px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.overview-item,
.stage-panel,
.run-panel {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
}

.overview-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px;
}

.value {
  color: var(--text-primary);
  font-size: 28px;
  font-weight: 700;
}

.label,
.run-meta,
.run-error {
  color: var(--text-muted);
  font-size: 13px;
}

.stage-panel,
.run-panel {
  padding: 16px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  color: var(--text-primary);
}

.stage-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-row {
  display: grid;
  grid-template-columns: 76px 1fr 48px;
  align-items: center;
  gap: 12px;
}

.stage-name {
  color: var(--text-secondary);
  font-size: 13px;
}

.stage-count {
  color: var(--text-primary);
  font-weight: 600;
  text-align: right;
}

.run-meta {
  display: flex;
  gap: 14px;
}

.run-error {
  margin: 10px 0 0;
  color: var(--danger-color);
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
}
</style>
