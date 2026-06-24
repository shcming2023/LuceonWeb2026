<template>
  <div class="settings-root">
    <div class="settings-shell">
      <div class="page-header">
        <div class="header-icon">
          <el-icon :size="22"><Setting /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">运行设置</h1>
          <p class="page-subtitle">资产层、GPU 调度与备份</p>
        </div>
        <el-button :loading="loading.status" @click="refreshStatus">
          <el-icon><RefreshRight /></el-icon>
          <span>刷新状态</span>
        </el-button>
      </div>

      <el-tabs v-model="activeTab" class="settings-tabs">
        <el-tab-pane label="系统状态" name="status">
          <section class="settings-panel">
            <div class="panel-title">
              <span>运行总览</span>
              <el-tag :type="runtimeTagType">{{ runtimeStatusText }}</el-tag>
            </div>
            <div class="status-grid">
              <div class="status-cell">
                <span class="status-label">MinIO 合约</span>
                <strong>{{ status?.minio.contract_ok ? '正常' : '待处理' }}</strong>
                <small>{{ status?.minio.endpoint || runtime.minio.endpoint || '-' }}</small>
              </div>
              <div class="status-cell">
                <span class="status-label">GPU Wrapper</span>
                <strong>{{ status?.gpu.wrapper_ok ? '可用' : '不可用' }}</strong>
                <small>{{ status?.gpu.wrapper_url || runtime.gpu.wrapper_url || '-' }}</small>
              </div>
              <div class="status-cell">
                <span class="status-label">Staged API</span>
                <strong>{{ status?.gpu.staged_api_ok ? '可用' : '待确认' }}</strong>
                <small>{{ status?.gpu.ssh_status || 'ssh skipped' }}</small>
              </div>
              <div class="status-cell">
                <span class="status-label">备份目标</span>
                <strong>{{ status?.backup.ready_count ?? 0 }} 个可写</strong>
                <small>{{ lastBackupText }}</small>
              </div>
            </div>
            <div v-if="status?.blockers.length || status?.warnings.length" class="issue-list">
              <el-tag v-for="item in status.blockers" :key="`b-${item}`" type="danger">{{ item }}</el-tag>
              <el-tag v-for="item in status.warnings" :key="`w-${item}`" type="warning">{{ item }}</el-tag>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane label="MinIO 资产" name="minio">
          <section class="settings-panel">
            <div class="panel-title">
              <span>MinIO</span>
              <el-tag :type="minioReady ? 'success' : 'warning'">{{ minioReady ? '合约正常' : '需要检查' }}</el-tag>
            </div>
            <el-form :model="runtime.minio" label-position="top" class="settings-form">
              <div class="form-grid">
                <el-form-item label="Endpoint">
                  <el-input v-model="runtime.minio.endpoint" placeholder="127.0.0.1:9000" />
                </el-form-item>
                <el-form-item label="Public Endpoint">
                  <el-input v-model="runtime.minio.public_endpoint" placeholder="http://公网或内网地址:9000" />
                </el-form-item>
                <el-form-item label="Access Key">
                  <el-input v-model="runtime.minio.access_key" placeholder="留空表示沿用已保存值" />
                </el-form-item>
                <el-form-item label="Secret Key">
                  <el-input v-model="runtime.minio.secret_key" type="password" show-password placeholder="留空表示沿用已保存值" />
                </el-form-item>
                <el-form-item label="Region">
                  <el-input v-model="runtime.minio.region" />
                </el-form-item>
                <el-form-item label="HTTPS">
                  <el-switch v-model="runtime.minio.secure" />
                </el-form-item>
              </div>
            </el-form>

            <div class="bucket-table">
              <div class="table-row table-head">
                <span>篮子</span>
                <span>角色</span>
                <span>状态</span>
              </div>
              <div v-for="bucket in bucketRows" :key="bucket.bucket" class="table-row">
                <span>{{ bucket.bucket }}</span>
                <span>{{ bucket.role }}</span>
                <el-tag :type="bucket.exists ? 'success' : 'danger'">{{ bucket.exists ? '存在' : '缺失' }}</el-tag>
              </div>
            </div>

            <div class="panel-actions">
              <el-button :loading="loading.saving" @click="saveRuntime">
                <el-icon><Check /></el-icon>
                <span>保存</span>
              </el-button>
              <el-button :loading="loading.minio" @click="checkMinioNow">
                <el-icon><Connection /></el-icon>
                <span>检查 MinIO</span>
              </el-button>
              <el-button type="primary" :loading="loading.ensure" @click="ensureBuckets">
                <el-icon><FolderChecked /></el-icon>
                <span>维护篮子</span>
              </el-button>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane label="GPU 算力" name="gpu">
          <section class="settings-panel">
            <div class="panel-title">
              <span>GPU Wrapper</span>
              <el-tag :type="gpuReady ? 'success' : 'warning'">{{ gpuReady ? '可用' : '待确认' }}</el-tag>
            </div>
            <el-form :model="runtime.gpu" label-position="top" class="settings-form">
              <div class="form-grid">
                <el-form-item label="Wrapper URL">
                  <el-input v-model="runtime.gpu.wrapper_url" placeholder="http://gpu-host:18080" />
                </el-form-item>
                <el-form-item label="API Key">
                  <el-input v-model="runtime.gpu.api_key" type="password" show-password placeholder="留空表示沿用已保存值" />
                </el-form-item>
                <el-form-item label="SSH Host">
                  <el-input v-model="runtime.gpu.ssh_host" placeholder="113.31.105.253" />
                </el-form-item>
                <el-form-item label="SSH Port">
                  <el-input-number v-model="runtime.gpu.ssh_port" :min="1" :max="65535" controls-position="right" />
                </el-form-item>
                <el-form-item label="SSH User">
                  <el-input v-model="runtime.gpu.ssh_user" />
                </el-form-item>
                <el-form-item label="SSH Key Path">
                  <el-input v-model="runtime.gpu.ssh_key_path" placeholder="~/.ssh/id_ed25519" />
                </el-form-item>
                <el-form-item label="SSH Password">
                  <el-input v-model="runtime.gpu.ssh_password" type="password" show-password placeholder="留空表示沿用已保存值" />
                </el-form-item>
                <el-form-item label="Service Root">
                  <el-input v-model="runtime.gpu.service_root" />
                </el-form-item>
              </div>
            </el-form>

            <div v-if="gpuCheck" class="probe-grid">
              <div class="probe-row">
                <span>Wrapper Health</span>
                <el-tag :type="gpuCheck.wrapper_ok ? 'success' : 'danger'">{{ gpuCheck.wrapper_ok ? 'OK' : 'FAIL' }}</el-tag>
              </div>
              <div class="probe-row">
                <span>Staged API</span>
                <el-tag :type="gpuCheck.staged_api_ok ? 'success' : 'warning'">{{ gpuCheck.staged_api_ok ? 'OK' : 'CHECK' }}</el-tag>
              </div>
              <div class="probe-row">
                <span>SSH</span>
                <el-tag :type="gpuCheck.ssh_ok ? 'success' : gpuCheck.ssh_status === 'skipped' ? 'info' : 'warning'">{{ gpuCheck.ssh_status }}</el-tag>
              </div>
            </div>

            <div class="panel-actions">
              <el-button :loading="loading.saving" @click="saveRuntime">
                <el-icon><Check /></el-icon>
                <span>保存</span>
              </el-button>
              <el-button type="primary" :loading="loading.gpu" @click="checkGpuNow">
                <el-icon><Monitor /></el-icon>
                <span>检查 GPU</span>
              </el-button>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane label="模型配置" name="models">
          <section class="settings-panel">
            <div class="panel-title">
              <span>模型配置</span>
              <el-tag :type="modelConnectivityTag">{{ modelConnectivityText }}</el-tag>
            </div>
            <el-form :model="runtime.models" label-position="top" class="settings-form">
              <div class="model-section">
                <div class="model-section-title">
                  <strong>目录重建 LLM</strong>
                  <el-switch v-model="runtime.models.llm.enabled" active-text="启用" inactive-text="停用" />
                </div>
                <div class="form-grid">
                  <el-form-item label="Provider">
                    <el-input v-model="runtime.models.llm.provider" disabled />
                  </el-form-item>
                  <el-form-item label="默认模型">
                    <el-input v-model="runtime.models.llm.default_model" placeholder="deepseek-v4-flash" />
                  </el-form-item>
                  <el-form-item label="推理模型">
                    <el-input v-model="runtime.models.llm.reasoning_model" placeholder="deepseek-v4-pro" />
                  </el-form-item>
                  <el-form-item label="DeepSeek Base URL">
                    <el-input v-model="runtime.models.llm.deepseek.base_url" placeholder="https://api.deepseek.com" />
                  </el-form-item>
                  <el-form-item label="DeepSeek API Key">
                    <el-input v-model="runtime.models.llm.deepseek.api_key" type="password" show-password placeholder="留空表示沿用已保存值" />
                  </el-form-item>
                  <el-form-item label="目录候选上限">
                    <el-input-number v-model="runtime.models.llm.outline_max_risk_candidates" :min="1" :max="1000" controls-position="right" />
                  </el-form-item>
                  <el-form-item label="全局候选上限">
                    <el-input-number v-model="runtime.models.llm.outline_global_max_candidates" :min="1" :max="5000" controls-position="right" />
                  </el-form-item>
                  <el-form-item label="输出 Token 上限">
                    <el-input-number v-model="runtime.models.llm.outline_decision_max_tokens" :min="1000" :max="64000" :step="1000" controls-position="right" />
                  </el-form-item>
                </div>
              </div>

              <div class="model-section">
                <div class="model-section-title">
                  <strong>目录视觉核实</strong>
                  <el-switch v-model="runtime.models.vision.enabled" active-text="启用" inactive-text="停用" />
                </div>
                <div class="form-grid">
                  <el-form-item label="Provider">
                    <el-input v-model="runtime.models.vision.provider" disabled />
                  </el-form-item>
                  <el-form-item label="视觉模型">
                    <el-input v-model="runtime.models.vision.model" placeholder="qwen3.7-plus" />
                  </el-form-item>
                  <el-form-item label="DashScope Base URL">
                    <el-input v-model="runtime.models.vision.dashscope.base_url" placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1" />
                  </el-form-item>
                  <el-form-item label="DashScope API Key">
                    <el-input v-model="runtime.models.vision.dashscope.api_key" type="password" show-password placeholder="留空表示沿用已保存值" />
                  </el-form-item>
                  <el-form-item label="视觉候选上限">
                    <el-input-number v-model="runtime.models.vision.outline_visual_max_candidates" :min="1" :max="1000" controls-position="right" />
                  </el-form-item>
                </div>
              </div>

              <div class="model-section">
                <div class="model-section-title">
                  <strong>预留模型</strong>
                </div>
                <div class="form-grid">
                  <el-form-item label="ASR 模型">
                    <el-input v-model="runtime.models.asr.model" placeholder="fun-asr-flash-2026-06-15" />
                  </el-form-item>
                  <el-form-item label="TTS 模型">
                    <el-input v-model="runtime.models.tts.model" placeholder="qwen3-tts-instruct-flash-realtime" />
                  </el-form-item>
                  <el-form-item label="图片生成模型">
                    <el-input v-model="runtime.models.image_generation.model" placeholder="qwen-image-2.0-pro" />
                  </el-form-item>
                </div>
              </div>
            </el-form>

            <div class="probe-grid">
              <div class="probe-row">
                <span>LLM</span>
                <el-tag :type="modelProbeType(modelCheck?.checks.llm, runtime.models.llm.enabled && llmKeyReady)">
                  {{ modelProbeText(modelCheck?.checks.llm, runtime.models.llm.enabled && llmKeyReady) }}
                </el-tag>
              </div>
              <div class="probe-row">
                <span>Vision</span>
                <el-tag :type="modelProbeType(modelCheck?.checks.vision, visionKeyReady)">
                  {{ modelProbeText(modelCheck?.checks.vision, visionKeyReady) }}
                </el-tag>
              </div>
            </div>
            <div v-if="modelCheck" class="model-test-detail">
              <span>{{ modelProbeDetail(modelCheck.checks.llm) }}</span>
              <span>{{ modelProbeDetail(modelCheck.checks.vision) }}</span>
            </div>

            <div class="panel-actions">
              <el-button :loading="loading.saving" @click="saveRuntime">
                <el-icon><Check /></el-icon>
                <span>保存</span>
              </el-button>
              <el-button type="primary" :loading="loading.models" @click="checkModelsNow">
                <el-icon><Connection /></el-icon>
                <span>测试模型</span>
              </el-button>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane label="备份策略" name="backup">
          <section class="settings-panel">
            <div class="panel-title">
              <span>资产备份</span>
              <el-tag :type="backupReady ? 'success' : 'warning'">{{ backupReady ? '目标可写' : '待检查' }}</el-tag>
            </div>
            <el-form :model="runtime.backup" label-position="top" class="settings-form">
              <div class="form-grid">
                <el-form-item label="启用备份">
                  <el-switch v-model="runtime.backup.enabled" />
                </el-form-item>
                <el-form-item label="备份模式">
                  <el-segmented v-model="runtime.backup.mode" :options="backupModes" />
                </el-form-item>
                <el-form-item label="定时策略">
                  <el-switch v-model="runtime.backup.schedule_enabled" />
                </el-form-item>
                <el-form-item label="间隔小时">
                  <el-input-number v-model="runtime.backup.interval_hours" :min="1" :max="720" controls-position="right" />
                </el-form-item>
                <el-form-item label="包含辅助对象">
                  <el-switch v-model="runtime.backup.include_auxiliary" />
                </el-form-item>
                <el-form-item label="对象上限">
                  <el-input-number v-model="runtime.backup.max_objects" :min="100" :max="500000" :step="1000" controls-position="right" />
                </el-form-item>
              </div>
            </el-form>

            <div class="target-list">
              <div v-for="target in runtime.backup.targets" :key="target.id" class="target-row">
                <el-switch v-model="target.enabled" />
                <span class="target-label">{{ target.label }}</span>
                <el-input v-model="target.path" placeholder="/Volumes/.../LuceonBackup" />
                <el-tag :type="targetStatusType(target.status)">{{ target.status || 'unknown' }}</el-tag>
              </div>
            </div>

            <div v-if="backupRun" class="backup-result">
              <span>最近手动备份</span>
              <strong>{{ backupRun.object_count }} 个对象</strong>
              <small>{{ backupRun.targets.map(target => target.path).join(' / ') || '-' }}</small>
            </div>

            <div class="panel-actions">
              <el-button :loading="loading.saving" @click="saveRuntime">
                <el-icon><Check /></el-icon>
                <span>保存</span>
              </el-button>
              <el-button :loading="loading.backup" @click="checkBackupNow">
                <el-icon><FolderChecked /></el-icon>
                <span>检查路径</span>
              </el-button>
              <el-button type="primary" :loading="loading.backupRun" @click="runBackupNow">
                <el-icon><Upload /></el-icon>
                <span>手动备份</span>
              </el-button>
            </div>
          </section>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Connection, FolderChecked, Monitor, RefreshRight, Setting, Upload } from '@element-plus/icons-vue'
