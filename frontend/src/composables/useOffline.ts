import { onMounted, onUnmounted } from 'vue'
import { useUiStore } from '@/stores/ui.store'

export function useOffline() {
  const ui = useUiStore()
  const onLine = () => ui.setOffline(false)
  const offLine = () => ui.setOffline(true)
  onMounted(() => {
    window.addEventListener('online', onLine)
    window.addEventListener('offline', offLine)
    ui.setOffline(!navigator.onLine)
  })
  onUnmounted(() => {
    window.removeEventListener('online', onLine)
    window.removeEventListener('offline', offLine)
  })
  return ui
}
