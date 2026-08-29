export type PoteSize = 'KG_1' | 'KG_HALF' | 'KG_QUARTER' | null
export type ProductType = 'POTE' | 'UNIT'
export function bounds(size: PoteSize, type: ProductType): { min: number; max: number } {
  if (type === 'UNIT' || !size) return { min: 0, max: 0 }
  if (size === 'KG_QUARTER') return { min: 1, max: 3 }
  return { min: 1, max: 4 }
}
export function boundsForProduct(p: any): { min: number; max: number } {
  if (p?.product_type === 'UNIT') return { min: 0, max: 0 }
  if (p?.min_flavors != null && p?.max_flavors != null) return { min: Number(p.min_flavors), max: Number(p.max_flavors) }
  return bounds(p?.pote_size ?? null, p?.product_type ?? 'POTE')
}
export function validate(size: PoteSize, type: ProductType, n: number): string | null {
  const { min, max } = bounds(size, type)
  if (n < min || n > max) return min === max ? `Elegí ${min} gustos` : `Elegí ${min} a ${max} gustos`
  return null
}
export function validateForProduct(p: any, n: number): string | null {
  const { min, max } = boundsForProduct(p)
  if (n < min || n > max) return min === max ? `Elegí ${min} gustos` : `Elegí ${min} a ${max} gustos`
  return null
}
export function hint(size: PoteSize, type: ProductType): string {
  const { min, max } = bounds(size, type)
  if (max === 0) return ''
  return min === max ? `Elegí ${min} gustos` : `Elegí ${min} a ${max} gustos`
}
export function hintForProduct(p: any): string {
  const { min, max } = boundsForProduct(p)
  if (max === 0) return ''
  return min === max ? `Elegí ${min} gustos` : `Elegí ${min} a ${max} gustos`
}
