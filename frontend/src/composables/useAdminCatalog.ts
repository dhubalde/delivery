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
    onMutate: async (v: object) => { await qc.cancelQueries({ queryKey: qk.adminCategories() }); const prev = qc.getQueryData(qk.adminCategories()); qc.setQueryData(qk.adminCategories(), (o: unknown) => [...((o as unknown[])??[]), { id: Date.now(), ...(v as object) }] as never); return { prev } },
    onError: (_e: unknown, _v: unknown, c: unknown) => (c as {prev:unknown})?.prev && qc.setQueryData(qk.adminCategories(), (c as {prev:unknown}).prev as never),
    onSettled: () => { qc.invalidateQueries({ queryKey: qk.adminCategories() }); qc.invalidateQueries({ queryKey: ['categories'] }) },
  })
}
export function useUpdateCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (p: { id: number } & Record<string, unknown>) => catalogApi.categories.update(p.id, p) as never,
    onMutate: async (p: { id:number } & Record<string,unknown>) => { const { id, ...b } = p; await qc.cancelQueries({ queryKey: qk.adminCategories() }); const prev = qc.getQueryData(qk.adminCategories()); qc.setQueryData(qk.adminCategories(), (o: unknown) => ((o as unknown[])??[]).map((x: unknown) => (x as {id:number}).id===id ? { ...(x as object), ...b } as never : x as never) as never); return { prev } },
    onError: (_e: unknown,_v: unknown,c: unknown) => (c as {prev:unknown})?.prev && qc.setQueryData(qk.adminCategories(), (c as {prev:unknown}).prev as never),
    onSettled: () => { qc.invalidateQueries({ queryKey: qk.adminCategories() }); qc.invalidateQueries({ queryKey: ['categories'] }) },
  })
}
export function useDeleteCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: catalogApi.categories.remove as never,
    onMutate: async (id: number) => { await qc.cancelQueries({ queryKey: qk.adminCategories() }); const prev = qc.getQueryData(qk.adminCategories()); qc.setQueryData(qk.adminCategories(), (o: unknown) => ((o as unknown[])??[]).filter((x: unknown) => (x as {id:number}).id!==id) as never); return { prev } },
    onError: (_e: unknown,_v: unknown,c: unknown) => (c as {prev:unknown})?.prev && qc.setQueryData(qk.adminCategories(), (c as {prev:unknown}).prev as never),
    onSettled: () => { qc.invalidateQueries({ queryKey: qk.adminCategories() }); qc.invalidateQueries({ queryKey: ['categories'] }) },
  })
}
export function useCreateProduct(k: readonly unknown[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: catalogApi.products.create as never,
    onMutate: async (v: object) => { await qc.cancelQueries({ queryKey: k }); const prev = qc.getQueryData(k); qc.setQueryData(k, (o: unknown) => [...((o as unknown[])??[]), { id: Date.now(), ...(v as object) }] as never); return { prev } },
    onError: (_e: unknown,_v: unknown,c: unknown) => (c as {prev:unknown})?.prev && qc.setQueryData(k, (c as {prev:unknown}).prev as never),
    onSettled: () => qc.invalidateQueries({ queryKey: k }),
  })
}
export function useUpdateProduct(k: readonly unknown[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (p: { id: number } & Record<string, unknown>) => catalogApi.products.update(p.id, p) as never,
    onMutate: async (p: { id:number } & Record<string,unknown>) => { const { id, ...b } = p; await qc.cancelQueries({ queryKey: k }); const prev = qc.getQueryData(k); qc.setQueryData(k, (o: unknown) => ((o as unknown[])??[]).map((x: unknown) => (x as {id:number}).id===id ? { ...(x as object), ...b } as never : x as never) as never); return { prev } },
    onError: (_e: unknown,_v: unknown,c: unknown) => (c as {prev:unknown})?.prev && qc.setQueryData(k, (c as {prev:unknown}).prev as never),
    onSettled: () => qc.invalidateQueries({ queryKey: k }),
  })
}
export function useDeleteProduct(k: readonly unknown[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: catalogApi.products.remove as never,
    onMutate: async (id: number) => { await qc.cancelQueries({ queryKey: k }); const prev = qc.getQueryData(k); qc.setQueryData(k, (o: unknown) => ((o as unknown[])??[]).filter((x: unknown) => (x as {id:number}).id!==id) as never); return { prev } },
    onError: (_e: unknown,_v: unknown,c: unknown) => (c as {prev:unknown})?.prev && qc.setQueryData(k, (c as {prev:unknown}).prev as never),
    onSettled: () => qc.invalidateQueries({ queryKey: k }),
  })
}
export function useCreateFlavor(k: readonly unknown[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: catalogApi.flavors.create as never,
    onMutate: async (v: object) => { await qc.cancelQueries({ queryKey: k }); const prev = qc.getQueryData(k); qc.setQueryData(k, (o: unknown) => [...((o as unknown[])??[]), { id: Date.now(), ...(v as object) }] as never); return { prev } },
    onError: (_e: unknown,_v: unknown,c: unknown) => (c as {prev:unknown})?.prev && qc.setQueryData(k, (c as {prev:unknown}).prev as never),
    onSettled: () => qc.invalidateQueries({ queryKey: k }),
  })
}
export function useUpdateFlavor(k: readonly unknown[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (p: { id: number } & Record<string, unknown>) => catalogApi.flavors.update(p.id, p) as never,
    onMutate: async (p: { id:number } & Record<string,unknown>) => { const { id, ...b } = p; await qc.cancelQueries({ queryKey: k }); const prev = qc.getQueryData(k); qc.setQueryData(k, (o: unknown) => ((o as unknown[])??[]).map((x: unknown) => (x as {id:number}).id===id ? { ...(x as object), ...b } as never : x as never) as never); return { prev } },
    onError: (_e: unknown,_v: unknown,c: unknown) => (c as {prev:unknown})?.prev && qc.setQueryData(k, (c as {prev:unknown}).prev as never),
    onSettled: () => qc.invalidateQueries({ queryKey: k }),
  })
}
export function useDeleteFlavor(k: readonly unknown[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: catalogApi.flavors.remove as never,
    onMutate: async (id: number) => { await qc.cancelQueries({ queryKey: k }); const prev = qc.getQueryData(k); qc.setQueryData(k, (o: unknown) => ((o as unknown[])??[]).filter((x: unknown) => (x as {id:number}).id!==id) as never); return { prev } },
    onError: (_e: unknown,_v: unknown,c: unknown) => (c as {prev:unknown})?.prev && qc.setQueryData(k, (c as {prev:unknown}).prev as never),
    onSettled: () => qc.invalidateQueries({ queryKey: k }),
  })
}
