import { useState, useCallback } from 'react'
import { searchPlayers, getProp } from '../api/client'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
import DistChart from '../components/DistChart'
import EVCard from '../components/EVCard'
import LineMove from '../components/LineMove'
import ChatSidebar from '../components/ChatSidebar'
import BetForm from '../components/BetForm'

const STAT_OPTIONS = ['points', 'rebounds', 'assists', 'steals', 'blocks', 'minutes']

export default function Analyze() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [statCategory, setStatCategory] = useState('points')
  const [window, setWindow] = useState(10)
  const [propData, setPropData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [chatOpen, setChatOpen] = useState(false)
  const [betFormOpen, setBetFormOpen] = useState(false)
  const [manualLine, setManualLine] = useState('')
  const [manualOdds, setManualOdds] = useState('')
  const [manualLoading, setManualLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (query.length < 2) return
    const r = await searchPlayers(query)
    setResults(r)
  }

  const handleSelectPlayer = (player) => {
    setSelectedPlayer(player)
    setResults([])
    setQuery(player.name)
  }

  const loadProp = useCallback(async (win = window) => {
    if (!selectedPlayer) return
    setLoading(true)
    setError(null)
    try {
      const data = await getProp(selectedPlayer.id, statCategory, {
        window: win,
        playerName: selectedPlayer.name,
      })
      setPropData(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load prop data')
    } finally {
      setLoading(false)
    }
  }, [selectedPlayer, statCategory, window])

  const handleWindowChange = (w) => {
    setWindow(w)
    loadProp(w)
  }

  const handleManualEV = async (e) => {
    e.preventDefault()
    if (!propData || !manualLine || !manualOdds) return
    setManualLoading(true)
    try {
      const values = propData.game_log.map((g) => g.value)
      const r = await axios.post(`${BASE_URL}/ev`, {
        game_log_values: values,
        line: parseFloat(manualLine),
        odds: parseInt(manualOdds),
        stat_category: propData.stat_category,
      })
      setPropData({
        ...propData,
        line: parseFloat(manualLine),
        over_odds: parseInt(manualOdds),
        odds_available: true,
        ...r.data,
      })
    } catch (err) {
      setError('Failed to calculate EV')
    } finally {
      setManualLoading(false)
    }
  }

  return (
    <div className="flex gap-6">
      <div className="flex-1 min-w-0">
        {/* Search */}
        <form onSubmit={handleSearch} className="flex gap-2 mb-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search player..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2
                       text-sm text-gray-100 placeholder-gray-500 focus:outline-none
                       focus:border-green-500"
          />
          <select
            value={statCategory}
            onChange={(e) => setStatCategory(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
                       text-sm text-gray-200 focus:outline-none"
          >
            {STAT_OPTIONS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button type="submit"
            className="px-4 py-2 bg-green-500 text-gray-900 rounded-lg text-sm font-medium
                       hover:bg-green-400 transition-colors">
            Search
          </button>
        </form>

        {/* Player results dropdown */}
        {results.length > 0 && (
          <div className="bg-gray-800 border border-gray-700 rounded-lg mb-4 overflow-hidden">
            {results.map((p) => (
              <button key={p.id} onClick={() => handleSelectPlayer(p)}
                className="w-full text-left px-4 py-2 hover:bg-gray-700 text-sm text-gray-200">
                <span className="font-medium">{p.name}</span>
                <span className="text-gray-500 ml-2">{p.team}</span>
              </button>
            ))}
          </div>
        )}

        {/* Analyze button */}
        {selectedPlayer && (
          <button onClick={() => loadProp(window)}
            className="mb-6 px-4 py-2 bg-gray-700 text-gray-200 rounded-lg text-sm
                       hover:bg-gray-600 transition-colors">
            {loading ? 'Loading...' : `Analyze ${selectedPlayer.name} — ${statCategory}`}
          </button>
        )}

        {error && (
          <p className="text-red-400 text-sm mb-4">{error}</p>
        )}

        {/* Manual odds input when no odds are available */}
        {propData && propData.odds_available === false && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6">
            <p className="text-sm text-gray-400 mb-3">
              No odds found automatically. Enter the line and odds manually to calculate EV.
            </p>
            <form onSubmit={handleManualEV} className="flex gap-2 items-end">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Line</label>
                <input
                  type="number" step="0.5" value={manualLine}
                  onChange={(e) => setManualLine(e.target.value)}
                  placeholder="24.5"
                  className="w-24 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
                             text-sm text-gray-100 focus:outline-none focus:border-green-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Over odds</label>
                <input
                  type="number" value={manualOdds}
                  onChange={(e) => setManualOdds(e.target.value)}
                  placeholder="-110"
                  className="w-24 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
                             text-sm text-gray-100 focus:outline-none focus:border-green-500"
                />
              </div>
              <button type="submit" disabled={manualLoading}
                className="px-4 py-2 bg-green-500 text-gray-900 rounded-lg text-sm
                           font-medium hover:bg-green-400 disabled:opacity-50">
                {manualLoading ? 'Calculating...' : 'Calculate EV'}
              </button>
            </form>
          </div>
        )}

        {/* Analytics grid */}
        {propData && (
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2">
              <DistChart
                gameLogs={propData.game_log}
                line={propData.line}
                statCategory={propData.stat_category}
                window={window}
                onWindowChange={handleWindowChange}
              />
            </div>
            <EVCard
              propData={propData}
              onLogBet={() => setBetFormOpen(true)}
            />
            <div className="col-span-3">
              <LineMove
                historicalLines={propData.historical_lines}
                currentLine={propData.line}
                openLine={propData.historical_lines?.[0]?.line ?? propData.line}
              />
            </div>
          </div>
        )}
      </div>

      {/* Chat toggle */}
      <div className="relative">
        <button
          onClick={() => setChatOpen((o) => !o)}
          className="fixed right-6 bottom-6 bg-green-500 text-gray-900 rounded-full
                     w-12 h-12 text-xl shadow-lg hover:bg-green-400 transition-colors z-20">
          💬
        </button>
        {chatOpen && (
          <ChatSidebar propData={propData} onClose={() => setChatOpen(false)} />
        )}
      </div>

      {betFormOpen && (
        <BetForm
          propData={propData}
          onClose={() => setBetFormOpen(false)}
          onSaved={() => setBetFormOpen(false)}
        />
      )}
    </div>
  )
}
