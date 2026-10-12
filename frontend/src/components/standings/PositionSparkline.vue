<script setup>
import { computed } from 'vue'

const props = defineProps({
  values: { type: Array, default: () => [] },
})

const chart = computed(() => {
  const idx = props.values.map((v, i) => ({ i, v })).filter((p) => p.v != null)
  if (idx.length < 2) return null
  const n = props.values.length
  const vs = idx.map((p) => p.v)
  const min = Math.min(...vs)
  const max = Math.max(...vs)
  const span = Math.max(max - min, 1)
  const coords = idx.map((p) => ({
    x: 3 + (p.i / Math.max(n - 1, 1)) * 58,
    y: 3 + ((p.v - min) / span) * 18,
  }))
  return {
    polyline: coords.map((c) => `${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(' '),
    last: coords[coords.length - 1],
    firstV: vs[0],
    lastV: vs[vs.length - 1],
  }
})

const color = computed(() => {
  if (!chart.value) return '#475569'
  if (chart.value.lastV < chart.value.firstV) return '#34D399'
  if (chart.value.lastV > chart.value.firstV) return '#FB7185'
  return '#38BDF8'
})

const title = computed(() => `Riwayat posisi akhir: ${props.values.join(' → ')}`)
</script>

<template>
  <svg v-if="chart" viewBox="0 0 64 24" class="h-6 w-16 shrink-0" :title="title">
    <polyline
      :points="chart.polyline"
      fill="none"
      :stroke="color"
      stroke-width="1.5"
      stroke-linejoin="round"
      stroke-linecap="round"
    />
    <circle :cx="chart.last.x" :cy="chart.last.y" r="2.2" :fill="color" />
  </svg>
  <span v-else class="text-[10px] text-slate-600" :title="title">—</span>
</template>
