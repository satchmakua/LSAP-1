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
type Entries = Record<string, Entry>

/** How many hand-scored segments the human↔model comparison needs before it is read. */
const TARGET = 8

/**
 * The set offered first. Chosen once, in brief space and before any human rating existed:
 * four public-domain passages, four from the original pilot briefs, and four from the
 * later briefs (including one twin pair, so a rater's own consistency can be read).
 * Nothing about where a segment sits in the fitted space went into the choice.
 */
const SUGGESTED = new Set([
  'pd-cather-antonia',
  'pd-twain-huck',
  'pd-gilman-wallpaper',
  'pd-james-beast',
  'courtroom',
  'fable-river',
  'paranoia-flat',
  'thriller-stairwell',
  'toast-hall',
  'toast-firehouse',
  'aphorism-table',
  'one-breath-beach',
])

const NAME_KEY = 'lsap.manual.rater'
const draftKey = (segmentId: string) => `lsap.manual.draft.v1.${segmentId}`

/* Browser storage can be unavailable (private windows, blocked site data): never let it
   break scoring — a draft is a convenience, the saved rating is the record. */
function readStore(key: string): string | null {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}
function writeStore(key: string, value: string | null) {
  try {
    if (value === null) window.localStorage.removeItem(key)
    else window.localStorage.setItem(key, value)
  } catch {
    /* storage unavailable — scoring still works, just without drafts */
  }
}
function readDraft(segmentId: string): Entries {
  const raw = readStore(draftKey(segmentId))
  if (!raw) return {}
  try {
    const parsed: unknown = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? (parsed as Entries) : {}
  } catch {
    return {}
  }
}

/** A short code that says nothing about the segment (FNV-1a over the id). */
function opaqueCode(id: string): string {
  let h = 0x811c9dc5
  for (let i = 0; i < id.length; i++) {
    h ^= id.charCodeAt(i)
    h = Math.imul(h, 0x01000193)
  }
  return (h >>> 0).toString(16).toUpperCase().padStart(8, '0').slice(0, 5)
}

/**
 * The human scoring mode. A person applies the manual to an existing corpus segment: every
 * axis shows its definition, anchors, and watch-fors, and needs both a value and a
 * confidence. The result is stored as `human:<name>` so the reliability report can compare
 * human↔model — where they diverge is data, not error.
 *
 * Scoring is blind on purpose. The model raters see only the text, so a person sees only
 * the text too: segments are listed under opaque codes rather than ids (an id such as
 * `baroque-memory` or an author's name would prime the very judgments being measured),
 * and no model score is ever shown here.
 */
