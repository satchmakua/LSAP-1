import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { ManualRater } from './ManualRater'
import type { AxisDef, SegmentSummary } from '../api'

const AXES: AxisDef[] = [
  {
    id: 'L1', field: 'L', name: 'Lexical Complexity', kind: 'scalar',
    definition: 'diction rarity', anchors: { 1: 'plain', 4: 'mixed', 7: 'rare' },
    choices: null, watch_for: ['not beauty'],
  },
  {
    id: 'A3', field: 'A', name: 'Dominant Affect', kind: 'forced_choice',
    definition: 'the affect', anchors: null, choices: ['awe', 'dread'], watch_for: [],
  },
]

const seg = (id: string, rater_ids: string[] = []): SegmentSummary => ({
  id, word_count: 3, source: 'pilot', rater_ids, rating_count: rater_ids.length,
})

let segments: SegmentSummary[] = []
let posted: unknown = null

beforeEach(() => {
  posted = null
  segments = [seg('seg-a'), seg('seg-b'), seg('courtroom')]
  window.localStorage.clear()
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, opts?: { method?: string; body?: string }) => {
      const u = String(url)
      if (u.endsWith('/api/segments') && !opts?.method) {
        return { ok: true, status: 200, json: async () => segments }
      }
      const one = u.match(/\/api\/segments\/([^/]+)$/)
      if (one) {
        return {
          ok: true, status: 200,
          json: async () => ({ id: one[1], text: `prose of ${one[1]}`, ratings: [] }),
        }
      }
      if (u.endsWith('/api/rate/manual') && opts?.method === 'POST') {
        posted = JSON.parse(opts.body as string)
        const body = posted as { segment_id: string; rater_name: string; scores: unknown[] }
        return {
          ok: true, status: 200,
          json: async () => ({
            segment_id: body.segment_id,
            word_count: 3,
            rating: {
              segment_id: body.segment_id, rater_id: `human:${body.rater_name}`,
              axes_version: 3, flagged: false, created_at: 't', scores: body.scores,
            },
          }),
        }
      }
      return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) }
    }),
  )
})

const picker = () => screen.getByRole('combobox', { name: /segment/i })
const pick = async (id: string) => {
  fireEvent.change(picker(), { target: { value: id } })
  await waitFor(() => screen.getByText(`prose of ${id}`))
}
const chips = (group: string) =>
  within(screen.getByRole('group', { name: group })).getAllByRole('button')
const scoreBoth = () => {
  fireEvent.click(chips('L1 value')[3]) // 4
  fireEvent.click(chips('L1 confidence')[4]) // 5
  fireEvent.click(chips('A3 value')[1]) // 'dread'
  fireEvent.click(chips('A3 confidence')[4]) // 5
}
const ready = async () => {
  render(<ManualRater axes={AXES} />)
  await waitFor(() => expect(picker().querySelectorAll('option').length).toBeGreaterThan(1))
}

describe('ManualRater', () => {
  it('shows the manual per axis and gates saving on every axis being scored', async () => {
    await ready()
    fireEvent.change(screen.getByLabelText(/rater name/i), { target: { value: 'sh' } })
    await pick('seg-a')

    expect(screen.getByText(/diction rarity/)).toBeInTheDocument() // definition
    expect(screen.getByText('rare')).toBeInTheDocument() // the 7 anchor
    expect(screen.getByText(/not beauty/)).toBeInTheDocument() // watch-for
    expect(screen.getByText('0/2 axes scored')).toBeInTheDocument()

    const save = screen.getByRole('button', { name: /save human rating/i })
    expect(save).toBeDisabled()
    fireEvent.click(chips('L1 value')[3])
    expect(save).toBeDisabled() // a value without a confidence is not a score
    expect(screen.getByText('0/2 axes scored')).toBeInTheDocument()
  })

  it('submits a complete rating as human:<name>, then clears the form', async () => {
    await ready()
    fireEvent.change(screen.getByLabelText(/rater name/i), { target: { value: 'sh' } })
    await pick('seg-a')
    scoreBoth()
    expect(screen.getByText('2/2 axes scored')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /save human rating/i }))
    await waitFor(() => screen.getByRole('status'))

    expect(screen.getByRole('status')).toHaveTextContent('human:sh')
    expect(posted).toMatchObject({
      segment_id: 'seg-a',
      rater_name: 'sh',
      scores: [
        { axis_id: 'L1', value: 4, confidence: 5 },
        { axis_id: 'A3', value: 2, confidence: 5 },
      ],
    })
    // the form is gone until the next segment is chosen, and progress has advanced
    expect(screen.queryByRole('button', { name: /save human rating/i })).toBeNull()
    expect(screen.getByText('1 of 8 scored as human:sh')).toBeInTheDocument()
  })

  it('never carries one segment’s scores over to the next', async () => {
    await ready()
    await pick('seg-a')
    scoreBoth()
    expect(screen.getByText('2/2 axes scored')).toBeInTheDocument()

    await pick('seg-b')
    expect(screen.getByText('0/2 axes scored')).toBeInTheDocument()
    expect(chips('L1 value').every((b) => b.getAttribute('aria-pressed') === 'false')).toBe(true)
  })

  it('keeps a per-segment draft so a half-scored segment survives leaving it', async () => {
    await ready()
    await pick('seg-a')
    fireEvent.click(chips('L1 value')[5]) // 6
    fireEvent.click(chips('L1 confidence')[2]) // 3

    await pick('seg-b')
    await pick('seg-a')
    expect(chips('L1 value')[5]).toHaveAttribute('aria-pressed', 'true')
    expect(chips('L1 confidence')[2]).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('1/2 axes scored')).toBeInTheDocument()
  })

  it('lists segments under neutral codes, not ids, unless unblinded', async () => {
    await ready()
    const labels = () => Array.from(picker().querySelectorAll('option')).map((o) => o.textContent)
    expect(labels().some((t) => t?.includes('seg-a'))).toBe(false)
    expect(labels().filter((t) => /^Segment [0-9A-F]{5}/.test(t ?? '')).length).toBe(3)

    fireEvent.click(screen.getByRole('checkbox', { name: /show ids/i }))
    expect(labels().some((t) => t?.includes('seg-a'))).toBe(true)
  })

  it('marks what this rater has already scored and offers the next suggested segment', async () => {
    segments = [seg('seg-a', ['claude-opus-4-8', 'human:sh']), seg('seg-b'), seg('courtroom')]
    await ready()
    fireEvent.change(screen.getByLabelText(/rater name/i), { target: { value: 'sh' } })

    expect(screen.getByText('1 of 8 scored as human:sh')).toBeInTheDocument()
    const scored = Array.from(picker().querySelectorAll('option')).filter((o) =>
      o.textContent?.startsWith('✓'),
    )
    expect(scored.map((o) => o.getAttribute('value'))).toEqual(['seg-a'])

    fireEvent.click(screen.getByRole('button', { name: /next suggested/i }))
    await waitFor(() => screen.getByText('prose of courtroom'))
    expect(picker()).toHaveValue('courtroom')
  })
})
