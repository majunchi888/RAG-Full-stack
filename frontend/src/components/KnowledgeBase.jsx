export default function KnowledgeBase({
  currentConversationId,
  sources,
  onUpload,
  uploading,
  uploadMsg,
}) {
  return (
    <div className="w-72 border-l border-gray-200 bg-white flex flex-col shrink-0">
      {/* Panel header */}
      <div className="px-4 py-3.5 border-b border-gray-100 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
          <svg
            className="w-4 h-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 6.253v13m0-13C6.5 6.253 2 10.998 2 17s4.5 10.747 10 10.747c5.5 0 10-4.998 10-10.747 0-5.002-4.5-10.747-10-10.747z"
            />
          </svg>
          知识库
        </h2>
        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
          {sources.length}
        </span>
      </div>

      {/* Add source button */}
      <div className="px-3 py-2.5 border-b border-gray-100">
        <button
          onClick={onUpload}
          disabled={!currentConversationId || uploading}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-all"
        >
          <svg
            className={`w-4 h-4 ${uploading ? "animate-spin" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          {uploading ? "处理中..." : " 添加知识源"}
        </button>
      </div>

      {/* Sources list */}
      <div className="flex-1 overflow-y-auto">
        {sources.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            <svg
              className="w-10 h-10 text-gray-200 mb-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12l2 2 4-4m7 0a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-sm text-gray-400">暂无知识源</p>
            <p className="text-xs text-gray-300 mt-1">
              {currentConversationId ? "点击上方按钮添加" : "先创建一个对话"}
            </p>
          </div>
        ) : (
          <div className="p-3 space-y-2">
            {sources.map((source, idx) => (
              <div
                key={idx}
                className="bg-gray-50 hover:bg-gray-100 border border-gray-100 hover:border-gray-200 rounded-lg p-3 transition-all duration-150"
              >
                <div className="flex items-start gap-2.5">
                  {/* Icon */}
                  <div className="mt-0.5 shrink-0">
                    {source.type === "url" ? (
                      <svg
                        className="w-4 h-4 text-blue-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.658 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                        />
                      </svg>
                    ) : (source.name || "").endsWith(".pdf") ? (
                      <svg
                        className="w-4 h-4 text-red-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                        />
                      </svg>
                    ) : (source.name || "").endsWith(".mp3") ||
                      (source.name || "").endsWith(".wav") ? (
                      <svg
                        className="w-4 h-4 text-purple-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                        />
                      </svg>
                    ) : (source.name || "").endsWith(".mp4") ||
                      (source.name || "").endsWith(".avi") ? (
                      <svg
                        className="w-4 h-4 text-orange-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                    ) : (
                      <svg
                        className="w-4 h-4 text-gray-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                    )}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p
                      className="text-sm font-medium text-gray-700 truncate"
                      title={source.name}
                    >
                      {source.name}
                    </p>
                    <p className="text-[10px] text-gray-400 mt-0.5">
                      {source.status === "completed" && (
                        <>
                          <span className="inline-flex items-center gap-0.5">
                            <svg
                              className="w-3 h-3 text-emerald-500"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                clipRule="evenodd"
                              />
                            </svg>
                            已完成
                          </span>
                        </>
                      )}
                      {source.status === "processing" && (
                        <span className="inline-flex items-center gap-0.5">
                          <svg
                            className="w-3 h-3 animate-spin text-blue-500"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                            />
                          </svg>
                          处理中
                        </span>
                      )}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer hint */}
      <div className="px-4 py-2.5 border-t border-gray-100">
        <p className="text-[10px] text-gray-400 text-center">
          支持 PDF、文档、音视频URL
        </p>
      </div>
    </div>
  )
}
