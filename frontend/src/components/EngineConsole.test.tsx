import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { EngineConsole } from './EngineConsole'
import type { EnginePreset, GenerationRun } from '../api'

const PRESETS: EnginePreset[] = [
  {
    id: 'minimal',
    name: 'Minimalist',
    description: 'flat',
    dials: { c1: 0.1, c2: 0.1, c3: 0.1, c4: 0.05, c5: 0.1 },
  },
]

const RUN: GenerationRun = {
  dials: { c1: 0.9, c2: 0.4, c3: 0.6, c4: 0.9, c5: 0.4 },
  situation: 'A man returns to a flat.',
  world: { facts: ['A door is closed.'], objects: ['the glass'] },
  spec: {
    bands: { c1: 'extreme', c2: 'med', c3: 'high', c4: 'extreme', c5: 'med' },
    rules: { c1: ['Stack metaphors.'] },
    agential_pressure: 'high',
    perception: 'modernist (fragmented cognition)',
    registers: ['elevated literary', 'fragmented modernist'],
    phases: ['establishment', 'residue'],
    style_seed: null,
  },
  paragraphs: [
    {
      index: 0,
      phase: 'establishment',
      language_register: 'elevated literary',
      emotional_energy: 0.5,
      text: 'The room had kept its own weather.',
      objects_seen: ['the glass'],
      memory_note: null,
    },
    {
      index: 1,
      phase: 'residue',
      language_register: 'fragmented modernist',
      emotional_energy: 3.2,
      text: 'The glass stood where it had not been left.',
      objects_seen: ['the glass'],
      memory_note: 'Memory contradicts the world about the glass.',
    },
  ],
}

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, opts?: { method?: string }) => {
      const u = String(url)
      if (u.endsWith('/api/presets')) return { ok: true, status: 200, json: async () => PRESETS }
      if (u.endsWith('/api/generate') && opts?.method === 'POST') {
        return { ok: true, status: 200, json: async () => RUN }
      }
      return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) }
    }),
  )
})

describe('EngineConsole', () => {
  it('renders a slider per operator with its compiled band', async () => {
    render(<EngineConsole axes={null} />)
    expect(screen.getByLabelText('Compression (B1)')).toBeInTheDocument()
    expect(screen.getByLabelText('(De)Stabilization (B4)')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('option', { name: 'Minimalist' })).toBeInTheDocument())
  })

  it('generates and shows each paragraph with its evolving state', async () => {
    render(<EngineConsole axes={null} />)
    fireEvent.click(screen.getByRole('button', { name: /generate/i }))

    await waitFor(() => screen.getByText(/The room had kept its own weather/))
    // per-paragraph state panel: phase, register, emotional energy
    expect(screen.getByText('establishment')).toBeInTheDocument()
    expect(screen.getByText('residue')).toBeInTheDocument()
    expect(screen.getByText('fragmented modernist')).toBeInTheDocument()
    expect(screen.getByText('EF 3.2/5')).toBeInTheDocument()
    // the memory field surfaces its contradiction
    expect(screen.getByText(/Memory contradicts the world/)).toBeInTheDocument()
    // the one-way crossing is offered
    expect(screen.getByRole('button', { name: /re-rate this output/i })).toBeInTheDocument()
  })
})
