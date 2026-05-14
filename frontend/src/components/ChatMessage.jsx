import SourceCard from './SourceCard'

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex items-end gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-white text-xs font-medium ${
          isUser
            ? 'bg-gradient-to-br from-blue-400 to-blue-600'
            : 'bg-gradient-to-br from-emerald-400 to-emerald-600'
        }`}
      >
        {isUser ? 'U' : 'AI'}
      </div>

      {/* Bubble */}
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? 'bg-blue-600 text-white rounded-br-md'
              : message.isError
                ? 'bg-red-50 text-red-700 border border-red-200 rounded-bl-md'
                : 'bg-white border border-gray-200 shadow-sm rounded-bl-md'
          }`}
        >
          {message.content}
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 space-y-2">
            <p className="text-xs font-semibold text-gray-400 tracking-wide uppercase flex items-center gap-1.5">
              <span className="w-3 h-0.5 bg-gray-300 rounded-full" />
              来源引用
              <span className="w-3 h-0.5 bg-gray-300 rounded-full" />
            </p>
            {(() => {
              const seen = new Set()
              const unique = message.sources.filter((src) => {
                const key = `${src.source || ''}||${src.page ?? ''}`
                if (seen.has(key)) return false
                seen.add(key)
                return true
              })
              return unique.map((src, i) => (
                <SourceCard key={i} source={src} />
              ))
            })()}
          </div>
        )}
      </div>
    </div>
  )
}
