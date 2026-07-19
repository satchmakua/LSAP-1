import { useMemo, useState } from 'react'
import type { CNeighbor, CSpace } from '../api'

const W = 560
const H = 380
const PAD = 46

const pct = (v: number) => `${(v * 100).toFixed(1)}%`
const short = (s: string, n = 70) => (s.length > n ? `${s.slice(0, n)}…` : s)

export function CSpaceMap({
  cspace,
  highlight,
  neighbors,
}: {
  cspace: CSpace
  highlight?: { segment_id: string; coords: number[] } | null
  neighbors?: CNeighbor[]
}) {
  const [xi, setXi] = useState(0)
  const [yi, setYi] = useState(cspace.factors.length > 1 ? 1 : 0)

  const nbIds = useMemo(
    () => new Set((neighbors ?? []).map((n) => n.segment_id)),
    [neighbors],
  )

  const fx = cspace.factors[xi]
  const fy = cspace.factors[yi]
  const sx = (v: number) => PAD + v * (W - 2 * PAD)
  const sy = (v: number) => H - PAD - v * (H - 2 * PAD)

  return (
    <section className="cspace">
      <h2>C-Space Map</h2>
      <p className="subtitle">
        {cspace.n_segments} corpus segments · {cspace.factors.length} locked factors ·
        unexplained residual (C6) {pct(cspace.residual)}
      </p>

      <div className="controls">
        <label>
          x{' '}
          <select value={xi} onChange={(e) => setXi(Number(e.target.value))} aria-label="x factor">
            {cspace.factors.map((f, i) => (
              <option key={f.id} value={i}>
                {f.id} — {short(f.label, 40)}
              </option>
            ))}
          </select>
        </label>
        <label>
          y{' '}
          <select value={yi} onChange={(e) => setYi(Number(e.target.value))} aria-label="y factor">
            {cspace.factors.map((f, i) => (
              <option key={f.id} value={i}>
                {f.id} — {short(f.label, 40)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <svg
        className="cspace-svg"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`C-space scatter of ${cspace.n_segments} segments`}
      >
        <rect x={PAD} y={PAD} width={W - 2 * PAD} height={H - 2 * PAD} className="plot-bg" />
        {cspace.points.map((p) => {
          const isHi = highlight?.segment_id === p.segment_id
          const isNb = nbIds.has(p.segment_id)
          return (
            <circle
              key={p.segment_id}
              cx={sx(p.coords[xi] ?? 0)}
              cy={sy(p.coords[yi] ?? 0)}
              r={isHi ? 7 : isNb ? 5.5 : 4}
              className={`pt${isHi ? ' hi' : isNb ? ' nb' : ''}`}
            >
              <title>
                {p.segment_id}
                {p.profile ? ` — ${short(p.profile, 90)}` : ''}
              </title>
            </circle>
          )
        })}
        {highlight && (
          <circle
            cx={sx(highlight.coords[xi] ?? 0)}
            cy={sy(highlight.coords[yi] ?? 0)}
            r={10}
            className="pt ring"
          >
            <title>{highlight.segment_id} (this segment)</title>
          </circle>
        )}
        <text x={W / 2} y={H - 12} className="ax" textAnchor="middle">
          {fx.id} — {short(fx.label, 46)} ({pct(fx.explained_variance)})
        </text>
        <text
          x={14}
          y={H / 2}
          className="ax"
          textAnchor="middle"
          transform={`rotate(-90 14 ${H / 2})`}
        >
          {fy.id} — {short(fy.label, 46)} ({pct(fy.explained_variance)})
        </text>
      </svg>

      {neighbors && neighbors.length > 0 && (
        <div className="neighbors">
          <h3>Nearest neighbours</h3>
          <ol>
            {neighbors.map((n) => (
              <li key={n.segment_id}>
                <span className="nb-id">{n.segment_id}</span>
                <span className="nb-d">d={n.distance.toFixed(2)}</span>
                {n.profile && <span className="nb-profile">{short(n.profile, 80)}</span>}
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  )
}