import { settingsApi } from '@/api/settings'
import type {
  BackupRunResult,
  BackupTarget,
  GpuCheckResult,
  ModelCheckResult,
  MinioCheckResult,
  RuntimeConfig,
  RuntimeStatus
} from '@/api/settings'

const backupModes = [
  { label: '清单', value: 'manifest' },
  { label: '复制', value: 'copy' }
]

const defaultRuntime = (): RuntimeConfig => ({
  minio: {
    endpoint: '',
    public_endpoint: '',
    secure: false,
    access_key: '',
    secret_key: '',
    region: 'us-east-1',
    contract_buckets: ['eduassets-input', 'eduassets-mineru', 'eduassets-minerupopo', 'eduassets-raw', 'eduassets-clean', 'eduassets-parsed']
  },
  gpu: {
    wrapper_url: '',
    api_key: '',
    ssh_host: '',
    ssh_port: 23,
    ssh_user: 'root',
    ssh_key_path: '',
    ssh_password: '',
    service_root: '/root/mineru-popo-service'
  },
  models: {
    llm: {
      enabled: true,
      provider: 'deepseek',
      default_model: 'deepseek-v4-flash',
      reasoning_model: 'deepseek-v4-pro',
      deepseek: {
        base_url: 'https://api.deepseek.com',
        api_key: ''
      },
      outline_decision_max_tokens: 16000,
      outline_global_max_candidates: 500,
      outline_max_risk_candidates: 120
    },
    vision: {
      enabled: false,
      provider: 'dashscope',
      model: 'qwen3.7-plus',
      dashscope: {
        base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        api_key: ''
      },
      outline_visual_max_candidates: 40
    },
    asr: { model: 'fun-asr-flash-2026-06-15' },
    tts: { model: 'qwen3-tts-instruct-flash-realtime' },
    image_generation: { model: 'qwen-image-2.0-pro' }
  },
  backup: {
    enabled: false,
    mode: 'manifest',
    schedule_enabled: false,
    interval_hours: 24,
    include_auxiliary: false,
    max_objects: 50000,
    targets: []
  }
})

