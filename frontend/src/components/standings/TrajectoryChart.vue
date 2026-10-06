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
  trajectory: { type: Object, default: () => ({}) },
})

const palette = ['#38BDF8', '#F59E0B', '#F43F5E']
const names = computed(() => Object.keys(props.trajectory || {}))

const chartData = computed(() => {
  const sets = names.value.map((name, i) => ({
    label: name,
    data: props.trajectory[name] || [],
    borderColor: palette[i % palette.length],
    backgroundColor: palette[i % palette.length],
    tension: 0.25,
    pointRadius: 0,
    borderWidth: 2,
  }))
  return {
    labels: Array.from({ length: 38 }, (_, i) => `P${i + 1}`),
    datasets: sets,
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: {
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
    },
  },
  scales: {
    x: {
      ticks: {
        color: '#64748B',
        maxTicksLimit: 10,
        font: { family: 'JetBrains Mono', size: 9 },
      },
      grid: { color: 'rgba(30,41,59,0.6)' },
    },
    y: {
      ticks: { color: '#64748B', font: { family: 'JetBrains Mono', size: 9 } },
      grid: { color: 'rgba(30,41,59,0.6)' },
    },
  },
}
</script>

<template>
  <div class="panel h-full p-5">
    <div class="label-caps">Trajektori Poin</div>
    <h3 class="mb-3 mt-1 text-base font-semibold text-slate-100">Perburuan Gelar · Proyeksi hingga Pekan 38</h3>
    <div class="h-[280px] w-full">
      <Line v-if="names.length" :data="chartData" :options="chartOptions" />
      <div v-else class="flex h-full items-center justify-center text-sm text-slate-500">
        Data trajektori belum tersedia
      </div>
    </div>
  </div>
</template>
