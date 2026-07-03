import { useEffect, useState, type FormEvent } from 'react'
import { fetchAxes, rateSegment, type AxisDef, type Rating } from './api'
import { ScoresView } from './components/ScoresView'
import './App.css'

const RATERS = [
  { id: 'claude-opus-4-8', label: 'Opus 4.8 (canonical)' },
  { id: 'claude-haiku-4-5', label: 'Haiku 4.5 (fast)' },
]

export default function App() {
  const [axes, setAxes] = useState<AxisDef[] | null>(null)
  const [axesError, setAxesError] = useState<string | null>(null)
  const [text, setText] = useState('')
  const [title, setTitle] = useState('')
  const [rater, setRater] = useState(RATERS[0].id)
  const [rating, setRating] = useState<Rating | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAxes()
      .then(setAxes)
      .catch((e: unknown) => setAxesError(String(e)))
  }, [])

  const words = text.trim() ? text.trim().split(/\s+/).length : 0
  const outOfRange = words > 0 && (words < 1000 || words > 3000)

  async function onRate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const res = await rateSegment({ text, title: title || undefined, rater })
      setRating(res.rating)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="app">
      <header>
        <h1>LSAP-1 · Rater Studio</h1>
        <p className="subtitle">Score a prose segment on the 30 observable-feature axes.</p>
      </header>

      {axesError && (
        <p className="error" role="alert">
          Backend not reachable ({axesError}). Start it with <code>npm run dev</code>.
        </p>
      )}

      <form className="rate-form" onSubmit={onRate}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste a coherent scene, ~1,000–3,000 words…"
          rows={10}
        />
        <div className="controls">
          <input
            className="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title (optional)"
          />
          <select value={rater} onChange={(e) => setRater(e.target.value)} aria-label="rater">
            {RATERS.map((r) => (
              <option key={r.id} value={r.id}>
                {r.label}
              </option>
            ))}
          </select>
          <button type="submit" disabled={busy || !text.trim() || !axes}>
            {busy ? 'Rating…' : 'Rate'}
          </button>
          <span className={`wc ${outOfRange ? 'wc-warn' : ''}`}>
            {words} words{outOfRange ? ' — outside 1,000–3,000' : ''}
          </span>
        </div>
      </form>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {rating && axes && <ScoresView axes={axes} rating={rating} />}
    </main>
  )
}
