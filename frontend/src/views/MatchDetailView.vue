<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, RefreshCw, Search } from 'lucide-vue-next'
import { fetchMatchDetail, fetchMatchDetailByTeams } from '@/services/api'
import MatchDetailPanel from '@/components/predict/MatchDetailPanel.vue'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'

const route = useRoute()
const router = useRouter()

const detail = ref(null)
const loading = ref(true)
let timer = null

const matchId = computed(() => String(route.query.id || ''))
const home = computed(() => String(route.query.home || ''))
const away = computed(() => String(route.query.away || ''))
const league = computed(() => String(route.query.league || ''))

async function load(force = false) {
  if (!matchId.value && !(home.value && away.value)) {
    loading.value = false
    detail.value = null
    return
  }
  loading.value = true
  try {
    const teams = { home: home.value, away: away.value, league: league.value }
    detail.value = matchId.value
      ? await fetchMatchDetail(matchId.value, force, teams)
      : await fetchMatchDetailByTeams(home.value, away.value, league.value, force)
    if (!detail.value?.available && detail.value?.reason === 'not_found' && home.value && away.value) {
      detail.value = await fetchMatchDetailByTeams(home.value, away.value, league.value, force)
    }
  } catch {
    detail.value = { available: false, reason: 'fetch_error' }
  } finally {
    loading.value = false
  }
}

const isLive = computed(() => ['IN_PLAY', 'PAUSED', 'LIVE'].includes(detail.value?.status))
const statusLabel = computed(() => {
  const d = detail.value
  if (!d) return ''
  if (d.status === 'PAUSED') return 'HT'
  if (isLive.value) return `${d.minute ?? '?'}'`
  if (d.status === 'FINISHED') return 'FT'
  return 'PRAPERTANDINGAN'
})
const sourceLabel = computed(() =>
  detail.value?.source === 'api' ? 'football-data.org' : detail.value?.source === 'espn' ? 'ESPN' : null
)

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/predict')
}

