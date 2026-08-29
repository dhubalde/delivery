import { ref } from 'vue'

export function useConfirm() {
  const show = ref(false)
  const title = ref('')
  const message = ref('')
  const confirmText = ref('Eliminar')
  const cancelText = ref('Cancelar')
  const confirmColor = ref('error')
  let resolver: ((v: boolean) => void) | null = null

  function ask(opts: { title: string; message: string; confirmText?: string; confirmColor?: string }): Promise<boolean> {
    title.value = opts.title
    message.value = opts.message
    confirmText.value = opts.confirmText ?? 'Eliminar'
    confirmColor.value = opts.confirmColor ?? 'error'
    show.value = true
    return new Promise<boolean>((resolve) => { resolver = resolve })
  }

  function onConfirm() {
    show.value = false
    resolver?.(true)
    resolver = null
  }

  function onCancel() {
    show.value = false
    resolver?.(false)
    resolver = null
  }

  return { show, title, message, confirmText, cancelText, confirmColor, ask, onConfirm, onCancel }
}

export function toast(msg: string, type: 'error' | 'warning' | 'success' = 'error') {
  window.dispatchEvent(new CustomEvent('app:toast', { detail: { msg, type } }))
}
