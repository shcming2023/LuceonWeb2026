export type MaterialStage =
  | 'input'
  | 'mineru_done'
  | 'popo_done'
  | 'latex_done'
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
  book_metadata?: MaterialBookMetadata | null
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
  latex_manifest: ObjectRef
  raw_manifest: ObjectRef
  clean_manifest: ObjectRef
  standard_manifest: ObjectRef
  mineru_available: boolean
  popo_available: boolean
  latex_available: boolean
  raw_available: boolean
  clean_available: boolean
  standard_available: boolean
  raw_dry_run_available?: boolean
  mineru_run_id: string
  popo_run_id: string
  latex_run_id: string
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

export interface MaterialBookMetadata {
  id: string
  material_pk: string
  original_title: string
  publication_date: string
  publication_year: number | null
  edition: string
  subject: string
  publication_country: string
  series_name: string
  publisher: string
  isbn: string
  language: string
  grade_level: string
  status: string
  source: string
  confidence: number | null
  manual_override: boolean
  evidence: Array<Record<string, unknown>>
  sample: Record<string, unknown>
  extraction_model: string
  extraction_error: string
  extracted_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface MaterialMetadataOptions {
  subjects: string[]
  countries: string[]
  series: string[]
  publishers: string[]
  languages: string[]
  editions: string[]
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
