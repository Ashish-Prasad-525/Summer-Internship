import { FileText, MessageSquare, Upload, RefreshCw, Trash2, CheckSquare, Square, Database, Loader2, AlertCircle } from 'lucide-react'
import clsx from 'clsx'
import { DocumentMeta, StatsResponse } from '../../services/api'

interface Props {
  view: 'chat' | 'upload'
  setView: (v: 'chat' | 'upload') => void
  documents: DocumentMeta[]
  stats: StatsResponse | null
  docsLoading: boolean
  selectedDocIds: string[]
  onToggleDoc: (id: string) => void
  onDeleteDoc: (id: string, name: string) => void
  onRefresh: () => void
}

const STATUS_COLOR: Record<string, string> = {
  indexed:    'bg-emerald-500',
  processing: 'bg-amber-400',
  pending:    'bg-amber-400',
  failed:     'bg-red-500',
}

export default function Sidebar({
  view, setView, documents, stats, docsLoading,
  selectedDocIds, onToggleDoc, onDeleteDoc, onRefresh,
}: Props) {
  const indexedDocs = documents.filter((d) => d.status === 'indexed')

  return (
    <aside className="w-72 flex flex-col bg-gray-900 border-r border-gray-800 shrink-0">
      {/* Header */}
      <div className="px-4 py-5 border-b border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
            <Database className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-gray-100">Doc Intelligence</h1>
            <p className="text-xs text-gray-500">RAG-powered search</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="px-3 py-3 border-b border-gray-800 space-y-1">
        <button
          onClick={() => setView('chat')}
          className={clsx(
            'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            view === 'chat'
              ? 'bg-brand-600/20 text-brand-300'
              : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'
          )}
        >
          <MessageSquare className="w-4 h-4" />
          Chat with Documents
        </button>
        <button
          onClick={() => setView('upload')}
          className={clsx(
            'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            view === 'upload'
              ? 'bg-brand-600/20 text-brand-300'
              : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'
          )}
        >
          <Upload className="w-4 h-4" />
          Upload Documents
        </button>
      </nav>

      {/* Stats bar */}
      {stats && (
        <div className="px-4 py-3 border-b border-gray-800 grid grid-cols-2 gap-2">
          {[
            { label: 'Documents', value: stats.indexed_documents },
            { label: 'Chunks', value: stats.total_chunks.toLocaleString() },
          ].map(({ label, value }) => (
            <div key={label} className="bg-gray-800 rounded-lg px-3 py-2 text-center">
              <p className="text-base font-semibold text-brand-400">{value}</p>
              <p className="text-xs text-gray-500">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Document list */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Knowledge Base
          </span>
          <button
            onClick={onRefresh}
            className="p-1 text-gray-500 hover:text-gray-300 transition-colors rounded"
            title="Refresh"
          >
            <RefreshCw className={clsx('w-3.5 h-3.5', docsLoading && 'animate-spin')} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-1">
          {docsLoading && documents.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 text-gray-600 animate-spin" />
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-8 px-4">
              <FileText className="w-8 h-8 text-gray-700 mx-auto mb-2" />
              <p className="text-xs text-gray-500">No documents yet.</p>
              <p className="text-xs text-gray-600 mt-1">Upload PDFs, DOCX, or TXT files to get started.</p>
            </div>
          ) : (
            documents.map((doc) => (
              <DocumentItem
                key={doc.doc_id}
                doc={doc}
                selected={selectedDocIds.includes(doc.doc_id)}
                onToggle={() => onToggleDoc(doc.doc_id)}
                onDelete={() => onDeleteDoc(doc.doc_id, doc.filename)}
              />
            ))
          )}
        </div>
      </div>

      {/* Filter hint */}
      {selectedDocIds.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-800 bg-brand-900/20">
          <p className="text-xs text-brand-400">
            🔍 Filtering by {selectedDocIds.length} document{selectedDocIds.length > 1 ? 's' : ''}
          </p>
        </div>
      )}
    </aside>
  )
}

function DocumentItem({
  doc, selected, onToggle, onDelete,
}: {
  doc: DocumentMeta
  selected: boolean
  onToggle: () => void
  onDelete: () => void
}) {
  const isReady = doc.status === 'indexed'
  const isPending = doc.status === 'pending' || doc.status === 'processing'
  const isFailed = doc.status === 'failed'

  return (
    <div
      className={clsx(
        'group flex items-start gap-2 px-2.5 py-2 rounded-lg cursor-pointer transition-colors',
        selected ? 'bg-brand-900/30 border border-brand-800/50' : 'hover:bg-gray-800/60'
      )}
      onClick={isReady ? onToggle : undefined}
    >
      {/* Checkbox */}
      <div className="mt-0.5 shrink-0 text-gray-500">
        {isReady ? (
          selected ? (
            <CheckSquare className="w-4 h-4 text-brand-400" />
          ) : (
            <Square className="w-4 h-4" />
          )
        ) : isFailed ? (
          <AlertCircle className="w-4 h-4 text-red-500" />
        ) : (
          <Loader2 className="w-4 h-4 text-amber-400 animate-spin" />
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-gray-200 truncate" title={doc.filename}>
          {doc.filename}
        </p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className={clsx('w-1.5 h-1.5 rounded-full shrink-0', STATUS_COLOR[doc.status] ?? 'bg-gray-600')} />
          <span className="text-xs text-gray-500 capitalize">{doc.status}</span>
          {doc.chunks_created > 0 && (
            <span className="text-xs text-gray-600">· {doc.chunks_created} chunks</span>
          )}
        </div>
      </div>

      {/* Delete */}
      <button
        onClick={(e) => { e.stopPropagation(); onDelete() }}
        className="shrink-0 opacity-0 group-hover:opacity-100 p-1 text-gray-600 hover:text-red-400 transition-all rounded"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}
