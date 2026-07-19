import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CSpaceMap } from './CSpaceMap'
import type { CSpace } from '../api'

const CSPACE: CSpace = {
  n_segments: 3,
  residual: 0.206,
  factors: [
    {
      id: 'C1',
      label: 'Figurative Density · Interior/Exterior Ratio',
      explained_variance: 0.448,
      top_axes: [['S4', 0.25]],
    },
    { id: 'C2', label: 'Meaning Structure', explained_variance: 0.115, top_axes: [['P4', 0.49]] },
  ],
  points: [
    { segment_id: 'min-kitchen', profile: 'compressed', pair: 'p_min', coords: [0.1, 0.2] },
    { segment_id: 'min-laundromat', profile: 'compressed', pair: 'p_min', coords: [0.15, 0.25] },
    { segment_id: 'baroque-memory', profile: 'expansive', pair: null, coords: [0.9, 0.8] },
  ],
}

describe('CSpaceMap', () => {
  it('renders the factors, the acknowledged residual, and one dot per corpus segment', () => {
    const { container } = render(<CSpaceMap cspace={CSPACE} />)
    expect(screen.getByText(/C-Space Map/)).toBeInTheDocument()
    expect(screen.getByText(/residual \(C6\) 20\.6%/)).toBeInTheDocument()
    expect(container.querySelectorAll('circle.pt')).toHaveLength(3)
    // The derived label appears in both the axis-picker <option> and the SVG axis text;
    // the variance share is unique to the axis label.
    expect(screen.getAllByText(/C1 — Figurative Density/).length).toBeGreaterThan(0)
    expect(screen.getByText(/44\.8%/)).toBeInTheDocument()
  })

  it('highlights the projected segment and lists its nearest neighbours', () => {
    render(
      <CSpaceMap
        cspace={CSPACE}
        highlight={{ segment_id: 'min-kitchen', coords: [0.1, 0.2] }}
        neighbors={[{ segment_id: 'min-laundromat', distance: 2.919, profile: 'compressed' }]}
      />,
    )
    expect(screen.getByText('Nearest neighbours')).toBeInTheDocument()
    expect(screen.getByText('min-laundromat')).toBeInTheDocument()
    expect(screen.getByText('d=2.92')).toBeInTheDocument()
  })
})
