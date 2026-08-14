import { useRef, useState, useEffect } from "react"

export default function UploadZone({ onUpload, uploading, uploadMsg }) {
  const inputRef = useRef(null)
  const [showToast, setShowToast] = useState(false)

  useEffect(() => {
    if (uploadMsg) {
      setShowToast(true)
      const timer = setTimeout(() => setShowToast(false), 4000)
      return () => clearTimeout(timer)
    }
  }, [uploadMsg])

  const handleClick = () => inputRef.current?.click()

  const handleChange = (e) => {
    if (e.target.files.length > 0) {
      onUpload(Array.from(e.target.files))
      e.target.value = ""
    }
  }

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.doc,.docx,.txt"
        onChange={handleChange}
        className="hidden"
      />
      <button
        onClick={handleClick}
        disabled={uploading}
        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-xl hover:bg-blue-100 disabled:opacity-50 transition-all duration-200"
      >
        <svg
          className={`w-4 h-4 ${uploading ? "animate-spin" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          {uploading ? (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          ) : (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          )}
        </svg>
        {uploading ? "上传中..." : "上传文档"}
      </button>

      {/* Toast notification */}
      {showToast && uploadMsg && (
        <div className="absolute top-full mt-2 right-0 z-50 animate-slide-down min-w-[200px]">
          <div
            className={`text-sm px-4 py-2.5 rounded-xl shadow-lg border flex items-center gap-2 ${
              uploadMsg.type === "success"
                ? "bg-green-50 text-green-800 border-green-200"
                : "bg-red-50 text-red-800 border-red-200"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full shrink-0 ${uploadMsg.type === "success" ? "bg-green-500" : "bg-red-500"}`}
            />
            {uploadMsg.text}
          </div>
        </div>
      )}
    </div>
  )
}
