import type { AxiosProgressEvent } from 'axios'
import api from './index'
import type {
  MaterialListResponse,
  MaterialSummary,
  MaterialSyncSummary,
  MaterialUploadResponse,
  PipelinePreflightResponse,
  PopoToRawPreflightResponse,
  CleanToStandardPreflightResponse,
  PipelineRun,
  RawToCleanPreflightResponse,
  PipelineStatusResponse
} from '@/types/material'

export interface MaterialListParams {
  page: number
  page_size: number
  search?: string
  stage?: string
}

export const materialsApi = {
  getMaterials(params: MaterialListParams) {
    return api.get<MaterialListResponse>('/materials', { params }).then(res => res.data)
  },

  getSummary() {
    return api.get<MaterialSummary>('/materials/summary').then(res => res.data)
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

  preflightPipeline(limit = 5) {
    return api.post<PipelinePreflightResponse>('/materials/pipeline/preflight', { limit }, { timeout: 120000 }).then(res => res.data)
  },

  startPipeline(apply = false, limit = 5) {
    return api.post<PipelineRun>('/materials/pipeline/start', { apply, limit }, { timeout: 120000 }).then(res => res.data)
  },

  preflightPopoToRaw(materialId: string, force = false, publish = false) {
    return api
      .post<PopoToRawPreflightResponse>(`/materials/${materialId}/popo2raw/preflight`, null, { params: { force, publish }, timeout: 120000 })
      .then(res => res.data)
  },

  startPopoToRaw(materialId: string, publish = false, force = false) {
    return api
      .post<PipelineRun>(`/materials/${materialId}/popo2raw/start`, { publish, force }, { timeout: 120000 })
      .then(res => res.data)
  },

  publishPopoToRawDryRun(materialId: string, runId: string | number, force = true) {
    return api
      .post<PipelineRun>(
        `/materials/${materialId}/popo2raw/publish_dry_run`,
        { run_id: Number(runId), force },
        { timeout: 120000 }
      )
      .then(res => res.data)
  },

  preflightRawToClean(materialId: string, force = false) {
    return api
      .post<RawToCleanPreflightResponse>(`/materials/${materialId}/raw2clean/preflight`, null, { params: { force }, timeout: 120000 })
      .then(res => res.data)
  },

  startRawToClean(materialId: string, publish = true, force = false) {
    return api
      .post<PipelineRun>(`/materials/${materialId}/raw2clean/start`, { publish, force }, { timeout: 120000 })
      .then(res => res.data)
  },

  preflightCleanToStandard(materialId: string, force = false) {
    return api
      .post<CleanToStandardPreflightResponse>(`/materials/${materialId}/clean2standard/preflight`, null, { params: { force }, timeout: 120000 })
      .then(res => res.data)
  },

  startCleanToStandard(materialId: string, publish = true, force = false) {
    return api
      .post<PipelineRun>(`/materials/${materialId}/clean2standard/start`, { publish, force }, { timeout: 120000 })
      .then(res => res.data)
  },

  getReviewTarget(materialId: string) {
    return api.get<{ review_asset_id: string }>(`/materials/${materialId}/review_target`).then(res => res.data)
  },

  getDownloadUrl(materialId: string) {
    return api.get<{ url: string }>(`/materials/${materialId}/download_url`).then(res => res.data)
  },

  getContentUrl(materialId: string) {
    return `/api/materials/${materialId}/content`
  }
}
