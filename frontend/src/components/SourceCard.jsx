export default function SourceCard({ source }) {
  return (
    <div className="bg-gray-50 border border-gray-100 rounded-xl p-3.5 text-xs shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 font-medium text-[11px] border border-blue-100">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          {source.source || '未知来源'}
        </span>
        {source.page != null && (
          <span className="text-gray-400 text-[11px] flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            第 {source.page} 页
          </span>
        )}
      </div>
      {source.snippet && (
        <p className="text-gray-500 leading-relaxed line-clamp-3">{source.snippet}</p>
      )}
    </div>
  )
}
