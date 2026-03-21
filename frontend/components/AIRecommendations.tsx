'use client'

import ReactMarkdown from 'react-markdown'
import { useMemo, useState } from 'react'

interface Props {
  content: string
  statusLabel?: string
  statusTone?: 'ok' | 'info' | 'warn'
}

export default function AIRecommendations({ content, statusLabel = 'Waiting', statusTone = 'info' }: Props) {
  const [question, setQuestion] = useState('')

  const sections = useMemo(() => {
    return content
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
      .slice(0, 6)
  }, [content])

  return (
    <div className='panel h-full p-4'>
      <div className='mb-3 flex items-center justify-between gap-2'>
        <h3 className='text-lg font-semibold'>AI Recommendations</h3>
        <span
          className={`rounded-full border px-2 py-1 text-[11px] ${
            statusTone === 'ok'
              ? 'border-green-400/50 bg-green-500/10 text-green-300'
              : statusTone === 'warn'
                ? 'border-amber-400/50 bg-amber-500/10 text-amber-300'
                : 'border-indigo/60 bg-indigo/20 text-indigo-200'
          }`}
        >
          {statusLabel}
        </span>
      </div>
      <div className='max-h-[480px] overflow-auto rounded-lg bg-black/35 p-3 text-sm'>
        {content ? <ReactMarkdown>{content}</ReactMarkdown> : <p className='text-muted'>Streaming insights...</p>}
      </div>

      <div className='mt-4 space-y-2'>
        {sections.map((s, idx) => (
          <button
            key={idx}
            onClick={() => navigator.clipboard.writeText(s)}
            className='w-full rounded-md border border-white/15 px-3 py-2 text-left text-xs text-muted transition hover:border-accent'
          >
            Copy insight #{idx + 1}
          </button>
        ))}
      </div>

      <div className='mt-4'>
        <label className='mb-1 block text-xs text-muted'>Ask Follow-up (local draft)</label>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder='Ask for deeper recommendations...'
          className='w-full rounded-lg border border-white/15 bg-black/30 px-3 py-2 text-sm outline-none focus:border-accent'
        />
      </div>
    </div>
  )
}
