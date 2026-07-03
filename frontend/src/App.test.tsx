import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from './App'
import type { AxisDef, RateResponse } from './api'

const AXES: AxisDef[] = [
  {
    id: 'L1', field: 'L', name: 'Lexical Complexity', kind: 'scalar',
    definition: '', anchors: { 1: 'a' }, choices: null, watch_for: [],
  },
  {
    id: 'A3', field: 'A', name: 'Dominant Affect', kind: 'forced_choice',
    definition: '', anchors: null, choices: ['awe', 'dread'], watch_for: [],
  },
]

const RATE_RESPONSE: RateResponse = {
  segment_id: 's',
  word_count: 3,
  rating: {
    segment_id: 's',
    rater_id: 'claude-opus-4-8',
    flagged: false,
    created_at: 't',
    scores: [
      { axis_id: 'L1', value: 5, confidence: 4 },
      { axis_id: 'A3', value: 2, confidence: 3 }, // choices[1] === 'dread'
    ],
  },
}

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, opts?: { method?: string }) => {
      const u = String(url)
      if (u.endsWith('/api/axes')) return { ok: true, status: 200, json: async () => AXES }
      if (u.endsWith('/api/rate') && opts?.method === 'POST') {
        return { ok: true, status: 200, json: async () => RATE_RESPONSE }
      }
      return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) }
    }),
  )
})

describe('App', () => {
  it('renders the header and disables Rate until text is entered', async () => {
    render(<App />)
    expect(screen.getByText(/LSAP-1 · Rater Studio/)).toBeInTheDocument()
    await waitFor(() => screen.getByPlaceholderText(/Paste a coherent scene/))
    expect(screen.getByRole('button', { name: /rate/i })).toBeDisabled()
  })

  it('rates a segment and renders scores with values and forced-choice labels', async () => {
    render(<App />)
    await waitFor(() => screen.getByPlaceholderText(/Paste a coherent scene/))

    fireEvent.change(screen.getByPlaceholderText(/Paste a coherent scene/), {
      target: { value: 'some prose to score' },
    })
    fireEvent.click(screen.getByRole('button', { name: /^rate$/i }))

    await waitFor(() => screen.getByText(/Rated by/))
    expect(screen.getByText('claude-opus-4-8')).toBeInTheDocument()
    expect(screen.getByText('5/7')).toBeInTheDocument() // scalar value
    expect(screen.getByText('dread')).toBeInTheDocument() // forced-choice label
  })
})
