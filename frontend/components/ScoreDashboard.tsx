'use client'

interface Props {
  technical: number
  onpage: number
  semantic: number
  ux: number
}

function gaugeColor(score: number) {
  if (score < 50) return '#ef4444'
  if (score < 75) return '#eab308'
  return '#00ff88'
}

function Ring({ label, score }: { label: string; score: number }) {
  const radius = 42
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  return (
    <div className='panel flex flex-col items-center p-4'>
      <svg width='110' height='110' className='-rotate-90'>
        <circle cx='55' cy='55' r={radius} stroke='rgba(255,255,255,0.1)' strokeWidth='10' fill='none' />
        <circle
          cx='55'
          cy='55'
          r={radius}
          stroke={gaugeColor(score)}
          strokeWidth='10'
          fill='none'
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap='round'
        />
      </svg>
      <p className='-mt-16 mb-12 text-2xl font-bold' style={{ fontFamily: 'var(--font-mono)' }}>
        {score}
      </p>
      <p className='text-xs uppercase tracking-wide text-muted'>{label}</p>
    </div>
  )
}

export default function ScoreDashboard({ technical, onpage, semantic, ux }: Props) {
  const overall = Math.round(technical * 0.35 + onpage * 0.3 + semantic * 0.2 + ux * 0.15)
  return (
    <section>
      <div className='mb-2 flex items-center justify-between'>
        <h2 className='text-xl font-semibold'>Score Dashboard</h2>
        <div className='rounded-lg border border-accent/50 bg-accent/10 px-3 py-1 text-sm text-accent'>Overall {overall}/100</div>
      </div>
      <div className='grid gap-3 sm:grid-cols-2 lg:grid-cols-4'>
        <Ring label='Technical' score={technical} />
        <Ring label='On-Page' score={onpage} />
        <Ring label='Semantic' score={semantic} />
        <Ring label='UX Signals' score={ux} />
      </div>
    </section>
  )
}
