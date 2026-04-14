import { useState, useEffect, useRef } from 'react'
import { streamChat } from '../api/client'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function ChatSidebar({ propData, onClose }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [chips, setChips] = useState([])
  const bottomRef = useRef(null)
  const cancelRef = useRef(null)

  useEffect(() => {
    if (!propData) return
    axios.post(`${BASE_URL}/chat/chips`, { prop_context: buildContext(propData) })
      .then((r) => setChips(r.data.chips))
  }, [propData])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = (text) => {
    if (!text.trim() || streaming) return
    const userMsg = { role: 'user', content: text }
    setMessages((m) => [...m, userMsg, { role: 'assistant', content: '' }])
    setInput('')
    setStreaming(true)
    setChips([])

    cancelRef.current = streamChat(
      { message: text, prop_context: buildContext(propData), history: messages },
      (chunk) => {
        setMessages((m) => {
          const updated = [...m]
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: updated[updated.length - 1].content + chunk,
          }
          return updated
        })
      },
      () => setStreaming(false),
    )
  }

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-gray-900 border-l
                    border-gray-800 flex flex-col z-10 shadow-2xl">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <span className="text-sm font-medium text-gray-200">AI Analyst</span>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-lg">✕</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-gray-500 text-sm text-center mt-8">
            {propData ? 'Ask anything about this prop.' : 'Select a prop to start.'}
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
              m.role === 'user'
                ? 'bg-green-500/20 text-green-100'
                : 'bg-gray-800 text-gray-200'
            }`}>
              {m.role === 'assistant' ? (
                m.content
                  ? <ReactMarkdown className="prose prose-invert prose-sm max-w-none
                                             prose-p:my-1 prose-ul:my-1 prose-li:my-0
                                             prose-table:text-xs prose-th:py-1 prose-td:py-1">
                      {m.content}
                    </ReactMarkdown>
                  : (streaming && i === messages.length - 1 ? '▋' : '')
              ) : (
                m.content
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {chips.length > 0 && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {chips.map((c, i) => (
            <button key={i} onClick={() => sendMessage(c)}
              className="text-xs bg-gray-800 text-gray-300 border border-gray-700
                         rounded-full px-3 py-1 hover:bg-gray-700 transition-colors">
              {c}
            </button>
          ))}
        </div>
      )}

      <div className="p-4 border-t border-gray-800 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage(input)}
          placeholder="Ask about this prop..."
          disabled={!propData || streaming}
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
                     text-sm text-gray-100 placeholder-gray-500 focus:outline-none
                     focus:border-green-500 disabled:opacity-50"
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={!propData || streaming || !input.trim()}
          className="px-3 py-2 bg-green-500 text-gray-900 rounded-lg text-sm font-medium
                     hover:bg-green-400 disabled:opacity-40 transition-colors"
        >
          →
        </button>
      </div>
    </div>
  )
}

function buildContext(p) {
  if (!p) return {}
  return {
    player_name: p.player_name,
    stat_category: p.stat_category,
    line: p.line,
    over_odds: p.over_odds,
    window: p.window,
    distribution: p.distribution,
    your_prob: p.your_prob,
    implied_prob: p.implied_prob,
    ev: p.ev,
    edge_pct: p.edge_pct,
    game_log_values: p.game_log?.map((g) => g.value) ?? [],
    full_season_log: p.full_season_log ?? [],
    open_line: p.historical_lines?.[0]?.line ?? p.line,
    sample_size: p.sample_size,
    low_confidence: p.low_confidence,
    opponent: p.game_log?.[0]?.opponent ?? '?',
    home_away: p.game_log?.[0]?.home_away ?? '?',
  }
}
