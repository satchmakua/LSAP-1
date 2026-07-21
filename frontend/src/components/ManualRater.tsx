import { useEffect, useMemo, useState } from 'react'
import {
  fetchSegment,
  fetchSegments,
  rateManual,
  FIELD_NAMES,
  FIELD_ORDER,
  type AxisDef,
  type AxisScore,
  type Rating,
  type SegmentSummary,
} from '../api'

type Entry = { value?: number; confidence?: number }

/**
 * M7 — the human scoring mode. A person applies the manual to an existing corpus segment:
 * every axis shows its definition, anchors, and watch-fors; a value and a confidence are
 * required per axis. The result is stored as `human:<name>`, so the reliability report can
 * compare human↔model (Charter P2: divergence is data, not error).
 */
export function ManualRater({ axes }: { axes: AxisDef[] | null }) {
  const [segments, setSegments] = useState<SegmentSummary[]>([])
  const [segmentId, setSegmentId] = useState('')
  const [text, setText] = useState('')
  const [raterName, setRaterName] = useState('')
  const [entries, setEntries] = useState<Record<string, Entry>>({})
  const [rating, setRating] = useState<Rating | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSegments()
      .then((s) => setSegments(s.filter((x) => x.source === 'pilot')))
      .catch((e: unknown) => setError(String(e)))
  }, [])

  async function onPickSegment(id: string) {
    setSegmentId(id)
    setRating(null)
    setText('')
    if (!id) return
    try {
      const seg = await fetchSegment(id)
      setText(seg.text)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  function setValue(axisId: string, value: number) {
    setEntries((e) => ({ ...e, [axisId]: { ...e[axisId], value } }))
  }
  function setConfidence(axisId: string, confidence: number) {
    setEntries((e) => ({ ...e, [axisId]: { ...e[axisId], confidence } }))
  }

  const scoredCount = useMemo(
    () => (axes ? axes.filter((a) => entries[a.id]?.value && entries[a.id]?.confidence).length : 0),
    [axes, entries],
  )
  const complete = axes != null && scoredCount === axes.length
  const canSubmit = complete && !!segmentId && !!raterName.trim() && !busy

  async function onSubmit() {
    if (!axes || !canSubmit) return
    setBusy(true)
    setError(null)
    try {
      const scores: AxisScore[] = axes.map((a) => ({
        axis_id: a.id,
        value: entries[a.id]!.value!,
        confidence: entries[a.id]!.confidence!,
      }))
      const res = await rateManual({ segment_id: segmentId, rater_name: raterName.trim(), scores })
      setRating(res.rating)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  if (!axes) return <p className="subtitle">Loading axes…</p>

  return (
    <section className="manual-rater">
      <p className="subtitle">
        Score an existing corpus segment by hand. Every axis needs a value and a confidence;
        your scores are stored as <code>human:{raterName.trim() || '<name>'}</code> and compared
        against the model raters. Where you and the model diverge is <em>data</em>, not error.
      </p>

      <div className="controls">
        <input
          className="title"
          value={raterName}
          onChange={(e) => setRaterName(e.target.value)}
          placeholder="Your name (e.g. sh)"
          aria-label="rater name"
        />
        <select
          value={segmentId}
          onChange={(e) => onPickSegment(e.target.value)}
          aria-label="segment"
        >
          <option value="">Pick a segment…</option>
          {segments.map((s) => (
            <option key={s.id} value={s.id}>
              {s.id} ({s.rating_count} ratings)
            </option>
          ))}
        </select>
        <span className={`wc ${complete ? '' : 'wc-warn'}`}>
          {scoredCount}/{axes.length} axes scored
        </span>
        <button type="button" onClick={onSubmit} disabled={!canSubmit}>
          {busy ? 'Saving…' : 'Save human rating'}
        </button>
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {text && (
        <details className="segment-text">
          <summary>Segment text ({text.trim().split(/\s+/).length} words)</summary>
          <div className="segment-body">{text}</div>
        </details>
      )}

      {segmentId && (
        <div className="fields">
          {FIELD_ORDER.map((f) => (
            <section key={f} className="field">
              <h3>{FIELD_NAMES[f]}</h3>
              <ul className="axis-score-list">
                {axes
                  .filter((a) => a.field === f)
                  .map((a) => {
                    const entry = entries[a.id] ?? {}
                    const options =
                      a.kind === 'forced_choice'
                        ? (a.choices ?? []).map((c, i) => ({ v: i + 1, label: c }))
                        : [1, 2, 3, 4, 5, 6, 7].map((v) => ({ v, label: String(v) }))
                    return (
                      <li key={a.id} className="axis-score">
                        <div className="axis-head">
                          <span className="axis-id">{a.id}</span>
                          <span className="axis-name">{a.name}</span>
                          <span className="axis-def">{a.definition}</span>
                        </div>
                        {a.anchors && (
                          <div className="anchors">
                            {[1, 4, 7].map((k) =>
                              a.anchors?.[k] ? (
                                <span key={k} className="anchor">
                                  <b>{k}</b> {a.anchors[k]}
                                </span>
                              ) : null,
                            )}
                          </div>
                        )}
                        {a.watch_for.length > 0 && (
                          <div className="watch-for">watch for: {a.watch_for.join('; ')}</div>
                        )}
                        <div className="pick" role="group" aria-label={`${a.id} value`}>
                          <span className="pick-label">value</span>
                          {options.map((o) => (
                            <button
                              key={o.v}
                              type="button"
                              className={`chip ${entry.value === o.v ? 'sel' : ''}`}
                              onClick={() => setValue(a.id, o.v)}
                            >
                              {o.label}
                            </button>
                          ))}
                        </div>
                        <div className="pick" role="group" aria-label={`${a.id} confidence`}>
                          <span className="pick-label">confidence</span>
                          {[1, 2, 3, 4, 5].map((c) => (
                            <button
                              key={c}
                              type="button"
                              className={`chip conf-chip ${entry.confidence === c ? 'sel' : ''}`}
                              onClick={() => setConfidence(a.id, c)}
                            >
                              {c}
                            </button>
                          ))}
                        </div>
                      </li>
                    )
                  })}
              </ul>
            </section>
          ))}
        </div>
      )}

      {rating && (
        <p className="rated-by" role="status">
          Saved <strong>{rating.rater_id}</strong> rating of <strong>{segmentId}</strong>
          {rating.flagged ? ' — flagged (low confidence on &gt;40% of axes)' : ''}.
        </p>
      )}
    </section>
  )
}
