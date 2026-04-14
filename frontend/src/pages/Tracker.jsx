import { useState, useEffect } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid
} from 'recharts'
import { getBets, updateBet, streamChat } from '../api/client'

export default function Tracker() {
  const [bets, setBets] = useState([])
  const [analysisText, setAnalysisText] = useState('')
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => { getBets().then(setBets) }, [])

  const totalPL = bets.reduce((sum, b) => sum + (b.profit_loss || 0), 0)
  const settled = bets.filter((b) => b.result !== 'pending')
  const wins = settled.filter((b) => b.result === 'win').length
  const hitRate = settled.length ? ((wins / settled.length) * 100).toFixed(1) : '--'

  // Running P&L for chart
  let running = 0
  const chartData = settled.map((b) => {
    running += b.profit_loss || 0
    return { label: b.player_name.split(' ')[1], pl: parseFloat(running.toFixed(2)) }
  })

  const handleSetResult = async (bet, result) => {
    const stake = bet.stake
    const profitLoss = result === 'win'
      ? bet.odds > 0 ? (bet.odds / 100) * stake : (100 / Math.abs(bet.odds)) * stake
      : result === 'push' ? 0 : -stake
    const updated = await updateBet(bet.id, { result, profit_loss: profitLoss })
    setBets((prev) => prev.map((b) => b.id === updated.id ? updated : b))
  }

  const handleAnalyze = () => {
    setAnalyzing(true)
    setAnalysisText('')
    const last30 = JSON.stringify(settled.slice(-30))
    streamChat(
      {
        message: `Analyze my last ${Math.min(30, settled.length)} bets for patterns, win rate, and leaks. Here is my bet history: ${last30}`,
        prop_context: {},
        history: [],
      },
      (chunk) => setAnalysisText((t) => t + chunk),
      () => setAnalyzing(false),
    )
  }

  const formatOdds = (o) => o > 0 ? `+${o}` : `${o}`

  return (
    <div className="max-w-4xl">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatBox label="Total P&L" value={`$${totalPL.toFixed(2)}`} accent={totalPL >= 0} />
        <StatBox label="Hit Rate" value={`${hitRate}%`} />
        <StatBox label="Bets" value={`${settled.length} / ${bets.length}`} />
      </div>

      {/* P&L chart */}
      {chartData.length > 1 && (
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-8">
          <h3 className="text-sm font-medium text-gray-300 mb-3">Running P&L</h3>
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#6b7280' }} />
              <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 6 }}
                formatter={(v) => [`$${v}`, 'P&L']}
              />
              <Line type="monotone" dataKey="pl" stroke="#4ade80" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* AI Analysis */}
      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 mb-8">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-300">Bet Analysis</h3>
          <button onClick={handleAnalyze} disabled={analyzing || settled.length === 0}
            className="text-xs px-3 py-1.5 bg-green-500/20 text-green-400 border
                       border-green-500/30 rounded-lg hover:bg-green-500/30 disabled:opacity-40">
            {analyzing ? 'Analyzing...' : 'Analyze my bets'}
          </button>
        </div>
        {analysisText ? (
          <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{analysisText}</p>
        ) : (
          <p className="text-sm text-gray-500">
            {settled.length === 0
              ? 'No settled bets to analyze yet.'
              : 'Click "Analyze my bets" to get an AI breakdown of your patterns and leaks.'}
          </p>
        )}
      </div>

      {/* Bet history */}
      <div className="space-y-2">
        {bets.map((bet) => (
          <div key={bet.id}
            className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 flex items-center gap-4">
            <div className="flex-1 min-w-0">
              <div className="text-sm text-gray-200 font-medium">
                {bet.player_name} · {bet.direction} {bet.line} {bet.stat_category}
              </div>
              <div className="text-xs text-gray-500 font-mono">
                {formatOdds(bet.odds)} · ${bet.stake} stake
                {bet.ev_at_bet != null && ` · EV was ${(bet.ev_at_bet * 100).toFixed(1)}%`}
              </div>
            </div>
            {bet.result === 'pending' ? (
              <div className="flex gap-1">
                {['win', 'loss', 'push'].map((r) => (
                  <button key={r} onClick={() => handleSetResult(bet, r)}
                    className="text-xs px-2 py-1 bg-gray-800 text-gray-400 rounded
                               hover:bg-gray-700 capitalize">
                    {r}
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-right">
                <span className={`text-xs font-medium capitalize ${
                  bet.result === 'win' ? 'text-green-400'
                  : bet.result === 'loss' ? 'text-red-400'
                  : 'text-gray-400'
                }`}>{bet.result}</span>
                {bet.profit_loss != null && (
                  <div className={`text-xs font-mono ${
                    bet.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {bet.profit_loss >= 0 ? '+' : ''}${bet.profit_loss.toFixed(2)}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {bets.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-8">
            No bets logged yet. Analyze a prop and click "Log Bet".
          </p>
        )}
      </div>
    </div>
  )
}

function StatBox({ label, value, accent = false }) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-2xl font-mono font-medium ${
        accent ? 'text-green-400' : 'text-gray-200'
      }`}>{value}</div>
    </div>
  )
}
