import { LineChart, Line, XAxis, Tooltip, ResponsiveContainer, ReferenceDot } from 'recharts'

export default function LineMove({ historicalLines = [], currentLine, openLine }) {
  if (!historicalLines.length) return null

  const data = historicalLines.map((snap, i) => ({
    i,
    line: snap.line,
    time: snap.snapshot_time
      ? new Date(snap.snapshot_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : `T${i}`,
    sharp: i > 0 && Math.abs(snap.line - historicalLines[i - 1].line) > 0.5,
  }))

  const delta = (currentLine ?? 0) - (openLine ?? 0)
  const sharpPoints = data.filter((d) => d.sharp)

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <h3 className="text-sm font-medium text-gray-300 mb-3">Line Movement</h3>

      <div className="flex gap-4 mb-3 text-xs font-mono">
        <div>
          <span className="text-gray-500">Open </span>
          <span className="text-gray-200">{openLine}</span>
        </div>
        <div>
          <span className="text-gray-500">Current </span>
          <span className="text-gray-200">{currentLine}</span>
        </div>
        <div>
          <span className="text-gray-500">Move </span>
          <span className={Math.abs(delta) > 0.5 ? 'text-amber-400' : 'text-gray-400'}>
            {delta > 0 ? '+' : ''}{delta.toFixed(1)}
            {Math.abs(delta) > 0.5 && ' ⚡'}
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={80}>
        <LineChart data={data}>
          <XAxis dataKey="time" hide />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 6, fontSize: 11 }}
            formatter={(v) => [v, 'line']}
          />
          <Line type="monotone" dataKey="line" stroke="#4ade80"
            strokeWidth={2} dot={false} />
          {sharpPoints.map((p) => (
            <ReferenceDot key={`${p.i}-${p.time}`} x={p.time} y={p.line} r={4} fill="#f59e0b" stroke="none" />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {sharpPoints.length > 0 && (
        <p className="text-xs text-amber-400 mt-1">⚡ Sharp move detected (line shifted &gt;0.5)</p>
      )}
    </div>
  )
}
