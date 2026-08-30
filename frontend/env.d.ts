/// <reference types="vite/client" />
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}
interface ImportMetaEnv {
  readonly VITE_API_BASE: string
  readonly VITE_WEATHER_KEY: string
  readonly VITE_WEATHER_CITY: string
  readonly VITE_WEATHER_LAT: string
  readonly VITE_WEATHER_LON: string
}
