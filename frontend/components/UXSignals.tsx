interface Props {
  data: any
  onOpenDetails?: () => void
}

export default function UXSignals({ data, onOpenDetails }: Props) {
  if (!data) {
    return (
      <div className='panel p-4'>
        <div className='mb-2 flex items-center justify-between'>
          <h3 className='text-lg font-semibold'>UX Signals</h3>
          {onOpenDetails && (
            <button
              onClick={onOpenDetails}
              className='rounded-md border border-accent/60 bg-accent/10 px-3 py-1 text-xs font-medium text-accent transition hover:border-accent hover:bg-accent/20 hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent/40'
              title='View more UX Signal details'
              aria-label='View more UX Signal details'
            >
              View More
            </button>
          )}
        </div>
        <p className='text-sm text-muted'>UX analysis pending...</p>
      </div>
    )
  }
  return (
    <div className='panel p-4'>
      <div className='mb-3 flex items-center justify-between'>
        <h3 className='text-lg font-semibold'>UX Signals</h3>
        {onOpenDetails && (
          <button
            onClick={onOpenDetails}
            className='rounded-md border border-accent/60 bg-accent/10 px-3 py-1 text-xs font-medium text-accent transition hover:border-accent hover:bg-accent/20 hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent/40'
            title='View more UX Signal details'
            aria-label='View more UX Signal details'
          >
            View More
          </button>
        )}
      </div>
      <div className='grid gap-2 text-sm md:grid-cols-2'>
        <p>Score: <span className='font-semibold text-accent'>{data.score}</span></p>
        <p>Readability: {data.avg_readability}</p>
        <p>FK grade: {data.fk_grade}</p>
        <p>Pages with CTA: {data.pages_with_cta}%</p>
        <p>Navigation score: {data.navigation_score}</p>
        <p>Structure score: {data.content_structure_score}</p>
      </div>
    </div>
  )
}
