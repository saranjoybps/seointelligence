'use client'

import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import URLInput from '@/components/URLInput'

interface RecentItem {
  id: string
  url: string
  createdAt: string
}

export default function HomePage() {
  const router = useRouter()
  const [recent, setRecent] = useState<RecentItem[]>([])

  useEffect(() => {
    try {
      const saved = localStorage.getItem('seo_recent')
      if (saved) setRecent(JSON.parse(saved))
    } catch {
      setRecent([])
    }
  }, [])

  const onSubmit = (url: string) => {
    router.push(`/analysis/new?url=${encodeURIComponent(url)}`)
  }

  return (
    <main className='grid-bg min-h-screen px-4 py-10 md:px-10'>
      <div className='mx-auto max-w-6xl'>
        <div className='mb-10 text-center'>
          <p className='mb-3 inline-block rounded-full border border-accent/40 bg-accent/10 px-3 py-1 text-xs font-medium text-accent'>
            AI-Powered SEO Intelligence
          </p>
          <h1 className='mb-4 text-3xl font-bold md:text-6xl' style={{ fontFamily: 'var(--font-syne)' }}>
            Full-Stack Digital Marketing Analysis Platform
          </h1>
          <p className='mx-auto max-w-3xl text-muted'>
            Crawl websites, score technical and on-page SEO, discover semantic content gaps, and stream AI recommendations in real time.
          </p>
        </div>

        <URLInput onSubmit={onSubmit} />

        <section className='mt-10 grid gap-4 md:grid-cols-4'>
          {[
            ['Technical SEO', 'HTTPS, speed, canonicals, redirects'],
            ['On-Page SEO', 'Titles, metadata, links, content depth'],
            ['Semantic SEO', 'Entities, topic clusters, content gaps'],
            ['AI Engine', 'Ollama-powered recommendations and plan']
          ].map(([title, body]) => (
            <article key={title} className='panel p-4'>
              <h2 className='mb-2 text-lg font-semibold'>{title}</h2>
              <p className='text-sm text-muted'>{body}</p>
            </article>
          ))}
        </section>

        <section className='mt-10'>
          <h3 className='mb-3 text-lg font-semibold'>Recent Analyses</h3>
          <div className='panel overflow-hidden'>
            {recent.length === 0 ? (
              <p className='p-4 text-sm text-muted'>No recent analyses yet.</p>
            ) : (
              recent.slice(0, 8).map((item) => (
                <button
                  key={item.id}
                  onClick={() => router.push(`/analysis/${item.id}`)}
                  className='flex w-full items-center justify-between border-b border-white/10 px-4 py-3 text-left transition hover:bg-white/5'
                >
                  <span className='truncate pr-4'>{item.url}</span>
                  <span className='text-xs text-muted'>{new Date(item.createdAt).toLocaleString()}</span>
                </button>
              ))
            )}
          </div>
        </section>
      </div>
    </main>
  )
}
