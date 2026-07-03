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

export const FIELD_NAMES: Record<FieldCode, string> = {
  L: 'Language',
  N: 'Narrative',
  C: 'Consciousness',
  P: 'Philosophy',
  A: 'Affective',
  S: 'Stylistic',
}

export async function fetchAxes(): Promise<AxisDef[]> {
  const res = await fetch('/api/axes')
  if (!res.ok) throw new Error(`GET /api/axes failed: ${res.status}`)
  return (await res.json()) as AxisDef[]
}
