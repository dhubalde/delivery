// @ts-nocheck
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { qk } from '@/queries/keys'
import { schedulesApi, specialDatesApi, deliveryApi, zonesApi } from '@/api/panel/ops.api'
export const errDetails = (e: unknown) => (e as { response?: { data?: { error?: { details?: Record<string,string>; code?: string; message?: string } } } })?.response?.data?.error?.details ?? {}
export const errCode = (e: unknown) => (e as { response?: { data?: { error?: { code?: string } }; status?: number } })?.response?.data?.error?.code ?? ''
export const errStatus = (e: unknown) => (e as { response?: { status?: number } })?.response?.status
export function useSchedules(){ return useQuery({ queryKey: qk.adminSchedules(), queryFn: schedulesApi.list }) }
export function useSpecialDates(){ return useQuery({ queryKey: qk.adminSpecialDates(), queryFn: specialDatesApi.list }) }
export function useDeliveryConfig(){ return useQuery({ queryKey: qk.adminDeliveryConfig(), queryFn: deliveryApi.get }) }
export function useZones(){ return useQuery({ queryKey: qk.adminZones(), queryFn: zonesApi.list }) }
export function useUpsertSchedule(){
  const qc=useQueryClient()
  return useMutation({
    mutationFn: schedulesApi.upsert as never,
    onMutate: async(v:{ weekday:number; ranges:{opens_at:string;closes_at:string}[]})=>{
      await qc.cancelQueries({ queryKey: qk.adminSchedules() })
      const prev=qc.getQueryData(qk.adminSchedules())
      qc.setQueryData(qk.adminSchedules(), (o:unknown)=>{ const arr=(o as unknown[])??[]; const idx=(arr as {weekday:number}[]).findIndex(x=>x.weekday===v.weekday); const next={ weekday:v.weekday, time_ranges:v.ranges, id: Date.now() }; if(idx>=0){ const c=[...arr]; (c as unknown[])[idx]=next as never; return c as never } return [...arr, next as never] as never })
      return { prev }
    },
    onError:(_e,_v,c)=> c?.prev && qc.setQueryData(qk.adminSchedules(), c.prev as never),
    onSettled:()=> qc.invalidateQueries({ queryKey: qk.adminSchedules() }),
  })
}
export function useDeleteSchedule(){
  const qc=useQueryClient()
  return useMutation({
    mutationFn: schedulesApi.remove as never,
    onMutate: async(id:number)=>{ await qc.cancelQueries({ queryKey: qk.adminSchedules() }); const prev=qc.getQueryData(qk.adminSchedules()); qc.setQueryData(qk.adminSchedules(), (o:unknown)=>((o as unknown[])??[]).filter((x:unknown)=>(x as {id:number}).id!==id) as never); return { prev } },
    onError:(_e,_v,c)=> c?.prev && qc.setQueryData(qk.adminSchedules(), c.prev as never),
    onSettled:()=> qc.invalidateQueries({ queryKey: qk.adminSchedules() }),
  })
}
export function useCreateSpecialDate(){
  const qc=useQueryClient()
  return useMutation({
    mutationFn: specialDatesApi.create as never,
    onMutate: async(v:object)=>{ await qc.cancelQueries({ queryKey: qk.adminSpecialDates() }); const prev=qc.getQueryData(qk.adminSpecialDates()); qc.setQueryData(qk.adminSpecialDates(), (o:unknown)=>[...((o as unknown[])??[]), { id: Date.now(), ...(v as object)}] as never); return { prev } },
    onError:(_e,_v,c)=> c?.prev && qc.setQueryData(qk.adminSpecialDates(), c.prev as never),
    onSettled:()=> qc.invalidateQueries({ queryKey: qk.adminSpecialDates() }),
  })
}
export function useDeleteSpecialDate(){
  const qc=useQueryClient()
  return useMutation({
    mutationFn: specialDatesApi.remove as never,
    onMutate: async(id:number)=>{ await qc.cancelQueries({ queryKey: qk.adminSpecialDates() }); const prev=qc.getQueryData(qk.adminSpecialDates()); qc.setQueryData(qk.adminSpecialDates(), (o:unknown)=>((o as unknown[])??[]).filter((x:unknown)=>(x as {id:number}).id!==id) as never); return { prev } },
    onError:(_e,_v,c)=> c?.prev && qc.setQueryData(qk.adminSpecialDates(), c.prev as never),
    onSettled:()=> qc.invalidateQueries({ queryKey: qk.adminSpecialDates() }),
  })
}
export function useUpdateDelivery(){
  const qc=useQueryClient()
  return useMutation({
    mutationFn: deliveryApi.update as never,
    onMutate: async(v:object)=>{ await qc.cancelQueries({ queryKey: qk.adminDeliveryConfig() }); const prev=qc.getQueryData(qk.adminDeliveryConfig()); qc.setQueryData(qk.adminDeliveryConfig(), (o:unknown)=>({ ...(o as object), ...(v as object)} as never)); return { prev } },
    onError:(_e,_v,c)=> c?.prev && qc.setQueryData(qk.adminDeliveryConfig(), c.prev as never),
    onSettled:()=> qc.invalidateQueries({ queryKey: qk.adminDeliveryConfig() }),
  })
}
export function useCreateZone(){
  const qc=useQueryClient()
  return useMutation({
    mutationFn: zonesApi.create as never,
    onMutate: async(v:object)=>{ await qc.cancelQueries({ queryKey: qk.adminZones() }); const prev=qc.getQueryData(qk.adminZones()); qc.setQueryData(qk.adminZones(), (o:unknown)=>[...((o as unknown[])??[]), { id: Date.now(), ...(v as object)}] as never); return { prev } },
    onError:(_e,_v,c)=> c?.prev && qc.setQueryData(qk.adminZones(), c.prev as never),
    onSettled:()=> qc.invalidateQueries({ queryKey: qk.adminZones() }),
  })
}
export function useUpdateZone(){
  const qc=useQueryClient()
  return useMutation({
    mutationFn: (p:{id:number}&Record<string,unknown>)=> zonesApi.update(p.id, p) as never,
    onMutate: async(p:{id:number}&Record<string,unknown>)=>{ const {id,...b}=p; await qc.cancelQueries({ queryKey: qk.adminZones() }); const prev=qc.getQueryData(qk.adminZones()); qc.setQueryData(qk.adminZones(), (o:unknown)=>((o as unknown[])??[]).map((x:unknown)=>(x as {id:number}).id===id?{...(x as object),...b} as never:x as never) as never); return { prev } },
    onError:(_e,_v,c)=> c?.prev && qc.setQueryData(qk.adminZones(), c.prev as never),
    onSettled:()=> qc.invalidateQueries({ queryKey: qk.adminZones() }),
  })
}
export function useDeleteZone(){
  const qc=useQueryClient()
  return useMutation({
    mutationFn: zonesApi.remove as never,
    onMutate: async(id:number)=>{ await qc.cancelQueries({ queryKey: qk.adminZones() }); const prev=qc.getQueryData(qk.adminZones()); qc.setQueryData(qk.adminZones(), (o:unknown)=>((o as unknown[])??[]).filter((x:unknown)=>(x as {id:number}).id!==id) as never); return { prev } },
    onError:(_e,_v,c)=> c?.prev && qc.setQueryData(qk.adminZones(), c.prev as never),
    onSettled:()=> qc.invalidateQueries({ queryKey: qk.adminZones() }),
  })
}
