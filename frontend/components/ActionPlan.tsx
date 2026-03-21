'use client'

import { useMemo, useState } from 'react'

interface Props {
  items: Array<Record<string, any>>
  analysisId?: string
}

const PRIORITY_WEIGHT: Record<string, number> = { high: 0, medium: 1, low: 2 }

export default function ActionPlan({ items, analysisId = 'default' }: Props) {
  const [sortBy, setSortBy] = useState<'priority' | 'impact' | 'effort'>('priority')
  const [completed, setCompleted] = useState<Record<string, boolean>>(() => {
    if (typeof window === 'undefined') return {}
    const raw = localStorage.getItem(`seo_plan_done_${analysisId}`)
    return raw ? JSON.parse(raw) : {}
  })

  const sorted = useMemo(() => {
    const list = [...items]
    if (sortBy === 'priority') {
      list.sort((a, b) => (PRIORITY_WEIGHT[a.priority] ?? 3) - (PRIORITY_WEIGHT[b.priority] ?? 3))
    }
    if (sortBy === 'impact') {
      list.sort((a, b) => String(b.impact).localeCompare(String(a.impact)))
    }
    if (sortBy === 'effort') {
      list.sort((a, b) => String(a.effort).localeCompare(String(b.effort)))
    }
    return list
  }, [items, sortBy])

  const toggle = (idx: number) => {
    const next = { ...completed, [idx]: !completed[idx] }
    setCompleted(next)
    localStorage.setItem(`seo_plan_done_${analysisId}`, JSON.stringify(next))
  }

  const exportCsv = () => {
    const header = ['priority', 'category', 'action', 'impact', 'effort', 'timeframe']
    const rows = [header.join(',')]
    for (const item of sorted) {
      rows.push(header.map((k) => JSON.stringify(item[k] ?? '')).join(','))
    }
    const blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'seo-action-plan.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className='panel p-4'>
      <div className='mb-3 flex flex-wrap items-center justify-between gap-2'>
        <h3 className='text-lg font-semibold'>Action Plan</h3>
        <div className='flex gap-2'>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'priority' | 'impact' | 'effort')}
            className='rounded-md border border-white/15 bg-black/30 px-2 py-1 text-xs'
          >
            <option value='priority'>Sort: Priority</option>
            <option value='impact'>Sort: Impact</option>
            <option value='effort'>Sort: Effort</option>
          </select>
          <button onClick={exportCsv} className='rounded-md border border-white/15 px-3 py-1 text-xs hover:border-accent'>
            Export CSV
          </button>
        </div>
      </div>
      <div className='overflow-auto'>
        <table className='min-w-full text-left text-sm'>
          <thead className='text-xs uppercase text-muted'>
            <tr>
              <th className='py-2'>Done</th>
              <th>Priority</th>
              <th>Category</th>
              <th>Action</th>
              <th>Impact</th>
              <th>Effort</th>
              <th>Timeframe</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((item, idx) => (
              <tr key={`${item.action}-${idx}`} className='border-t border-white/10'>
                <td className='py-2'>
                  <input type='checkbox' checked={!!completed[idx]} onChange={() => toggle(idx)} />
                </td>
                <td>{item.priority}</td>
                <td>{item.category}</td>
                <td>{item.action}</td>
                <td>{item.impact}</td>
                <td>{item.effort}</td>
                <td>{item.timeframe}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
