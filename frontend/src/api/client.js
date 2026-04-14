import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE_URL })

export const searchPlayers = (q) =>
  api.get('/props/search', { params: { q } }).then((r) => r.data)

export const getProp = (playerId, statCategory, { window = 10, playerName }) =>
  api
    .get(`/props/${playerId}/${statCategory}`, {
      params: { window, player_name: playerName },
    })
    .then((r) => r.data)

export const logBet = (bet) => api.post('/bets', bet).then((r) => r.data)

export const getBets = () => api.get('/bets').then((r) => r.data)

export const updateBet = (id, data) =>
  api.patch(`/bets/${id}`, data).then((r) => r.data)

export const streamChat = (payload, onChunk, onDone) => {
  const url = `${BASE_URL}/chat`
  const ctrl = new AbortController()
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: ctrl.signal,
  }).then(async (res) => {
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) { onDone(); break }
      const text = decoder.decode(value)
      text.split('\n').forEach((line) => {
        if (line.startsWith('data: ')) {
          const chunk = line.slice(6)
          if (chunk === '[DONE]') return
          if (chunk.startsWith('[ERROR] ')) {
            onChunk(`⚠️ ${chunk.slice(8)}`)
          } else {
            onChunk(chunk)
          }
        }
      })
    }
  }).catch((err) => {
    if (err.name !== 'AbortError') onDone()
  })
  return () => ctrl.abort()
}
