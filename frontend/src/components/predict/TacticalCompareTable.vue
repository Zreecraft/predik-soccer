<script setup>
import { computed } from 'vue'

const props = defineProps({
  home: { type: Object, default: () => ({}) },
  away: { type: Object, default: () => ({}) },
  homeName: { type: String, default: 'Home' },
  awayName: { type: String, default: 'Away' },
})

const rows = computed(() => [
  { key: 'xg', label: 'Expected Goals', home: props.home.xg, away: props.away.xg, higherBetter: true },
  { key: 'conversion_pct', label: 'Konversi Peluang', home: props.home.conversion_pct, away: props.away.conversion_pct, suffix: '%', higherBetter: true },
  { key: 'duels_pct', label: 'Rebutan Bola', home: props.home.duels_pct, away: props.away.duels_pct, suffix: '%', higherBetter: true },
  { key: 'ppda', label: 'PPDA', home: props.home.ppda, away: props.away.ppda, higherBetter: false },
  { key: 'possession_pct', label: 'Penguasaan Bola', home: props.home.possession_pct, away: props.away.possession_pct, suffix: '%', higherBetter: true },
  { key: 'win_rate', label: 'Win Rate', home: props.home.win_rate, away: props.away.win_rate, suffix: '%', higherBetter: true },
])

function winner(row) {
  const h = Number(row.home)
  const a = Number(row.away)
  if (!Number.isFinite(h) || !Number.isFinite(a) || h === a) return null
  if (row.higherBetter) return h > a ? 'home' : 'away'
  return h < a ? 'home' : 'away'
}

function barPct(row, side) {
  const h = Number(row.home) || 0
  const a = Number(row.away) || 0
  const total = h + a
  if (!total) return 50
  const val = side === 'home' ? h : a
  return Math.round((val / total) * 100)
}
</script>

<template>
  <div class="panel h-full p-5">
    <div class="mb-4 flex items-center justify-between">
      <div>
        <div class="label-caps">Komparasi Taktis</div>
        <h3 class="mt-1 text-base font-semibold text-slate-100">Model Statistik & Form</h3>
      </div>
    </div>

    <div class="mb-4 grid grid-cols-2 gap-3 text-center">
      <div class="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
        <div class="truncate text-sm font-semibold text-sky-400">{{ homeName }}</div>
      </div>
      <div class="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
        <div class="truncate text-sm font-semibold text-rose-400">{{ awayName }}</div>
      </div>
    </div>

    <div class="space-y-3">
      <div v-for="row in rows" :key="row.key">
        <div class="mb-1 flex items-center justify-between text-xs">
          <span
            class="num font-bold"
            :class="winner(row) === 'home' ? 'text-sky-400' : 'text-slate-400'"
          >
            {{ row.home ?? '—' }}{{ row.suffix || '' }}
          </span>
          <span class="text-slate-400">{{ row.label }}</span>
          <span
            class="num font-bold"
            :class="winner(row) === 'away' ? 'text-rose-400' : 'text-slate-400'"
          >
            {{ row.away ?? '—' }}{{ row.suffix || '' }}
          </span>
        </div>
        <div class="flex h-1.5 gap-0.5 overflow-hidden rounded-full bg-slate-800">
          <div
            class="h-full rounded-l-full transition-all"
            :class="winner(row) === 'home' ? 'bg-sky-500' : 'bg-sky-500/45'"
            :style="{ width: barPct(row, 'home') + '%' }"
          />
          <div
            class="h-full rounded-r-full transition-all"
            :class="winner(row) === 'away' ? 'bg-rose-500' : 'bg-rose-500/45'"
            :style="{ width: barPct(row, 'away') + '%' }"
          />
        </div>
      </div>
    </div>
  </div>
</template>
