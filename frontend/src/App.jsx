import { useState, useRef, useEffect } from 'react'
import { uploadFiles, sendChat, deleteDocument } from './api'
import UploadZone from './components/UploadZone'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import DocumentPanel from './components/DocumentPanel'

function loadDocuments() {
  try {
    const saved = localStorage.getItem('rag_documents')
    return saved ? JSON.parse(saved) : []
  } catch {
    return []
  }
}

function saveDocuments(docs) {
  localStorage.setItem('rag_documents', JSON.stringify(docs))
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState(null)
  const [documents, setDocuments] = useState(loadDocuments)
  const [deleting, setDeleting] = useState(null) // 正在删除的文档名
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleUpload = async (files) => {
    setUploading(true)
    setUploadMsg(null)
    try {
      const data = await uploadFiles(files)
      setUploadMsg({ type: 'success', text: data.message, time: Date.now() })

      const now = Date.now()
      const newDocs = files.map((f) => ({ name: f.name, uploadedAt: now }))
      setDocuments((prev) => {
        const merged = [...prev]
        for (const doc of newDocs) {
          const idx = merged.findIndex((d) => d.name === doc.name)
          if (idx >= 0) {
            merged[idx] = { ...merged[idx], uploadedAt: now }
          } else {
            merged.push(doc)
          }
        }
        saveDocuments(merged)
        return merged
      })
    } catch (e) {
      const msg =
        e.name === 'AbortError'
          ? '上传超时：后端处理时间过长或未启动，请确认后端正在运行'
          : e.message
      setUploadMsg({ type: 'error', text: msg, time: Date.now() })
    } finally {
      setUploading(false)
    }
  }

  const handleSend = async (question) => {
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setLoading(true)
    try {
      const data = await sendChat(question)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources || [],
        },
      ])
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `错误: ${e.message}`, isError: true },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (source) => {
    setDeleting(source)
    try {
      await deleteDocument(source)
      setDocuments((prev) => {
        const updated = prev.filter((d) => d.name !== source)
        saveDocuments(updated)
        return updated
      })
    } catch (e) {
      alert(`删除失败：${e.message}`)
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white px-6 py-3 flex items-center justify-between shrink-0 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-lg font-semibold text-gray-800">RAG 知识库问答</h1>
        </div>
        <UploadZone onUpload={handleUpload} uploading={uploading} uploadMsg={uploadMsg} />
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Chat area */}
        <div className="flex flex-col flex-1 min-w-0">
          <div className="flex-1 overflow-y-auto px-4 py-6">
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-[60vh] text-gray-400">
                  <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  <p className="text-lg font-medium mb-1">开始提问吧！</p>
                  <p className="text-sm">点击右上角上传文档到知识库，然后在下方向我提问</p>
                </div>
              )}
              {messages.map((msg, i) => (
                <ChatMessage key={i} message={msg} />
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-5 py-3.5 shadow-sm">
                    <div className="flex gap-1.5">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
          <ChatInput onSend={handleSend} loading={loading} />
        </div>

        {/* Document sidebar */}
        <DocumentPanel documents={documents} onDelete={handleDelete} deleting={deleting} />
      </div>
    </div>
  )
}
