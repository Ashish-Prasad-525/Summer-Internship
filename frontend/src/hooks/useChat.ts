/**
 * useChat - manages chat messages, streaming state, and session.
 */

import { useCallback, useRef, useState } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { chatStreaming, Source, StreamEvent } from '../services/api'
import toast from 'react-hot-toast'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  isStreaming?: boolean
  timestamp: Date
}

export function useChat(selectedDocIds: string[]) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string>(uuidv4())
  const abortRef = useRef<(() => void) | null>(null)

  const sendMessage = useCallback(
    (question: string) => {
      if (!question.trim() || isLoading) return

      const userMsg: ChatMessage = {
        id: uuidv4(),
        role: 'user',
        content: question.trim(),
        timestamp: new Date(),
      }

      const assistantMsgId = uuidv4()
      const assistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        sources: [],
        isStreaming: true,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, userMsg, assistantMsg])
      setIsLoading(true)

      let currentSources: Source[] = []

      const onEvent = (event: StreamEvent) => {
        if (event.type === 'metadata') {
          currentSources = event.sources ?? []
          // Update session_id from server
          if (event.session_id) setSessionId(event.session_id)
          // Attach sources early so they appear while streaming
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId ? { ...m, sources: currentSources } : m
            )
          )
        } else if (event.type === 'token') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? { ...m, content: m.content + event.content }
                : m
            )
          )
        } else if (event.type === 'done') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? { ...m, isStreaming: false, sources: currentSources }
                : m
            )
          )
          setIsLoading(false)
        } else if (event.type === 'error') {
          toast.error(event.message || 'Streaming error')
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? {
                    ...m,
                    content: '⚠️ An error occurred. Please try again.',
                    isStreaming: false,
                  }
                : m
            )
          )
          setIsLoading(false)
        }
      }

      const onError = (err: Error) => {
        toast.error(`Connection error: ${err.message}`)
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, content: '⚠️ Connection failed.', isStreaming: false }
              : m
          )
        )
        setIsLoading(false)
      }

      const abort = chatStreaming(
        {
          question: question.trim(),
          session_id: sessionId,
          document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
        },
        onEvent,
        onError
      )
      abortRef.current = abort
    },
    [isLoading, sessionId, selectedDocIds]
  )

  const stopStreaming = useCallback(() => {
    abortRef.current?.()
    setIsLoading(false)
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m))
    )
  }, [])

  const clearChat = useCallback(() => {
    setMessages([])
    setSessionId(uuidv4())
    setIsLoading(false)
  }, [])

  return { messages, isLoading, sessionId, sendMessage, stopStreaming, clearChat }
}
