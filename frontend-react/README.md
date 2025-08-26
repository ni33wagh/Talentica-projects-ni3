CI/CD Dashboard (React + Vite + Tailwind + Recharts)

Run

```bash
npm i
npm run dev
```

Env vars:
- VITE_API_BASE (default: empty → relative to same origin)
- VITE_POLL_MS (default: 10000)

The app polls GET /api/metrics/summary every N seconds and falls back to dummy data if unreachable.

Structure
- src/components/*: charts and stat cards
- src/lib/*: types, constants, API
- src/App.tsx: page layout

API shape
```json
{
  "activity": [{"t": 1700000000000, "count": 5}],
  "successRate": [{"t": 1700000000000, "pct": 78.3}],
  "buildDurations": [{"t": 1, "seconds": 120}],
  "status": {"success": 42, "failure": 7},
  "tests": {"pass": 320, "fail": 18}
}
```

