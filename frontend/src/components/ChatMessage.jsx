import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import "highlight.js/styles/atom-one-light.css"

export default function ChatMessage({ message }) {
  const isUser = message.role === "user"

  return (
    <div className={`flex items-end gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-white text-xs font-medium ${
          isUser
            ? "bg-gradient-to-br from-blue-400 to-blue-600"
            : "bg-gradient-to-br from-emerald-400 to-emerald-600"
        }`}
      >
        {isUser ? "U" : "AI"}
      </div>

      {/* Bubble */}
      <div className={`max-w-[75%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-blue-600 text-white rounded-br-md"
              : message.isError
                ? "bg-red-50 text-red-700 border border-red-200 rounded-bl-md"
                : "bg-white border border-gray-200 shadow-sm rounded-bl-md"
          }`}
        >
          {isUser ? (
            message.content
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={{
                p: ({ node, ...props }) => (
                  <p className="mb-2 last:mb-0" {...props} />
                ),
                ul: ({ node, ...props }) => (
                  <ul
                    className="list-disc list-inside mb-2 space-y-1"
                    {...props}
                  />
                ),
                ol: ({ node, ...props }) => (
                  <ol
                    className="list-decimal list-inside mb-2 space-y-1"
                    {...props}
                  />
                ),
                li: ({ node, ...props }) => <li className="mb-1" {...props} />,
                code: ({ node, inline, ...props }) =>
                  inline ? (
                    <code
                      className="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono text-red-600"
                      {...props}
                    />
                  ) : (
                    <code
                      className="block bg-gray-900 text-gray-100 p-3 rounded-lg mb-2 text-xs font-mono overflow-x-auto"
                      {...props}
                    />
                  ),
                pre: ({ node, ...props }) => (
                  <pre className="mb-2" {...props} />
                ),
                blockquote: ({ node, ...props }) => (
                  <blockquote
                    className="border-l-4 border-gray-300 pl-3 py-1 italic text-gray-600 mb-2"
                    {...props}
                  />
                ),
                h1: ({ node, ...props }) => (
                  <h1 className="text-lg font-bold mb-2 mt-3" {...props} />
                ),
                h2: ({ node, ...props }) => (
                  <h2 className="text-base font-bold mb-2 mt-2" {...props} />
                ),
                h3: ({ node, ...props }) => (
                  <h3 className="text-sm font-bold mb-1 mt-2" {...props} />
                ),
                table: ({ node, ...props }) => (
                  <table
                    className="border-collapse w-full text-xs mb-2"
                    {...props}
                  />
                ),
                th: ({ node, ...props }) => (
                  <th
                    className="border border-gray-300 bg-gray-100 px-2 py-1 text-left"
                    {...props}
                  />
                ),
                td: ({ node, ...props }) => (
                  <td className="border border-gray-300 px-2 py-1" {...props} />
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
      </div>
    </div>
  )
}
