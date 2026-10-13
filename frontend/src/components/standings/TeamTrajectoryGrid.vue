<script setup>
import { computed, ref } from 'vue'
import { abbrTeam, trajectoryColor } from '@/utils/format'

const props = defineProps({
  trajectory: { type: Object, default: () => ({}) },
  rows: { type: Array, default: () => [] },
  positionHistory: { type: Object, default: null },
})

// 'projection' -> jalur poin P1-P38 hasil Monte Carlo
// 'history'    -> riwayat posisi akhir per musim (2020 -> sekarang)
const source = ref('projection')

const VIEW_OPTIONS = [
  { id: 'projection', label: 'Proyeksi Musim Ini' },
  { id: 'history', label: 'Riwayat 2020 → kini' },
]

const clubs = computed(() =>
  [...props.rows].sort((a, b) => (a.projected_position ?? 99) - (b.projected_position ?? 99)),
)

const historySeasons = computed(() => props.positionHistory?.seasons || [])

function seriesFor(team) {
  if (source.value === 'projection') return props.trajectory[team] || []
  return props.positionHistory?.teams?.[team] || []
}

function colorFor(team) {
  const row = props.rows.find((r) => r.team === team)
  return trajectoryColor(row || {})
}

// Mini chart SVG: polyline + titik akhir. Y dibalik untuk mode riwayat (pos 1 = atas).
function buildChart(team) {
  const raw = seriesFor(team)
  const pts = raw.map((v, i) => ({ i, v })).filter((p) => p.v != null)
  if (pts.length < 2) return null
  const n = raw.length
  const vs = pts.map((p) => p.v)
  const min = Math.min(...vs)
  const max = Math.max(...vs)
  const span = Math.max(max - min, 1)
  const W = 120
  const H = 44
  const coords = pts.map((p) => ({
    x: 3 + (p.i / Math.max(n - 1, 1)) * (W - 6),
    y: 4 + ((p.v - min) / span) * (H - 10),
  }))
  return {
    width: W,
    height: H,
    polyline: coords.map((c) => `${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(' '),
    last: coords[coords.length - 1],
    firstV: vs[0],
    lastV: vs[vs.length - 1],
    min,
    max,
  }
}

function tooltipFor(team) {
  const raw = seriesFor(team)
  if (source.value === 'projection') {
    const last = raw[raw.length - 1]
    return `P1: ${raw[0] ?? '-'} → P38: ${last ?? '-'} poin (rerata simulasi)`
  }
  const seasons = historySeasons.value
  const parts = raw
    .map((v, i) => (v == null ? null : `${seasons[i] ?? i}: pos ${v}`))
    .filter(Boolean)
  return parts.length ? parts.join(' · ') : 'Belum ada riwayat'
}

function deltaLabel(team) {
  const c = buildChart(team)
  if (!c) return { text: '—', cls: 'text-slate-500' }
  if (source.value === 'projection') {
    return { text: `${c.lastV} pts`, cls: 'text-slate-300' }
  }
  // Riwayat: posisi lebih kecil = lebih baik
  const diff = c.firstV - c.lastV
  if (diff > 0) return { text: `▲ +${diff}`, cls: 'text-emerald-400' }
  if (diff < 0) return { text: `▼ ${diff}`, cls: 'text-rose-400' }
  return { text: '—', cls: 'text-slate-500' }
}
</script>

<template>
  <div class="panel p-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <div class="label-caps">Grafik Per Klub</div>
        <h3 class="mt-1 text-base font-semibold text-slate-100">Jalur Setiap Klub</h3>
      </div>
      <div class="flex rounded-lg border border-slate-700 bg-slate-900/50 p-1">
        <button
          v-for="opt in VIEW_OPTIONS"
          :key="opt.id"
          type="button"
          class="rounded-md px-3 py-1.5 text-xs font-semibold transition"
          :class="source === opt.id ? 'bg-sky-500/15 text-sky-400' : 'text-slate-400 hover:text-slate-200'"
          @click="source = opt.id"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <div
      v-if="source === 'history' && !historySeasons.length"
      class="mt-4 rounded-lg border border-slate-800 bg-slate-950/40 px-4 py-3 text-sm text-slate-500"
    >
      Riwayat posisi musiman belum tersedia untuk liga ini.
    </div>

    <div v-else class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
      <div
        v-for="club in clubs"
        :key="club.team"
        class="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
      >
        <div class="flex items-center gap-2">
          <img
            v-if="club.logo"
            :src="club.logo"
            :alt="club.team"
            class="h-6 w-6 shrink-0 object-contain"
            loading="lazy"
          >
          <div class="min-w-0 flex-1">
            <div class="truncate text-xs font-semibold text-slate-200">{{ club.team }}</div>
            <div class="num text-[10px] text-slate-500">
              <template v-if="source === 'projection'">
                Proyeksi #{{ club.projected_position }}
              </template>
              <template v-else>
                {{ abbrTeam(club.team) }} · riwayat posisi
              </template>
            </div>
          </div>
          <span class="num text-[11px] font-semibold" :class="deltaLabel(club.team).cls">
            {{ deltaLabel(club.team).text }}
          </span>
        </div>

        <svg
          v-if="buildChart(club.team)"
          :viewBox="`0 0 ${buildChart(club.team).width} ${buildChart(club.team).height}`"
          class="mt-2 h-11 w-full"
          preserveAspectRatio="none"
          :title="tooltipFor(club.team)"
        >
          <polyline
            :points="buildChart(club.team).polyline"
            fill="none"
            :stroke="colorFor(club.team)"
            stroke-width="1.6"
            stroke-linejoin="round"
            stroke-linecap="round"
            vector-effect="non-scaling-stroke"
          />
          <circle
            :cx="buildChart(club.team).last.x"
            :cy="buildChart(club.team).last.y"
            r="2"
            :fill="colorFor(club.team)"
          />
        </svg>
        <div v-else class="mt-2 flex h-11 items-center justify-center text-[10px] text-slate-600">
          Data belum cukup untuk grafik
        </div>
      </div>
    </div>
  </div>
</template>
