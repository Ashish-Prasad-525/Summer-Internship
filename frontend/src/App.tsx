import { useState } from 'react'
import { Toaster } from 'react-hot-toast'
import Sidebar from './components/layout/Sidebar'
import ChatPanel from './components/chat/ChatPanel'
import UploadPanel from './components/upload/UploadPanel'
import { useDocuments } from './hooks/useDocuments'
import { useChat } from './hooks/useChat'

type View = 'chat' | 'upload'

export default function App() {
  const [view, setView] = useState<View>('chat')
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([])

  const { documents, stats, loading, refresh, remove } = useDocuments()
  const { messages, isLoading, sendMessage, stopStreaming, clearChat } =
    useChat(selectedDocIds)

  const toggleDocFilter = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    )
  }

  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#1f2937', color: '#f9fafb', border: '1px solid #374151' },
        }}
      />

      {/* ── Sidebar ─────────────────────────────────────────────── */}
      <Sidebar
        view={view}
        setView={setView}
        documents={documents}
        stats={stats}
        docsLoading={loading}
        selectedDocIds={selectedDocIds}
        onToggleDoc={toggleDocFilter}
        onDeleteDoc={remove}
        onRefresh={refresh}
      />

      {/* ── Main Panel ──────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col min-w-0">
        {view === 'chat' ? (
          <ChatPanel
            messages={messages}
            isLoading={isLoading}
            onSend={sendMessage}
            onStop={stopStreaming}
            onClear={clearChat}
            selectedDocIds={selectedDocIds}
            documents={documents}
          />
        ) : (
          <UploadPanel onUploaded={() => { refresh(); setView('chat') }} />
        )}
      </main>
    </div>
  )
}
