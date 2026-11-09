import { defineStore } from 'pinia'

/** sessionStorage flag: operator enters the storefront from the kanban to register a phone order. */
export const operatorActiveKey = 'operator:manual'

/** Payment methods offered to the operator at manual checkout (cash expected; transfer recorded as pending). */
export function coordinatorMethods(): string[] {
  return ['EFECTIVO', 'TRANSFER']
}

/** Order body `source` value: MANUAL only while operator mode is active. */
export function isManualBodySource(manual: boolean): 'MANUAL' | 'WEB' {
  return manual ? 'MANUAL' : 'WEB'
}

export const useOperatorStore = defineStore('operator', {
  state: () => ({
    active: false,
  }),
  actions: {
    enter() {
      this.active = true
      sessionStorage.setItem(operatorActiveKey, '1')
    },
    exit() {
      this.active = false
      sessionStorage.removeItem(operatorActiveKey)
    },
    hydrate() {
      this.active = sessionStorage.getItem(operatorActiveKey) === '1'
    },
  },
})
