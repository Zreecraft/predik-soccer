<script setup>
import { computed } from 'vue'

const props = defineProps({
  home: { type: Object, default: () => ({ points: [], team: 'Home' }) },
  away: { type: Object, default: () => ({ points: [], team: 'Away' }) },
  summary: { type: Object, default: () => ({}) },
})

// Understat X: 0..1 menuju gawang (kanan). Y: 0..1 (bawah ke atas).
function mapX(x) {
  return 40 + x * 520
}
function mapY(y) {
  return 250 - y * 220
}

// Batasi jumlah titik agar tidak menumpuk, dan agar peta tetap terbaca.
const MAX_POINTS = 120
const homePoints = computed(() => (props.home.points || []).slice(0, MAX_POINTS))
const awayPoints = computed(() => (props.away.points || []).slice(0, MAX_POINTS))

// Gol: kuning dengan outline. Tembakan lain: abu transparan.
const GOAL_COLOR = '#e8c547'
const SHOT_COLOR = '#93a79b'

function isGoal(result) {
  return result === 'Goal'
}
function fillFor(result) {
  return isGoal(result) ? GOAL_COLOR : SHOT_COLOR
}
// Titik lebih transparan; gol tetap menonjol.
function fillOpacity(result) {
  return isGoal(result) ? 0.9 : 0.22
}
function strokeFor(result) {
  return isGoal(result) ? '#0f1a15' : 'none'
}
function radiusFor(xg) {
  return 3.5 + Math.min(8, Number(xg || 0) * 22)
}

const zone14Home = computed(() => props.summary.zone14_home ?? props.home.zone14_shots ?? 0)
const zone14Away = computed(() => props.summary.zone14_away ?? props.away.zone14_shots ?? 0)
const totalShots = computed(() => `${props.home.shots ?? 0} / ${props.away.shots ?? 0}`)
</script>

<template>
  <section>
    <h2 class="font-display text-[19px] font-bold" style="color: var(--ink)">Peta tembakan</h2>
    <p class="mt-1 text-[15px]" style="color: var(--mute)">
      Sebaran tembakan (xG). Ukuran titik = peluang gol.
    </p>

    <div class="relative mt-4 overflow-hidden rounded-block border" style="border-color: var(--line); background: var(--card)">
      <svg viewBox="0 0 600 270" class="block h-auto w-full">
        <!-- pitch -->
        <rect x="20" y="15" width="560" height="240" fill="none" stroke="#27392f" stroke-width="2" />
        <line x1="300" y1="15" x2="300" y2="255" stroke="#27392f" stroke-width="1.5" />
        <circle cx="300" cy="135" r="40" fill="none" stroke="#27392f" stroke-width="1.5" />
        <!-- boxes -->
        <rect x="20" y="70" width="70" height="130" fill="none" stroke="#27392f" stroke-width="1.5" />
        <rect x="510" y="70" width="70" height="130" fill="none" stroke="#27392f" stroke-width="1.5" />
        <rect x="20" y="100" width="28" height="70" fill="none" stroke="#27392f" stroke-width="1" />
        <rect x="552" y="100" width="28" height="70" fill="none" stroke="#27392f" stroke-width="1" />

        <!-- away shots (serangan ke kiri) -->
        <g>
          <circle
            v-for="(p, i) in awayPoints"
            :key="'a' + i"
            :cx="mapX(1 - p.x)"
            :cy="mapY(p.y)"
            :r="radiusFor(p.xg)"
            :fill="fillFor(p.result)"
            :fill-opacity="fillOpacity(p.result)"
            :stroke="strokeFor(p.result)"
            :stroke-width="isGoal(p.result) ? 1.5 : 0"
          />
        </g>

        <!-- home shots -->
        <g>
          <circle
            v-for="(p, i) in homePoints"
            :key="'h' + i"
            :cx="mapX(p.x)"
            :cy="mapY(p.y)"
            :r="radiusFor(p.xg)"
            :fill="fillFor(p.result)"
            :fill-opacity="fillOpacity(p.result)"
            :stroke="strokeFor(p.result)"
            :stroke-width="isGoal(p.result) ? 1.5 : 0"
          />
        </g>
      </svg>
    </div>

    <!-- Legenda satu baris -->
    <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px]" style="color: var(--mute)">
      <span class="inline-flex items-center gap-1.5">
        <span class="inline-block h-2.5 w-2.5 rounded-full" :style="{ background: GOAL_COLOR, outline: '1.5px solid #0f1a15' }" />
        Gol
      </span>
      <span class="inline-flex items-center gap-1.5">
        <span class="inline-block h-2.5 w-2.5 rounded-full" :style="{ background: SHOT_COLOR, opacity: 0.5 }" />
        Tembakan lain
      </span>
    </div>

    <!-- Ringkasan ringkas -->
    <div class="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 text-[13px]" style="color: var(--mute)">
      <span>
        Tembakan Zone 14:
        <span class="num font-semibold" style="color: var(--home)">{{ zone14Home }}</span>
        <span style="color: var(--mute)">vs</span>
        <span class="num font-semibold" style="color: var(--away)">{{ zone14Away }}</span>
      </span>
      <span v-if="summary.zone14_dominance">
        Dominasi: <span class="font-semibold" style="color: var(--ink)">{{ summary.zone14_dominance }}</span>
      </span>
      <span>
        Total tembakan: <span class="num font-semibold" style="color: var(--ink)">{{ totalShots }}</span>
      </span>
    </div>
  </section>
</template>
