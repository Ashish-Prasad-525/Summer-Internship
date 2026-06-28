import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, CheckCircle, XCircle, Loader2, X, FilePlus } from 'lucide-react'
import clsx from 'clsx'
import { uploadDocument } from '../../services/api'
import toast from 'react-hot-toast'

interface UploadFile {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
  documentId?: string
}

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'text/markdown': ['.md'],
}

const MAX_MB = 50

interface Props {
  onUploaded: () => void
}

export default function UploadPanel({ onUploaded }: Props) {
  const [files, setFiles] = useState<UploadFile[]>([])
  const [isUploading, setIsUploading] = useState(false)

  const onDrop = useCallback((accepted: File[], rejected: any[]) => {
    if (rejected.length > 0) {
      rejected.forEach((r) => {
        const reason = r.errors?.[0]?.message ?? 'Invalid file'
        toast.error(`${r.file.name}: ${reason}`)
      })
    }
    const newEntries: UploadFile[] = accepted.map((f) => ({
      id: `${f.name}-${Date.now()}-${Math.random()}`,
      file: f,
      status: 'pending',
      progress: 0,
    }))
    setFiles((prev) => [...prev, ...newEntries])
  }, [])

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxSize: MAX_MB * 1024 * 1024,
    multiple: true,
  })

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

  const uploadAll = async () => {
    const pending = files.filter((f) => f.status === 'pending')
    if (pending.length === 0) return

    setIsUploading(true)
    let successCount = 0

    for (const entry of pending) {
      setFiles((prev) =>
        prev.map((f) => (f.id === entry.id ? { ...f, status: 'uploading' } : f))
      )

      try {
        await uploadDocument(entry.file, (pct) => {
          setFiles((prev) =>
            prev.map((f) => (f.id === entry.id ? { ...f, progress: pct } : f))
          )
        })
        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id ? { ...f, status: 'success', progress: 100 } : f
          )
        )
        successCount++
      } catch (err: any) {
        const msg = err?.response?.data?.detail ?? err?.message ?? 'Upload failed'
        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id ? { ...f, status: 'error', error: msg } : f
          )
        )
        toast.error(`Failed: ${entry.file.name}`)
      }
    }

    setIsUploading(false)

    if (successCount > 0) {
      toast.success(`${successCount} file${successCount > 1 ? 's' : ''} uploaded — indexing in background`)
      onUploaded()
    }
  }

  const pendingCount = files.filter((f) => f.status === 'pending').length
  const allDone = files.length > 0 && files.every((f) => f.status === 'success' || f.status === 'error')

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800">
        <h2 className="text-sm font-semibold text-gray-100">Upload Documents</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          PDF, DOCX, TXT, MD · max {MAX_MB}MB per file
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 max-w-2xl mx-auto w-full space-y-6">
        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={clsx(
            'border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200',
            isDragActive && !isDragReject && 'border-brand-500 bg-brand-900/20 scale-[1.01]',
            isDragReject && 'border-red-500 bg-red-900/10',
            !isDragActive && 'border-gray-700 hover:border-gray-500 hover:bg-gray-800/30'
          )}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-4">
            <div className={clsx(
              'w-16 h-16 rounded-2xl flex items-center justify-center transition-colors',
              isDragActive ? 'bg-brand-700/30' : 'bg-gray-800'
            )}>
              {isDragActive ? (
                <FilePlus className="w-8 h-8 text-brand-400" />
              ) : (
                <Upload className="w-8 h-8 text-gray-500" />
              )}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-200">
                {isDragActive ? 'Drop files here…' : 'Drag & drop files'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                or <span className="text-brand-400 underline underline-offset-2">browse</span> to choose files
              </p>
            </div>
            <div className="flex items-center gap-3">
              {['PDF', 'DOCX', 'TXT', 'MD'].map((ext) => (
                <span key={ext} className="text-xs px-2.5 py-1 bg-gray-800 text-gray-400 rounded-full border border-gray-700">
                  .{ext.toLowerCase()}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Files ({files.length})
              </h3>
              {!isUploading && (
                <button
                  onClick={() => setFiles([])}
                  className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
                >
                  Clear all
                </button>
              )}
            </div>

            <div className="space-y-2">
              {files.map((entry) => (
                <FileRow
                  key={entry.id}
                  entry={entry}
                  onRemove={() => removeFile(entry.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Upload button */}
        {files.length > 0 && !allDone && (
          <button
            onClick={uploadAll}
            disabled={isUploading || pendingCount === 0}
            className="btn-primary w-full justify-center py-3"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Uploading…
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload {pendingCount} file{pendingCount !== 1 ? 's' : ''}
              </>
            )}
          </button>
        )}

        {allDone && (
          <div className="text-center py-4">
            <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            <p className="text-sm text-gray-300">Upload complete!</p>
            <p className="text-xs text-gray-500 mt-1">
              Documents are being indexed. Switch to Chat to start asking questions.
            </p>
          </div>
        )}

        {/* Info cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
          {[
            { icon: '🧠', title: 'Smart Chunking', desc: 'Documents are split into semantic chunks for accurate retrieval' },
            { icon: '🔍', title: 'Vector Search', desc: 'FAISS-powered similarity search finds the most relevant passages' },
            { icon: '📖', title: 'Source Citations', desc: 'Every answer includes page numbers and document references' },
          ].map(({ icon, title, desc }) => (
            <div key={title} className="card px-4 py-3">
              <p className="text-lg mb-1">{icon}</p>
              <p className="text-xs font-semibold text-gray-300">{title}</p>
              <p className="text-xs text-gray-600 mt-0.5 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── File Row ───────────────────────────────────────────────────────────────────

function FileRow({ entry, onRemove }: { entry: UploadFile; onRemove: () => void }) {
  const sizeKb = (entry.file.size / 1024).toFixed(1)

  return (
    <div className="card px-4 py-3">
      <div className="flex items-center gap-3">
        <FileText className="w-5 h-5 text-gray-500 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-200 truncate">{entry.file.name}</p>
          <p className="text-xs text-gray-600">{sizeKb} KB</p>
        </div>

        {/* Status icon */}
        <div className="shrink-0">
          {entry.status === 'pending' && (
            <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">Queued</span>
          )}
          {entry.status === 'uploading' && (
            <Loader2 className="w-4 h-4 text-brand-400 animate-spin" />
          )}
          {entry.status === 'success' && (
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          )}
          {entry.status === 'error' && (
            <XCircle className="w-4 h-4 text-red-400" title={entry.error} />
          )}
        </div>

        {entry.status === 'pending' && (
          <button onClick={onRemove} className="p-1 text-gray-600 hover:text-red-400 transition-colors">
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Progress bar */}
      {entry.status === 'uploading' && (
        <div className="mt-2 h-1 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all duration-300"
            style={{ width: `${entry.progress}%` }}
          />
        </div>
      )}

      {entry.status === 'error' && entry.error && (
        <p className="text-xs text-red-400 mt-1.5">{entry.error}</p>
      )}
    </div>
  )
}
