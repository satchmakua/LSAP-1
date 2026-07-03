import { FIELD_NAMES, FIELD_ORDER, type AxisDef, type Rating } from '../api'

function confidenceDots(c: number): string {
  const n = Math.max(0, Math.min(5, c))
  return '●'.repeat(n) + '○'.repeat(5 - n)
}

export function ScoresView({ axes, rating }: { axes: AxisDef[]; rating: Rating }) {
  const scoreById = new Map(rating.scores.map((s) => [s.axis_id, s]))

  return (
    <section className="scores" aria-label="rating">
      {rating.flagged && (
        <p className="flag" role="alert">
          Flagged for review — low confidence (≤2) on more than 40% of axes.
        </p>
      )}
      <p className="rated-by">
        Rated by <strong>{rating.rater_id}</strong>
      </p>

      <div className="fields">
        {FIELD_ORDER.map((f) => (
          <section key={f} className="field">
            <h3>{FIELD_NAMES[f]}</h3>
            <ul>
              {axes
                .filter((a) => a.field === f)
                .map((a) => {
                  const s = scoreById.get(a.id)
                  if (!s) return null
                  const isForced = a.kind === 'forced_choice'
                  const label = isForced
                    ? (a.choices?.[s.value - 1] ?? String(s.value))
                    : `${s.value}/7`
                  return (
                    <li key={a.id}>
                      <span className="axis-id">{a.id}</span>
                      <span className="axis-name">{a.name}</span>
                      {isForced ? (
                        <span className="choice">{label}</span>
                      ) : (
                        <span className="bar" aria-label={`${s.value} of 7`}>
                          <span className="bar-fill" style={{ width: `${(s.value / 7) * 100}%` }} />
                          <span className="val">{label}</span>
                        </span>
                      )}
                      <span className="conf" title={`confidence ${s.confidence}/5`}>
                        {confidenceDots(s.confidence)}
                      </span>
                    </li>
                  )
                })}
            </ul>
          </section>
        ))}
      </div>
    </section>
  )
}
