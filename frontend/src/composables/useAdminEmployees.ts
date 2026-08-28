import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { qk } from '@/queries/keys'
import { employeesApi, type Role } from '@/api/panel/employees.api'
export const empErrDetails = (e: unknown) => (e as { response?: { data?: { error?: { details?: Record<string,string> } } } })?.response?.data?.error?.details ?? {}
export const empErrCode = (e: unknown) => (e as { response?: { data?: { error?: { code?: string } } } })?.response?.data?.error?.code ?? ''
export const empErrStatus = (e: unknown) => (e as { response?: { status?: number } })?.response?.status
export function useEmployees(){ return useQuery({ queryKey: qk.adminEmployees(), queryFn: employeesApi.list }) }
export function useCreateEmployee(){
  const qc=useQueryClient()
  return useMutation({
    mutationFn: employeesApi.create as never,
    onMutate: async(v:{display_name:string;is_active:boolean;roles:Role[]})=>{
      await qc.cancelQueries({ queryKey: qk.adminEmployees() })
      const prev=qc.getQueryData(qk.adminEmployees())
      qc.setQueryData(qk.adminEmployees(), (o:unknown)=>[...((o as unknown[])??[]), { id: Date.now(), ...v}] as never)
      return { prev }
    },
    onError:(_e,_v,c)=> c?.prev && qc.setQueryData(qk.adminEmployees(), c.prev as never),
    onSettled:()=> qc.invalidateQueries({ queryKey: qk.adminEmployees() }),
  })
}
export function useUpdateEmployee(){
  const qc=useQueryClient()
  return useMutation({
    mutationFn: (p:{id:number}&Record<string,unknown>)=> employeesApi.update(p.id, p as Parameters<typeof employeesApi.update>[1]) as never,
    onMutate: async(p:{id:number}&Record<string,unknown>)=>{
      const {id,...b}=p; await qc.cancelQueries({ queryKey: qk.adminEmployees() })
      const prev=qc.getQueryData(qk.adminEmployees())
      qc.setQueryData(qk.adminEmployees(), (o:unknown)=>((o as unknown[])??[]).map((x:unknown)=>(x as {id:number}).id===id?{...(x as object),...b} as never:x as never) as never)
      return { prev }
    },
    onError:(_e,_v,c)=> c?.prev && qc.setQueryData(qk.adminEmployees(), c.prev as never),
    onSettled:()=> qc.invalidateQueries({ queryKey: qk.adminEmployees() }),
  })
}
export function useDeleteEmployee(){
  const qc=useQueryClient()
  return useMutation({
    mutationFn: employeesApi.remove as never,
    onMutate: async(id:number)=>{
      await qc.cancelQueries({ queryKey: qk.adminEmployees() })
      const prev=qc.getQueryData(qk.adminEmployees())
      qc.setQueryData(qk.adminEmployees(), (o:unknown)=>((o as unknown[])??[]).filter((x:unknown)=>(x as {id:number}).id!==id) as never)
      return { prev }
    },
    onError:(_e,_v,c)=> c?.prev && qc.setQueryData(qk.adminEmployees(), c.prev as never),
    onSettled:()=> qc.invalidateQueries({ queryKey: qk.adminEmployees() }),
  })
}
