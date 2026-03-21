'use client'

interface Props {
  phase: string
  progress: number
  logs: string[]
  pagesDiscovered?: number
}

const PHASES = ['crawling', 'technical', 'onpage', 'semantic', 'ux', 'ai', 'complete']

export default function CrawlProgress({ phase, progress, logs, pagesDiscovered = 0 }: Props) {
  return (
    <div className='panel p-4'>
      <h3 className='mb-3 text-sm font-semibold uppercase tracking-wide text-muted'>Analysis Progress</h3>
      <div className='mb-4 h-3 overflow-hidden rounded-full bg-black/40'>
        <div className='h-full bg-gradient-to-r from-indigo to-accent transition-all duration-500' style={{ width: `${progress}%` }} />
      </div>
      <div className='mb-3 text-xs text-muted'>Pages discovered: {pagesDiscovered}</div>
      <div className='mb-4 flex flex-wrap gap-2'>
        {PHASES.map((p) => (
          <span
            key={p}
            className={`rounded-md border px-2 py-1 text-xs ${phase === p ? 'border-accent bg-accent/10 text-accent' : 'border-white/10 text-muted'}`}
          >
            {p}
          </span>
        ))}
      </div>
      <div className='max-h-36 space-y-1 overflow-auto rounded-lg bg-black/30 p-2 text-xs text-muted'>
        {logs.length === 0 ? <p>Awaiting updates...</p> : logs.slice(-12).map((line, idx) => <p key={idx}>- {line}</p>)}
      </div>
    </div>
  )
}
