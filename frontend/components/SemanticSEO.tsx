interface Props {
  data: any
}

export default function SemanticSEO({ data }: Props) {
  if (!data) return <div className='panel p-4 text-sm text-muted'>Semantic analysis pending...</div>

  return (
    <div className='panel p-4'>
      <h3 className='mb-3 text-lg font-semibold'>Semantic SEO</h3>
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
