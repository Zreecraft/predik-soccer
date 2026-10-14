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
  history: { type: Array, default: () => [] },
  selectedSeason: { type: Number, default: null },
})

const labels = computed(() => props.history.map((h) => h.label))

const pointRadius = computed(() =>
  props.history.map((h) => {
    if (props.selectedSeason != null && h.season === props.selectedSeason) return 7
    return h.in_progress ? 5 : 3
  }),
)

const pointStyles = computed(() =>
  props.history.map((h) => (h.in_progress ? 'rectRot' : 'circle')),
)

const chartData = computed(() => ({
  labels: labels.value,
  datasets: [
    {
      label: 'Poin',
      data: props.history.map((h) => h.points),
      borderColor: '#6aa0ff',
      backgroundColor: '#6aa0ff',
      tension: 0.3,
      borderWidth: 2,
      pointRadius: pointRadius.value,
      pointStyle: pointStyles.value,
      pointHoverRadius: 7,
      yAxisID: 'y',
    },
    {
      label: 'Posisi',
      data: props.history.map((h) => h.position),
      borderColor: '#5d6f65',
      backgroundColor: '#5d6f65',
      tension: 0.3,
      borderWidth: 2,
      borderDash: [6, 4],
      pointRadius: pointRadius.value,
      pointStyle: pointStyles.value,
      pointHoverRadius: 7,
      yAxisID: 'y1',
    },
  ],
}))

const maxPos = computed(() => Math.max(...props.history.map((h) => h.position), 10))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: {
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
        label(ctx) {
          if (ctx.dataset.label === 'Posisi') return ` Posisi ke-${ctx.parsed.y}`
          const h = props.history[ctx.dataIndex]
          const suffix = h?.in_progress ? ' (berlangsung)' : ''
          return ` ${ctx.parsed.y} poin${suffix}`
        },
      },
    },
  },
  scales: {
    y: {
      position: 'left',
      beginAtZero: true,
      title: { display: true, text: 'Poin', color: '#728578', font: { size: 10 } },
      ticks: { color: '#728578', font: { family: 'JetBrains Mono', size: 9 } },
      grid: { color: 'rgba(30,41,59,0.6)' },
    },
    y1: {
      position: 'right',
      reverse: true,
      min: 1,
      max: maxPos.value,
      title: {
        display: true,
        text: 'Posisi (makin atas = makin baik)',
        color: '#728578',
        font: { size: 10 },
      },
      ticks: { color: '#728578', stepSize: 1, font: { family: 'JetBrains Mono', size: 9 } },
      grid: { display: false },
    },
    x: {
      ticks: { color: '#728578', font: { family: 'JetBrains Mono', size: 9 } },
      grid: { color: 'rgba(30,41,59,0.4)' },
    },
  },
}))
</script>

<template>
  <div class="h-[300px] w-full">
    <Line v-if="history.length" :data="chartData" :options="chartOptions" />
    <div v-else class="flex h-full items-center justify-center text-sm text-mute">
      Belum ada data musiman (butuh data historis 2020+)
    </div>
  </div>
</template>
