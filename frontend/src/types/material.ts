export type MaterialStage =
  | 'input'
  | 'mineru_done'
  | 'popo_done'
  | 'raw_done'
  | 'clean_stale'
  | 'clean_done'
  | 'standard_done'
  | 'failed'

export type PipelineRunStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'idle' | string

export interface ObjectRef {
  bucket: string
  object: string
}

export interface MaterialItem {
  id: string
  material_id: string
  source_hash: string
  title: string
  filename: string
  source_type: string
  input_bucket: string
  input_object: string
  input_sha256: string
  size: number
  content_type: string
  stage_status: MaterialStage
  pipeline_status: string
  mineru_manifest: ObjectRef
  popo_manifest: ObjectRef
  raw_manifest: ObjectRef
  clean_manifest: ObjectRef
  standard_manifest: ObjectRef
  mineru_available: boolean
  popo_available: boolean
  raw_available: boolean
  clean_available: boolean
  standard_available: boolean
  raw_dry_run_available?: boolean
  mineru_run_id: string
  popo_run_id: string
  raw_run_id: string
  raw_dry_run_id?: string
  clean_run_id: string
  standard_run_id: string
  standard_quality_score: number | null
  review_asset_id: string
  ignored: boolean
  last_synced_at: string | null
  created_at: string | null
}

export interface MaterialListResponse {
  total: number
  page: number
  page_size: number
  materials: MaterialItem[]
}

export interface MaterialSyncSummary {
  total: number
  scanned: Record<string, number>
  stages: Record<MaterialStage | string, number>
  availability: Record<MaterialStage | string, number>
}

export interface PipelineRun {
  id: string
  status: PipelineRunStatus
  mode: string
  current_stage: string
  total: number
  processed: number
  success: number
  failed: number
  summary: Record<string, unknown>
  error_message: string
  started_at: string | null
  finished_at: string | null
  created_at: string | null
}

export interface PipelineEvent {
  id: string
  run_id: string
  level: string
  stage: string
  message: string
  payload: Record<string, unknown>
  created_at: string | null
}

export interface MaterialSummary {
  total: number
  stages: Record<MaterialStage | string, number>
  availability: Record<MaterialStage | string, number>
  latest_run: PipelineRun | null
}

export interface PipelineStatusResponse {
  run: PipelineRun | null
  events: PipelineEvent[]
  audit?: Record<string, unknown> | null
}

export interface PipelinePreflightResponse {
  ready: boolean
  status: string
  checked_at: string
  limit: number
  gpu_ok: boolean
  staged_api_ok: boolean
  plan_status: string
  selected_count: number
  active_marker_count: number
  scheduler_state_counts: Record<string, number>
  health: Record<string, unknown>
  staged_api_probe: Record<string, unknown>
  plan: Record<string, unknown>
  returncode: number
  command_text: string
}

export interface PopoToRawPreflightResponse {
  ready: boolean
  stage: string
  material_pk: string
  material_id: string
  filename: string
  popo_run_id: string
  mineru_run_id: string
  raw_bucket: string
  raw_prefix: string
  publish: boolean
  checks: Record<string, boolean>
  blockers: string[]
  checked_at: string
}

export interface RawToCleanPreflightResponse {
  ready: boolean
  stage: string
  material_pk: string
  material_id: string
  filename: string
  raw_run_id: string
  raw_bucket: string
  raw_prefix: string
  clean_bucket: string
  clean_prefix: string
  llm_mode: string
  checks: Record<string, boolean>
  blockers: string[]
  checked_at: string
}

export interface CleanToStandardPreflightResponse {
  ready: boolean
  stage: string
  material_pk: string
  material_id: string
  filename: string
  clean_run_id: string
  clean_bucket: string
  clean_prefix: string
  raw_bucket: string
  raw_prefix: string
  standard_bucket: string
  standard_prefix: string
  checks: Record<string, boolean>
  blockers: string[]
  checked_at: string
}

export interface MaterialUploadResponse {
  total: number
  success: number
  failed: number
  files: Array<{
    filename: string
    status: string
    error_message?: string
    material?: MaterialItem
  }>
}
