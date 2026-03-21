interface Props {
  data: any
  onOpenDetails?: () => void
}

export default function SemanticSEO({ data, onOpenDetails }: Props) {
  if (!data) {
    return (
      <div className='panel p-4'>
        <div className='mb-2 flex items-center justify-between'>
          <h3 className='text-lg font-semibold'>Semantic SEO</h3>
          {onOpenDetails && (
            <button
              onClick={onOpenDetails}
              className='rounded-md border border-accent/60 bg-accent/10 px-3 py-1 text-xs font-medium text-accent transition hover:border-accent hover:bg-accent/20 hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent/40'
              title='View more Semantic SEO details'
              aria-label='View more Semantic SEO details'
            >
              View More
            </button>
          )}
        </div>
        <p className='text-sm text-muted'>Semantic analysis pending...</p>
      </div>
    )
  }

  return (
    <div className='panel p-4'>
      <div className='mb-3 flex items-center justify-between'>
        <h3 className='text-lg font-semibold'>Semantic SEO</h3>
        {onOpenDetails && (
          <button
            onClick={onOpenDetails}
            className='rounded-md border border-accent/60 bg-accent/10 px-3 py-1 text-xs font-medium text-accent transition hover:border-accent hover:bg-accent/20 hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent/40'
            title='View more Semantic SEO details'
            aria-label='View more Semantic SEO details'
          >
            View More
          </button>
        )}
      </div>
      <div className='grid gap-2 text-sm md:grid-cols-2'>
        <p>Score: <span className='font-semibold text-accent'>{data.score}</span></p>
        <p>Topical authority: {data.topical_authority_score}</p>
        <p>Topic clusters: {data.topic_clusters?.length || 0}</p>
        <p>No schema pages: {data.no_schema_pages?.length || 0}</p>
      </div>
      <div className='mt-3'>
        <p className='mb-2 text-sm font-medium'>Entities</p>
        <div className='flex flex-wrap gap-2'>
          {(data.top_entities || []).slice(0, 12).map((entity: string) => (
            <span key={entity} className='rounded-md border border-indigo/40 bg-indigo/10 px-2 py-1 text-xs'>
              {entity}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
