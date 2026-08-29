// @ts-nocheck
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, unref } from 'vue'
import type { Ref } from 'vue'
import { catalogApi } from '@/api/panel/catalog.api'
import { qk } from '@/queries/keys'
export function useAdminCategories() {
  return useQuery({ queryKey: qk.adminCategories(), queryFn: () => catalogApi.categories.list() })
}
export function useAdminProducts(category: Ref<number|undefined>, search: Ref<string|undefined>) {
  return useQuery({
    queryKey: computed(() => qk.adminProducts({ category: unref(category), search: unref(search) || undefined })),
    queryFn: () => catalogApi.products.list({ category: unref(category), search: unref(search) || undefined }),
  })
}
export function useAdminFlavors(category: Ref<number|undefined>, search: Ref<string|undefined>) {
  return useQuery({
    queryKey: computed(() => qk.adminFlavors({ category: unref(category), search: unref(search) || undefined })),
    queryFn: () => catalogApi.flavors.list({ category: unref(category), search: unref(search) || undefined }),
  })
}
type Err = { response?: { status?: number; data?: { error?: { details?: Record<string,string> } } } }
export const errDetails = (e: unknown) => (e as Err)?.response?.data?.error?.details ?? {}
export function useCreateCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: catalogApi.categories.create as never,
    onSettled: () => qc.invalidateQueries({ queryKey: qk.adminCategories() }),
  })
}
export function useUpdateCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (p: { id: number } & Record<string, unknown>) => catalogApi.categories.update(p.id, p) as never,
    onSettled: () => qc.invalidateQueries({ queryKey: qk.adminCategories() }),
  })
}
export function useDeleteCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: catalogApi.categories.remove as never,
    onSettled: () => qc.invalidateQueries({ queryKey: qk.adminCategories() }),
  })
}
export function useCreateProduct(k: readonly unknown[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: catalogApi.products.create as never,
    onSettled: () => qc.invalidateQueries({ queryKey: k }),
  })
}
export function useUpdateProduct(k: readonly unknown[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (p: { id: number } & Record<string, unknown>) => catalogApi.products.update(p.id, p) as never,
    onSettled: () => qc.invalidateQueries({ queryKey: k }),
  })
}
export function useDeleteProduct(k: readonly unknown[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: catalogApi.products.remove as never,
    onSettled: () => qc.invalidateQueries({ queryKey: k }),
  })
}
export function useCreateFlavor(k: readonly unknown[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: catalogApi.flavors.create as never,
    onSettled: () => qc.invalidateQueries({ queryKey: k }),
  })
}
export function useUpdateFlavor(k: readonly unknown[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (p: { id: number } & Record<string, unknown>) => catalogApi.flavors.update(p.id, p) as never,
    onSettled: () => qc.invalidateQueries({ queryKey: k }),
  })
}
export function useDeleteFlavor(k: readonly unknown[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: catalogApi.flavors.remove as never,
    onSettled: () => qc.invalidateQueries({ queryKey: k }),
  })
}
