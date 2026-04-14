import { useState } from 'react'
import { logBet } from '../api/client'

export default function BetForm({ propData, onClose, onSaved }) {
  const [stake, setStake] = useState('')
  const [direction, setDirection] = useState('over')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  if (!propData) return null

  const { player_name, stat_category, line, over_odds, under_odds, ev } = propData
  const odds = direction === 'over' ? over_odds : under_odds
  const formatOdds = (o) => o > 0 ? `+${o}` : `${o}`

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!stake || parseFloat(stake) <= 0) {
      setError('Enter a valid stake amount')
      return
    }
    setSaving(true)
    try {
      await logBet({
        player_name,
        stat_category,
        line,
        direction,
        odds,
        stake: parseFloat(stake),
        ev_at_bet: ev,
      })
      onSaved()
    } catch {
      setError('Failed to save bet')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-30"
         onClick={onClose}>
      <div className="bg-gray-900 rounded-xl p-6 w-96 border border-gray-700 shadow-2xl"
           onClick={(e) => e.stopPropagation()}>
        <h2 className="text-base font-medium text-gray-100 mb-4">Log Bet</h2>

        <div className="bg-gray-800 rounded-lg p-3 mb-4 text-sm">
          <div className="text-gray-400">{player_name}</div>
          <div className="text-gray-200 font-medium">{direction} {line} {stat_category}</div>
          <div className="text-gray-400 font-mono">{formatOdds(odds)}</div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex gap-2">
            {['over', 'under'].map((d) => (
              <button key={d} type="button"
                onClick={() => setDirection(d)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                  direction === d
                    ? 'bg-green-500 text-gray-900'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}>
                {d.charAt(0).toUpperCase() + d.slice(1)} {formatOdds(d === 'over' ? over_odds : under_odds)}
              </button>
            ))}
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Stake ($)</label>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={stake}
              onChange={(e) => setStake(e.target.value)}
              placeholder="50.00"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
                         text-sm text-gray-100 focus:outline-none focus:border-green-500"
            />
          </div>

          {error && <p className="text-red-400 text-xs">{error}</p>}

          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 py-2 bg-gray-800 text-gray-400 rounded-lg text-sm hover:bg-gray-700">
              Cancel
            </button>
            <button type="submit" disabled={saving}
              className="flex-1 py-2 bg-green-500 text-gray-900 rounded-lg text-sm
                         font-medium hover:bg-green-400 disabled:opacity-50">
              {saving ? 'Saving...' : 'Log Bet'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