const activeTab = ref('status')
const runtime = ref<RuntimeConfig>(defaultRuntime())
const status = ref<RuntimeStatus | null>(null)
const minioCheck = ref<MinioCheckResult | null>(null)
const gpuCheck = ref<GpuCheckResult | null>(null)
const modelCheck = ref<ModelCheckResult | null>(null)
const backupRun = ref<BackupRunResult | null>(null)
const loading = reactive({
  initial: false,
  saving: false,
  status: false,
  minio: false,
  ensure: false,
  gpu: false,
  models: false,
  backup: false,
  backupRun: false
})

const runtimeTagType = computed(() => {
  if (status.value?.status === 'ready') return 'success'
  if (status.value?.status === 'blocked') return 'danger'
  return 'warning'
})

const runtimeStatusText = computed(() => {
  if (!status.value) return '未检查'
  return status.value.status === 'ready' ? '就绪' : status.value.status === 'blocked' ? '阻断' : '警告'
})

const minioReady = computed(() => Boolean(minioCheck.value?.contract_ok || status.value?.minio.contract_ok))
const gpuReady = computed(() => Boolean(gpuCheck.value?.wrapper_ok || status.value?.gpu.wrapper_ok))
const llmKeyReady = computed(() => Boolean(runtime.value.models.llm.deepseek.api_key || runtime.value.models.llm.deepseek.api_key_configured || status.value?.models.llm.api_key_configured))
const visionKeyReady = computed(() => Boolean(runtime.value.models.vision.dashscope.api_key || runtime.value.models.vision.dashscope.api_key_configured || status.value?.models.vision.api_key_configured))
const modelsReady = computed(() => {
  const llmOk = !runtime.value.models.llm.enabled || llmKeyReady.value
  const visionOk = !runtime.value.models.vision.enabled || visionKeyReady.value
  return llmOk && visionOk
})
const modelConnectivityText = computed(() => {
  if (modelCheck.value?.checks.llm.ok && modelCheck.value?.checks.vision.ok) return '连通正常'
  if (modelCheck.value && !modelCheck.value.ok) return '连通异常'
  return modelsReady.value ? '配置完整' : '待配置'
})
const modelConnectivityTag = computed(() => {
  if (modelCheck.value?.checks.llm.ok && modelCheck.value?.checks.vision.ok) return 'success'
  if (modelCheck.value && !modelCheck.value.ok) return 'danger'
  return modelsReady.value ? 'warning' : 'info'
})
const backupReady = computed(() => Boolean(status.value?.backup.ready_count || runtime.value.backup.targets.some(target => target.status === 'ready')))

