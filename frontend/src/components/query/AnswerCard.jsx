/**
 * AnswerCard — Displays the generated LLM response
 * @param {Object} props
 * @param {string} props.answer - The generated text
 * @param {Array} props.citations - List of source chunk IDs or indices
 */
export default function AnswerCard({ answer, citations }) {
  if (!answer) return null

  return (
    <div className="bg-navy-800/80 border border-electric/30 rounded-2xl p-6 shadow-[0_0_30px_rgba(59,130,246,0.1)] overflow-hidden relative">
      <div className="absolute top-0 left-0 w-1 h-full bg-electric" />
      
      <div className="flex items-center gap-2 mb-4">
        <div className="w-6 h-6 bg-electric/20 text-electric rounded-full flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        </div>
        <h3 className="font-mono font-bold uppercase tracking-widest text-xs text-electric">Generated Response</h3>
      </div>

      <div className="prose prose-invert max-w-none">
        <p className="text-slate-100 leading-relaxed whitespace-pre-wrap">
          {answer}
        </p>
      </div>

      {citations && citations.length > 0 && (
        <div className="mt-6 flex flex-wrap gap-2 items-center">
          <span className="text-[10px] font-mono uppercase text-slate-500 font-bold mr-2">Citations:</span>
          {citations.map((cite, i) => (
            <span 
              key={i} 
              className="px-2 py-0.5 bg-navy-700 text-electric text-[10px] font-mono rounded border border-electric/20"
            >
              [{cite}]
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
