'use client'

import { FormEvent, useEffect, useState } from 'react'

const EXAMPLES = ['https://example.com', 'https://stripe.com', 'https://hubspot.com', 'https://www.shopify.com']

interface Props {
  initialValue?: string
  onSubmit: (url: string) => void
  loading?: boolean
}

export default function URLInput({ initialValue = '', onSubmit, loading = false }: Props) {
  const [url, setUrl] = useState(initialValue)
  const [exampleIndex, setExampleIndex] = useState(0)

  useEffect(() => {
    const id = setInterval(() => {
      setExampleIndex((prev) => (prev + 1) % EXAMPLES.length)
    }, 1800)
    return () => clearInterval(id)
  }, [])

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!url.trim()) return
    onSubmit(url.trim())
  }

  return (
    <form onSubmit={submit} className='panel mx-auto w-full max-w-3xl p-4 md:p-6'>
      <label className='mb-3 block text-sm text-muted'>Website URL</label>
      <div className='flex flex-col gap-3 md:flex-row'>
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder={EXAMPLES[exampleIndex]}
          className='w-full rounded-xl border border-white/15 bg-black/30 px-4 py-3 text-base outline-none transition focus:border-accent'
        />
        <button
          disabled={loading}
          className='rounded-xl bg-accent px-6 py-3 font-semibold text-black transition hover:shadow-glow disabled:cursor-not-allowed disabled:opacity-50'
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
    </form>
  )
}