const bucketRows = computed(() => {
  if (minioCheck.value?.buckets?.length) return minioCheck.value.buckets
  return runtime.value.minio.contract_buckets.map(bucket => ({
    bucket,
    role: bucketRole(bucket),
    exists: false,
    created: false
  }))
})

const lastBackupText = computed(() => {
  const last = runtime.value.backup.last_backup
  if (!last || typeof last !== 'object') return '未记录'
  const createdAt = (last as Record<string, unknown>).created_at
  return typeof createdAt === 'string' ? createdAt : '已记录'
})

const loadRuntime = async () => {
  loading.initial = true
  try {
    runtime.value = await settingsApi.getRuntimeSettings()
  } catch {
    ElMessage.error('加载运行设置失败')
  } finally {
    loading.initial = false
  }
}

const refreshStatus = async () => {
  loading.status = true
  try {
    status.value = await settingsApi.getRuntimeStatus()
    minioCheck.value = status.value.minio
    gpuCheck.value = status.value.gpu
    applyBackupCheck(status.value.backup.targets)
  } catch {
    ElMessage.error('刷新运行状态失败')
  } finally {
    loading.status = false
  }
}

const saveRuntime = async () => {
  loading.saving = true
  try {
    runtime.value = await settingsApi.updateRuntimeSettings(runtime.value)
    ElMessage.success('运行设置已保存')
  } catch {
    ElMessage.error('保存运行设置失败')
  } finally {
    loading.saving = false
  }
}

