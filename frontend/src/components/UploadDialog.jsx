import { useState, useRef } from "react"

export default function UploadDialog({
  conversationId,
  onClose,
  onUpload,
  uploading,
}) {
  const [activeTab, setActiveTab] = useState("files") // "files" or "url"
  const [files, setFiles] = useState([])
  const [url, setUrl] = useState("")
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef(null)
  const dragRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const droppedFiles = [...e.dataTransfer.files]
    setFiles((prev) => [...prev, ...droppedFiles])
  }

  const handleFileSelect = (e) => {
    const selectedFiles = [...e.target.files]
    setFiles((prev) => [...prev, ...selectedFiles])
  }

  const removeFile = (idx) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx))
  }

  const handleUploadFiles = async () => {
    if (files.length === 0) return

    try {
      await onUpload(files, null)
      setFiles([])
      setActiveTab("files")
      onClose()
    } catch (e) {
      console.error("Upload error:", e)
    }
  }

  const handleUploadUrl = async () => {
    if (!url.trim()) return

    try {
      await onUpload([], url)
      setUrl("")
      setActiveTab("files")
      onClose()
    } catch (e) {
      console.error("Upload error:", e)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">添加知识源</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
            disabled={uploading}
          >
            <svg
              className="w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 px-6">
          <div className="flex gap-6">
            <button
              onClick={() => setActiveTab("files")}
              className={`py-3 px-1 font-medium text-sm border-b-2 transition-colors ${
                activeTab === "files"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-600 hover:text-gray-900"
              }`}
            >
              <svg
                className="w-4 h-4 inline mr-2"
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
              上传文件
            </button>
            <button
              onClick={() => setActiveTab("url")}
              className={`py-3 px-1 font-medium text-sm border-b-2 transition-colors ${
                activeTab === "url"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-600 hover:text-gray-900"
              }`}
            >
              <svg
                className="w-4 h-4 inline mr-2"
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
              视频链接
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Files Tab */}
          {activeTab === "files" && (
            <div className="space-y-4">
              {/* Drag & Drop Area */}
              <div
                ref={dragRef}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  dragActive
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-300 hover:border-gray-400 bg-gray-50"
                }`}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  accept=".pdf,.doc,.docx,.txt,.mp3,.mp4,.wav,.avi,.mov,.webm"
                  disabled={uploading}
                />

                <svg
                  className="w-8 h-8 mx-auto mb-2 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>

                <p className="text-sm font-medium text-gray-700">
                  拖拽文件到这里或点击选择
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  支持 PDF、Word、文本、音视频
                </p>
              </div>

              {/* File List */}
              {files.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-gray-600">
                    {files.length} 个文件已选择
                  </p>
                  {files.map((file, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200"
                    >
                      <svg
                        className="w-4 h-4 text-gray-400 shrink-0"
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
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-700 truncate">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                      <button
                        onClick={() => removeFile(idx)}
                        className="p-1 hover:bg-red-100 rounded text-gray-400 hover:text-red-500 transition-colors"
                        disabled={uploading}
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* URL Tab */}
          {activeTab === "url" && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  视频链接
                </label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://www.bilibili.com/video/..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  disabled={uploading}
                />
                <p className="text-xs text-gray-500 mt-2">
                  支持 Bilibili、YouTube 等视频平台
                </p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-xs text-blue-800">
                  <strong>提示：</strong>
                  输入视频链接后，系统将自动下载视频并进行语音识别转录。
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex gap-3 justify-end">
          <button
            onClick={onClose}
            disabled={uploading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            取消
          </button>
          <button
            onClick={
              activeTab === "files" ? handleUploadFiles : handleUploadUrl
            }
            disabled={
              uploading ||
              (activeTab === "files" ? files.length === 0 : !url.trim())
            }
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {uploading && (
              <svg
                className="w-4 h-4 animate-spin"
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
            )}
            {uploading
              ? activeTab === "files"
                ? "上传中..."
                : "处理中..."
              : "添加"}
          </button>
        </div>
      </div>
    </div>
  )
}
