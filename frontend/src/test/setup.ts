// jsdom lacks the browser APIs Vuetify's overlay/resize composables touch on
// mount. Polyfill them once for every component test.
import { vi } from 'vitest'

if (!('ResizeObserver' in globalThis)) {
  class ResizeObserverStub {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }
  ;(globalThis as Record<string, unknown>).ResizeObserver = ResizeObserverStub
}

if (!('visualViewport' in window)) {
  Object.defineProperty(window, 'visualViewport', {
    configurable: true,
    value: { width: 1024, height: 768, addEventListener: vi.fn(), removeEventListener: vi.fn() },
  })
}
