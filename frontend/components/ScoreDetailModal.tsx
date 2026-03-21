'use client'

import { useEffect } from 'react'
import type { ScoreSection } from '@/components/ScoreDashboard'

interface Props {
  section: ScoreSection | null
  onClose: () => void
  technicalData: any
  onpageData: any
  semanticData: any
  uxData: any
}

function UrlList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <p className='mb-2 text-sm font-medium'>{title} ({items.length})</p>
      {items.length === 0 ? (
        <p className='text-xs text-muted'>None</p>
      ) : (
        <div className='max-h-36 space-y-1 overflow-auto rounded-lg border border-white/10 bg-black/25 p-2 text-xs'>
          {items.slice(0, 50).map((url) => (
            <p key={url} className='truncate text-muted'>
              {url}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

function IssueList({ title, items }: { title: string; items: Array<Record<string, any>> }) {
  return (
    <div>
      <p className='mb-2 text-sm font-medium'>{title} ({items.length})</p>
      {items.length === 0 ? (
        <p className='text-xs text-muted'>None</p>
      ) : (
        <div className='space-y-2'>
          {items.slice(0, 8).map((issue, idx) => (
            <div key={`${issue.description}-${idx}`} className='rounded-lg border border-white/10 bg-black/25 p-2 text-xs'>
              <p className='font-medium'>{issue.description}</p>
              <p className='text-muted'>Recommendation: {issue.recommendation}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ScoreDetailModal({ section, onClose, technicalData, onpageData, semanticData, uxData }: Props) {
  useEffect(() => {
    if (!section) return
    const onKey = (evt: KeyboardEvent) => {
      if (evt.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [section, onClose])

  if (!section) return null

  const renderSection = () => {
    if (section === 'technical') {
      const d = technicalData || {}
      return (
        <div className='space-y-4'>
          <div className='grid gap-2 text-sm md:grid-cols-2'>
            <p>Score: <span className='font-semibold text-accent'>{d.score ?? 0}</span></p>
            <p>Avg response: {d.page_speed?.avg_response_ms ?? 0} ms</p>
            <p>Robots.txt: {d.robots_txt?.found ? 'Found' : 'Not found'}</p>
            <p>Sitemap: {d.sitemap?.found ? 'Found' : 'Not found'}</p>
          </div>
          <UrlList title='Broken Links' items={d.broken_links || []} />
          <UrlList title='Insecure URLs (HTTP)' items={d.https_status?.insecure_urls || []} />
          <UrlList title='Slow URLs' items={d.page_speed?.slow_urls || []} />
          <IssueList title='Critical Issues' items={d.critical_issues || []} />
          <IssueList title='Warnings / Info Issues' items={d.issues || []} />
          <div>
            <p className='mb-2 text-sm font-medium'>Redirect Chains ({(d.redirect_chains || []).length})</p>
            <div className='max-h-40 space-y-2 overflow-auto'>
              {(d.redirect_chains || []).slice(0, 10).map((item: any) => (
                <div key={item.url} className='rounded-lg border border-white/10 bg-black/25 p-2 text-xs'>
                  <p className='font-medium'>{item.url}</p>
                  <p className='text-muted'>Hops: {item.hops}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )
    }

    if (section === 'onpage') {
      const d = onpageData || {}
      return (
        <div className='space-y-4'>
          <div className='grid gap-2 text-sm md:grid-cols-2'>
            <p>Score: <span className='font-semibold text-accent'>{d.score ?? 0}</span></p>
            <p>Keyword density: {d.avg_keyword_density ?? 0}%</p>
            <p>Missing image alts: {d.missing_alt_count ?? 0}</p>
            <p>Keyword stuffing flag: {d.keyword_stuffing_flag ? 'Yes' : 'No'}</p>
          </div>
          <UrlList title='Missing Title Pages' items={d.missing_title_urls || []} />
          <UrlList title='Missing Meta Description Pages' items={d.missing_meta_urls || []} />
          <UrlList title='Thin Content Pages' items={d.thin_content_pages || []} />
          <UrlList title='URL Readability Issues' items={d.url_readability_issues || []} />
          <IssueList title='H1 Issues' items={d.h1_issues || []} />
          <IssueList title='Internal Linking Issues' items={d.internal_linking_issues || []} />
          <div>
            <p className='mb-2 text-sm font-medium'>Top Keywords</p>
            <div className='flex flex-wrap gap-2'>
              {(d.top_keywords || []).slice(0, 20).map((k: any) => (
                <span key={k.keyword} className='rounded-md border border-white/15 px-2 py-1 text-xs'>
                  {k.keyword} ({k.count})
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className='mb-2 text-sm font-medium'>Per-Page Heading And Tag Review ({(d.page_tag_audit || []).length})</p>
            {(d.page_tag_audit || []).length === 0 ? (
              <p className='text-xs text-muted'>No per-page heading/tag details available.</p>
            ) : (
              <div className='max-h-[420px] space-y-2 overflow-auto pr-1'>
                {(d.page_tag_audit || []).map((page: any) => (
                  <details key={page.url} className='rounded-lg border border-white/10 bg-black/25 p-2'>
                    <summary className='cursor-pointer text-xs font-medium text-muted'>
                      {page.url}
                    </summary>
                    <div className='mt-2 space-y-2 text-xs'>
                      <div className='grid gap-2 md:grid-cols-3'>
                        <p>
                          Word count: <span className='text-accent'>{page.word_count || 0}</span>
                        </p>
                        <p>Missing title: {page.missing_title ? 'Yes' : 'No'}</p>
                        <p>Missing meta: {page.missing_meta ? 'Yes' : 'No'}</p>
                      </div>
                      <div>
                        <p className='mb-1 text-muted'>Title</p>
                        <p className='rounded border border-white/10 bg-black/20 p-2'>{page.title || '-'}</p>
                      </div>
                      <div>
                        <p className='mb-1 text-muted'>Meta Description</p>
                        <p className='rounded border border-white/10 bg-black/20 p-2'>{page.meta_description || '-'}</p>
                      </div>
                      <UrlList title='H1 Tags' items={page.h1 || []} />
                      <UrlList title='H2 Tags' items={page.h2 || []} />
                      <UrlList title='H3 Tags' items={page.h3 || []} />
                      <UrlList title='H4-H6 Tags' items={page.h4_h6 || []} />
                    </div>
                  </details>
                ))}
              </div>
            )}
          </div>
        </div>
      )
    }

    if (section === 'semantic') {
      const d = semanticData || {}
      return (
        <div className='space-y-4'>
          <div className='grid gap-2 text-sm md:grid-cols-2'>
            <p>Score: <span className='font-semibold text-accent'>{d.score ?? 0}</span></p>
            <p>Topical authority: {d.topical_authority_score ?? 0}</p>
            <p>Topic clusters: {(d.topic_clusters || []).length}</p>
            <p>No schema pages: {(d.no_schema_pages || []).length}</p>
          </div>
          <UrlList title='No Schema Pages' items={d.no_schema_pages || []} />
          <div>
            <p className='mb-2 text-sm font-medium'>Content Gaps ({(d.content_gaps || []).length})</p>
            <div className='max-h-36 space-y-1 overflow-auto rounded-lg border border-white/10 bg-black/25 p-2 text-xs'>
              {(d.content_gaps || []).slice(0, 40).map((gap: string) => (
                <p key={gap} className='text-muted'>{gap}</p>
              ))}
            </div>
          </div>
          <div>
            <p className='mb-2 text-sm font-medium'>Top Entities</p>
            <div className='flex flex-wrap gap-2'>
              {(d.top_entities || []).slice(0, 30).map((entity: string) => (
                <span key={entity} className='rounded-md border border-indigo/40 bg-indigo/10 px-2 py-1 text-xs'>
                  {entity}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className='mb-2 text-sm font-medium'>LSI Keywords</p>
            <div className='flex flex-wrap gap-2'>
              {(d.lsi_keywords || []).slice(0, 20).map((kw: string) => (
                <span key={kw} className='rounded-md border border-white/15 px-2 py-1 text-xs'>{kw}</span>
              ))}
            </div>
          </div>
        </div>
      )
    }

    const d = uxData || {}
    return (
      <div className='space-y-4'>
        <div className='grid gap-2 text-sm md:grid-cols-2'>
          <p>Score: <span className='font-semibold text-accent'>{d.score ?? 0}</span></p>
          <p>Readability: {d.avg_readability ?? 0}</p>
          <p>FK grade: {d.fk_grade ?? 0}</p>
          <p>Pages with CTA: {d.pages_with_cta ?? 0}%</p>
          <p>Navigation score: {d.navigation_score ?? 0}</p>
          <p>Structure score: {d.content_structure_score ?? 0}</p>
        </div>
        <UrlList title='Low Readability Pages' items={d.low_readability_pages || []} />
        <UrlList title='Pages Without CTA' items={d.no_cta_pages || []} />
        <UrlList title='Pages Without Navigation' items={d.no_navigation_pages || []} />
        <UrlList title='Weak Content Structure Pages' items={d.weak_structure_pages || []} />
      </div>
    )
  }

  const title =
    section === 'technical'
      ? 'Technical SEO Details'
      : section === 'onpage'
        ? 'On-Page SEO Details'
        : section === 'semantic'
          ? 'Semantic SEO Details'
          : 'UX Signal Details'

  return (
    <div className='fixed inset-0 z-40 flex items-center justify-center bg-black/70 p-4' onClick={onClose}>
      <div className='panel max-h-[85vh] w-full max-w-4xl overflow-hidden' onClick={(e) => e.stopPropagation()}>
        <div className='flex items-center justify-between border-b border-white/10 px-4 py-3'>
          <h3 className='text-lg font-semibold'>{title}</h3>
          <button onClick={onClose} className='rounded-md border border-white/15 px-2 py-1 text-xs hover:border-accent'>
            Close
          </button>
        </div>
        <div className='max-h-[calc(85vh-64px)] overflow-auto p-4'>{renderSection()}</div>
      </div>
    </div>
  )
}
