<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MonitorPlay, RefreshCw } from 'lucide-vue-next'
import { fetchFixtures, fetchLeagues, fetchLiveMatches, fetchPredict, fetchShots, fetchTeams } from '@/services/api'
import { LEAGUE_LABELS } from '@/utils/format'
import { useAsyncData } from '@/composables/useAsyncData'
import MatchHeroCard from '@/components/predict/MatchHeroCard.vue'
import TacticalCompareTable from '@/components/predict/TacticalCompareTable.vue'
import DifferentialPanel from '@/components/predict/DifferentialPanel.vue'
import ShotMap from '@/components/predict/ShotMap.vue'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'
import PageHeader from '@/components/shared/PageHeader.vue'

const route = useRoute()
const router = useRouter()

const leagues = ref([])
const teams = ref([])
const fixtures = ref([])
const league = ref(route.query.league || 'EPL')
const homeTeam = ref(route.query.home || '')
const awayTeam = ref(route.query.away || '')
const shotsData = ref({ home: {}, away: {}, summary: {} })
const shotsLoading = ref(false)

const { data: predict, loading, error, load } = useAsyncData(fetchPredict)

// Live score untuk laga yang sedang dipilih
const liveMatches = ref([])
let liveTimer = null

async function refreshLive() {
  try {
    const d = await fetchLiveMatches()
    liveMatches.value = d.matches || []
  } catch {
    liveMatches.value = []
  }
}

const currentLiveMatch = computed(() => {
  const h = (homeTeam.value || '').toLowerCase()
  const a = (awayTeam.value || '').toLowerCase()
  if (!h || !a) return null
  return (
    liveMatches.value.find(
      (m) => m.live && m.home?.toLowerCase() === h && m.away?.toLowerCase() === a
    ) || null
  )
})

// Laga terpilih di daftar livescore (live > selesai) — tombol menuju Match Centre
const selectedMatch = computed(() => {
  const h = (homeTeam.value || '').toLowerCase()
  const a = (awayTeam.value || '').toLowerCase()
  if (!h || !a) return null
  const exact = liveMatches.value.filter(
    (m) => m.home?.toLowerCase() === h && m.away?.toLowerCase() === a
  )
  return exact.find((m) => m.live) || exact.find((m) => m.status === 'FINISHED') || null
})

// Link menuju halaman Match Centre (data asli, terpisah dari prediksi)
const matchCentreLink = computed(() => ({
  path: '/match',
  query: {
    ...(selectedMatch.value?.id ? { id: String(selectedMatch.value.id) } : {}),
    home: homeTeam.value,
    away: awayTeam.value,
    league: league.value,
  },
}))

// Kickoff laga terpilih dalam WIB (data UTC) — tampil saat tidak sedang live
function formatWib(dateStr) {
  if (!dateStr) return ''
  const d = new Date(String(dateStr).replace(' ', 'T') + 'Z')
  if (isNaN(d.getTime())) return ''
  const wib = new Date(d.getTime() + 7 * 3600 * 1000)
  const days = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab']
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
  const pad = (n) => String(n).padStart(2, '0')
  return `${days[wib.getUTCDay()]}, ${wib.getUTCDate()} ${months[wib.getUTCMonth()]} ${wib.getUTCFullYear()} • ${pad(wib.getUTCHours())}:${pad(wib.getUTCMinutes())} WIB`
}

const kickoffWib = computed(() => {
  const h = (homeTeam.value || '').toLowerCase()
  const a = (awayTeam.value || '').toLowerCase()
  const f = fixtures.value.find(
    (x) => x.home_team?.toLowerCase() === h && x.away_team?.toLowerCase() === a
  )
  return formatWib(f?.date)
})

async function loadTeams() {
  const data = await fetchTeams(league.value)
  teams.value = (data.teams || []).map((t) => t.name)
}

async function loadFixtures() {
  const data = await fetchFixtures(league.value, 40)
  fixtures.value = data.fixtures || []
}

function applyDefaults() {
  if (fixtures.value.length) {
    const f = fixtures.value[0]
    if (!homeTeam.value) homeTeam.value = f.home_team
    if (!awayTeam.value) awayTeam.value = f.away_team
  } else if (teams.value.length >= 2) {
    if (!homeTeam.value) homeTeam.value = teams.value[0]
    if (!awayTeam.value) awayTeam.value = teams.value[1]
  }
}

async function runPredict() {
  if (!homeTeam.value || !awayTeam.value) return
  router.replace({
    query: {
      league: league.value,
      home: homeTeam.value,
      away: awayTeam.value,
    },
  })
  shotsLoading.value = true
  const [pred, shots] = await Promise.all([
    load(homeTeam.value, awayTeam.value),
    fetchShots(homeTeam.value, awayTeam.value).catch(() => ({ home: {}, away: {}, summary: {} })),
  ])
  shotsData.value = shots || { home: {}, away: {}, summary: {} }
  shotsLoading.value = false
  return pred
}

watch(league, async () => {
  homeTeam.value = ''
  awayTeam.value = ''
  await Promise.all([loadTeams(), loadFixtures()])
  applyDefaults()
  await runPredict()
})

onMounted(async () => {
  leagues.value = await fetchLeagues()
  await Promise.all([loadTeams(), loadFixtures()])
  applyDefaults()
  await runPredict()
  await refreshLive()
  liveTimer = setInterval(refreshLive, 60000)
})
onBeforeUnmount(() => clearInterval(liveTimer))
</script>

