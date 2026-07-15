<script setup lang="ts">
import { computed } from 'vue'
import type { MaterialArtifact } from '@/types/material'
import { materialsApi } from '@/api/materials'
import { formatFileSize } from '@/utils/format'
import StageStatusBadge from './StageStatusBadge.vue'

const props = defineProps<{ materialPk: string | number; artifacts: MaterialArtifact[] }>()
const groups = computed(() => {
  const order = ['source', 'mineru', 'popo', 'elegantbook', 'candidate']
  return order.map(stage => ({ stage, rows: props.artifacts.filter(row => row.stage === stage) })).filter(group => group.rows.length)
})
const stageLabel: Record<string, string> = { source: '源 PDF', mineru: 'MinerU', popo: 'MinerU + Popo', elegantbook: '精修输出', candidate: '人工接手候选' }
</script>

<template>
  <div v-if="groups.length" class="artifact-groups">
    <section v-for="group in groups" :key="group.stage" class="artifact-group">
      <h4>{{ stageLabel[group.stage] || group.stage }}</h4>
      <div v-for="artifact in group.rows" :key="artifact.artifact_id" class="artifact-row">
        <div class="artifact-copy">
          <strong>{{ artifact.label }}</strong>
          <span>{{ artifact.run_id || artifact.output_id || '当前资产' }} · {{ formatFileSize(artifact.size_bytes || 0) }}</span>
          <span v-if="artifact.sha256" class="mono-note">SHA {{ artifact.sha256.slice(0, 18) }}…</span>
        </div>
        <StageStatusBadge :status="artifact.download_available ? artifact.verification_status : 'unavailable'" />
        <el-button
          size="small"
          :disabled="!artifact.download_available"
          tag="a"
          :href="materialsApi.getArtifactDownloadUrl(String(materialPk), artifact.artifact_id)"
        >下载</el-button>
      </div>
    </section>
  </div>
  <div v-else class="empty-note">暂无已登记数字资产</div>
</template>

<style scoped>
.artifact-groups { display: grid; gap: 16px; }
.artifact-group h4 { margin: 0 0 7px; color: var(--text-secondary); font-size: 12px; }
.artifact-row { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 10px; align-items: center; padding: 9px 0; border-bottom: 1px solid var(--border-light); }
.artifact-copy { display: flex; min-width: 0; flex-direction: column; }
.artifact-copy strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.artifact-copy span { color: var(--text-muted); font-size: 11px; }
</style>
