import { useEffect, useRef, useState } from 'react'
import { Send, Square, Trash2, Bot, User, FileText, ChevronDown, ChevronUp } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import clsx from 'clsx'
import { ChatMessage } from '../../hooks/useChat'
import { DocumentMeta, Source } from '../../services/api'

interface Props {
  messages: ChatMessage[]
  isLoading: boolean
  onSend: (q: string) => void
  onStop: () => void
  onClear: () => void
  selectedDocIds: string[]
  documents: DocumentMeta[]
}

const SUGGESTIONS = [
  'Summarize the key points of the uploaded documents',
  'What are the main topics covered?',
  'Find any mentions of deadlines or dates',
  'What conclusions are drawn in the documents?',
]

export default function ChatPanel({
  messages, isLoading, onSend, onStop, onClear, selectedDocIds, documents,
}: Props) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [input])

  const handleSubmit = () => {
    if (!input.trim() || isLoading) return
    onSend(input)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const filterLabel =
    selectedDocIds.length > 0
      ? `${selectedDocIds.length} doc${selectedDocIds.length > 1 ? 's' : ''} selected`
      : 'All documents'

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm">
        <div>
          <h2 className="text-sm font-semibold text-gray-100">AI Document Chat</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            {filterLabel} · RAG-powered answers with citations
          </p>
        </div>
        {messages.length > 0 && (
          <button onClick={onClear} className="btn-ghost text-xs">
            <Trash2 className="w-3.5 h-3.5" />
            Clear chat
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {messages.length === 0 ? (
          <EmptyState onSuggestion={(s) => { setInput(s); textareaRef.current?.focus() }} />
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 pb-4">
        <div className="max-w-3xl mx-auto">
          <div className="relative bg-gray-800 border border-gray-700 rounded-xl shadow-lg focus-within:border-brand-500 transition-colors">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your documents…"
              rows={1}
              disabled={isLoading}
              className="w-full bg-transparent text-gray-100 placeholder-gray-500 text-sm px-4 py-3.5 pr-14 resize-none focus:outline-none leading-relaxed disabled:opacity-60"
            />
            <div className="absolute right-3 bottom-3 flex items-center gap-1.5">
              {isLoading ? (
                <button
                  onClick={onStop}
                  className="p-1.5 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors"
                  title="Stop generating"
                >
                  <Square className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={!input.trim()}
                  className="p-1.5 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  title="Send (Enter)"
                >
                  <Send className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
          <p className="text-xs text-gray-600 text-center mt-2">
            Shift+Enter for new line · Enter to send
          </p>
        </div>
      </div>
    </div>
  )
}

// ── Message Bubble ─────────────────────────────────────────────────────────────

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={clsx('flex gap-3 max-w-3xl mx-auto animate-fade-in', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div className={clsx(
        'w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5',
        isUser ? 'bg-brand-700' : 'bg-gray-700'
      )}>
        {isUser ? <User className="w-4 h-4 text-brand-200" /> : <Bot className="w-4 h-4 text-gray-300" />}
      </div>

      {/* Content */}
      <div className={clsx('flex-1 min-w-0', isUser && 'flex justify-end')}>
        {isUser ? (
          <div className="bg-brand-600/20 border border-brand-700/30 rounded-2xl rounded-tr-sm px-4 py-3 max-w-lg">
            <p className="text-sm text-gray-100 whitespace-pre-wrap">{message.content}</p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className={clsx(
              'bg-gray-800/60 border border-gray-700/50 rounded-2xl rounded-tl-sm px-4 py-3',
              message.isStreaming && 'streaming-cursor'
            )}>
              {message.content ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  className="prose-chat"
                >
                  {message.content}
                </ReactMarkdown>
              ) : (
                <TypingIndicator />
              )}
            </div>

            {/* Sources */}
            {message.sources && message.sources.length > 0 && (
              <SourcesList sources={message.sources} />
            )}
          </div>
        )}
        <p className="text-xs text-gray-600 mt-1.5 px-1">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  )
}

// ── Sources List ───────────────────────────────────────────────────────────────

function SourcesList({ sources }: { sources: Source[] }) {
  const [expanded, setExpanded] = useState(false)
  const visible = expanded ? sources : sources.slice(0, 2)

  return (
    <div className="space-y-1.5">
      <p className="text-xs text-gray-500 font-medium px-1">Sources used:</p>
      {visible.map((src, i) => (
        <SourceCard key={i} source={src} index={i + 1} />
      ))}
      {sources.length > 2 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 px-1 transition-colors"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {expanded ? 'Show less' : `+${sources.length - 2} more sources`}
        </button>
      )}
    </div>
  )
}

function SourceCard({ source, index }: { source: Source; index: number }) {
  const [open, setOpen] = useState(false)
  const score = Math.round(source.relevance_score * 100)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2.5 px-3 py-2 hover:bg-gray-800/50 transition-colors text-left"
      >
        <span className="source-badge">[{index}]</span>
        <FileText className="w-3.5 h-3.5 text-gray-500 shrink-0" />
        <span className="text-xs text-gray-300 flex-1 truncate">{source.filename}</span>
        {source.page && (
          <span className="text-xs text-gray-600 shrink-0">p.{source.page}</span>
        )}
        <span className={clsx(
          'text-xs px-1.5 py-0.5 rounded-full shrink-0',
          score >= 70 ? 'bg-emerald-900/50 text-emerald-400' :
          score >= 40 ? 'bg-amber-900/50 text-amber-400' :
          'bg-gray-800 text-gray-500'
        )}>
          {score}%
        </span>
        {open ? <ChevronUp className="w-3.5 h-3.5 text-gray-600" /> : <ChevronDown className="w-3.5 h-3.5 text-gray-600" />}
      </button>
      {open && (
        <div className="px-3 pb-3 border-t border-gray-800">
          <p className="text-xs text-gray-400 leading-relaxed mt-2 font-mono whitespace-pre-wrap">
            {source.excerpt}
          </p>
        </div>
      )}
    </div>
  )
}

// ── Typing Indicator ───────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  )
}

// ── Empty State ────────────────────────────────────────────────────────────────

function EmptyState({ onSuggestion }: { onSuggestion: (s: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4 py-16">
      <div className="w-16 h-16 bg-brand-900/30 rounded-2xl flex items-center justify-center mb-4">
        <Bot className="w-8 h-8 text-brand-400" />
      </div>
      <h2 className="text-lg font-semibold text-gray-200 mb-1">Ready to help</h2>
      <p className="text-sm text-gray-500 max-w-sm mb-8">
        Ask questions about your uploaded documents. I'll find the most relevant information and cite my sources.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-xl">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onSuggestion(s)}
            className="text-left px-4 py-3 bg-gray-800/60 border border-gray-700/50 rounded-xl text-xs text-gray-400 hover:text-gray-200 hover:border-gray-600 hover:bg-gray-800 transition-all"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
