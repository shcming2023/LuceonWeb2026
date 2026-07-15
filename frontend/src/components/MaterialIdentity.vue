<script setup lang="ts">
defineProps<{
  filename: string
  materialId: string
  materialPk?: string | number
  sha256?: string
}>()
</script>

<template>
  <div class="material-identity" :title="filename">
    <span class="identity-title">{{ filename || '未命名 PDF' }}</span>
    <span class="identity-meta">#{{ materialPk || '—' }} · {{ materialId || '无 material_id' }}</span>
    <span v-if="sha256" class="identity-meta">SHA {{ sha256.slice(0, 14) }}…</span>
  </div>
</template>

<style scoped>
.material-identity { min-width: 0; line-height: 1.55; }
</style>
