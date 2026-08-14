const API_BASE = "/api"
const UPLOAD_TIMEOUT = 300_000 // 5 分钟（大文档处理慢）
const CHAT_TIMEOUT = 120_000 // 2 分钟

async function fetchWithTimeout(url, options, timeoutMs) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(url, { ...options, signal: controller.signal })
    return res
  } finally {
    clearTimeout(timer)
  }
}

// ========================
// Conversation API
// ========================

export async function createConversation() {
  const res = await fetchWithTimeout(
    `${API_BASE}/conversations`,
    { method: "POST" },
    10_000,
  )
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `创建对话失败 (${res.status})`)
  }
  return res.json()
}

// ========================
// Chat API - SSE 流式
// ========================

export async function sendChat(question, currentConversationId, onToken) {
  const params = new URLSearchParams({
    query: question,
    conversation_id: String(currentConversationId),
  })

  const controller = new AbortController()

  const timer = setTimeout(() => {
    controller.abort()
  }, CHAT_TIMEOUT)

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: question,
        conversation_id: Number(currentConversationId),
      }),
      signal: controller.signal,
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))

      let message = `聊天请求失败 (${res.status})`

      if (Array.isArray(err.detail)) {
        message = err.detail.map((item) => item.msg).join("; ")
      } else if (typeof err.detail === "string") {
        message = err.detail
      }

      throw new Error(message)
    }

    if (!res.body) {
      throw new Error("浏览器不支持流式响应")
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder("utf-8")

    let buffer = ""

    while (true) {
      const { value, done } = await reader.read()

      if (done) {
        break
      }

      buffer += decoder.decode(value, {
        stream: true,
      })

      // SSE 每条消息以两个换行符结束
      const events = buffer.split("\n\n")

      // 最后一段可能还没接收完整
      buffer = events.pop() || ""

      for (const event of events) {
        const line = event.split("\n").find((line) => line.startsWith("data: "))

        if (!line) {
          continue
        }

        const jsonString = line.slice(6)

        try {
          const data = JSON.parse(jsonString)

          // ------------------------
          // Token
          // ------------------------
          if (data.type === "token") {
            if (onToken) {
              onToken(data.content)
            }
          }

          // ------------------------
          // 完成
          // ------------------------
          else if (data.type === "done") {
            console.log("AI回答完成")
          }

          // ------------------------
          // 错误
          // ------------------------
          else if (data.type === "error") {
            throw new Error(data.message || "AI生成失败")
          }
        } catch (error) {
          console.error("SSE 数据解析失败:", error)
        }
      }
    }
  } finally {
    clearTimeout(timer)
  }
}

// ========================
// Sources API
// ========================

export async function addSources(conversationId, files = [], url = null) {
  const formData = new FormData()

  // 添加文件
  if (files && files.length > 0) {
    files.forEach((file) => {
      formData.append("files", file)
    })
  }

  // 添加 URL
  if (url) {
    formData.append("url", url)
  }

  const res = await fetchWithTimeout(
    `${API_BASE}/conversations/${conversationId}/sources`,
    { method: "POST", body: formData },
    UPLOAD_TIMEOUT,
  )

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `添加知识源失败 (${res.status})`)
  }
  return res.json()
}

// ========================
// Local Storage Helpers (for Conversation list)
// ========================

export function saveConversationsToLocal(conversations) {
  localStorage.setItem("conversations", JSON.stringify(conversations))
}

export function loadConversationsFromLocal() {
  try {
    const raw = localStorage.getItem("conversations")
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function saveMessagesToLocal(conversationId, messages) {
  localStorage.setItem(`messages_${conversationId}`, JSON.stringify(messages))
}

export function loadMessagesFromLocal(conversationId) {
  try {
    const raw = localStorage.getItem(`messages_${conversationId}`)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}
