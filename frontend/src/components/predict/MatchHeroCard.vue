<script setup>
import { computed } from 'vue'
import PlayerCutout from '@/components/shared/PlayerCutout.vue'
import WinProbabilityBar from '@/components/shared/WinProbabilityBar.vue'
import FormBadges from '@/components/shared/FormBadges.vue'
import { Shield, MapPin, UserRound, Swords } from 'lucide-vue-next'

const props = defineProps({
  data: { type: Object, required: true },
})

const home = computed(() => props.data.home_team || {})
const away = computed(() => props.data.away_team || {})
const projection = computed(() => props.data.projection || {})
const probs = computed(() => props.data.probabilities || {})
const analytics = computed(() => props.data.analytics || {})
const meta = computed(() => props.data.meta || {})
const tactical = computed(() => props.data.tactical || {})
const gap = computed(() => props.data.strength_gap || {})

const fmtStr = (v) => (v != null ? Number(v).toFixed(1) : '—')
const gapTone = computed(() => {
  const g = gap.value.value ?? 0
  if (g >= 15) return 'border-rose-500/40 bg-rose-500/10 text-rose-300'
  if (g >= 8) return 'border-amber-500/40 bg-amber-500/10 text-amber-300'
  return 'border-slate-600/60 bg-slate-800/60 text-slate-300'
})
const gapLabel = computed(() => {
  const g = gap.value.value ?? 0
  if (g >= 15) return 'Jarak jauh'
  if (g >= 8) return 'Unggul'
  if (g >= 3) return 'Sedikit unggul'
  return 'Seimbang'
})
</script>