<template>
  <div class="space-y-5">
    <PageHeader
      eyebrow="Match Prediction Engine"
      title="Prediksi Laga"
      subtitle="Simulasi Monte Carlo 10.000 iterasi minute-by-minute dengan model xG. Data pertandingan asli (skor, kartu, line-up) ada di Match Centre — terpisah."
    >
      <template #actions>
        <button class="btn-ghost" type="button" :disabled="loading" @click="runPredict">
          <RefreshCw :size="14" :class="loading ? 'animate-spin' : ''" />
          {{ loading ? 'Menghitung…' : 'Jalankan Prediksi' }}
        </button>
      </template>
    </PageHeader>

    <!-- Selectors -->
    <div class="panel grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
      <label class="block">
        <span class="label-caps">Liga</span>
        <select
          v-model="league"
          class="mt-1.5 w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none focus:border-sky-500/60"
        >
          <option v-for="l in leagues" :key="l.id" :value="l.id">{{ l.name }}</option>
        </select>
      </label>
      <label class="block">
        <span class="label-caps">Tim Kandang</span>
        <select
          v-model="homeTeam"
          class="mt-1.5 w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none focus:border-sky-500/60"
        >
          <option v-for="t in teams" :key="'h' + t" :value="t">{{ t }}</option>
        </select>
      </label>
      <label class="block">
        <span class="label-caps">Tim Tandang</span>
        <select
          v-model="awayTeam"
          class="mt-1.5 w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none focus:border-sky-500/60"
        >
          <option v-for="t in teams" :key="'a' + t" :value="t">{{ t }}</option>
        </select>
      </label>
      <label class="block">
        <span class="label-caps">Fixture Cepat</span>
        <select
          class="mt-1.5 w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none focus:border-sky-500/60"
          @change="
            (e) => {
              const [h, a] = e.target.value.split('||')
              if (h && a) {
                homeTeam = h
                awayTeam = a
                runPredict()
              }
            }
          "
        >
          <option value="">Pilih fixture…</option>
          <option v-for="f in fixtures" :key="f.match_id" :value="`${f.home_team}||${f.away_team}`">
            {{ f.home_team }} vs {{ f.away_team }}
          </option>
        </select>
      </label>
    </div>

    <div v-if="error" class="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
      {{ error }}
    </div>

    <div v-if="loading && !predict">
      <SkeletonCard :lines="4" />
      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <SkeletonCard :lines="6" />
        <SkeletonCard :lines="6" />
      </div>
    </div>

    <template v-else-if="predict">
      <!-- Bukan live & belum selesai: tampilkan jam kickoff (WIB) saja -->
      <div
        v-if="kickoffWib && !currentLiveMatch && predict.result?.status !== 'finished'"
        class="panel flex flex-wrap items-center gap-3 border-slate-700/70 bg-slate-900/40 px-4 py-3"
      >
        <span class="eyebrow rounded border border-sky-500/40 bg-sky-500/10 px-2 py-1">
          KICKOFF
        </span>
        <span class="text-sm font-medium text-slate-200">{{ kickoffWib }}</span>
        <span class="ml-auto text-[11px] text-slate-500">Belum dimulai — prediksi = pra-pertandingan</span>
      </div>

      <MatchHeroCard :data="predict" :live-match="currentLiveMatch" />

      <!-- Jembatan ke Match Centre (data asli, halaman terpisah) -->
      <RouterLink
        :to="matchCentreLink"
        class="panel group flex flex-wrap items-center justify-between gap-3 border-emerald-500/25 bg-emerald-500/[0.04] px-4 py-3 transition hover:border-emerald-500/50 hover:bg-emerald-500/[0.08]"
      >
        <div class="flex items-center gap-3">
          <span
            class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
          >
            <MonitorPlay :size="16" />
          </span>
          <div>
            <div class="text-sm font-bold text-slate-100">
              Match Centre
              <span class="ml-2 rounded border border-emerald-500/40 bg-emerald-500/10 px-1.5 py-0.5 align-middle text-[9px] font-extrabold tracking-widest text-emerald-400">
                DATA ASLI
              </span>
            </div>
            <div class="mt-0.5 text-xs text-slate-400">
              Skor asli, pencetak gol & menit, kartu, offside, line-up — dari ESPN, tanpa simulasi model.
            </div>
          </div>
        </div>
        <span class="text-xs font-semibold text-emerald-400 transition group-hover:translate-x-0.5">
          Buka Match Centre →
        </span>
      </RouterLink>

      <div class="grid gap-4 lg:grid-cols-2">
        <TacticalCompareTable
          :home="predict.tactical?.home || {}"
          :away="predict.tactical?.away || {}"
          :home-name="predict.home_team?.name"
          :away-name="predict.away_team?.name"
        />
        <div v-if="shotsLoading">
          <SkeletonCard :lines="6" />
        </div>
        <ShotMap
          v-else
          :home="shotsData.home || {}"
          :away="shotsData.away || {}"
          :summary="shotsData.summary || {}"
        />
      </div>

      <DifferentialPanel
        :summary="predict.differential_summary"
        :home-name="predict.home_team?.name"
        :away-name="predict.away_team?.name"
        :shots="predict.shots || {}"
      />
    </template>
  </div>
</template>
