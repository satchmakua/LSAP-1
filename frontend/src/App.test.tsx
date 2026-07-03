import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'
import type { AxisDef } from './api'

const AXES: AxisDef[] = [
  {
    id: 'L1', field: 'L', name: 'Lexical Complexity', kind: 'scalar',
    definition: '', anchors: { 1: 'a' }, choices: null, watch_for: [],
  },
  {
    id: 'A3', field: 'A', name: 'Dominant Affect', kind: 'forced_choice',
    definition: '', anchors: null, choices: ['awe'], watch_for: [],
  },
]

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, status: 200, json: async () => AXES })),
  )
})

describe('App', () => {
  it('renders the Rater Studio header', () => {
    render(<App />)
    expect(screen.getByText(/LSAP-1 · Rater Studio/)).toBeInTheDocument()
  })

  it('lists axes from the backend and tags forced-choice axes', async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByText('Lexical Complexity')).toBeInTheDocument())
    expect(screen.getByText('Dominant Affect')).toBeInTheDocument()
    expect(screen.getByText('forced choice')).toBeInTheDocument()
  })
})
