interface Props {
  data: any
}

export default function OnPageSEO({ data }: Props) {
  if (!data) return <div className='panel p-4 text-sm text-muted'>On-page analysis pending...</div>

  return (
    <div className='panel p-4'>
      <h3 className='mb-3 text-lg font-semibold'>On-Page SEO</h3>
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
