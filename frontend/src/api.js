const API_BASE = '/api'
const UPLOAD_TIMEOUT = 300_000 // 5 分钟（大文档处理慢）
const CHAT_TIMEOUT = 120_000   // 2 分钟

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

export async function uploadFiles(files) {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  const res = await fetchWithTimeout(
    `${API_BASE}/upload`,
    { method: 'POST', body: formData },
    UPLOAD_TIMEOUT,
  )
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `上传失败 (${res.status})`)
  }
  return res.json()
}

export async function deleteDocument(source) {
  const res = await fetchWithTimeout(
    `${API_BASE}/delete?source=${encodeURIComponent(source)}`,
    { method: 'DELETE' },
    30_000,
  )
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `删除失败 (${res.status})`)
  }
  const data = await res.json()
  // 后端异常时返回 200 但 body 里有 error 字段
  if (data.error) {
    throw new Error(data.error)
  }
  return data
}

export async function sendChat(question, threadId = 'default_thread') {
  const res = await fetchWithTimeout(
    `${API_BASE}/chat`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, thread_id: threadId }),
    },
    CHAT_TIMEOUT,
  )
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `请求失败 (${res.status})`)
  }
  return res.json()
}
