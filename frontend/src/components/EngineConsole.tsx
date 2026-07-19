import { useEffect, useState, type FormEvent } from 'react'
import {
  fetchPresets,
  generateProse,
  rateSegment,
  type AxisDef,
  type EngineDials,
  type EnginePreset,
  type GenerationRun,
  type Rating,
} from '../api'
import { ScoresView } from './ScoresView'

const DIALS: { key: keyof EngineDials; label: string }[] = [
  { key: 'c1', label: 'Compression (B1)' },
  { key: 'c2', label: 'Temporal Structure (B2)' },
  { key: 'c3', label: 'Interiorization (B3)' },
  { key: 'c4', label: '(De)Stabilization (B4)' },
  { key: 'c5', label: 'Affective Amplification (B5)' },
]

const DEFAULT: EngineDials = { c1: 0.5, c2: 0.4, c3: 0.6, c4: 0.4, c5: 0.4 }

// Mirrors the backend band thresholds (display only — the server recompiles authoritatively).
const band = (v: number) => (v < 0.25 ? 'low' : v < 0.55 ? 'med' : v < 0.85 ? 'high' : 'extreme')

export function EngineConsole({ axes }: { axes: AxisDef[] | null }) {
  const [presets, setPresets] = useState<EnginePreset[]>([])
  const [dials, setDials] = useState<EngineDials>(DEFAULT)
  const [situation, setSituation] = useState('A man returns to an apartment he has not visited in months.')
  const [paragraphs, setParagraphs] = useState(4)
  const [run, setRun] = useState<GenerationRun | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [rerating, setRerating] = useState(false)
  const [rated, setRated] = useState<Rating | null>(null)

  useEffect(() => {
    fetchPresets()
      .then(setPresets)
      .catch(() => setPresets([]))
  }, [])

  async function onGenerate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setRated(null)
    try {
      setRun(await generateProse({ dials, situation, paragraphs }))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  async function onRerate() {
    if (!run) return
    setRerating(true)
    setError(null)
    try {
      // The one sanctioned crossing: generated prose goes back through the instrument.
      // One-way and offline of generation — the engine never sees the result.
      const text = run.paragraphs.map((p) => p.text).join('\n\n')
      const res = await rateSegment({ text })
      setRated(res.rating)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setRerating(false)
    }
  }

  return (
    <section className="engine">
      <h2>Engine Console</h2>
      <p className="subtitle">
        Dial the operators, not the adjectives. The compiler turns each band into
        generation rules; the runtime advances a state machine between paragraphs.
      </p>

      <form className="rate-form" onSubmit={onGenerate}>
        <div className="controls">
          <select
            aria-label="preset"
            value=""
            onChange={(e) => {
              const p = presets.find((x) => x.id === e.target.value)
              if (p) setDials(p.dials)
            }}
          >
            <option value="">Preset…</option>
            {presets.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <input
            className="title"
            value={situation}
            onChange={(e) => setSituation(e.target.value)}
            placeholder="Situation"
            aria-label="situation"
          />
          <label className="wc">
            paragraphs{' '}
            <input
              type="number"
              min={1}
              max={8}
              value={paragraphs}
              onChange={(e) => setParagraphs(Number(e.target.value))}
              aria-label="paragraphs"
              style={{ width: '3.5rem' }}
            />
          </label>
          <button type="submit" disabled={busy || !situation.trim()}>
            {busy ? 'Generating…' : 'Generate'}
          </button>
        </div>

        <div className="dials">
          {DIALS.map(({ key, label }) => (
            <label key={key} className="dial">
              <span className="dial-label">{label}</span>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={dials[key] as number}
                aria-label={label}
                onChange={(e) => setDials({ ...dials, [key]: Number(e.target.value) })}
              />
              <span className="dial-band">
                {(dials[key] as number).toFixed(2)} · {band(dials[key] as number)}
              </span>
            </label>
          ))}
        </div>
      </form>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {run && (
        <div className="run">
          <p className="rated-by">
            perception: <strong>{run.spec.perception}</strong> · agential pressure (B6):{' '}
            <strong>{run.spec.agential_pressure}</strong>
          </p>
          <details className="world">
            <summary>World state ({run.world.objects.length} objects)</summary>
            <ul>
              {run.world.facts.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
            <p className="wc">objects: {run.world.objects.join(', ')}</p>
          </details>

          {run.paragraphs.map((p) => (
            <article key={p.index} className="para">
              <p className="para-state">
                <span className="chip">{p.phase}</span>
                <span className="chip">{p.language_register}</span>
                <span className="chip">EF {p.emotional_energy}/5</span>
                {p.objects_seen.length > 0 && (
                  <span className="wc">objects: {p.objects_seen.join(', ')}</span>
                )}
              </p>
              {p.memory_note && <p className="memory">MF: {p.memory_note}</p>}
              <p className="prose">{p.text}</p>
            </article>
          ))}

          <button type="button" onClick={onRerate} disabled={rerating}>
            {rerating ? 'Re-rating…' : 'Re-rate this output'}
          </button>
          <p className="wc">
            Re-rating sends the generated prose back through the instrument — one-way and
            offline of generation (Charter P4).
          </p>
          {rated && axes && <ScoresView axes={axes} rating={rated} />}
        </div>
      )}
    </section>
  )
}
