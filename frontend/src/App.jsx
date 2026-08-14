import { useState, useRef, useEffect, useCallback } from "react"
import {
  createConversation,
  sendChat,
  addSources,
  saveConversationsToLocal,
  loadConversationsFromLocal,
  saveMessagesToLocal,
  loadMessagesFromLocal,
} from "./api"
import UploadZone from "./components/UploadZone"
import ChatMessage from "./components/ChatMessage"
import ChatInput from "./components/ChatInput"
import KnowledgeBase from "./components/KnowledgeBase"
import ConversationSidebar from "./components/ConversationSidebar"
import UploadDialog from "./components/UploadDialog"

function loadJSON(key) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveJSON(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

function initConversation() {
  const existing = localStorage.getItem("currentConversationId")
  if (existing) return parseInt(existing)
  return null
}

export default function App() {
  // Conversation state
  const [conversations, setConversations] = useState(
    loadConversationsFromLocal(),
  )
  const [currentConversationId, setCurrentConversationId] =
    useState(initConversation())

  // Messages state
  const [messages, setMessages] = useState(() => {
    if (currentConversationId) {
      return loadMessagesFromLocal(currentConversationId)
    }
    return []
  })

  // Sources state (knowledge base)
  const [sources, setSources] = useState(() => {
    if (!currentConversationId) return []
    return loadJSON(`sources_${currentConversationId}`) || []
  })

  // UI state
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState(null)
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Persist conversations
  useEffect(() => {
    saveConversationsToLocal(conversations)
  }, [conversations])

  // Persist current conversation ID
  useEffect(() => {
    if (currentConversationId) {
      localStorage.setItem(
        "currentConversationId",
        String(currentConversationId),
      )
    }
  }, [currentConversationId])

  // Persist messages for current conversation
  useEffect(() => {
    if (currentConversationId) {
      saveMessagesToLocal(currentConversationId, messages)
    }
  }, [messages, currentConversationId])

  // Persist sources for current conversation
  useEffect(() => {
    if (currentConversationId) {
      saveJSON(`sources_${currentConversationId}`, sources)
    }
  }, [sources, currentConversationId])

  // Create new conversation
  const handleNewConversation = useCallback(async () => {
    try {
      setError(null)
      const data = await createConversation()

      const newConversation = {
        id: data.conversation_id,
        title: data.title,
        created_at: new Date().toISOString(),
      }

      setConversations((prev) => [newConversation, ...prev])
      setCurrentConversationId(data.conversation_id)
      setMessages([])
      setSources([])
    } catch (e) {
      setError(`创建对话失败: ${e.message}`)
    }
  }, [])

  // Select conversation
  const handleSelectConversation = useCallback((id) => {
    setCurrentConversationId(id)
    setMessages(loadMessagesFromLocal(id))
    setSources(loadJSON(`sources_${id}`) || [])
    setError(null)
  }, [])

  // Delete conversation
  const handleDeleteConversation = useCallback(
    (id) => {
      localStorage.removeItem(`sources_${id}`)

      setConversations((prev) => {
        const updated = prev.filter((c) => c.id !== id)

        if (id === currentConversationId) {
          const nextConversation = updated[0] || null

          setCurrentConversationId(
            nextConversation ? nextConversation.id : null,
          )
          setMessages(
            nextConversation ? loadMessagesFromLocal(nextConversation.id) : [],
          )
          setSources(
            nextConversation
              ? loadJSON(`sources_${nextConversation.id}`) || []
              : [],
          )
        }

        return updated
      })
    },
    [currentConversationId],
  )

  // Send chat message
  const handleSend = useCallback(
    async (question) => {
      if (!currentConversationId) {
        setError("请先创建或选择一个对话")
        return
      }

      setMessages((prev) => [
        ...prev,
        { role: "user", content: question },
        { role: "assistant", content: "" },
      ])
      setLoading(true)
      setError(null)

      try {
        // Update conversation title if it's the first message
        setConversations((prev) => {
          const updated = [...prev]
          const idx = updated.findIndex((c) => c.id === currentConversationId)
          if (
            idx >= 0 &&
            (!updated[idx].title || updated[idx].title === "新聊天")
          ) {
            updated[idx].title =
              question.slice(0, 50) + (question.length > 50 ? "..." : "")
          }
          return updated
        })

        await sendChat(question, currentConversationId, (token) => {
          setMessages((prev) => {
            const newMessages = [...prev]
            const assistantIndex = newMessages.findLastIndex(
              (msg) => msg.role === "assistant",
            )

            if (assistantIndex === -1) return prev

            const current = newMessages[assistantIndex]
            newMessages[assistantIndex] = {
              ...current,
              content: (current.content || "") + token,
            }

            return newMessages
          })
        })
      } catch (e) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `错误: ${e.message}`, isError: true },
        ])
        setError(`聊天请求失败: ${e.message}`)
      } finally {
        setLoading(false)
      }
    },
    [currentConversationId],
  )

  // Upload files or URL
  const handleUpload = useCallback(
    async (files = [], url = null) => {
      if (!currentConversationId) {
        setError("请先创建或选择一个对话")
        return
      }

      setUploading(true)
      setUploadMsg(null)
      setError(null)

      try {
        const result = await addSources(currentConversationId, files, url)
        setUploadMsg({
          type: "success",
          text:
            result.message ||
            `成功添加知识源，共 ${result.total_chunks} 个 chunks`,
          time: Date.now(),
        })

        // Update sources list
        if (files.length > 0) {
          const newSources = files.map((file) => ({
            name: file.name,
            type: "file",
            chunks: 0,
            status: "completed",
            uploadedAt: new Date().toISOString(),
          }))
          setSources((prev) => [...prev, ...newSources])
        }

        if (url) {
          setSources((prev) => [
            ...prev,
            {
              name: url,
              type: "url",
              chunks: 0,
              status: "completed",
              uploadedAt: new Date().toISOString(),
            },
          ])
        }

        setShowUploadDialog(false)
      } catch (e) {
        const msg =
          e.name === "AbortError"
            ? "上传超时：后端处理时间过长或未启动"
            : e.message
        setUploadMsg({ type: "error", text: msg, time: Date.now() })
        setError(`知识源添加失败: ${msg}`)
      } finally {
        setUploading(false)
      }
    },
    [currentConversationId],
  )

  const currentConversation = conversations.find(
    (c) => c.id === currentConversationId,
  )

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white px-6 py-3 flex items-center justify-between shrink-0 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg flex items-center justify-center">
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          </div>
          <h1 className="text-lg font-semibold text-gray-800">
            多模态 RAG 知识库
          </h1>
        </div>
        {error && (
          <div className="flex items-center gap-2 px-3 py-2 bg-red-50 text-red-700 rounded-lg text-sm border border-red-200">
            <svg
              className="w-4 h-4 shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            {error}
          </div>
        )}
      </header>

      {/* Body: 3-column layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Conversation Sidebar */}
        <ConversationSidebar
          conversations={conversations}
          currentConversationId={currentConversationId}
          onNewConversation={handleNewConversation}
          onSelectConversation={handleSelectConversation}
          onDeleteConversation={handleDeleteConversation}
        />

        {/* Middle: Chat Window */}
        <div className="flex flex-col flex-1 min-w-0">
          {/* Chat header */}
          {currentConversation && (
            <div className="border-b border-gray-200 bg-white px-6 py-3 shrink-0">
              <h2 className="text-base font-semibold text-gray-800">
                {currentConversation.title}
              </h2>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6">
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-[60vh] text-gray-400">
                  <svg
                    className="w-16 h-16 mb-4 text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1}
                      d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                    />
                  </svg>
                  <p className="text-lg font-medium mb-1">开始提问吧！</p>
                  <p className="text-sm">
                    向知识库提问，AI 将基于你上传的文档进行回答
                  </p>
                </div>
              )}
              {messages.map((msg, i) => (
                <ChatMessage key={i} message={msg} />
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-5 py-3.5 shadow-sm">
                    <div className="flex gap-1.5">
                      <span
                        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0ms" }}
                      />
                      <span
                        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                        style={{ animationDelay: "150ms" }}
                      />
                      <span
                        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                        style={{ animationDelay: "300ms" }}
                      />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input */}
          <ChatInput onSend={handleSend} loading={loading} />
        </div>

        {/* Right: Knowledge Base */}
        <KnowledgeBase
          currentConversationId={currentConversationId}
          sources={sources}
          onUpload={() => setShowUploadDialog(true)}
          uploading={uploading}
          uploadMsg={uploadMsg}
        />
      </div>

      {/* Upload Dialog */}
      {showUploadDialog && (
        <UploadDialog
          conversationId={currentConversationId}
          onClose={() => setShowUploadDialog(false)}
          onUpload={handleUpload}
          uploading={uploading}
        />
      )}
    </div>
  )
}