const saveRuntimeQuietly = async () => {
  runtime.value = await settingsApi.updateRuntimeSettings(runtime.value)
}

const checkMinioNow = async () => {
  loading.minio = true
  try {
    await saveRuntimeQuietly()
    minioCheck.value = await settingsApi.checkMinio()
    ElMessage[minioCheck.value.contract_ok ? 'success' : 'warning'](minioCheck.value.contract_ok ? 'MinIO 合约正常' : 'MinIO 合约需要处理')
  } catch {
    ElMessage.error('检查 MinIO 失败')
  } finally {
    loading.minio = false
  }
}

const ensureBuckets = async () => {
  loading.ensure = true
  try {
    await saveRuntimeQuietly()
    minioCheck.value = await settingsApi.ensureMinioBuckets()
    ElMessage[minioCheck.value.contract_ok ? 'success' : 'warning'](minioCheck.value.contract_ok ? '篮子合约已维护' : '仍有篮子不可用')
  } catch {
    ElMessage.error('维护篮子失败')
  } finally {
    loading.ensure = false
  }
}

const checkGpuNow = async () => {
  loading.gpu = true
  try {
    await saveRuntimeQuietly()
    gpuCheck.value = await settingsApi.checkGpu()
    ElMessage[gpuCheck.value.wrapper_ok ? 'success' : 'warning'](gpuCheck.value.wrapper_ok ? 'GPU Wrapper 可用' : 'GPU Wrapper 不可用')
  } catch {
    ElMessage.error('检查 GPU 失败')
  } finally {
    loading.gpu = false
  }
}

