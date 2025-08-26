import React, { useEffect, useMemo, useState } from 'react'
import { ActivityChart, DurationBar, SuccessRateChart, TestsDonut } from './components/Charts'
import { StatCard } from './components/StatCard'
import { POLL_INTERVAL_MS } from './lib/constants'
import { fetchSummary } from './lib/api'
import type { DashboardData } from './lib/types'

export default function App() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [intervalMs, setIntervalMs] = useState<number>(POLL_INTERVAL_MS)

  useEffect(() => {
    let mounted = true
    let timer: any
    const load = async () => {
      try {
        const d = await fetchSummary()
        if (!mounted) return
        setData(d)
        setError(null)
      } catch (e: any) {
        if (!mounted) return
        setError('Failed to load metrics')
      } finally {
        if (!mounted) return
        setLoading(false)
      }
    }
    load()
    timer = setInterval(load, intervalMs)
    return () => { mounted = false; if (timer) clearInterval(timer) }
  }, [intervalMs])

  const status = useMemo(() => ({
    success: data?.status?.success ?? 0,
    failure: data?.status?.failure ?? 0,
  }), [data])

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="px-4 py-3 border-b border-gray-800 sticky top-0 bg-gray-950/70 backdrop-blur">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="text-lg font-semibold">CI/CD Dashboard</div>
          <div className="flex items-center gap-3 text-sm text-gray-400">
            <label className="flex items-center gap-2">
              <span>Poll</span>
              <select className="bg-gray-900 border border-gray-800 rounded px-2 py-1" value={intervalMs} onChange={(e) => setIntervalMs(Number(e.target.value))}>
                <option value={5000}>5s</option>
                <option value={10000}>10s</option>
                <option value={30000}>30s</option>
                <option value={60000}>60s</option>
              </select>
            </label>
            {loading && <span className="text-amber-400">Loading...</span>}
            {error && <span className="text-rose-400">{error}</span>}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-4 grid gap-4 grid-cols-1 md:grid-cols-2">
        <div className="grid grid-cols-2 gap-4">
          <StatCard title="Successful" value={status.success} color="green" icon={<span>✔️</span>} />
          <StatCard title="Failed" value={status.failure} color="red" icon={<span>❌</span>} />
        </div>

        <ActivityChart data={data?.activity ?? []} />
        <DurationBar data={data?.buildDurations ?? []} />
        <SuccessRateChart data={data?.successRate ?? []} />

        <div className="grid grid-cols-2 gap-4">
          <div className="card">
            <div className="card-header">Tests (numbers)</div>
            <div className="card-body">
              <div className="grid grid-cols-2 gap-4">
                <StatCard title="Passing" value={data?.tests?.pass ?? 0} color="green" icon={<span>🧪</span>} />
                <StatCard title="Failed" value={data?.tests?.fail ?? 0} color="red" icon={<span>🧪</span>} />
              </div>
            </div>
          </div>
          <TestsDonut pass={data?.tests?.pass ?? 0} fail={data?.tests?.fail ?? 0} />
        </div>
      </main>
    </div>
  )
}

