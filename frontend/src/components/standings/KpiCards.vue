<script setup>
import { computed } from 'vue'

const props = defineProps({
  kpi: { type: Object, default: () => ({}) },
})

const cards = computed(() => [
  {
    title: 'Ambang Batas Juara',
    value: `${props.kpi.title_threshold ?? '—'} Poin`,
    sub: 'Rerata poin juara simulasi musim',
    tone: 'amber',
  },
  {
    title: 'Garis Batas Top 4 UCL',
    value: `${props.kpi.ucl_threshold ?? '—'} Poin`,
    sub: 'Ambang zona Champions League',
    tone: 'sky',
  },
  {
    title: 'Garis Aman Degradasi',
    value: `${props.kpi.relegation_line ?? '—'} Poin`,
    sub: 'Ambang bertahan dari degradasi',
    tone: 'rose',
  },
  {
    title: 'Dispersi Simulasi / RMSE',
    value: `±${props.kpi.rmse_pct ?? '—'}%`,
    sub: 'Sebaran proyeksi antar-simulasi',
    tone: 'emerald',
  },
])
</script>

<template>
  <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
    <div
      v-for="c in cards"
      :key="c.title"
      class="panel p-4"
    >
      <div class="label-caps">{{ c.title }}</div>
      <div
        class="num mt-2 text-2xl font-bold"
        :class="{
          'text-draw': c.tone === 'amber',
          'text-home': c.tone === 'sky',
          'text-bad': c.tone === 'rose',
          'text-ok': c.tone === 'emerald',
        }"
      >
        {{ c.value }}
      </div>
      <div class="mt-1 text-xs text-mute">{{ c.sub }}</div>
    </div>
  </div>
</template>
