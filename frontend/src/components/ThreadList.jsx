function formatTime(ts) {
  const d = new Date(ts)
  const now = new Date()
  const diffMs = now - d
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour} 小时前`
  const diffDay = Math.floor(diffHour / 24)
  if (diffDay < 7) return `${diffDay} 天前`
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export default function ThreadList({ threads, currentThreadId, onNewThread, onSelectThread, onDeleteThread }) {
  const sorted = [...threads].sort((a, b) => b.createdAt - a.createdAt)

  return (
    <div className="w-64 border-r border-gray-200 bg-gray-50/50 flex flex-col shrink-0">
      {/* Header */}
      <div className="px-4 py-3.5 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          对话历史
        </h2>
        <span className="text-xs text-gray-400 bg-gray-200/70 px-2 py-0.5 rounded-full">
          {threads.length}
        </span>
      </div>

      {/* New conversation button */}
      <div className="px-3 py-3">
        <button
          onClick={onNewThread}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 active:bg-blue-800 rounded-xl transition-all shadow-sm hover:shadow-md"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          新建对话
        </button>
      </div>

      {/* Divider */}
      <div className="mx-4 border-t border-gray-200" />

      {/* Thread list */}
      <div className="flex-1 overflow-y-auto">
        {sorted.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <div className="w-14 h-14 rounded-2xl bg-gray-100 flex items-center justify-center mb-3">
              <svg className="w-7 h-7 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p className="text-sm text-gray-400 font-medium">暂无对话</p>
            <p className="text-xs text-gray-300 mt-1">点击上方按钮开始新对话</p>
          </div>
        ) : (
          <div className="p-2 space-y-0.5">
            {sorted.map((t) => {
              const isActive = t.id === currentThreadId
              return (
                <div
                  key={t.id}
                  className={`group relative rounded-xl transition-all ${
                    isActive
                      ? 'bg-blue-50 border border-blue-200 shadow-sm'
                      : 'border border-transparent hover:bg-white hover:border-gray-200 hover:shadow-sm'
                  }`}
                >
                  <button
                    onClick={() => onSelectThread(t.id)}
                    className="w-full text-left px-3 py-3 pr-10"
                  >
                    <div className="flex items-center gap-2">
                      {/* Active indicator dot */}
                      <span
                        className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                          isActive ? 'bg-blue-500 shadow-sm shadow-blue-300' : 'bg-gray-300'
                        }`}
                      />
                      <div className="min-w-0 flex-1">
                        <div
                          className={`truncate text-[13px] font-medium leading-tight ${
                            isActive ? 'text-blue-800' : 'text-gray-700'
                          }`}
                        >
                          {t.title || '新对话'}
                        </div>
                        <div className="text-[10px] text-gray-400 mt-1">
                          {formatTime(t.createdAt)}
                        </div>
                      </div>
                    </div>
                  </button>

                  {/* Delete button — visible on hover */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteThread(t.id)
                    }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all"
                    title="删除对话"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 border-t border-gray-200">
        <p className="text-[10px] text-gray-400 text-center">
          悬停对话卡片可删除
        </p>
      </div>
    </div>
  )
}
