interface Props {
  data: any
}

export default function TechnicalSEO({ data }: Props) {
  if (!data) return <div className='panel p-4 text-sm text-muted'>Technical analysis pending...</div>
  return (
    <div className='panel p-4'>
      <h3 className='mb-3 text-lg font-semibold'>Technical SEO</h3>
      <div className='grid gap-2 text-sm md:grid-cols-2'>
        <p>Score: <span className='font-semibold text-accent'>{data.score}</span></p>
        <p>Broken links: {data.broken_links?.length || 0}</p>
        <p>Insecure pages: {data.https_status?.insecure_pages || 0}</p>
        <p>Redirect chains: {data.redirect_chains?.length || 0}</p>
        <p>Robots found: {data.robots_txt?.found ? 'Yes' : 'No'}</p>
        <p>Sitemap found: {data.sitemap?.found ? 'Yes' : 'No'}</p>
      </div>
      <div className='mt-3 space-y-2'>
        {(data.critical_issues || []).slice(0, 4).map((issue: any, idx: number) => (
          <div key={idx} className='rounded-lg border border-red-400/40 bg-red-500/10 p-2 text-sm'>
            <p className='font-medium'>{issue.description}</p>
            <p className='text-xs text-muted'>{issue.recommendation}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
