<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { abbrTeam, trajectoryColor } from '@/utils/format'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const props = defineProps({
  trajectory: { type: Object, default: () => ({}) },
  rows: { type: Array, default: () => [] },
})

// Urut klub sesuai posisi proyeksi agar legend terbaca seperti klasemen
const teams = computed(() => {
  const byPos = [...props.rows].sort((a, b) => (a.projected_position ?? 99) - (b.projected_position ?? 99))
  const ordered = byPos.map((r) => r.team).filter((t) => props.trajectory[t])
  const rest = Object.keys(props.trajectory).filter((t) => !ordered.includes(t))
  return [...ordered, ...rest]
})

const colorOf = computed(() => {
  const map = {}
  for (const r of props.rows) map[r.team] = trajectoryColor(r)
  return map
})

const chartData = computed(() => ({
  labels: Array.from({ length: 38 }, (_, i) => `P${i + 1}`),
  datasets: teams.value.map((name) => {
    const c = colorOf.value[name] || '#93a79b'
    return {
      label: abbrTeam(name),
      fullName: name,
      data: props.trajectory[name] || [],
      borderColor: c,
      backgroundColor: c,
      tension: 0.25,
      pointRadius: 0,
      pointHoverRadius: 4,
      borderWidth: 2,
    }
  }),
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: '#93a79b',
        usePointStyle: true,
        pointStyle: 'line',
        boxWidth: 14,
        boxHeight: 8,
        padding: 8,
        font: { family: 'JetBrains Mono', size: 9 },
      },
    },
    tooltip: {
      backgroundColor: '#111827',
      borderColor: '#16241d',
      borderWidth: 1,
      titleColor: '#F8FAFC',
      bodyColor: '#93a79b',
      callbacks: {
        title(items) {
          return items[0]?.dataset?.fullName || items[0]?.dataset?.label || ''
        },
      },
    },
  },
  scales: {
    x: {
      ticks: {
        color: '#728578',
        maxTicksLimit: 10,
        font: { family: 'JetBrains Mono', size: 9 },
      },
      grid: { color: 'rgba(30,41,59,0.6)' },
    },
    y: {
      ticks: { color: '#728578', font: { family: 'JetBrains Mono', size: 9 } },
      grid: { color: 'rgba(30,41,59,0.6)' },
    },
  },
}))
</script>

<template>
  <div class="panel h-full p-5">
    <div class="label-caps">Trajektori Poin</div>
    <h3 class="mb-1 mt-1 text-base font-semibold text-ink">
      Jalur Poin Semua Klub · Proyeksi hingga Pekan 38
    </h3>
    <p class="mb-3 text-xs text-mute">
      Klik nama klub di legend untuk menampilkan/menyembunyikan garisnya.
    </p>
    <div class="h-[360px] w-full">
      <Line v-if="teams.length" :data="chartData" :options="chartOptions" />
      <div v-else class="flex h-full items-center justify-center text-sm text-mute">
        Data trajektori belum tersedia
      </div>
    </div>
  </div>
</template>
