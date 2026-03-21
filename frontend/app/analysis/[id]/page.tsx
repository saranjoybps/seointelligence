'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import AIRecommendations from '@/components/AIRecommendations'
import ActionPlan from '@/components/ActionPlan'
import CrawlProgress from '@/components/CrawlProgress'
import ExportReport from '@/components/ExportReport'
import OnPageSEO from '@/components/OnPageSEO'
import ScoreDashboard from '@/components/ScoreDashboard'
import SemanticSEO from '@/components/SemanticSEO'
import TechnicalSEO from '@/components/TechnicalSEO'
import URLInput from '@/components/URLInput'
import UXSignals from '@/components/UXSignals'
import { getAnalysis, healthCheck, streamAnalysis } from '@/lib/api'
import { AnalysisPayload, StreamEvent } from '@/lib/types'

export default function AnalysisPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const search = useSearchParams()
  const urlFromQuery = search.get('url') || ''

  const [targetUrl, setTargetUrl] = useState(urlFromQuery)
  const [loading, setLoading] = useState(false)
  const [phase, setPhase] = useState('init')
  const [progress, setProgress] = useState(0)
  const [logs, setLogs] = useState<string[]>([])
  const [aiContent, setAiContent] = useState('')
  const [analysis, setAnalysis] = useState<AnalysisPayload | null>(null)
  const [technicalData, setTechnicalData] = useState<any>(null)
  const [onpageData, setOnpageData] = useState<any>(null)
  const [semanticData, setSemanticData] = useState<any>(null)
  const [uxData, setUxData] = useState<any>(null)
  const [actionPlan, setActionPlan] = useState<Array<Record<string, any>>>([])
  const [scores, setScores] = useState({ technical: 0, onpage: 0, semantic: 0, ux: 0 })
  const [aiStatusLabel, setAiStatusLabel] = useState('Waiting')
  const [aiStatusTone, setAiStatusTone] = useState<'ok' | 'info' | 'warn'>('info')
  const [toasts, setToasts] = useState<Array<{ id: string; text: string; tone: 'ok' | 'info' | 'warn' }>>([])
  const streamStartedFor = useRef<string | null>(null)
  const sawCompleteRef = useRef(false)

  const addLog = (line: string) => setLogs((prev) => [...prev, `${new Date().toLocaleTimeString()}  ${line}`])
  const pushToast = (text: string, tone: 'ok' | 'info' | 'warn' = 'info') => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
    setToasts((prev) => [...prev, { id, text, tone }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 3200)
  }

  useEffect(() => {
    if (params.id !== 'new') {
      if (loading && !analysis) return
      if (analysis?.analysis_id === params.id) return
      setLoading(true)
      getAnalysis(params.id)
        .then((res) => {
          setAnalysis(res)
          setTargetUrl(res.url)
          setAiContent(res.ai_analysis || '')
          setActionPlan(res.action_plan || [])
          setTechnicalData(res.technical || null)
          setOnpageData(res.onpage || null)
          setSemanticData(res.semantic || null)
          setUxData(res.ux || null)
          setScores({
            technical: res.technical?.score || 0,
            onpage: res.onpage?.score || 0,
            semantic: res.semantic?.score || 0,
            ux: res.ux?.score || 0
          })
          setPhase('complete')
          setProgress(100)
        })
        .catch((err) => addLog(`Failed to load analysis: ${err.message}`))
        .finally(() => setLoading(false))
      return
    }

    if (!urlFromQuery) return
    const streamKey = `${params.id}:${urlFromQuery}`
    if (streamStartedFor.current === streamKey) return
    streamStartedFor.current = streamKey

    setLoading(true)
    setTargetUrl(urlFromQuery)
    setAiContent('')
    setAnalysis(null)
    setTechnicalData(null)
    setOnpageData(null)
    setSemanticData(null)
    setUxData(null)
    setActionPlan([])
    setScores({ technical: 0, onpage: 0, semantic: 0, ux: 0 })
    setPhase('init')
    setProgress(1)
    setLogs([])
    setAiStatusLabel('Checking AI connection...')
    setAiStatusTone('info')
    sawCompleteRef.current = false

    healthCheck()
      .then((res) => {
        if (res?.ollama?.ok) {
          setAiStatusLabel('AI connected')
          setAiStatusTone('ok')
          pushToast('AI Connected', 'ok')
        } else {
          setAiStatusLabel('AI unavailable')
          setAiStatusTone('warn')
          pushToast('AI unavailable. Running analysis without insights.', 'warn')
        }
      })
      .catch(() => {
        setAiStatusLabel('AI health check failed')
        setAiStatusTone('warn')
        pushToast('AI health check failed', 'warn')
      })

    streamAnalysis({ url: urlFromQuery, max_pages: 50, include_subdomains: false }, (evt: StreamEvent) => {
      if (evt.phase) setPhase(evt.phase)
      if (typeof evt.progress === 'number') setProgress(evt.progress)
      if (evt.message) addLog(evt.message)

      if (evt.phase === 'ai') {
        setAiStatusLabel('Streaming...')
        setAiStatusTone('info')
        pushToast('AI streaming started', 'info')
        if (evt.data) {
          console.log('[AI Input Payload -> Ollama]', evt.data)
        }
      }

      if (evt.phase === 'technical' && evt.data) {
        setTechnicalData(evt.data)
        setScores((s) => ({ ...s, technical: evt.data.score || 0 }))
      }
      if (evt.phase === 'onpage' && evt.data) {
        setOnpageData(evt.data)
        setScores((s) => ({ ...s, onpage: evt.data.score || 0 }))
      }
      if (evt.phase === 'semantic' && evt.data) {
        setSemanticData(evt.data)
        setScores((s) => ({ ...s, semantic: evt.data.score || 0 }))
      }
      if (evt.phase === 'ux' && evt.data) {
        setUxData(evt.data)
        setScores((s) => ({ ...s, ux: evt.data.score || 0 }))
      }
      if (evt.phase === 'ai_stream' && evt.chunk) {
        console.log('[AI Stream Chunk]', {
          section: evt.data?.section || 'unknown',
          fallback: !!evt.data?.fallback,
          chunkChars: evt.chunk.length
        })
        if (evt.chunk.includes('[AI stream unavailable:')) {
          setAiStatusLabel('No tokens from stream')
          setAiStatusTone('warn')
          pushToast('AI stream returned no tokens; trying fallback.', 'warn')
        } else {
          setAiStatusLabel('Receiving insights')
          setAiStatusTone('ok')
        }
        setAiContent((prev) => prev + evt.chunk)
      }
      if (evt.phase === 'warning' && evt.message) {
        console.warn('[AI Warning Event]', { section: evt.data?.section || 'unknown', message: evt.message, data: evt.data })
        setAiStatusLabel('AI warning')
        setAiStatusTone('warn')
        pushToast(evt.message, 'warn')
      }
      if (evt.phase === 'core_complete' && evt.data) {
        setAnalysis(evt.data)
        setActionPlan(evt.data.action_plan || evt.action_plan || [])
        setTechnicalData(evt.data.technical || null)
        setOnpageData(evt.data.onpage || null)
        setSemanticData(evt.data.semantic || null)
        setUxData(evt.data.ux || null)
        setScores({
          technical: evt.data.technical?.score || 0,
          onpage: evt.data.onpage?.score || 0,
          semantic: evt.data.semantic?.score || 0,
          ux: evt.data.ux?.score || 0
        })
        setLoading(false)
        addLog('Core analysis ready. AI recommendations will continue separately.')
        pushToast('Core insights ready', 'ok')
      }
      if (evt.phase === 'complete') {
        sawCompleteRef.current = true
        if (evt.data) {
          setAnalysis(evt.data)
          setAiContent(evt.data.ai_analysis || '')
          setActionPlan(evt.data.action_plan || evt.action_plan || [])
          setTechnicalData(evt.data.technical || null)
          setOnpageData(evt.data.onpage || null)
          setSemanticData(evt.data.semantic || null)
          setUxData(evt.data.ux || null)
          setScores({
            technical: evt.data.technical?.score || 0,
            onpage: evt.data.onpage?.score || 0,
            semantic: evt.data.semantic?.score || 0,
            ux: evt.data.ux?.score || 0
          })

          try {
            const raw = localStorage.getItem('seo_recent')
            const parsed = raw ? JSON.parse(raw) : []
            const item = {
              id: evt.data.analysis_id,
              url: evt.data.url,
              createdAt: evt.data.created_at
            }
            const next = [item, ...parsed.filter((x: any) => x.id !== item.id)].slice(0, 10)
            localStorage.setItem('seo_recent', JSON.stringify(next))
          } catch {
            // noop
          }
        }
        const finalText = evt.data?.ai_analysis || aiContent
        if (!finalText || !finalText.trim()) {
          setAiStatusLabel('No insights returned')
          setAiStatusTone('warn')
          pushToast('No AI insights returned for this run.', 'warn')
        } else {
          setAiStatusLabel('Insights ready')
          setAiStatusTone('ok')
          pushToast('AI insights ready', 'ok')
        }
        setLoading(false)
        if (params.id === 'new' && evt.data?.analysis_id) {
          router.replace(`/analysis/${evt.data.analysis_id}`)
        }
      }
      if (evt.phase === 'error') {
        console.error('[AI Error Event]', evt)
        setLoading(false)
        setAiStatusLabel('AI/error')
        setAiStatusTone('warn')
        pushToast('Analysis failed. Check backend logs.', 'warn')
        streamStartedFor.current = null
      }
    })
      .then(() => {
        if (!sawCompleteRef.current) {
          addLog('Stream ended before completion.')
          setLoading(false)
          setAiStatusLabel('Stream ended early')
          setAiStatusTone('warn')
          pushToast('Stream ended before completion. Partial results may be shown.', 'warn')
          streamStartedFor.current = null
        }
      })
      .catch((err) => {
        addLog(`Stream error: ${err.message}`)
        setLoading(false)
        setAiStatusLabel('Stream failed')
        setAiStatusTone('warn')
        pushToast('Stream failed. Please retry.', 'warn')
        streamStartedFor.current = null
      })
  }, [analysis?.analysis_id, params.id, router, urlFromQuery])

  const overall = useMemo(() => {
    return Math.round(scores.technical * 0.35 + scores.onpage * 0.3 + scores.semantic * 0.2 + scores.ux * 0.15)
  }, [scores])

  const startNew = (url: string) => {
    router.push(`/analysis/new?url=${encodeURIComponent(url)}`)
  }

  return (
    <main className='min-h-screen px-4 py-5 md:px-8'>
      <div className='mx-auto max-w-[1500px] space-y-4'>
        <header className='panel flex flex-col gap-2 p-4 md:flex-row md:items-center md:justify-between'>
          <div>
            <p className='text-xs uppercase tracking-wide text-muted'>Live Analysis</p>
            <h1 className='text-xl font-semibold md:text-2xl'>{targetUrl || 'SEO Intelligence Dashboard'}</h1>
          </div>
          <div className='rounded-lg border border-accent/50 bg-accent/10 px-3 py-2 text-sm'>Overall Score: {overall}/100</div>
        </header>

        <URLInput initialValue={targetUrl} onSubmit={startNew} loading={loading} />

        <div className='grid gap-4 lg:grid-cols-[280px_1fr_360px]'>
          <div className='space-y-4'>
            <CrawlProgress
              phase={phase}
              progress={progress}
              logs={logs}
              pagesDiscovered={technicalData?.sitemap?.crawled_urls || 0}
            />
            {analysis && <ExportReport analysis={analysis} />}
          </div>

          <div className='space-y-4'>
            <ScoreDashboard technical={scores.technical} onpage={scores.onpage} semantic={scores.semantic} ux={scores.ux} />
            <TechnicalSEO data={technicalData} />
            <OnPageSEO data={onpageData} />
            <SemanticSEO data={semanticData} />
            <UXSignals data={uxData} />
            <ActionPlan items={actionPlan} analysisId={analysis?.analysis_id || params.id} />
          </div>

          <div>
            <AIRecommendations content={aiContent} statusLabel={aiStatusLabel} statusTone={aiStatusTone} />
          </div>
        </div>
      </div>
      <div className='fixed right-4 top-4 z-50 flex w-[300px] flex-col gap-2'>
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`rounded-lg border px-3 py-2 text-sm shadow-lg backdrop-blur ${
              toast.tone === 'ok'
                ? 'border-green-400/40 bg-green-500/15 text-green-100'
                : toast.tone === 'warn'
                  ? 'border-amber-400/40 bg-amber-500/15 text-amber-100'
                  : 'border-indigo/50 bg-indigo/20 text-indigo-100'
            }`}
          >
            {toast.text}
          </div>
        ))}
      </div>
    </main>
  )
}
