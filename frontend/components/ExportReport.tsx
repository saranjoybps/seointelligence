'use client'

interface Props {
  analysis: any
}

export default function ExportReport({ analysis }: Props) {
  const exportJson = () => {
    const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `seo-analysis-${analysis.analysis_id || 'report'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportHtml = () => {
    const html = `<!doctype html><html><head><meta charset="utf-8"/><title>SEO Report</title></head><body><pre>${JSON.stringify(
      analysis,
      null,
      2
    )}</pre></body></html>`
    const blob = new Blob([html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `seo-analysis-${analysis.analysis_id || 'report'}.html`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className='panel flex flex-wrap gap-2 p-4'>
      <button onClick={exportJson} className='rounded-md border border-white/15 px-3 py-2 text-sm hover:border-accent'>
        Export JSON
      </button>
      <button onClick={exportHtml} className='rounded-md border border-white/15 px-3 py-2 text-sm hover:border-accent'>
        Export HTML
      </button>
      <button onClick={() => window.print()} className='rounded-md border border-white/15 px-3 py-2 text-sm hover:border-accent'>
        Export PDF
      </button>
    </div>
  )
}
