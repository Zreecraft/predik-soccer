<script setup>
import { computed } from 'vue'

const props = defineProps({
  home: { type: Object, default: () => ({ points: [], team: 'Home' }) },
  away: { type: Object, default: () => ({ points: [], team: 'Away' }) },
  summary: { type: Object, default: () => ({}) },
})

// Understat X: 0..1 menuju gawang (kanan). Y: 0..1 (bawah ke atas).
function mapX(x) {
  // pitch SVG: gawang kiri? Kita gambar serangan home ke kanan
  return 40 + x * 520
}
function mapY(y) {
  return 250 - y * 220
}

const homePoints = computed(() => (props.home.points || []).slice(0, 400))
const awayPoints = computed(() => (props.away.points || []).slice(0, 400))

function colorFor(result) {
  if (result === 'Goal') return '#10B981'
  if (result === 'SavedShot') return '#38BDF8'
  return '#64748B'
}

function radiusFor(xg) {
  return 4 + Math.min(10, Number(xg || 0) * 28)
}
</script>

<template>
  <div class="panel h-full p-5">
    <div class="mb-3 flex items-start justify-between gap-3">
      <div>
        <div class="label-caps">Peta Sebaran Tembakan</div>
        <h3 class="mt-1 text-base font-semibold text-slate-100">Shot Map Taktis (xG)</h3>
      </div>
      <div class="flex flex-wrap items-center justify-end gap-2 text-[10px] text-slate-400">
        <span class="inline-flex items-center gap-1">
          <span class="inline-block h-2 w-2 rounded-full bg-emerald-500" /> Gol
        </span>
        <span class="inline-flex items-center gap-1">
          <span class="inline-block h-2 w-2 rounded-full bg-sky-500" /> Saved
        </span>
        <span class="inline-flex items-center gap-1">
          <span class="inline-block h-2 w-2 rounded-full bg-slate-500" /> Miss/Block
        </span>
      </div>
    </div>

    <div class="relative overflow-hidden rounded-xl border border-emerald-900/40 bg-[#0B1F1A]">
      <svg viewBox="0 0 600 270" class="block h-auto w-full">
        <!-- pitch -->
        <rect x="20" y="15" width="560" height="240" fill="#0D2A22" stroke="#1E5C46" stroke-width="2" />
        <line x1="300" y1="15" x2="300" y2="255" stroke="#1E5C46" stroke-width="1.5" />
        <circle cx="300" cy="135" r="40" fill="none" stroke="#1E5C46" stroke-width="1.5" />
        <!-- boxes -->
        <rect x="20" y="70" width="70" height="130" fill="none" stroke="#1E5C46" stroke-width="1.5" />
        <rect x="510" y="70" width="70" height="130" fill="none" stroke="#1E5C46" stroke-width="1.5" />
        <rect x="20" y="100" width="28" height="70" fill="none" stroke="#1E5C46" stroke-width="1" />
        <rect x="552" y="100" width="28" height="70" fill="none" stroke="#1E5C46" stroke-width="1" />
        <!-- zone 14 highlight -->
        <rect x="430" y="85" width="70" height="100" fill="#38BDF8" fill-opacity="0.06" stroke="#38BDF8" stroke-opacity="0.15" stroke-dasharray="4 3" />
        <text x="465" y="80" text-anchor="middle" fill="#38BDF8" fill-opacity="0.55" font-size="9" font-family="monospace">ZONE 14</text>

        <!-- away shots (serangan ke kiri) -->
        <g>
          <g v-for="(p, i) in awayPoints" :key="'a' + i">
            <circle
              :cx="mapX(1 - p.x)"
              :cy="mapY(p.y)"
              :r="radiusFor(p.xg)"
              :fill="colorFor(p.result)"
              :fill-opacity="p.result === 'Goal' ? 0.35 : 0.2"
              :stroke="colorFor(p.result)"
              stroke-width="1.2"
            />
          </g>
        </g>

        <!-- home shots -->
        <g>
          <g v-for="(p, i) in homePoints" :key="'h' + i">
            <circle
              :cx="mapX(p.x)"
              :cy="mapY(p.y)"
              :r="radiusFor(p.xg)"
              :fill="colorFor(p.result)"
              :fill-opacity="p.result === 'Goal' ? 0.4 : 0.18"
              :stroke="colorFor(p.result)"
              stroke-width="1.2"
            />
          </g>
        </g>
      </svg>
    </div>

    <div class="mt-4 grid grid-cols-2 gap-3 text-center sm:grid-cols-4">
      <div class="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
        <div class="label-caps">Zone 14 Home</div>
        <div class="num mt-1 text-lg font-bold text-sky-400">{{ summary.zone14_home ?? home.zone14_shots ?? 0 }}</div>
      </div>
      <div class="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
        <div class="label-caps">Zone 14 Away</div>
        <div class="num mt-1 text-lg font-bold text-rose-400">{{ summary.zone14_away ?? away.zone14_shots ?? 0 }}</div>
      </div>
      <div class="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
        <div class="label-caps">Dominasi Zona</div>
        <div class="mt-1 truncate text-sm font-semibold text-slate-100">
          {{ summary.zone14_dominance || '—' }}
        </div>
      </div>
      <div class="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
        <div class="label-caps">Total Tembakan</div>
        <div class="num mt-1 text-lg font-bold text-slate-100">
          {{ home.shots ?? 0 }} <span class="text-slate-600">/</span> {{ away.shots ?? 0 }}
        </div>
      </div>
    </div>
  </div>
</template>
