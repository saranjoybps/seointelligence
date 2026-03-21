import { AnalysisPayload, StreamEvent } from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export async function streamAnalysis(
  body: { url: string; max_pages?: number; include_subdomains?: boolean },
  onEvent: (event: StreamEvent) => void
) {
  const response = await fetch(`${API_BASE}/api/analyze/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })

  if (!response.ok || !response.body) {
    let details = ''
    try {
      details = await response.text()
    } catch {
      details = ''
    }
    throw new Error(`Stream request failed: ${response.status} ${response.statusText}${details ? ` | ${details.slice(0, 280)}` : ''}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      if (buffer.trim()) {
        const line = buffer
          .split('\n')
          .find((part) => part.startsWith('data:'))
          ?.replace(/^data:\s*/, '')
        if (line) {
          try {
            onEvent(JSON.parse(line))
          } catch {
            // ignore trailing malformed payload
          }
        }
      }
      break
    }
    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() || ''

    for (const evt of events) {
      const line = evt
        .split('\n')
        .find((part) => part.startsWith('data:'))
        ?.replace(/^data:\s*/, '')
      if (!line) continue
      try {
        onEvent(JSON.parse(line))
      } catch {
        continue
      }
    }
  }
}

export async function getAnalysis(id: string): Promise<AnalysisPayload> {
  const response = await fetch(`${API_BASE}/api/analysis/${id}`, { cache: 'no-store' })
  if (!response.ok) {
    throw new Error('Could not load analysis')
  }
  return response.json()
}

export async function healthCheck() {
  const response = await fetch(`${API_BASE}/api/health`, { cache: 'no-store' })
  return response.json()
}
