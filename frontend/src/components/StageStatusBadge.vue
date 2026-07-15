<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string; label?: string }>()

const type = computed(() => {
  if (['succeeded', 'success', 'completed', 'done', 'frozen', 'available', 'passed', 'published'].includes(props.status)) return 'success'
  if (['failed', 'error', 'cancelled', 'rejected'].includes(props.status)) return 'danger'
  if (['queued', 'running', 'validating', 'needs_review', 'partial', 'retrying'].includes(props.status)) return 'warning'
  return 'info'
})

const text = computed(() => props.label || ({
  queued: '排队中', running: '运行中', succeeded: '已完成', partial: '部分失败', failed: '失败',
  needs_review: '需人工接手', frozen: '已冻结', available: '可下载', unavailable: '不可用',
  input: '仅 PDF', mineru_done: 'MinerU 完成', popo_done: '解析完成', idle: '空闲'
} as Record<string, string>)[props.status] || props.status || '未知')
</script>

<template><el-tag :type="type" effect="plain" size="small">{{ text }}</el-tag></template>
