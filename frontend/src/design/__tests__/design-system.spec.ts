import { describe, it, expect, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import { h } from 'vue'
import { componentDefaults, statusColors, themes } from '@/design/tokens'
import PageHeader from '@/design/PageHeader.vue'
import StatusChip from '@/design/StatusChip.vue'
import FormDialog from '@/design/FormDialog.vue'

const vuetify = createVuetify()
const global = { plugins: [vuetify] }

afterEach(() => {
  document.body.innerHTML = ''
})

describe('design tokens', () => {
  it('keeps every form control dense so forms fit without scrolling', () => {
    for (const name of ['VTextField', 'VTextarea', 'VSelect', 'VAutocomplete', 'VCombobox', 'VFileInput', 'VSwitch', 'VCheckbox']) {
      const defaults = componentDefaults[name as keyof typeof componentDefaults] as { density: string; hideDetails: string }
      expect(defaults.density).toBe('compact')
      // 'auto' is what removes the reserved hint/error row when there is no message.
      expect(defaults.hideDetails).toBe('auto')
    }
  })

  it('keeps buttons compact and status green', () => {
    expect(componentDefaults.VBtn.density).toBe('compact')
    expect(statusColors.positive).toBe('success')
    expect(statusColors.neutral).toBe('default')
  })

  it('exposes both themes with a surface color', () => {
    expect(themes.light.surface).toBeTruthy()
    expect(themes.dark.surface).toBeTruthy()
  })
})

describe('PageHeader', () => {
  it('renders title, subtitle and the action slot', () => {
    const wrapper = mount(PageHeader, {
      props: { title: 'Empresas cliente', subtitle: 'Buscá y filtrá' },
      slots: { default: '<button class="action">Onboarding</button>' },
      global,
    })
    expect(wrapper.text()).toContain('Empresas cliente')
    expect(wrapper.text()).toContain('Buscá y filtrá')
    expect(wrapper.find('.action').exists()).toBe(true)
  })
})

describe('StatusChip', () => {
  it('renders a positive state in green', () => {
    const wrapper = mount(StatusChip, {
      props: { value: true, positive: 'Activa', negative: 'Inactiva' },
      global,
    })
    expect(wrapper.text()).toBe('Activa')
    expect(wrapper.classes().join(' ')).toContain('text-success')
  })

  it('renders a negative state neutral', () => {
    const wrapper = mount(StatusChip, {
      props: { value: false, positive: 'Activa', negative: 'Inactiva' },
      global,
    })
    expect(wrapper.text()).toBe('Inactiva')
    expect(wrapper.classes().join(' ')).not.toContain('text-success')
  })

  it('matches a string state against the positive label', () => {
    const wrapper = mount(StatusChip, {
      props: { value: 'Abierto', positive: 'Abierto', negative: 'Cerrado' },
      global,
    })
    expect(wrapper.text()).toBe('Abierto')
    expect(wrapper.classes().join(' ')).toContain('text-success')
  })
})

describe('FormDialog', () => {
  it('renders the form inside and emits submit / close with the compact actions', async () => {
    const wrapper = mount(FormDialog, {
      props: { modelValue: true, title: 'Nueva categoría', submitLabel: 'Crear' },
      slots: { default: '<input data-test="field" />' },
      global,
    })
    await flushPromises()
    expect(document.body.textContent).toContain('Nueva categoría')
    expect(document.querySelector('[data-test="field"]')).toBeTruthy()

    const buttons = Array.from(document.querySelectorAll('button'))
    buttons.find((b) => b.textContent?.includes('Crear'))!.click()
    await flushPromises()
    expect(wrapper.emitted('submit')).toHaveLength(1)

    buttons.find((b) => b.textContent?.includes('Cancelar'))!.click()
    await flushPromises()
    expect(wrapper.emitted('close')).toHaveLength(1)
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([false])
  })

  it('hides the submit button for info dialogs', async () => {
    mount(FormDialog, {
      props: { modelValue: true, title: 'Sesiones', hideSubmit: true },
      slots: { actions: h('button', { class: 'extra' }, 'Revocar todas') },
      global,
    })
    await flushPromises()
    const labels = Array.from(document.querySelectorAll('button')).map((b) => b.textContent?.trim())
    expect(labels).toContain('Revocar todas')
    expect(labels).not.toContain('Guardar')
  })
})
