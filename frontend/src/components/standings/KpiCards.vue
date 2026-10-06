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
          'text-amber-400': c.tone === 'amber',
          'text-sky-400': c.tone === 'sky',
          'text-rose-400': c.tone === 'rose',
          'text-emerald-400': c.tone === 'emerald',
        }"
      >
        {{ c.value }}
      </div>
      <div class="mt-1 text-xs text-slate-400">{{ c.sub }}</div>
    </div>
  </div>
</template>