export function ManualRater({ axes }: { axes: AxisDef[] | null }) {
  const [segments, setSegments] = useState<SegmentSummary[]>([])
  const [segmentId, setSegmentId] = useState('')
  const [text, setText] = useState('')
  const [raterName, setRaterName] = useState(() => readStore(NAME_KEY) ?? '')
  const [entries, setEntries] = useState<Entries>({})
  const [saved, setSaved] = useState<{ rating: Rating; label: string } | null>(null)
  const [showIds, setShowIds] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSegments()
      .then((s) => setSegments(s.filter((x) => x.source === 'pilot')))
      .catch((e: unknown) => setError(String(e)))
  }, [])

  const raterId = raterName.trim() ? `human:${raterName.trim()}` : ''

  // Opaque label per segment, listed in code order so the picker's order carries no signal.
  const listed = useMemo(() => {
    const seen = new Map<string, number>()
    return segments
      .map((s) => {
        const code = opaqueCode(s.id)
        const n = (seen.get(code) ?? 0) + 1
        seen.set(code, n)
        return { ...s, label: n === 1 ? code : `${code}-${n}` }
      })
      .sort((a, b) => a.label.localeCompare(b.label))
  }, [segments])

  const isScored = (s: SegmentSummary) => raterId !== '' && s.rater_ids.includes(raterId)
  const scoredTotal = listed.filter(isScored).length
  const current = listed.find((s) => s.id === segmentId)
  const nextSuggested = listed.find((s) => SUGGESTED.has(s.id) && !isScored(s) && s.id !== segmentId)

  function onNameChange(name: string) {
    setRaterName(name)
    writeStore(NAME_KEY, name.trim() ? name : null)
  }

  async function onPickSegment(id: string) {
    setSegmentId(id)
    setSaved(null)
    setError(null)
    setText('')
    // Scores belong to one segment: start from that segment's own draft, never from
    // whatever was entered for the previous one.
    setEntries(id ? readDraft(id) : {})
    if (!id) return
    try {
      setText((await fetchSegment(id)).text)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  function update(axisId: string, patch: Entry) {
    setEntries((prev) => {
      const next = { ...prev, [axisId]: { ...prev[axisId], ...patch } }
      if (segmentId) writeStore(draftKey(segmentId), JSON.stringify(next))
      return next
    })
  }

  const scoredAxes = axes
    ? axes.filter((a) => entries[a.id]?.value && entries[a.id]?.confidence).length
    : 0
  const complete = axes != null && scoredAxes === axes.length
  const canSubmit = complete && !!segmentId && !!raterId && !busy

  async function onSubmit() {
    if (!axes || !canSubmit || !current) return
    setBusy(true)
    setError(null)
    try {
      const scores: AxisScore[] = axes.map((a) => ({
        axis_id: a.id,
        value: entries[a.id]!.value!,
        confidence: entries[a.id]!.confidence!,
      }))
      const res = await rateManual({ segment_id: segmentId, rater_name: raterName.trim(), scores })
      writeStore(draftKey(segmentId), null)
      setSegments((prev) =>
        prev.map((s) =>
          s.id === segmentId && !s.rater_ids.includes(res.rating.rater_id)
            ? { ...s, rater_ids: [...s.rater_ids, res.rating.rater_id], rating_count: s.rating_count + 1 }
            : s,
        ),
      )
      setSaved({ rating: res.rating, label: current.label })
      setSegmentId('')
      setText('')
      setEntries({})
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  if (!axes) return <p className="subtitle">Loading axes…</p>

  const optionText = (s: (typeof listed)[number]) =>
    `${isScored(s) ? '✓ ' : ''}Segment ${s.label}${showIds ? ` — ${s.id}` : ''}`
  const suggested = listed.filter((s) => SUGGESTED.has(s.id))
  const others = listed.filter((s) => !SUGGESTED.has(s.id))
  const words = text.trim() ? text.trim().split(/\s+/).length : 0

  return (
    <section className="manual-rater">
      <p className="subtitle">
        Score a corpus segment by hand against the same manual the model raters use. Segments
        are listed under neutral codes and no model score is shown, so your reading is your
        own; where it differs from the models' is data, not error.
      </p>

      <div className="mr-bar">
        <input
          value={raterName}
          onChange={(e) => onNameChange(e.target.value)}
          placeholder="Your name (e.g. sh)"
          aria-label="rater name"
        />
        <select
          value={segmentId}
          onChange={(e) => onPickSegment(e.target.value)}
          aria-label="segment"
        >
          <option value="">Pick a segment…</option>
          <optgroup label={`Suggested set — score at least ${TARGET}`}>
            {suggested.map((s) => (
              <option key={s.id} value={s.id}>
                {optionText(s)}
              </option>
            ))}
          </optgroup>
          <optgroup label="All other segments">
            {others.map((s) => (
              <option key={s.id} value={s.id}>
                {optionText(s)}
              </option>
            ))}
          </optgroup>
        </select>
        {nextSuggested && (
          <button type="button" onClick={() => onPickSegment(nextSuggested.id)}>
            Next suggested →
          </button>
        )}
        <span className={`mr-progress ${scoredTotal >= TARGET ? 'done' : ''}`}>
          {raterId
            ? `${scoredTotal} of ${TARGET} scored as ${raterId}`
            : 'Enter your name to track progress'}
        </span>
        <label className="mr-unblind">
          <input type="checkbox" checked={showIds} onChange={(e) => setShowIds(e.target.checked)} />
          show ids (unblinds — leave off while scoring)
        </label>
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {saved && (
        <p className="mr-saved" role="status">
          Saved <strong>{saved.rating.rater_id}</strong> rating of Segment {saved.label}
          {saved.rating.flagged ? ' — flagged (low confidence on more than 40% of axes)' : ''}.{' '}
          {scoredTotal >= TARGET
            ? `That makes ${scoredTotal} — enough for the human↔model comparison.`
            : `${TARGET - scoredTotal} more to reach ${TARGET}.`}
        </p>
      )}

      {current && (
        <div className="mr-split">
          <aside className="mr-text" aria-label="segment text">
            <h3>
              Segment {current.label}
              <span className="mr-words">{words ? ` · ${words.toLocaleString()} words` : ''}</span>
            </h3>
            <div className="mr-text-body">{text || 'Loading…'}</div>
          </aside>

          <div className="mr-axes">
            {isScored(current) && (
              <p className="mr-note">
                You have already scored this segment. Saving again adds a new rating; the
                analysis uses your newest one.
              </p>
            )}
            {FIELD_ORDER.map((f) => (
              <section key={f} className="mr-field">
                <h3>{FIELD_NAMES[f]}</h3>
                {axes
                  .filter((a) => a.field === f)
                  .map((a) => {
                    const entry = entries[a.id] ?? {}
                    const options =
                      a.kind === 'forced_choice'
                        ? (a.choices ?? []).map((c, i) => ({ v: i + 1, label: c }))
                        : [1, 2, 3, 4, 5, 6, 7].map((v) => ({ v, label: String(v) }))
                    const done = !!entry.value && !!entry.confidence
                    return (
                      <article key={a.id} className={`mr-axis ${done ? 'done' : ''}`}>
                        <header>
                          <span className="axis-id">{a.id}</span>
                          <strong>{a.name}</strong>
                        </header>
                        <p className="mr-def">{a.definition}</p>
                        {a.anchors && (
                          <dl className="mr-anchors">
                            {[1, 4, 7].map((k) =>
                              a.anchors?.[k] ? (
                                <div key={k}>
                                  <dt>{k}</dt>
                                  <dd>{a.anchors[k]}</dd>
                                </div>
                              ) : null,
                            )}
                          </dl>
                        )}
                        {a.watch_for.length > 0 && (
                          <p className="mr-watch">Watch for: {a.watch_for.join(' · ')}</p>
                        )}
                        <div className="mr-pick" role="group" aria-label={`${a.id} value`}>
                          <span className="mr-pick-label">value</span>
                          {options.map((o) => (
                            <button
                              key={o.v}
                              type="button"
                              aria-pressed={entry.value === o.v}
                              className={entry.value === o.v ? 'sel' : ''}
                              onClick={() => update(a.id, { value: o.v })}
                            >
                              {o.label}
                            </button>
                          ))}
                        </div>
                        <div className="mr-pick" role="group" aria-label={`${a.id} confidence`}>
                          <span className="mr-pick-label">confidence</span>
                          {[1, 2, 3, 4, 5].map((c) => (
                            <button
                              key={c}
                              type="button"
                              aria-pressed={entry.confidence === c}
                              className={entry.confidence === c ? 'sel conf' : 'conf'}
                              onClick={() => update(a.id, { confidence: c })}
                            >
                              {c}
                            </button>
                          ))}
                          <span className="mr-conf-hint">1 guessing · 5 certain</span>
                        </div>
                      </article>
                    )
                  })}
              </section>
            ))}

            <div className="mr-save">
              <span className={`wc ${complete ? '' : 'wc-warn'}`}>
                {scoredAxes}/{axes.length} axes scored
              </span>
              <button type="button" onClick={onSubmit} disabled={!canSubmit}>
                {busy ? 'Saving…' : 'Save human rating'}
              </button>
              {!raterId && <span className="wc wc-warn">enter your name to save</span>}
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
