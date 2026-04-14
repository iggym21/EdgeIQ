export default function EVCard({ propData, onLogBet }) {
  if (!propData) return null

  const { your_prob, implied_prob, ev, edge_pct, kelly_fraction,
          line, over_odds, stat_category, low_confidence, sample_size } = propData

  const isPositive = ev > 0
  const formatOdds = (o) => o > 0 ? `+${o}` : `${o}`
  const formatPct = (p) => p != null ? `${(p * 100).toFixed(1)}%` : '—'

  return (
    <div className={`bg-gray-900 rounded-xl p-4 border ${
      isPositive ? 'border-green-500/40' : 'border-red-500/30'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-300">
          Over {line} {stat_category} · {formatOdds(over_odds)}
        </h3>
        <span className={`text-xs font-mono px-2 py-0.5 rounded-full ${
          isPositive
            ? 'bg-green-500/20 text-green-400'
            : 'bg-red-500/20 text-red-400'
        }`}>
          {isPositive ? '+' : ''}{ev != null ? (ev * 100).toFixed(1) : '—'}% EV
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <Stat label="Your Prob" value={formatPct(your_prob)} accent={isPositive} />
        <Stat label="Implied Prob" value={formatPct(implied_prob)} />
        <Stat label="Edge" value={`${edge_pct > 0 ? '+' : ''}${edge_pct != null ? edge_pct.toFixed(1) : '—'}%`} accent={edge_pct > 0} />
        <Stat label="Kelly" value={`${kelly_fraction != null ? (kelly_fraction * 100).toFixed(1) : '—'}%`} />
      </div>

      {low_confidence && (
        <p className="text-xs text-amber-400 mb-3 flex items-center gap-1">
          ⚠ Small sample (N={sample_size}) — model confidence low
        </p>
      )}

      <button
        onClick={() => onLogBet?.(propData)}
        className="w-full py-2 rounded-lg bg-gray-800 text-gray-300 text-sm
                   hover:bg-gray-700 transition-colors border border-gray-700"
      >
        Log Bet
      </button>
    </div>
  )
}

function Stat({ label, value, accent = false }) {
  return (
    <div className="bg-gray-800/50 rounded-lg p-2">
      <div className="text-xs text-gray-500 mb-0.5">{label}</div>
      <div className={`text-sm font-mono font-medium ${
        accent ? 'text-green-400' : 'text-gray-200'
      }`}>{value}</div>
    </div>
  )
}
