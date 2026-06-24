import api from './index'

export type MineruBackend =
  | 'pipeline'
  | 'vlm-engine'
  | 'vlm-http-client'
  | 'hybrid-engine'
  | 'hybrid-http-client'
  | (string & {})

// 设置相关类型定义
export interface SettingsData {
  force_ocr: boolean
  ocr_lang: string
  formula_recognition: boolean
  table_recognition: boolean
  backend: MineruBackend
  version?: string
}

export interface SettingsResponse extends SettingsData {
  user_id: string
}

export interface MineruHealthResponse {
  available: boolean
  base_url: string
  status?: string
  version?: string
  error?: string
  [key: string]: unknown
}

export interface RuntimeMinioConfig {
  endpoint: string
  public_endpoint: string
  secure: boolean
  access_key: string
  secret_key: string
  region: string
  contract_buckets: string[]
  access_key_configured?: boolean
  secret_key_configured?: boolean
}

export interface RuntimeGpuConfig {
  wrapper_url: string
  api_key: string
  ssh_host: string
  ssh_port: number
  ssh_user: string
  ssh_key_path: string
  ssh_password: string
  service_root: string
  api_key_configured?: boolean
  ssh_password_configured?: boolean
}

export interface BackupTarget {
  id: string
  label: string
  provider: string
  path: string
  enabled: boolean
  exists?: boolean
  writable?: boolean
  status?: string
}

export interface RuntimeBackupConfig {
  enabled: boolean
  mode: 'manifest' | 'copy'
  schedule_enabled: boolean
  interval_hours: number
  include_auxiliary: boolean
  max_objects: number
  targets: BackupTarget[]
  last_backup?: Record<string, unknown> | null
}

export interface RuntimeConfig {
  minio: RuntimeMinioConfig
  gpu: RuntimeGpuConfig
  backup: RuntimeBackupConfig
}

export interface MinioCheckResult {
  connected: boolean
  endpoint: string
  contract_ok: boolean
  missing: string[]
  buckets: Array<{ bucket: string; exists: boolean; created: boolean; role: string; error?: string }>
  error?: string
}

export interface GpuCheckResult {
  wrapper_url: string
  wrapper_ok: boolean
  staged_api_ok: boolean
  ssh_ok: boolean
  ssh_status: string
  health: Record<string, unknown>
  staged_api: Record<string, number | null>
  errors: string[]
}

export interface BackupCheckResult {
  targets: BackupTarget[]
  ready_count: number
}

export interface BackupRunResult {
  mode: string
  object_count: number
  truncated: boolean
  targets: Array<{ id: string; path: string; manifest: string; copied: number }>
}

export interface RuntimeStatus {
  status: 'ready' | 'warning' | 'blocked' | string
  blockers: string[]
  warnings: string[]
  minio: MinioCheckResult
  gpu: GpuCheckResult
  backup: BackupCheckResult
}

// 设置 API
export const settingsApi = {
  /**
   * 获取用户设置
   */
  getSettings() {
    return api.get<SettingsResponse>('/settings')
      .then(res => res.data)
  },

  /**
   * 更新用户设置
   */
  updateSettings(settings: SettingsData) {
    return api.put('/settings', settings)
      .then(res => res.data)
  },

  getMineruHealth() {
    return api.get<MineruHealthResponse>('/system/mineru-health')
      .then(res => res.data)
  },

  getRuntimeSettings() {
    return api.get<RuntimeConfig>('/runtime/settings')
      .then(res => res.data)
  },

  updateRuntimeSettings(settings: RuntimeConfig) {
    return api.put<RuntimeConfig>('/runtime/settings', settings)
      .then(res => res.data)
  },

  getRuntimeStatus() {
    return api.get<RuntimeStatus>('/runtime/status')
      .then(res => res.data)
  },

  checkMinio() {
    return api.post<MinioCheckResult>('/runtime/minio/check')
      .then(res => res.data)
  },

  ensureMinioBuckets() {
    return api.post<MinioCheckResult>('/runtime/minio/ensure-buckets')
      .then(res => res.data)
  },

  checkGpu() {
    return api.post<GpuCheckResult>('/runtime/gpu/check')
      .then(res => res.data)
  },

  checkBackupTargets() {
    return api.post<BackupCheckResult>('/runtime/backup/check')
      .then(res => res.data)
  },

  runBackup() {
    return api.post<BackupRunResult>('/runtime/backup/run')
      .then(res => res.data)
  }
}
