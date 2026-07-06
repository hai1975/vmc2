import type { AppSettings, DocumentScanResult, EmailSendResult, FormProgress, FormSchema, FormSession, FormSummary, LiveToken, VoiceConfig } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''
const DEFAULT_TIMEOUT_MS = 30_000
export const BOOT_TIMEOUT_MS = 90_000

export class ApiTimeoutError extends Error {
  constructor(seconds: number) {
    super(`Request timed out after ${seconds}s. The server may be waking up — please try again.`)
    this.name = 'ApiTimeoutError'
  }
}

async function fetchWithTimeout(path: string, init?: RequestInit, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(`${API_BASE}${path}`, {
      ...init,
      signal: controller.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiTimeoutError(Math.round(timeoutMs / 1000))
    }
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      throw new Error(
        'Cannot reach API server. Render may be waking up (wait 30–90s) then click Retry.',
      )
    }
    throw error
  } finally {
    window.clearTimeout(timer)
  }
}

async function request<T>(path: string, init?: RequestInit, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<T> {
  const res = await fetchWithTimeout(
    path,
    {
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
      ...init,
    },
    timeoutMs,
  )
  if (!res.ok) {
    const raw = await res.text()
    try {
      const parsed = JSON.parse(raw) as { detail?: string | { errors?: string[] } }
      if (typeof parsed.detail === 'string') {
        throw new Error(parsed.detail)
      }
      if (parsed.detail && typeof parsed.detail === 'object' && parsed.detail.errors) {
        throw new Error(parsed.detail.errors.join(', '))
      }
    } catch (error) {
      if (error instanceof Error && error.message !== raw) {
        throw error
      }
    }
    throw new Error(raw || `Request failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

/** Ping API early to reduce Render cold-start wait before real requests. */
export function wakeApi(): void {
  if (!API_BASE) return
  void fetchWithTimeout('/api/health', {}, 45_000).catch(() => {})
}

export const api = {
  listForms: (timeoutMs?: number) => request<FormSummary[]>('/api/forms', undefined, timeoutMs),
  getSchema: (formId: string, timeoutMs?: number) =>
    request<FormSchema>(`/api/forms/${formId}/schema`, undefined, timeoutMs),
  createSession: (formId: string, language: string, timeoutMs?: number) =>
    request<FormSession>(
      '/api/sessions',
      {
        method: 'POST',
        body: JSON.stringify({ form_id: formId, language }),
      },
      timeoutMs,
    ),
  getSession: (sessionId: string) => request<FormSession>(`/api/sessions/${sessionId}`),
  getFormProgress: (sessionId: string, savedFieldId?: string) => {
    const query = savedFieldId ? `?saved_field=${encodeURIComponent(savedFieldId)}` : ''
    return request<FormProgress>(`/api/sessions/${sessionId}/form-progress${query}`)
  },
  updateAnswers: (sessionId: string, answers: Record<string, unknown>) =>
    request<FormSession>(`/api/sessions/${sessionId}/answers`, {
      method: 'PATCH',
      body: JSON.stringify({ answers, merge: true }),
    }),
  saveSession: (sessionId: string) =>
    request<FormSession>(`/api/sessions/${sessionId}/save`, { method: 'POST' }),
  submitSession: (sessionId: string) =>
    request<FormSession>(`/api/sessions/${sessionId}/submit`, { method: 'POST' }),
  getVoiceConfig: (sessionId: string) =>
    request<VoiceConfig>(`/api/sessions/${sessionId}/voice-config`),
  createLiveToken: (sessionId: string) =>
    request<LiveToken>(`/api/sessions/${sessionId}/live-token`, { method: 'POST' }),
  scanDocument: (sessionId: string, image: string, docType = 'auto', merge = true) =>
    request<DocumentScanResult>(
      `/api/sessions/${sessionId}/scan-document`,
      {
        method: 'POST',
        body: JSON.stringify({ image, doc_type: docType, merge }),
      },
      60_000,
    ),
  pdfUrl: (sessionId: string, cacheBust?: number) =>
    `${API_BASE}/api/sessions/${sessionId}/pdf${cacheBust ? `?v=${cacheBust}` : ''}`,
  fetchPdfBlob: async (sessionId: string, attempt = 1): Promise<Blob> => {
    const maxAttempts = 3
    const timeoutMs = 120_000
    const cacheBust = Date.now()
    try {
      const res = await fetchWithTimeout(`/api/sessions/${sessionId}/pdf?v=${cacheBust}`, {}, timeoutMs)
      if (!res.ok) {
        const raw = await res.text()
        try {
          const parsed = JSON.parse(raw) as { detail?: string }
          throw new Error(parsed.detail || raw)
        } catch (error) {
          if (error instanceof Error && error.message !== raw) throw error
          throw new Error(raw || `Preview failed: ${res.status}`)
        }
      }
      return res.blob()
    } catch (error) {
      if (attempt < maxAttempts) {
        await new Promise((resolve) => window.setTimeout(resolve, 2000 * attempt))
        return api.fetchPdfBlob(sessionId, attempt + 1)
      }
      throw error
    }
  },
  downloadPdf: async (sessionId: string, filename: string) => {
    const blob = await api.fetchPdfBlob(sessionId)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  },
  sendSessionEmail: (sessionId: string) =>
    request<EmailSendResult>(`/api/sessions/${sessionId}/send-email`, { method: 'POST' }, 90_000),
  getSettings: () => request<AppSettings>('/api/settings'),
  updateSettings: (payload: Partial<AppSettings>) =>
    request<AppSettings>('/api/settings', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
}
