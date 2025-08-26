import React from 'react'

export function StatCard({ title, value, icon, color }: { title: string; value: string | number; icon: React.ReactNode; color?: 'green'|'red'|'indigo'|'amber' }) {
  const colorMap: Record<string, string> = {
    green: 'text-emerald-400',
    red: 'text-rose-400',
    indigo: 'text-indigo-400',
    amber: 'text-amber-400'
  }
  return (
    <div className="card">
      <div className="card-body flex items-center gap-4">
        <div className={`text-2xl ${color ? colorMap[color] : 'text-gray-400'}`}>{icon}</div>
        <div>
          <div className="text-sm text-gray-400">{title}</div>
          <div className="text-2xl font-semibold text-gray-100">{value}</div>
        </div>
      </div>
    </div>
  )
}

