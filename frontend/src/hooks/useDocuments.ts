/**
 * useDocuments - manages document list state with polling for indexing status.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  listDocuments,
  deleteDocument,
  getStats,
  DocumentMeta,
  StatsResponse,
} from '../services/api'
import toast from 'react-hot-toast'

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentMeta[]>([])
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const refresh = useCallback(async () => {
    try {
      const [docs, st] = await Promise.all([listDocuments(), getStats()])
      setDocuments(docs)
      setStats(st)
    } catch {
      // silently fail on background refreshes
    }
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    await refresh()
    setLoading(false)
  }, [refresh])

  // Poll while any doc is in pending/processing state
  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    const hasPending = documents.some(
      (d) => d.status === 'pending' || d.status === 'processing'
    )
    if (hasPending && !pollingRef.current) {
      pollingRef.current = setInterval(refresh, 2500)
    } else if (!hasPending && pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [documents, refresh])

  const remove = useCallback(
    async (docId: string, filename: string) => {
      try {
        await deleteDocument(docId)
        setDocuments((prev) => prev.filter((d) => d.doc_id !== docId))
        toast.success(`"${filename}" deleted`)
        refresh()
      } catch {
        toast.error('Failed to delete document')
      }
    },
    [refresh]
  )

  return { documents, stats, loading, refresh, remove }
}
