import { useEffect, useState } from 'react'
import { fetchAxes, FIELD_NAMES, type AxisDef, type FieldCode } from './api'
import './App.css'

const FIELD_ORDER: FieldCode[] = ['L', 'N', 'C', 'P', 'A', 'S']

export default function App() {
  const [axes, setAxes] = useState<AxisDef[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAxes()
      .then(setAxes)
      .catch((e: unknown) => setError(String(e)))
  }, [])

  return (
    <main className="app">
      <header>
        <h1>LSAP-1 · Rater Studio</h1>
        <p className="subtitle">
          The 30-axis instrument (M0 skeleton). Scoring a segment arrives in M1.
        </p>
      </header>

      {error && (
        <p className="error" role="alert">
          Backend not reachable ({error}). Start it with <code>npm run dev</code>.
        </p>
      )}
      {!axes && !error && <p>Loading axes…</p>}

      {axes && (
        <div className="fields">
          {FIELD_ORDER.map((f) => {
            const inField = axes.filter((a) => a.field === f)
            return (
              <section key={f} className="field">
                <h2>
                  {FIELD_NAMES[f]} <span className="count">{inField.length}</span>
                </h2>
                <ul>
                  {inField.map((a) => (
                    <li key={a.id}>
                      <span className="axis-id">{a.id}</span>
                      <span className="axis-name">{a.name}</span>
                      {a.kind === 'forced_choice' && <span className="tag">forced choice</span>}
                    </li>
                  ))}
                </ul>
              </section>
            )
          })}
        </div>
      )}
    </main>
  )
}
