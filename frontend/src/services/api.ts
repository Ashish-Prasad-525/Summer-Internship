/**
 * API Service - typed axios client for all backend endpoints.
 * Handles base URL, error normalization, and SSE streaming.
 */

import axios, { AxiosInstance } from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Types ─────────────────────────────────────────────────────────────────────

export interface DocumentMeta {
  doc_id: string
  filename: string
  status: 'pending' | 'processing' | 'indexed' | 'failed'
  chunks_created: number
  file_size_kb: number
  created_at: string
}

export interface Source {
  document_id: string
  filename: string
  page: number | null
  chunk_index: number
  relevance_score: number
  excerpt: string
}

export interface ChatResponse {
  session_id: string
  answer: string
  sources: Source[]
  tokens_used: number
}

export interface StreamMetadata {
  type: 'metadata'
  session_id: string
  sources: Source[]
}

export interface StreamToken {
  type: 'token'
  content: string
}

export interface StreamDone {
  type: 'done'
  full_answer: string
}

export interface StreamError {
  type: 'error'
  message: string
}

export type StreamEvent = StreamMetadata | StreamToken | StreamDone | StreamError

export interface StatsResponse {
  total_documents: number
  indexed_documents: number
  total_chunks: number
  vector_store_type: string
}

// ── Upload ────────────────────────────────────────────────────────────────────

export const uploadDocument = async (
  file: File,
  onProgress?: (pct: number) => void
) => {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/upload/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  })
  return data
}

export const getUploadStatus = async (documentId: string) => {
  const { data } = await api.get(`/upload/status/${documentId}`)
  return data as DocumentMeta
}

// ── Documents ─────────────────────────────────────────────────────────────────

export const listDocuments = async (): Promise<DocumentMeta[]> => {
  const { data } = await api.get('/documents/')
  return data
}

export const deleteDocument = async (documentId: string) => {
  const { data } = await api.delete(`/documents/${documentId}`)
  return data
}

export const getStats = async (): Promise<StatsResponse> => {
  const { data } = await api.get('/documents/stats/overview')
  return data
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export const chatNonStreaming = async (params: {
  question: string
  session_id?: string
  document_ids?: string[]
  top_k?: number
}): Promise<ChatResponse> => {
  const { data } = await api.post('/chat/', { ...params, stream: false })
  return data
}

/**
 * Chat with SSE streaming. Calls onEvent for each parsed SSE event.
 * Returns a cleanup function to abort the stream.
 */
export const chatStreaming = (
  params: {
    question: string
    session_id?: string
    document_ids?: string[]
    top_k?: number
  },
  onEvent: (event: StreamEvent) => void,
  onError: (err: Error) => void
): (() => void) => {
  const controller = new AbortController()

  const run = async () => {
    try {
      const response = await fetch(`${BASE_URL}/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...params, stream: true, include_sources: true }),
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const raw = line.slice(6).trim()
            if (!raw) continue
            try {
              const event: StreamEvent = JSON.parse(raw)
              onEvent(event)
            } catch {
              // ignore malformed JSON lines
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') {
        onError(err)
      }
    }
  }

  run()
  return () => controller.abort()
}

export const getChatHistory = async (sessionId: string) => {
  const { data } = await api.get(`/chat/sessions/${sessionId}/history`)
  return data
}

export const clearSession = async (sessionId: string) => {
  const { data } = await api.delete(`/chat/sessions/${sessionId}`)
  return data
}

export const summarizeDocument = async (documentId: string, style = 'concise') => {
  const { data } = await api.post('/chat/summarize', { document_id: documentId, style })
  return data
}

export default api
