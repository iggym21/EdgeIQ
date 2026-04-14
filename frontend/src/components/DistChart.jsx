import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  ReferenceLine, Cell
} from 'recharts'

const WINDOWS = [5, 10, 20, 0]
const WINDOW_LABELS = { 5: 'L5', 10: 'L10', 20: 'L20', 0: 'Season' }

export default function DistChart({ gameLogs = [], line, statCategory, window, onWindowChange }) {
  if (!gameLogs.length) return null

  // Build histogram buckets
  const values = gameLogs.map((g) => g.value)
  const min = Math.floor(Math.min(...values))
  const max = Math.ceil(Math.max(...values))
  const buckets = {}
  for (let i = min; i <= max; i++) buckets[i] = 0
  values.forEach((v) => {
    const bucket = Math.floor(v)
    if (buckets[bucket] !== undefined) buckets[bucket]++
  })

  const data = Object.entries(buckets).map(([val, count]) => ({
    val: Number(val),
    count,
  }))

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-300">
          Distribution — {statCategory}
        </h3>
        <div className="flex gap-1">
          {WINDOWS.map((w) => (
            <button
              key={w}
              onClick={() => onWindowChange(w)}
              className={`px-2 py-1 rounded text-xs font-mono ${
                window === w
                  ? 'bg-green-400 text-gray-900'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {WINDOW_LABELS[w]}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <XAxis dataKey="val" tick={{ fontSize: 11, fill: '#6b7280' }} />
          <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 6 }}
            labelStyle={{ color: '#9ca3af' }}
          />
          <ReferenceLine x={Math.floor(line)} stroke="#f59e0b" strokeDasharray="4 2"
            label={{ value: `${line}`, fill: '#f59e0b', fontSize: 11 }} />
          <Bar dataKey="count" radius={[3, 3, 0, 0]}>
            {data.map((entry) => (
              <Cell
                key={entry.val}
                // strictly > line: hitting exactly the line is a push (not a clear)
                fill={entry.val > line ? '#4ade80' : '#374151'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="text-xs text-gray-500 mt-2">
        Green bars = would clear the line · Dashed line = prop threshold ({line})
      </p>
    </div>
  )
}
