import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import type { MaybeRef } from 'vue'
import { printingApi } from '@/api/panel/printing.api'
import { qk } from '@/queries/keys'

export function usePendingPrintJobs(enabled: MaybeRef<boolean> = true) {
  return useQuery({
    queryKey: qk.printJobsPending(),
    queryFn: () => printingApi.pending(),
    // The comandera station is a browser tab: it polls for pending tickets
    // instead of receiving push events.
    refetchInterval: 15000,
    enabled,
  })
}

export function useMarkPrinted() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => printingApi.markPrinted(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.printJobsPending() }),
  })
}
