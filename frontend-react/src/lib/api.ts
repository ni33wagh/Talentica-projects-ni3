import { API_BASE } from './constants'
import type { DashboardData, SummaryResponse } from './types'

const dummy: DashboardData = {
  activity: Array.from({ length: 12 }).map((_, i) => ({ t: Date.now() - (11 - i) * 3600000, count: Math.floor(Math.random() * 8) })),
  successRate: Array.from({ length: 12 }).map((_, i) => ({ t: Date.now() - (11 - i) * 3600000, pct: 50 + Math.random() * 50 })),
  buildDurations: Array.from({ length: 14 }).map((_, i) => ({ t: i + 1, seconds: 60 + Math.floor(Math.random() * 600) })),
  status: { success: 42, failure: 7 },
  tests: { pass: 320, fail: 18 }
}

export async function fetchSummary(): Promise<DashboardData> {
  try {
    const res = await fetch(`${API_BASE}/api/metrics/summary`)
    if (!res.ok) throw new Error('Bad response')
    const data = await res.json() as SummaryResponse
    return data
  } catch (_) {
    return dummy
  }
}