<template>
  <section class="panel overflow-hidden">
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-3">
      <div class="flex flex-wrap items-center gap-4 text-xs text-slate-400">
        <span class="inline-flex items-center gap-1.5">
          <MapPin :size="13" class="text-slate-500" />
          {{ meta.stadium || 'Stadion' }}
        </span>
        <span class="inline-flex items-center gap-1.5">
          <UserRound :size="13" class="text-slate-500" />
          {{ meta.referee || 'Wasit' }}
        </span>
        <span class="inline-flex items-center gap-1.5">
          <Shield :size="13" class="text-slate-500" />
          {{ data.match }}
        </span>
      </div>
      <div class="chip border-amber-500/30 bg-amber-500/10 text-amber-400">
        <span class="num font-bold">{{ projection.confidence_pct ?? '—' }}%</span>
        <span class="ml-1 text-amber-500/80">Keyakinan Model</span>
      </div>
    </div>

    <div class="grid grid-cols-1 items-center gap-4 px-4 py-6 md:grid-cols-[1fr_auto_1fr] md:px-6">
      <!-- Home -->
      <div class="relative flex items-center gap-4 overflow-hidden rounded-xl border border-slate-800/80 bg-slate-900/40 p-4">
        <div class="pointer-events-none absolute -right-4 top-1/2 -translate-y-1/2 opacity-40">
          <PlayerCutout
            :image="home.star_player?.image"
            :name="home.star_player?.player_name || home.name"
            side="left"
            size="lg"
          />
        </div>
        <div class="relative z-10 flex min-w-0 items-center gap-4">
          <img
            v-if="home.logo"
            :src="home.logo"
            :alt="home.name"
            class="h-14 w-14 rounded-xl border border-slate-700/60 bg-slate-950/60 object-contain p-1"
          />
          <div class="min-w-0">
            <div class="label-caps">Home</div>
            <div class="truncate text-xl font-bold text-slate-50">{{ home.name }}</div>
            <div class="mt-1 text-xs text-slate-400">
              <span class="text-slate-500">Pelatih</span> {{ home.coach || '—' }}
              <span class="mx-1 text-slate-600">·</span>
              <span class="num text-slate-300">{{ home.formation || '—' }}</span>
            </div>
            <div class="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-400">
              <span
                class="num inline-flex items-center gap-1 rounded-md border border-sky-500/30 bg-sky-500/10 px-1.5 py-0.5 font-bold text-sky-300"
                title="Rating kekuatan klub"
              >
                <Swords :size="11" />
                {{ fmtStr(home.strength?.overall) }}
              </span>
              <span>
                {{ home.star_player?.player_name }}
                <span class="text-slate-600">·</span>
                {{ home.star_player?.position }}
              </span>
            </div>
            <div class="mt-3">
              <FormBadges :form="home.form || []" label="Form" />
            </div>
          </div>
        </div>
      </div>

      <!-- Center score -->
      <div class="flex flex-col items-center justify-center gap-3 px-2 py-2 text-center">
        <div class="num text-5xl font-bold tracking-tight text-slate-50 sm:text-6xl">
          <span class="text-sky-400">{{ projection.home_score ?? '—' }}</span>
          <span class="mx-2 text-slate-600">-</span>
          <span class="text-rose-400">{{ projection.away_score ?? '—' }}</span>
        </div>
        <div class="label-caps">Ekspektasi Skor</div>
        <div class="flex items-center gap-3 text-xs text-slate-400">
          <span class="num rounded-md border border-sky-500/30 bg-sky-500/10 px-2 py-1 text-sky-400">
            {{ analytics.home_xg ?? '—' }} xG
          </span>
          <span class="text-slate-600">vs</span>
          <span class="num rounded-md border border-rose-500/30 bg-rose-500/10 px-2 py-1 text-rose-400">
            {{ analytics.away_xg ?? '—' }} xG
          </span>
        </div>
        <div v-if="analytics.first_half_goal_probability != null" class="text-[11px] text-slate-500">
          Peluang gol babak I:
          <span class="num text-slate-300">{{ analytics.first_half_goal_probability }}%</span>
        </div>
        <div
          v-if="gap.value != null"
          class="flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[11px]"
          :class="gapTone"
          title="Selisih rating kekuatan klub — membatasi margin skor proyeksi"
        >
          <Swords :size="12" />
          <span class="num font-bold">{{ fmtStr(gap.home) }} - {{ fmtStr(gap.away) }}</span>
          <span class="text-[10px] opacity-80">{{ gapLabel }}</span>
        </div>
      </div>

      <!-- Away -->
      <div class="relative flex items-center justify-end gap-4 overflow-hidden rounded-xl border border-slate-800/80 bg-slate-900/40 p-4">
        <div class="pointer-events-none absolute -left-4 top-1/2 -translate-y-1/2 opacity-40">
          <PlayerCutout
            :image="away.star_player?.image"
            :name="away.star_player?.player_name || away.name"
            side="right"
            size="lg"
          />
        </div>
        <div class="relative z-10 flex min-w-0 flex-row-reverse items-center gap-4 text-right">
          <img
            v-if="away.logo"
            :src="away.logo"
            :alt="away.name"
            class="h-14 w-14 rounded-xl border border-slate-700/60 bg-slate-950/60 object-contain p-1"
          />
          <div class="min-w-0">
            <div class="label-caps">Away</div>
            <div class="truncate text-xl font-bold text-slate-50">{{ away.name }}</div>
            <div class="mt-1 text-xs text-slate-400">
              <span class="num text-slate-300">{{ away.formation || '—' }}</span>
              <span class="mx-1 text-slate-600">·</span>
              <span class="text-slate-500">Pelatih</span> {{ away.coach || '—' }}
            </div>
            <div class="mt-1 flex flex-wrap items-center justify-end gap-2 text-xs text-slate-400">
              <span>
                {{ away.star_player?.player_name }}
                <span class="text-slate-600">·</span>
                {{ away.star_player?.position }}
              </span>
              <span
                class="num inline-flex items-center gap-1 rounded-md border border-rose-500/30 bg-rose-500/10 px-1.5 py-0.5 font-bold text-rose-300"
                title="Rating kekuatan klub"
              >
                <Swords :size="11" />
                {{ fmtStr(away.strength?.overall) }}
              </span>
            </div>
            <div class="mt-3 flex justify-end">
              <FormBadges :form="away.form || []" label="Form" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="border-t border-slate-800 px-5 py-4">
      <WinProbabilityBar
        :home-win="probs.home_win || 0"
        :draw="probs.draw || 0"
        :away-win="probs.away_win || 0"
        :home-label="home.name || 'HOME'"
        :away-label="away.name || 'AWAY'"
      />
    </div>
  </section>
</template>
