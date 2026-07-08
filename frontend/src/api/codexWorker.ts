import type { CodexSkillJob, ObjectRef } from '@/types/material'

const baseUrl = (import.meta.env.VITE_CODEX_WORKER_URL || 'http://127.0.0.1:28082/api/codex-worker').replace(/\/$/, '')

export interface CodexWorkerStatus {
  job_id: string
  state: 'queued' | 'running' | 'publishing' | 'published' | 'failed' | 'missing' | string
  running: boolean
  message?: string
  db_status?: string
  started_at?: string | null
  finished_at?: string | null
  returncode?: number | null
  log_path?: string
  material_output_id?: string
  output_manifest?: ObjectRef
  job?: CodexSkillJob
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {})
    }
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Worker request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const codexWorkerApi = {
  health() {
    return request<Record<string, unknown>>('/health')
  },

  getJob(jobId: string) {
    return request<CodexWorkerStatus>(`/jobs/${jobId}`)
  },

  runJob(jobId: string) {
    return request<CodexWorkerStatus>(`/jobs/${jobId}/run`, { method: 'POST' })
  }
}
