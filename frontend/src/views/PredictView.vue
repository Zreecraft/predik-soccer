<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { RefreshCw } from 'lucide-vue-next'
import { fetchFixtures, fetchLeagues, fetchPredict, fetchShots, fetchTeams } from '@/services/api'
import { LEAGUE_LABELS } from '@/utils/format'
import { useAsyncData } from '@/composables/useAsyncData'
import MatchHeroCard from '@/components/predict/MatchHeroCard.vue'
import TacticalCompareTable from '@/components/predict/TacticalCompareTable.vue'
import DifferentialPanel from '@/components/predict/DifferentialPanel.vue'
import ShotMap from '@/components/predict/ShotMap.vue'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'

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
})
</script>

<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <div class="label-caps text-sky-400/90">Match Prediction Engine</div>
        <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-50">Prediksi Laga</h1>
        <p class="mt-1 text-sm text-slate-400">
          Simulasi Monte Carlo 10.000 iterasi minute-by-minute + model xG.
        </p>
      </div>
      <button class="btn-ghost" type="button" :disabled="loading" @click="runPredict">
        <RefreshCw :size="14" :class="loading ? 'animate-spin' : ''" />
        {{ loading ? 'Menghitung…' : 'Jalankan Prediksi' }}
      </button>
    </div>

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
      <MatchHeroCard :data="predict" />

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