const checkModelsNow = async () => {
  loading.models = true
  try {
    await saveRuntimeQuietly()
    modelCheck.value = await settingsApi.checkModels()
    const llmOk = Boolean(modelCheck.value.checks.llm.ok)
    const visionOk = Boolean(modelCheck.value.checks.vision.ok)
    ElMessage[llmOk && visionOk ? 'success' : 'warning'](llmOk && visionOk ? '模型连通正常' : '模型连通检查未全部通过')
  } catch {
    ElMessage.error('测试模型失败')
  } finally {
    loading.models = false
  }
}

const checkBackupNow = async () => {
  loading.backup = true
  try {
    await saveRuntimeQuietly()
    const result = await settingsApi.checkBackupTargets()
    applyBackupCheck(result.targets)
    ElMessage[result.ready_count > 0 ? 'success' : 'warning'](result.ready_count > 0 ? '备份路径可用' : '没有可写备份路径')
  } catch {
    ElMessage.error('检查备份路径失败')
  } finally {
    loading.backup = false
  }
}

const runBackupNow = async () => {
  loading.backupRun = true
  try {
    await saveRuntimeQuietly()
    backupRun.value = await settingsApi.runBackup()
    await loadRuntime()
    ElMessage.success('手动备份已完成')
  } catch {
    ElMessage.error('手动备份失败')
  } finally {
    loading.backupRun = false
  }
}

const applyBackupCheck = (targets: BackupTarget[]) => {
  const byId = new Map(targets.map(target => [target.id, target]))
  runtime.value.backup.targets = runtime.value.backup.targets.map(target => ({
    ...target,
    ...byId.get(target.id),
    path: byId.get(target.id)?.path ?? target.path
  }))
}

const bucketRole = (bucket: string) => {
  const roles: Record<string, string> = {
    'eduassets-input': 'source_pdf',
    'eduassets-mineru': 'mineru_official',
    'eduassets-minerupopo': 'popo_official',
    'eduassets-raw': 'raw_master',
    'eduassets-clean': 'clean_candidate',
    'eduassets-parsed': 'archive_optional'
  }
  return roles[bucket] || 'unknown'
}

const targetStatusType = (statusText?: string) => {
  if (statusText === 'ready') return 'success'
  if (statusText === 'disabled') return 'info'
  return 'warning'
}

