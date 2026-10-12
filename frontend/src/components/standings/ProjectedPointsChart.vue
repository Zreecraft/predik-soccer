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
      borderColor: '#94A3B8',
      backgroundColor: '#94A3B8',
      borderWidth: 1.5,
      tension: 0.25,
      pointRadius: 3,
      pointHoverRadius: 6,
    },
    {
      label: 'Proyeksi Poin',
      data: props.rows.map((r) => r.projected_points),
      borderColor: '#38BDF8',
      backgroundColor: '#38BDF8',
      borderWidth: 2.5,
      tension: 0.25,
      pointRadius: 3,
      pointHoverRadius: 6,
    },
    {
      label: 'Ambang Degradasi',
      data: props.rows.map(() => props.kpi.relegation_line ?? null),
      borderColor: '#F43F5E',
      backgroundColor: '#F43F5E',
      borderWidth: 1.5,
      borderDash: [7, 5],
      pointRadius: 0,
      tension: 0,
    },
    {
      label: 'Ambang UCL',
      data: props.rows.map(() => props.kpi.ucl_threshold ?? null),
      borderColor: '#34D399',
      backgroundColor: '#34D399',
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
        color: '#94A3B8',
        boxWidth: 12,
        font: { family: 'JetBrains Mono', size: 10 },
      },
    },
    tooltip: {
      backgroundColor: '#111827',
      borderColor: '#1E293B',
      borderWidth: 1,
      titleColor: '#F8FAFC',
      bodyColor: '#94A3B8',
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
      title: { display: true, text: 'Poin', color: '#64748B', font: { size: 10 } },
      ticks: { color: '#64748B', font: { family: 'JetBrains Mono', size: 9 } },
      grid: { color: 'rgba(30,41,59,0.6)' },
    },
    x: {
      ticks: {
        color: '#64748B',
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
    <h3 class="mb-3 mt-1 text-base font-semibold text-slate-100">
      Poin Aktual vs Proyeksi — Grafik Garis
    </h3>
    <div class="h-[320px] w-full">
      <Line v-if="rows.length" :data="chartData" :options="chartOptions" />
      <div v-else class="flex h-full items-center justify-center text-sm text-slate-500">
        Data proyeksi belum tersedia
      </div>
    </div>
  </div>
</template>
