import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { ManualRater } from './ManualRater'
import type { AxisDef } from '../api'

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

let posted: unknown = null

beforeEach(() => {
  posted = null
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, opts?: { method?: string; body?: string }) => {
      const u = String(url)
      if (u.endsWith('/api/segments') && !opts?.method) {
        return {
          ok: true,
          status: 200,
          json: async () => [{ id: 'seg-a', word_count: 3, source: 'pilot', rater_ids: [], rating_count: 0 }],
        }
      }
      if (u.endsWith('/api/segments/seg-a')) {
        return { ok: true, status: 200, json: async () => ({ id: 'seg-a', text: 'some prose', ratings: [] }) }
      }
      if (u.endsWith('/api/rate/manual') && opts?.method === 'POST') {
        posted = JSON.parse(opts.body as string)
        return {
          ok: true,
          status: 200,
          json: async () => ({
            segment_id: 'seg-a',
            word_count: 3,
            rating: {
              segment_id: 'seg-a', rater_id: 'human:sh', axes_version: 3,
              flagged: false, created_at: 't',
              scores: [
                { axis_id: 'L1', value: 4, confidence: 5 },
                { axis_id: 'A3', value: 2, confidence: 5 },
              ],
            },
          }),
        }
      }
      return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) }
    }),
  )
})

describe('ManualRater', () => {
  it('requires a name, a segment, and every axis scored before submitting', async () => {
    render(<ManualRater axes={AXES} />)
    await waitFor(() => screen.getByRole('combobox', { name: /segment/i }))

    const save = screen.getByRole('button', { name: /save human rating/i })
    expect(save).toBeDisabled()

    // shows the count of scored axes out of the total
    expect(screen.getByText('0/2 axes scored')).toBeInTheDocument()
  })

  it('submits a complete human rating as human:<name>', async () => {
    render(<ManualRater axes={AXES} />)
    await waitFor(() => screen.getByRole('combobox', { name: /segment/i }))

    fireEvent.change(screen.getByLabelText(/rater name/i), { target: { value: 'sh' } })
    fireEvent.change(screen.getByRole('combobox', { name: /segment/i }), {
      target: { value: 'seg-a' },
    })
    // the anchors are visible per axis
    await waitFor(() => screen.getByText(/diction rarity/))

    // score both axes: value then confidence
    fireEvent.click(screen.getByRole('group', { name: 'L1 value' }).querySelectorAll('button')[3]) // value 4
    fireEvent.click(screen.getByRole('group', { name: 'L1 confidence' }).querySelectorAll('button')[4]) // conf 5
    fireEvent.click(screen.getByRole('group', { name: 'A3 value' }).querySelectorAll('button')[1]) // 'dread'
    fireEvent.click(screen.getByRole('group', { name: 'A3 confidence' }).querySelectorAll('button')[4]) // conf 5

    expect(screen.getByText('2/2 axes scored')).toBeInTheDocument()
    const save = screen.getByRole('button', { name: /save human rating/i })
    await waitFor(() => expect(save).not.toBeDisabled())
    fireEvent.click(save)

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
  })
})
