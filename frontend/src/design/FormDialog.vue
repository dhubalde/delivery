<template>
  <v-dialog
    :model-value="modelValue"
    :max-width="maxWidth"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title :style="{ fontFamily: titleFont }">{{ title }}</v-card-title>
      <v-card-text>
        <slot />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" density="compact" @click="close">{{ cancelLabel }}</v-btn>
        <v-btn
          v-if="!hideSubmit"
          color="primary"
          density="compact"
          :loading="loading"
          :disabled="submitDisabled"
          @click="emit('submit')"
        >
          {{ submitLabel }}
        </v-btn>
        <slot name="actions" />
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { titleFont } from '@/design/tokens'

/**
 * Standard dialog for create/edit forms: title, body, compact Cancel/Submit.
 * Info dialogs (sessions, reset token) use `hide-submit` and the `actions` slot.
 */
withDefaults(
  defineProps<{
    modelValue: boolean
    title: string
    submitLabel?: string
    cancelLabel?: string
    loading?: boolean
    submitDisabled?: boolean
    hideSubmit?: boolean
    maxWidth?: number | string
  }>(),
  {
    submitLabel: 'Guardar',
    cancelLabel: 'Cancelar',
    loading: false,
    submitDisabled: false,
    hideSubmit: false,
    maxWidth: 520,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  submit: []
  close: []
}>()

function close() {
  emit('update:modelValue', false)
  emit('close')
}
</script>
