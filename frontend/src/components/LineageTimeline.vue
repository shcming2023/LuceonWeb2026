<script setup lang="ts">
import type { MaterialLineage } from '@/types/material'
import StageStatusBadge from './StageStatusBadge.vue'
import { formatDateTime } from '@/utils/status'

defineProps<{ lineage: MaterialLineage }>()
</script>

<template>
  <el-timeline>
    <el-timeline-item v-for="item in lineage.pipeline_items" :key="`p-${item.id}`" :timestamp="formatDateTime(item.created_at || '')" placement="top">
      <strong>解析批次 #{{ item.run_id }}</strong>
      <StageStatusBadge :status="item.status" />
      <div class="mono-note">MinerU {{ item.mineru_run_id || '—' }} · Popo {{ item.popo_run_id || '—' }}</div>
    </el-timeline-item>
    <el-timeline-item v-for="job in lineage.metadata_jobs" :key="`m-${job.id}`" :timestamp="formatDateTime(job.created_at || '')" placement="top">
      <strong>AI 元数据任务 #{{ job.id }}</strong> <StageStatusBadge :status="job.status" />
    </el-timeline-item>
    <el-timeline-item v-for="job in lineage.workflow_jobs" :key="`w-${job.id}`" :timestamp="formatDateTime(job.created_at || '')" placement="top">
      <strong>Worker V2.3 {{ job.id }}</strong> <StageStatusBadge :status="job.status" />
      <div class="mono-note">{{ job.current_stage_key || '未开始' }}</div>
    </el-timeline-item>
    <el-timeline-item v-if="lineage.review.available" type="success">
      <strong>审阅对象 #{{ lineage.review.asset_id }}</strong>
    </el-timeline-item>
  </el-timeline>
</template>

<style scoped>
strong { margin-right: 8px; }
</style>
