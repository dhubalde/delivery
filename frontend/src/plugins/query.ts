import { VueQueryPlugin, type VueQueryPluginOptions } from '@tanstack/vue-query'

export const queryOptions: VueQueryPluginOptions = {
  queryClientConfig: {
    defaultOptions: {
      queries: { retry: 1, refetchOnWindowFocus: true },
      mutations: { retry: 0 },
    },
  },
}

export { VueQueryPlugin }
