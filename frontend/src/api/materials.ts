import type { AxiosProgressEvent } from 'axios'
import api from './index'
import type {
  CodexSkillJob,
  MaterialBookMetadata,
  MaterialListResponse,
  MaterialMetadataOptions,
  MaterialSummary,
  MaterialSyncSummary,
  MaterialUploadResponse,
  PipelinePreflightResponse,
  PipelineRun,
  PipelineStatusResponse
} from '@/types/material'

export interface MaterialListParams {
  page: number
  page_size: number
  search?: string
  stage?: string
  metadata_status?: string
  subject?: string
  country?: string
  series?: string
  year_from?: number | null
  year_to?: number | null
}

export interface PipelineTarget {
  material_id?: string
  input_object?: string
}

export interface CodexJobCreatePayload {
  mode?: string
  requested_skill?: string
  skill_version?: string
  run_reason?: string
  force?: boolean
  payload?: Record<string, unknown>
}

export const materialsApi = {
  getMaterials(params: MaterialListParams) {
    return api.get<MaterialListResponse>('/materials', { params }).then(res => res.data)
  },

  getSummary() {
    return api.get<MaterialSummary>('/materials/summary').then(res => res.data)
  },

  getMetadataOptions() {
    return api.get<MaterialMetadataOptions>('/materials/metadata/options').then(res => res.data)
  },

  getMetadata(materialId: string) {
    return api.get<MaterialBookMetadata>(`/materials/${materialId}/metadata`).then(res => res.data)
  },

  updateMetadata(materialId: string, payload: Partial<MaterialBookMetadata>) {
    return api.patch<MaterialBookMetadata>(`/materials/${materialId}/metadata`, payload).then(res => res.data)
  },

  extractMetadata(materialId: string, force = false) {
    return api
      .post<MaterialBookMetadata>(`/materials/${materialId}/metadata/extract`, { force }, { timeout: 120000 })
      .then(res => res.data)
  },

  sync(limit?: number) {
    return api.post<MaterialSyncSummary>('/materials/sync', null, { params: { limit } }).then(res => res.data)
  },

  upload(files: File[], onProgress?: (progress: number) => void) {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    return api.post<MaterialUploadResponse>('/materials/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event: AxiosProgressEvent) => {
        if (onProgress && event.total) {
          onProgress(Math.round((event.loaded * 100) / event.total))
        }
      }
    }).then(res => res.data)
  },

  getPipelineStatus() {
    return api.get<PipelineStatusResponse>('/materials/pipeline/status').then(res => res.data)
  },

  preflightPipeline(limit = 5, target: PipelineTarget = {}) {
    return api.post<PipelinePreflightResponse>('/materials/pipeline/preflight', { limit, ...target }, { timeout: 120000 }).then(res => res.data)
  },

  startPipeline(apply = false, limit = 5, target: PipelineTarget = {}) {
    return api.post<PipelineRun>('/materials/pipeline/start', { apply, limit, ...target }, { timeout: 120000 }).then(res => res.data)
  },

  getReviewTarget(materialId: string) {
    return api.get<{ review_asset_id: string }>(`/materials/${materialId}/review_target`).then(res => res.data)
  },

  getDownloadUrl(materialId: string) {
    return api.get<{ url: string }>(`/materials/${materialId}/download_url`).then(res => res.data)
  },

  getContentUrl(materialId: string) {
    return `/api/materials/${materialId}/content`
  },

  createCodexJob(materialId: string, payload: CodexJobCreatePayload) {
    return api.post<CodexSkillJob>(`/materials/${materialId}/codex-jobs`, payload).then(res => res.data)
  }
}