const modelProbeType = (probe: ModelCheckResult['checks']['llm'] | undefined, configured: boolean) => {
  if (probe?.ok) return 'success'
  if (probe && !probe.skipped) return 'danger'
  return configured ? 'warning' : 'info'
}

const modelProbeText = (probe: ModelCheckResult['checks']['llm'] | undefined, configured: boolean) => {
  if (probe?.ok) return '连通正常'
  if (probe?.skipped) return '跳过'
  if (probe) return '连通异常'
  return configured ? '待测试' : '未配置'
}

const modelProbeDetail = (probe: ModelCheckResult['checks']['llm']) => {
  const latency = probe.latency_ms ? `${probe.latency_ms}ms` : ''
  const status = probe.status_code ? `HTTP ${probe.status_code}` : ''
  const error = probe.error ? ` · ${probe.error}` : ''
  return `${probe.provider}/${probe.model || '-'} ${status} ${latency}${error}`.trim()
}

onMounted(async () => {
  await loadRuntime()
  await refreshStatus()
})
</script>

<style scoped>
.settings-root {
  width: 100%;
  height: 100%;
  overflow: auto;
  padding: 24px;
}

.settings-shell {
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 52px;
}

.header-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-sm);
  flex-shrink: 0;
}

.header-text {
  min-width: 0;
  flex: 1;
}

.page-title {
  margin: 0 0 4px;
  font-size: 24px;
  line-height: 1.2;
  color: var(--text-primary);
}

.page-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}

.settings-tabs {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 0 20px 20px;
  box-shadow: var(--shadow-sm);
}

.settings-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 360px;
}

.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 4px;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 700;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.status-cell {
  min-width: 0;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-right: 1px solid var(--border-light);
}

.status-cell:last-child {
  border-right: none;
}

.status-label,
.table-head,
.probe-row span,
.target-label,
.backup-result span {
  color: var(--text-muted);
  font-size: 13px;
}

.status-cell strong,
.backup-result strong {
  color: var(--text-primary);
  font-size: 18px;
}

.status-cell small,
.backup-result small {
  color: var(--text-secondary);
  font-size: 12px;
  overflow-wrap: anywhere;
}

.issue-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.settings-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.settings-form :deep(.el-form-item__label) {
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  padding-bottom: 6px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.bucket-table {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.table-row {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) 180px 96px;
  align-items: center;
  gap: 12px;
  min-height: 44px;
  padding: 0 14px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-secondary);
  font-size: 13px;
}

.table-row:last-child {
  border-bottom: none;
}

.table-head {
  background: var(--bg-secondary);
  font-weight: 700;
}

.probe-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.probe-row {
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 14px;
  border-right: 1px solid var(--border-light);
}

.probe-row:last-child {
  border-right: none;
}

.model-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
}

.model-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--text-primary);
}

.model-test-detail {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--text-secondary);
  font-size: 12px;
  overflow-wrap: anywhere;
}

.target-list {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.target-row {
  display: grid;
  grid-template-columns: 52px 120px minmax(0, 1fr) 96px;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  padding: 8px 14px;
  border-bottom: 1px solid var(--border-light);
}

.target-row:last-child {
  border-bottom: none;
}

.backup-result {
  display: grid;
  grid-template-columns: 120px 140px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
}

.panel-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 2px;
}

@media (max-width: 920px) {
  .settings-root {
    padding: 16px;
  }

  .page-header {
    flex-wrap: wrap;
  }

  .status-grid,
  .form-grid,
  .probe-grid {
    grid-template-columns: 1fr;
  }

  .status-cell,
  .probe-row {
    border-right: none;
    border-bottom: 1px solid var(--border-light);
  }

  .status-cell:last-child,
  .probe-row:last-child {
    border-bottom: none;
  }

  .table-row {
    grid-template-columns: minmax(0, 1fr) 120px 80px;
  }

  .target-row {
    grid-template-columns: 52px 92px minmax(0, 1fr);
  }

  .target-row .el-tag {
    grid-column: 2 / 4;
    width: fit-content;
  }

  .backup-result {
    grid-template-columns: 1fr;
    padding: 12px 14px;
  }

  .panel-actions {
    justify-content: stretch;
    flex-wrap: wrap;
  }
}
</style>
