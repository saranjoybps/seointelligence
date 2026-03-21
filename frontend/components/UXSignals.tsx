interface Props {
  data: any
}

export default function UXSignals({ data }: Props) {
  if (!data) return <div className='panel p-4 text-sm text-muted'>UX analysis pending...</div>
  return (
    <div className='panel p-4'>
      <h3 className='mb-3 text-lg font-semibold'>UX Signals</h3>
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
