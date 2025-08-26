import React from 'react'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, BarChart, Bar, PieChart, Pie, Cell, Legend } from 'recharts'

export function ActivityChart({ data }: { data: { t: string|number, count?: number }[] }) {
  const fmtX = (v: any) => new Date(v).toLocaleTimeString([], { hour: '2-digit' })
  return (
    <div className="card">
      <div className="card-header">Pipeline Activity (runs/hour)</div>
      <div className="card-body h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
            <CartesianGrid stroke="#1f2937" />
            <XAxis dataKey="t" tickFormatter={fmtX} stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip labelFormatter={(l) => new Date(l as any).toLocaleString()} />
            <Line type="monotone" dataKey="count" stroke="#60a5fa" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export function DurationBar({ data }: { data: { t: string|number, seconds?: number }[] }) {
  return (
    <div className="card">
      <div className="card-header">Build Duration (recent)</div>
      <div className="card-body h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
            <CartesianGrid stroke="#1f2937" />
            <XAxis dataKey="t" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip formatter={(v: any) => [`${Math.round(v)}s`, 'duration']} />
            <Bar dataKey="seconds" fill="#34d399" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export function SuccessRateChart({ data }: { data: { t: string|number, pct?: number }[] }) {
  const fmtX = (v: any) => new Date(v).toLocaleTimeString([], { hour: '2-digit' })
  return (
    <div className="card">
      <div className="card-header">Success Rate</div>
      <div className="card-body h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
            <CartesianGrid stroke="#1f2937" />
            <XAxis dataKey="t" tickFormatter={fmtX} stroke="#9ca3af" />
            <YAxis domain={[0, 100]} stroke="#9ca3af" />
            <Tooltip formatter={(v: any) => [`${Number(v).toFixed(1)}%`, 'success']} labelFormatter={(l) => new Date(l as any).toLocaleString()} />
            <Line type="monotone" dataKey="pct" stroke="#a78bfa" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

const COLORS = ['#10B981', '#EF4444']
export function TestsDonut({ pass, fail }: { pass: number; fail: number }) {
  const data = [ { name: 'Passing', value: pass }, { name: 'Failed', value: fail } ]
  return (
    <div className="card">
      <div className="card-header">Test Results</div>
      <div className="card-body h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={60} outerRadius={90} paddingAngle={2}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Legend />
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

