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
  axes_version: number
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

export interface SegmentSummary {
  id: string
  word_count: number | null
  source: string | null
  rater_ids: string[]
  rating_count: number
}

export interface SegmentDetail {
  id: string
  text: string
  word_count?: number | null
  source?: string | null
  origin?: string | null
  ratings: Rating[]
  [key: string]: unknown
}

export async function fetchSegments(): Promise<SegmentSummary[]> {
  const res = await fetch('/api/segments')
  if (!res.ok) throw new Error(await detail(res))
  return (await res.json()) as SegmentSummary[]
}

export async function fetchSegment(id: string): Promise<SegmentDetail> {
  const res = await fetch(`/api/segments/${encodeURIComponent(id)}`)
  if (!res.ok) throw new Error(await detail(res))
  return (await res.json()) as SegmentDetail
}

/* M7: a human rating of an existing corpus segment (no model call) */
export async function rateManual(body: {
  segment_id: string
  rater_name: string
  scores: AxisScore[]
}): Promise<RateResponse> {
  const res = await fetch('/api/rate/manual', {
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

/* --- M4: the generative engine --- */

export interface EngineDials {
  c1: number
  c2: number
  c3: number
  c4: number
  c5: number
  style_seed?: string | null
}

export interface EnginePreset {
  id: string
  name: string
  description: string
  dials: EngineDials
}

export interface EngineParagraph {
  index: number
  phase: string
  language_register: string
  emotional_energy: number
  text: string
  objects_seen: string[]
  memory_note: string | null
}

export interface ConstraintSpec {
  bands: Record<string, string>
  rules: Record<string, string[]>
  agential_pressure: string
  perception: string
  registers: string[]
  phases: string[]
  style_seed: string | null
}

export interface GenerationRun {
  dials: EngineDials
  spec: ConstraintSpec
  situation: string
  world: { facts: string[]; objects: string[] }
  paragraphs: EngineParagraph[]
}

export async function fetchPresets(): Promise<EnginePreset[]> {
  const res = await fetch('/api/presets')
  if (!res.ok) throw new Error(await detail(res))
  return (await res.json()) as EnginePreset[]
}

export async function generateProse(body: {
  dials: EngineDials
  situation: string
  paragraphs: number
}): Promise<GenerationRun> {
  const res = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await detail(res))
  return (await res.json()) as GenerationRun
}
