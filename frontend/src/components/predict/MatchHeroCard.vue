<script setup>
import { computed } from 'vue'
import PlayerCutout from '@/components/shared/PlayerCutout.vue'
import WinProbabilityBar from '@/components/shared/WinProbabilityBar.vue'
import FormBadges from '@/components/shared/FormBadges.vue'
import { MapPin, UserRound, Swords } from 'lucide-vue-next'

const props = defineProps({
  data: { type: Object, required: true },
  liveMatch: { type: Object, default: null },
})

const home = computed(() => props.data.home_team || {})
const away = computed(() => props.data.away_team || {})
const projection = computed(() => props.data.projection || {})
const probs = computed(() => props.data.probabilities || {})
const analytics = computed(() => props.data.analytics || {})
const meta = computed(() => props.data.meta || {})
const gap = computed(() => props.data.strength_gap || {})
const result = computed(() => props.data.result || {})

// Gabungkan data live dari frontend + backend result
const live = computed(() => {
  if (props.liveMatch?.live) {
    return {
      home_score: props.liveMatch.home_score ?? 0,
      away_score: props.liveMatch.away_score ?? 0,
      minute: props.liveMatch.minute,
      paused: props.liveMatch.status === 'PAUSED',
    }
  }
  if (result.value.status === 'live') {
    return {
      home_score: result.value.actual_home ?? 0,
      away_score: result.value.actual_away ?? 0,
      minute: result.value.minute,
      paused: false,
    }
  }
  return null
})

const isFinished = computed(() => result.value.status === 'finished')

// Satu baris verdict: badge + satu kalimat penjelasan.
// Hijau/merah hanya untuk benar/salah prediksi.
const verdict = computed(() => {
  if (!isFinished.value) return null
  if (result.value.exact) {
    return {
      label: 'Tepat skor',
      tone: 'ok',
      sentence: `Model memprediksi ${result.value.predicted_score} dan skor akhir memang ${result.value.actual_score}.`,
    }
  }
  if (result.value.outcome_correct) {
    return {
      label: 'Tepat hasil',
      tone: 'ok',
      sentence: `Arah hasil benar, tapi skor meleset — prediksi ${result.value.predicted_score}, akhir ${result.value.actual_score}.`,
    }
  }
  return {
    label: 'Meleset',
    tone: 'bad',
    sentence: `Prediksi ${result.value.predicted_score} tidak cocok dengan skor akhir ${result.value.actual_score}.`,
  }
})

const sourceLabel = computed(() => {
  switch (result.value.source) {
    case 'espn': return 'ESPN'
    case 'api': return 'football-data.org'
    case 'understat': return 'Understat'
    case 'mock': return 'data simulasi'
    default: return null
  }
})

const fmtStr = (v) => (v != null ? Number(v).toFixed(1) : '—')

// Sumber data kekuatan tim (data_source dari backend): teks 13px di bawah nama
const SOURCE_LABELS = {
  'xg+elo': 'Data lengkap',
  elo: 'Berbasis Elo',
  manual: 'Rating manual',
  default: 'Belum terverifikasi',
}
const teamSourceLabel = (src) => SOURCE_LABELS[src] || null

const gapLabel = computed(() => {
  const g = gap.value.value ?? 0
  if (g >= 15) return 'Jarak jauh'
  if (g >= 8) return 'Unggul'
  if (g >= 3) return 'Sedikit unggul'
  return 'Seimbang'
})

const data_match = computed(() => props.data.match)
</script>

