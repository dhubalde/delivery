<template>
  <v-card class="mb-4" elevation="1">
    <v-card-title class="d-flex align-center justify-space-between text-subtitle-2">
      <span><v-icon size="small" class="mr-1">mdi-weather-cloudy</v-icon>Pronóstico 5 días</span>
      <v-chip v-if="isDemo" size="x-small" color="secondary" variant="tonal">demo</v-chip>
      <v-chip v-else size="x-small" color="primary" variant="tonal">live</v-chip>
    </v-card-title>
    <v-divider />
    <v-card-text class="pa-2">
      <v-row dense no-gutters class="ma-0 pa-0 mx-0 px-0" style="display:flex;width:100%;margin:0;padding:0;box-sizing:border-box">
        <v-col v-for="d in days" :key="d.date" cols="auto" class="text-center flex-grow-1 pa-1 ma-0" style="flex:1 1 0;min-width:0;max-width:none;padding:4px;margin:0;box-sizing:border-box">
          <v-card variant="tonal" class="pa-2 ma-0" style="width:100%;height:100%;margin:0;box-sizing:border-box">
            <div class="text-caption font-weight-bold">{{ d.date }}</div>
            <v-icon :icon="d.icon" size="28" color="primary" class="my-1" />
            <div class="text-caption">{{ d.condition }}</div>
            <div class="text-caption"><span class="font-weight-bold">{{ d.tempMax }}°</span> / {{ d.tempMin }}°</div>
          </v-card>
        </v-col>
      </v-row>
      <div v-if="isLoading" class="d-flex justify-center mt-2"><v-progress-circular indeterminate size="20" /></div>
    </v-card-text>
  </v-card>
</template>
<script setup lang="ts">
import { useForecast } from '@/composables/useForecast'
const { days, isDemo, isLoading } = useForecast()
</script>
