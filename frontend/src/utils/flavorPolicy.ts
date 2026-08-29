export type PoteSize = 'KG_1' | 'KG_HALF' | 'KG_QUARTER' | null
export type ProductType = 'POTE' | 'UNIT'
export function bounds(size: PoteSize, type: ProductType): { min: number; max: number } {
  if (type === 'UNIT' || !size) return { min: 0, max: 0 }
  if (size === 'KG_QUARTER') return { min: 1, max: 3 }
  return { min: 1, max: 4 }
}
// Flexible: KG_1/KG_HALF 1-4 (antes 3-4), KG_QUARTER 1-3 (antes 2-3). Checkbox "Permite elegir gustos" desactiva bounds (null).
export function validate(size: PoteSize, type: ProductType, n: number): string | null {
  const { min, max } = bounds(size, type)
  if (n < min || n > max) return min === max ? `Elegí ${min} gustos` : `Elegí ${min} a ${max} gustos`
  return null
}
export function hint(size: PoteSize, type: ProductType): string {
  const { min, max } = bounds(size, type)
  if (max === 0) return ''
  return min === max ? `Elegí ${min} gustos` : `Elegí ${min} a ${max} gustos`
}
