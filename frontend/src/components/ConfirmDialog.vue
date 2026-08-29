<template>
  <v-dialog :model-value="modelValue" max-width="440" @update:model-value="v=>emit('update:modelValue',v)">
    <v-card rounded="lg">
      <v-card-title class="d-flex align-center ga-2" style="font-family:Comfortaa">
        <v-icon :icon="icon" :color="confirmColor" />
        {{ title }}
      </v-card-title>
      <v-divider />
      <v-card-text class="pt-4" style="white-space:pre-wrap">{{ message }}</v-card-text>
      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn variant="text" @click="emit('cancel')">{{ cancelText }}</v-btn>
        <v-btn :color="confirmColor" variant="flat" @click="emit('confirm')">{{ confirmText }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup lang="ts">
withDefaults(defineProps<{
  modelValue: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  confirmColor?: string
  icon?: string
}>(), {
  confirmText: 'Eliminar',
  cancelText: 'Cancelar',
  confirmColor: 'error',
  icon: 'mdi-alert-circle-outline',
})
const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  confirm: []
  cancel: []
}>()
</script>
