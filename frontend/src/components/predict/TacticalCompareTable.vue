<script setup>
import { computed, ref } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  home: { type: Object, default: () => ({}) },
  away: { type: Object, default: () => ({}) },
  homeName: { type: String, default: 'Home' },
  awayName: { type: String, default: 'Away' },
  homeSource: { type: String, default: '' },
  awaySource: { type: String, default: '' },
})

// Tim tanpa data xG historis (sumber elo/manual/default) -> teks prioritas Elo
const anyNoXg = computed(
  () => props.homeSource !== 'xg+elo' || props.awaySource !== 'xg+elo',
)

const rows = computed(() => [
  { key: 'xg', label: 'Expected Goals', home: props.home.xg, away: props.away.xg, higherBetter: true },
  { key: 'conversion_pct', label: 'Konversi peluang', home: props.home.conversion_pct, away: props.away.conversion_pct, suffix: '%', higherBetter: true },
  { key: 'duels_pct', label: 'Rebutan bola', home: props.home.duels_pct, away: props.away.duels_pct, suffix: '%', higherBetter: true },
  { key: 'ppda', label: 'PPDA', home: props.home.ppda, away: props.away.ppda, higherBetter: false },
  { key: 'possession_pct', label: 'Penguasaan bola', home: props.home.possession_pct, away: props.away.possession_pct, suffix: '%', higherBetter: true },
  { key: 'win_rate', label: 'Win rate', home: props.home.win_rate, away: props.away.win_rate, suffix: '%', higherBetter: true },
])

// 3 statistik paling berpengaruh pada prediksi: xG, konversi peluang, PPDA.
const KEY_KEYS = ['xg', 'conversion_pct', 'ppda']
const keyRows = computed(() => rows.value.filter((r) => KEY_KEYS.includes(r.key)))
const otherRows = computed(() => rows.value.filter((r) => !KEY_KEYS.includes(r.key)))

const showAll = ref(false)

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

const fmt = (v, suffix) => (v == null || v === '' ? '—' : `${v}${suffix || ''}`)
</script>

<template>
  <section>
    <h2 class="font-display text-[19px] font-bold" style="color: var(--ink)">
      Kenapa model memprediksi ini?
    </h2>
    <p class="mt-1 text-[15px]" style="color: var(--mute)">
      <template v-if="anyNoXg">Prediksi berbasis rating Elo klub.</template>
      <template v-else>Tiga statistik yang paling berpengaruh pada prediksi laga ini.</template>
    </p>

    <div class="mt-4 space-y-4">
      <div v-for="row in keyRows" :key="row.key">
        <div class="mb-1.5 flex items-baseline justify-between gap-3">
          <span class="num text-[15px] font-semibold" :style="{ color: winner(row) === 'home' ? 'var(--home)' : 'var(--mute)' }">
            {{ fmt(row.home, row.suffix) }}
          </span>
          <span class="text-[13px]" style="color: var(--mute)">{{ row.label }}</span>
          <span class="num text-[15px] font-semibold" :style="{ color: winner(row) === 'away' ? 'var(--away)' : 'var(--mute)' }">
            {{ fmt(row.away, row.suffix) }}
          </span>
        </div>
        <div class="flex h-2 gap-0.5 overflow-hidden rounded-full" style="background: var(--line)">
          <div
            class="h-full rounded-l-full transition-all"
            :style="{ width: barPct(row, 'home') + '%', background: 'var(--home)', opacity: winner(row) === 'home' ? 1 : 0.4 }"
          />
          <div
            class="h-full rounded-r-full transition-all"
            :style="{ width: barPct(row, 'away') + '%', background: 'var(--away)', opacity: winner(row) === 'away' ? 1 : 0.4 }"
          />
        </div>
      </div>
    </div>

    <!-- Accordion: statistik lain -->
    <button
      type="button"
      class="mt-4 inline-flex items-center gap-1.5 text-[15px] font-medium"
      style="color: var(--mute)"
      :aria-expanded="showAll"
      @click="showAll = !showAll"
    >
      Statistik lengkap
      <ChevronDown :size="16" class="transition-transform" :class="showAll ? 'rotate-180' : ''" />
    </button>

    <div v-show="showAll" class="mt-3 space-y-4">
      <div v-for="row in otherRows" :key="row.key">
        <div class="mb-1.5 flex items-baseline justify-between gap-3">
          <span class="num text-[15px] font-semibold" :style="{ color: winner(row) === 'home' ? 'var(--home)' : 'var(--mute)' }">
            {{ fmt(row.home, row.suffix) }}
          </span>
          <span class="text-[13px]" style="color: var(--mute)">{{ row.label }}</span>
          <span class="num text-[15px] font-semibold" :style="{ color: winner(row) === 'away' ? 'var(--away)' : 'var(--mute)' }">
            {{ fmt(row.away, row.suffix) }}
          </span>
        </div>
        <div class="flex h-2 gap-0.5 overflow-hidden rounded-full" style="background: var(--line)">
          <div
            class="h-full rounded-l-full transition-all"
            :style="{ width: barPct(row, 'home') + '%', background: 'var(--home)', opacity: winner(row) === 'home' ? 1 : 0.4 }"
          />
          <div
            class="h-full rounded-r-full transition-all"
            :style="{ width: barPct(row, 'away') + '%', background: 'var(--away)', opacity: winner(row) === 'away' ? 1 : 0.4 }"
          />
        </div>
      </div>
    </div>
  </section>
</template>