<template>
  <section class="panel overflow-hidden">
    <!-- 1. Info laga: satu baris kecil -->
    <div
      class="flex flex-wrap items-center gap-x-4 gap-y-1 border-b px-5 py-3 text-[13px]"
      style="border-color: var(--line); color: var(--mute)"
    >
      <span v-if="data_match" class="font-medium" style="color: var(--ink)">{{ data_match }}</span>
      <span v-if="meta.stadium" class="inline-flex items-center gap-1.5">
        <MapPin :size="13" />
        {{ meta.stadium }}
      </span>
      <span v-if="meta.referee" class="inline-flex items-center gap-1.5">
        <UserRound :size="13" />
        {{ meta.referee }}
      </span>
      <span v-if="live" class="ml-auto inline-flex items-center gap-1.5 font-semibold" style="color: var(--away)">
        <span class="inline-block h-1.5 w-1.5 animate-pulse rounded-full" style="background: var(--away)" />
        {{ live.paused ? 'HT' : `${live.minute ?? '?'}'` }}
      </span>
      <span v-else-if="isFinished" class="ml-auto font-semibold">Selesai</span>
    </div>

    <!-- Hero: panel tim kiri/kanan (logo di sisi luar, foto pemain di latar), skor BESAR di tengah -->
    <div class="grid grid-cols-1 items-stretch gap-4 px-4 py-6 md:grid-cols-[1fr_auto_1fr] md:gap-6 md:px-6">
      <!-- Home -->
      <div
        class="relative flex min-w-0 items-center gap-4 overflow-hidden rounded-block border p-4"
        style="border-color: var(--line); background: color-mix(in srgb, var(--card) 70%, transparent)"
      >
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
            class="h-14 w-14 shrink-0 rounded-elem border bg-card object-contain p-1"
            style="border-color: var(--line)"
          />
          <div class="min-w-0">
            <div class="label-caps">Home</div>
            <div class="truncate font-display text-xl font-bold leading-tight" style="color: var(--ink)">
              {{ home.name }}
            </div>
            <div v-if="teamSourceLabel(home.data_source)" class="text-[13px]" style="color: var(--mute)">
              {{ teamSourceLabel(home.data_source) }}
            </div>
            <div class="mt-1 text-[13px]" style="color: var(--mute)">
              <span>{{ home.coach || '—' }}</span>
              <span class="mx-1">·</span>
              <span class="num">{{ home.formation || '—' }}</span>
            </div>
            <div class="mt-1 flex flex-wrap items-center gap-2 text-[13px]" style="color: var(--mute)">
              <span
                class="num inline-flex items-center gap-1 rounded-elem border px-1.5 py-0.5 font-bold"
                style="border-color: var(--home); color: var(--home)"
                title="Rating kekuatan klub"
              >
                <Swords :size="11" />
                {{ fmtStr(home.strength?.overall) }}
              </span>
              <span v-if="home.star_player?.player_name">
                {{ home.star_player.player_name }}
                <template v-if="home.star_player?.position"> · {{ home.star_player.position }}</template>
              </span>
            </div>
            <div class="mt-3">
              <FormBadges :form="home.form || []" label="Form" />
            </div>
          </div>
        </div>
      </div>

      <!-- Skor besar -->
      <div class="flex flex-col items-center justify-center px-2 py-2 text-center">
        <div
          class="num font-display font-extrabold leading-none tracking-tight"
          style="font-size: clamp(52px, 12vw, 96px)"
        >
          <span style="color: var(--home)">{{ live ? (live.home_score ?? '?') : isFinished ? result.actual_home : (projection.home_score ?? '—') }}</span>
          <span class="mx-1 sm:mx-2" style="color: var(--mute)">–</span>
          <span style="color: var(--away)">{{ live ? (live.away_score ?? '?') : isFinished ? result.actual_away : (projection.away_score ?? '—') }}</span>
        </div>
        <div class="mt-2 text-[13px]" style="color: var(--mute)">
          <template v-if="live">Skor live</template>
          <template v-else-if="isFinished">Skor akhir</template>
          <template v-else>Ekspektasi skor</template>
        </div>

        <!-- xG kedua tim -->
        <div class="mt-3 flex items-center gap-3 text-[13px]" style="color: var(--mute)">
          <span class="num rounded-elem border px-2 py-1" style="border-color: var(--home); color: var(--home)">
            {{ analytics.home_xg ?? '—' }} xG
          </span>
          <span>vs</span>
          <span class="num rounded-elem border px-2 py-1" style="border-color: var(--away); color: var(--away)">
            {{ analytics.away_xg ?? '—' }} xG
          </span>
        </div>

        <!-- Selisih kekuatan -->
        <div
          v-if="gap.value != null"
          class="mt-3 inline-flex items-center gap-1.5 rounded-elem border px-2.5 py-1 text-[13px]"
          :style="{
            'border-color': gap.value >= 8 ? 'var(--bad)' : 'var(--line)',
            color: gap.value >= 8 ? 'var(--bad)' : 'var(--mute)',
          }"
          title="Selisih rating kekuatan klub — membatasi margin skor proyeksi"
        >
          <Swords :size="12" />
          <span class="num font-bold">{{ fmtStr(gap.home) }} - {{ fmtStr(gap.away) }}</span>
          <span class="opacity-80">{{ gapLabel }}</span>
        </div>
      </div>

      <!-- Away -->
      <div
        class="relative flex min-w-0 flex-row-reverse items-center gap-4 overflow-hidden rounded-block border p-4"
        style="border-color: var(--line); background: color-mix(in srgb, var(--card) 70%, transparent)"
      >
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
            class="h-14 w-14 shrink-0 rounded-elem border bg-card object-contain p-1"
            style="border-color: var(--line)"
          />
          <div class="min-w-0">
            <div class="label-caps">Away</div>
            <div class="truncate font-display text-xl font-bold leading-tight" style="color: var(--ink)">
              {{ away.name }}
            </div>
            <div v-if="teamSourceLabel(away.data_source)" class="text-[13px]" style="color: var(--mute)">
              {{ teamSourceLabel(away.data_source) }}
            </div>
            <div class="mt-1 text-[13px]" style="color: var(--mute)">
              <span class="num">{{ away.formation || '—' }}</span>
              <span class="mx-1">·</span>
              <span>{{ away.coach || '—' }}</span>
            </div>
            <div class="mt-1 flex flex-wrap items-center justify-end gap-2 text-[13px]" style="color: var(--mute)">
              <span v-if="away.star_player?.player_name">
                {{ away.star_player.player_name }}
                <template v-if="away.star_player?.position"> · {{ away.star_player.position }}</template>
              </span>
              <span
                class="num inline-flex items-center gap-1 rounded-elem border px-1.5 py-0.5 font-bold"
                style="border-color: var(--away); color: var(--away)"
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

    <!-- 2. Verdict: badge + satu kalimat -->
    <div
      v-if="verdict"
      class="flex flex-wrap items-center gap-3 border-t px-5 py-3"
      style="border-color: var(--line)"
    >
      <span
        class="chip shrink-0 font-semibold"
        :style="{
          color: verdict.tone === 'ok' ? 'var(--ok)' : 'var(--bad)',
          borderColor: verdict.tone === 'ok' ? 'var(--ok)' : 'var(--bad)',
        }"
      >
        {{ verdict.label }}
      </span>
      <p class="text-[15px] leading-snug" style="color: var(--ink)">{{ verdict.sentence }}</p>
      <span v-if="sourceLabel" class="ml-auto text-[13px]" style="color: var(--mute)">
        Sumber: {{ sourceLabel }}
      </span>
    </div>

    <!-- 3. Bar probabilitas 3 segmen + persentase -->
    <div class="border-t px-5 py-4" style="border-color: var(--line)">
      <WinProbabilityBar
        :home-win="probs.home_win || 0"
        :draw="probs.draw || 0"
        :away-win="probs.away_win || 0"
        :home-label="home.name || 'Home'"
        :away-label="away.name || 'Away'"
      />
      <!-- keyakinan model: teks kecil, bukan badge di pojok -->
      <p class="mt-3 text-[13px]" style="color: var(--mute)">
        <template v-if="projection.confidence_pct != null">
          Keyakinan model {{ projection.confidence_pct }}%
          <template v-if="analytics.first_half_goal_probability != null && !live && !isFinished">
            · Peluang gol babak I {{ analytics.first_half_goal_probability }}%
          </template>
        </template>
        <template v-else-if="analytics.first_half_goal_probability != null && !live && !isFinished">
          Peluang gol babak I {{ analytics.first_half_goal_probability }}%
        </template>
      </p>
    </div>
  </section>
</template>
