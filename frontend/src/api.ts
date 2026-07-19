export type FieldCode = 'L' | 'N' | 'C' | 'P' | 'A' | 'S'

export interface AxisDef {
  id: string
  field: FieldCode
  name: string
  kind: 'scalar' | 'forced_choice'
  definition: string
  anchors: Record<number, string> | null
  choices: string[] | null
  watch_for: string[]
}

export interface AxisScore {
  axis_id: string
  value: number
  confidence: number
}

export interface Rating {
  segment_id: string
  rater_id: string
  scores: AxisScore[]
  flagged: boolean
  created_at: string
}

export interface RateResponse {
  rating: Rating
  segment_id: string
  word_count: number
}

export const FIELD_NAMES: Record<FieldCode, string> = {
  L: 'Language',
  N: 'Narrative',
  C: 'Consciousness',
  P: 'Philosophy',
  A: 'Affective',
  S: 'Stylistic',
}

export const FIELD_ORDER: FieldCode[] = ['L', 'N', 'C', 'P', 'A', 'S']

async function detail(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (body && typeof body.detail === 'string') return body.detail
  } catch {
    /* non-JSON error body */
  }
  return `HTTP ${res.status}`
}

export async function fetchAxes(): Promise<AxisDef[]> {
  const res = await fetch('/api/axes')
  if (!res.ok) throw new Error(await detail(res))
  return (await res.json()) as AxisDef[]
}

export async function rateSegment(body: {
  text: string
  title?: string
  segment_id?: string
  rater?: string
}): Promise<RateResponse> {
  const res = await fetch('/api/rate', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await detail(res))
  return (await res.json()) as RateResponse
}

/* --- M3: the coordinate system --- */

export interface CFactor {
  id: string
  label: string
  explained_variance: number
  top_axes: [string, number][]
}

export interface CSpacePoint {
  segment_id: string
  profile: string | null
  pair: string | null
  coords: number[]
}

export interface CSpace {
  factors: CFactor[]
  residual: number
  n_segments: number
  points: CSpacePoint[]
}

export interface CNeighbor {
  segment_id: string
  distance: number
  profile: string | null
}

export interface SegmentProjection {
  segment_id: string
  vector: { coords: number[]; residual: number }
  neighbors: CNeighbor[]
}

export async function fetchCSpace(): Promise<CSpace> {
  const res = await fetch('/api/cspace')
  if (!res.ok) throw new Error(await detail(res))
  return (await res.json()) as CSpace
}

export async function fetchProjection(segmentId: string, k = 5): Promise<SegmentProjection> {
  const res = await fetch(`/api/segments/${encodeURIComponent(segmentId)}/projection?k=${k}`)
  if (!res.ok) throw new Error(await detail(res))
  return (await res.json()) as SegmentProjection
}
