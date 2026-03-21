interface Props {
  data: any
  onOpenDetails?: () => void
}

export default function OnPageSEO({ data, onOpenDetails }: Props) {
  if (!data) {
    return (
      <div className='panel p-4'>
        <div className='mb-2 flex items-center justify-between'>
          <h3 className='text-lg font-semibold'>On-Page SEO</h3>
          {onOpenDetails && (
            <button
              onClick={onOpenDetails}
              className='rounded-md border border-accent/60 bg-accent/10 px-3 py-1 text-xs font-medium text-accent transition hover:border-accent hover:bg-accent/20 hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent/40'
              title='View more On-Page SEO details'
              aria-label='View more On-Page SEO details'
            >
              View More
            </button>
          )}
        </div>
        <p className='text-sm text-muted'>On-page analysis pending...</p>
      </div>
    )
  }

  return (
    <div className='panel p-4'>
      <div className='mb-3 flex items-center justify-between'>
        <h3 className='text-lg font-semibold'>On-Page SEO</h3>
        {onOpenDetails && (
          <button
            onClick={onOpenDetails}
            className='rounded-md border border-accent/60 bg-accent/10 px-3 py-1 text-xs font-medium text-accent transition hover:border-accent hover:bg-accent/20 hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent/40'
            title='View more On-Page SEO details'
            aria-label='View more On-Page SEO details'
          >
            View More
          </button>
        )}
      </div>
      <div className='grid gap-2 text-sm md:grid-cols-2'>
        <p>Score: <span className='font-semibold text-accent'>{data.score}</span></p>
        <p>Missing titles: {data.missing_titles}</p>
        <p>Missing meta descriptions: {data.missing_metas}</p>
        <p>Thin content pages: {data.thin_content_pages?.length || 0}</p>
        <p>Missing image alts: {data.missing_alt_count}</p>
        <p>Avg keyword density: {data.avg_keyword_density}%</p>
      </div>
      <div className='mt-3'>
        <p className='mb-2 text-sm font-medium'>Top Keywords</p>
        <div className='flex flex-wrap gap-2'>
          {(data.top_keywords || []).slice(0, 8).map((k: any) => (
            <span key={k.keyword} className='rounded-md border border-white/15 px-2 py-1 text-xs'>
              {k.keyword} ({k.count})
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
