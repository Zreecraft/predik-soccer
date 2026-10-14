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

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const props = defineProps({
  rows: { type: Array, default: () => [] },
  kpi: { type: Object, default: () => ({}) },
})

const chartData = computed(() => ({
  labels: props.rows.map((r) => r.team),
  datasets: [
    {
      label: 'Poin Aktual',
      data: props.rows.map((r) => r.PTS),
      borderColor: '#93a79b',
      backgroundColor: '#93a79b',
      borderWidth: 1.5,
      tension: 0.25,
      pointRadius: 3,
      pointHoverRadius: 6,
    },
    {
      label: 'Proyeksi Poin',
      data: props.rows.map((r) => r.projected_points),
      borderColor: '#6aa0ff',
      backgroundColor: '#6aa0ff',
      borderWidth: 2.5,
      tension: 0.25,
      pointRadius: 3,
      pointHoverRadius: 6,
    },
    {
      label: 'Ambang Degradasi',
      data: props.rows.map(() => props.kpi.relegation_line ?? null),
      borderColor: '#ff8a73',
      backgroundColor: '#ff8a73',
      borderWidth: 1.5,
      borderDash: [7, 5],
      pointRadius: 0,
      tension: 0,
    },
    {
      label: 'Ambang UCL',
      data: props.rows.map(() => props.kpi.ucl_threshold ?? null),
      borderColor: '#52c58a',
      backgroundColor: '#52c58a',
      borderWidth: 1.5,
      borderDash: [7, 5],
      pointRadius: 0,
      tension: 0,
    },
  ],
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
        boxWidth: 12,
        font: { family: 'JetBrains Mono', size: 10 },
      },
    },
    tooltip: {
      backgroundColor: '#111827',
      borderColor: '#16241d',
      borderWidth: 1,
      titleColor: '#F8FAFC',
      bodyColor: '#93a79b',
      callbacks: {
        footer(items) {
          const row = props.rows[items[0]?.dataIndex]
          if (!row) return ''
          const bits = [`Proyeksi ke-${row.projected_position}`]
          if (row.status === 'DEGRADASI') bits.push('DEGRADASI')
          if (row.promoted) bits.push('PROMOSI')
          return bits.join(' · ')
        },
      },
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      title: { display: true, text: 'Poin', color: '#728578', font: { size: 10 } },
      ticks: { color: '#728578', font: { family: 'JetBrains Mono', size: 9 } },
      grid: { color: 'rgba(30,41,59,0.6)' },
    },
    x: {
      ticks: {
        color: '#728578',
        autoSkip: false,
        maxRotation: 60,
        minRotation: 45,
        font: { family: 'JetBrains Mono', size: 9 },
      },
      grid: { color: 'rgba(30,41,59,0.4)' },
    },
  },
}))
</script>

<template>
  <div class="panel p-5">
    <div class="label-caps">Semua Klub</div>
    <h3 class="mb-3 mt-1 text-base font-semibold text-ink">
      Poin Aktual vs Proyeksi — Grafik Garis
    </h3>
    <div class="h-[320px] w-full">
      <Line v-if="rows.length" :data="chartData" :options="chartOptions" />
      <div v-else class="flex h-full items-center justify-center text-sm text-mute">
        Data proyeksi belum tersedia
      </div>
    </div>
  </div>
</template>