onMounted(async () => {
  await load(true)
  timer = setInterval(() => {
    if (isLive.value) load(true)
  }, 60000)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <button class="btn-ghost" type="button" @click="goBack">
          <ArrowLeft :size="14" />
          Kembali
        </button>
        <div>
          <div class="eyebrow flex items-center gap-2">
            <span class="text-emerald-500/50">//</span> MATCH CENTRE
          </div>
          <h1 class="mt-1 text-xl font-extrabold tracking-tight text-slate-50 sm:text-2xl">
            Detail Laga
            <span class="ml-2 rounded border border-emerald-500/40 bg-emerald-500/10 px-1.5 py-0.5 align-middle text-[10px] font-extrabold tracking-widest text-emerald-400">
              DATA ASLI
            </span>
          </h1>
        </div>
      </div>
      <button class="btn-ghost" type="button" :disabled="loading" @click="load(true)">
        <RefreshCw :size="14" :class="loading ? 'animate-spin' : ''" />
        Segarkan
      </button>
    </div>

    <!-- Tanpa parameter -->
    <div v-if="!matchId && !(home && away)" class="panel px-6 py-12 text-center">
      <Search :size="28" class="mx-auto text-slate-600" />
      <p class="mx-auto mt-3 max-w-sm text-sm text-slate-400">
        Belum ada laga dipilih. Klik laga di ticker <span class="text-rose-400">LIVE</span> di atas,
        atau buka dari halaman prediksi.
      </p>
      <button class="btn-ghost mx-auto mt-4" type="button" @click="router.push('/predict')">
        Buka Halaman Prediksi
      </button>
    </div>

    <!-- Loading -->
    <div v-else-if="loading && !detail">
      <SkeletonCard :lines="3" />
      <div class="mt-4"><SkeletonCard :lines="8" /></div>
    </div>

    <template v-else>
      <!-- Scoreboard asli -->
      <section
        v-if="detail?.available"
        class="panel overflow-hidden"
        :class="isLive ? 'border-rose-500/30' : ''"
      >
        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 bg-slate-950/40 px-4 py-2">
          <span class="label-caps text-slate-500">{{ detail.competition_name || 'Laga' }}</span>
          <span v-if="sourceLabel" class="chip border-emerald-500/40 bg-emerald-500/10 text-emerald-400">
            Sumber: {{ sourceLabel }} — data pertandingan asli
          </span>
        </div>

        <div class="grid grid-cols-[1fr_auto_1fr] items-center gap-3 px-4 py-6 sm:px-8">
          <!-- Home -->
          <div class="flex min-w-0 items-center justify-end gap-3 text-right">
            <div class="min-w-0">
              <div class="truncate text-base font-bold text-slate-50 sm:text-xl">{{ detail.home }}</div>
              <div class="num text-[11px] text-slate-500">{{ detail.home_short }}</div>
            </div>
            <img
              v-if="detail.crest_home"
              :src="detail.crest_home"
              :alt="detail.home"
              class="h-12 w-12 shrink-0 rounded-xl border border-slate-700/60 bg-slate-950/60 object-contain p-1 sm:h-14 sm:w-14"
            />
          </div>

          <!-- Skor -->
          <div class="flex flex-col items-center gap-1.5 px-2">
            <div class="flex items-center gap-2">
              <span
                v-if="isLive"
                class="flex items-center gap-1.5 rounded bg-rose-600 px-2 py-0.5 text-[10px] font-extrabold tracking-widest text-white"
              >
                <span class="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-white" />
                LIVE
              </span>
              <span
                v-else-if="detail.status === 'FINISHED'"
                class="rounded bg-slate-700 px-2 py-0.5 text-[10px] font-extrabold tracking-widest text-slate-300"
              >
                FT
              </span>
              <span v-else class="label-caps text-slate-500">PRAPERTANDINGAN</span>
              <span v-if="isLive || detail.status === 'FINISHED'" class="num text-xs font-bold text-slate-400">
                {{ statusLabel }}
              </span>
            </div>
            <div class="num text-4xl font-bold tracking-tight text-slate-50 sm:text-5xl">
              <span class="text-sky-400">{{ detail.home_score ?? '–' }}</span>
              <span class="mx-2 text-slate-600">-</span>
              <span class="text-rose-400">{{ detail.away_score ?? '–' }}</span>
            </div>
            <div v-if="detail.status === 'TIMED'" class="text-[11px] text-slate-500">
              Skor muncul setelah pertandingan dimulai.
            </div>
          </div>

          <!-- Away -->
          <div class="flex min-w-0 items-center gap-3">
            <img
              v-if="detail.crest_away"
              :src="detail.crest_away"
              :alt="detail.away"
              class="h-12 w-12 shrink-0 rounded-xl border border-slate-700/60 bg-slate-950/60 object-contain p-1 sm:h-14 sm:w-14"
            />
            <div class="min-w-0">
              <div class="truncate text-base font-bold text-slate-50 sm:text-xl">{{ detail.away }}</div>
              <div class="num text-[11px] text-slate-500">{{ detail.away_short }}</div>
            </div>
          </div>
        </div>

        <!-- Pencetak gol -->
        <div
          v-if="detail.scorers && (detail.scorers.home?.length || detail.scorers.away?.length)"
          class="border-t border-slate-800 px-4 py-3 sm:px-8"
        >
          <div class="grid gap-3 sm:grid-cols-2">
            <div v-for="side in ['home', 'away']" :key="side" class="space-y-1">
              <div
                v-for="(g, i) in detail.scorers[side] || []"
                :key="i"
                class="flex items-center gap-2 text-xs"
                :class="side === 'home' ? 'justify-end text-sky-300 sm:text-right' : 'text-rose-300'"
              >
                <template v-if="side === 'home'">
                  <span class="truncate text-slate-300">{{ g.player }}</span>
                  <span v-if="g.own_goal" class="text-[10px] text-slate-500">(b.diri)</span>
                  <span class="num w-8 font-bold opacity-80">{{ g.minute }}</span>
                </template>
                <template v-else>
                  <span class="num w-8 font-bold opacity-80">{{ g.minute }}</span>
                  <span class="truncate text-slate-300">{{ g.player }}</span>
                  <span v-if="g.own_goal" class="text-[10px] text-slate-500">(b.diri)</span>
                </template>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Tidak tersedia -->
      <div v-else class="panel px-6 py-10 text-center">
        <div class="label-caps text-slate-500">Data tidak tersedia</div>
        <p class="mx-auto mt-2 max-w-md text-sm text-slate-400">
          <template v-if="detail?.reason === 'mock'">
            Laga ini berasal dari mode simulasi — halaman ini hanya menampilkan data pertandingan asli.
          </template>
          <template v-else-if="detail?.reason === 'not_found'">
            Laga tidak ditemukan di sumber data (ESPN). Coba laga lain yang lebih baru (maks. 7 hari terakhir).
          </template>
          <template v-else>
            Gagal memuat data dari sumber. Coba segarkan beberapa saat lagi.
          </template>
        </p>
      </div>

      <!-- Timeline / Line-up / Statistik -->
      <MatchDetailPanel v-if="detail?.available" :detail="detail" :loading="loading" />
    </template>
  </div>
</template>
