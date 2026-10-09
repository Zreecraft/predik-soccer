<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { RefreshCw } from 'lucide-vue-next'
import { fetchAnalytics, fetchLeagues, fetchTeams } from '@/services/api'
import { useAsyncData } from '@/composables/useAsyncData'
import { LEAGUE_LABELS } from '@/utils/format'
import ClubHeader from '@/components/analytics/ClubHeader.vue'
import TerritorialHeatmap from '@/components/analytics/TerritorialHeatmap.vue'
import TacticalBullets from '@/components/analytics/TacticalBullets.vue'
import UpcomingFixturesTable from '@/components/analytics/UpcomingFixturesTable.vue'
import FormHistoryTable from '@/components/analytics/FormHistoryTable.vue'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'

const route = useRoute()
const router = useRouter()

const selectedLeague = ref(route.query.league || '')
const selectedTeam = ref(route.query.team || 'Arsenal')
const leagues = ref([])
const leagueTeams = ref([])
const allTeams = ref([])

const { data, loading, error, load } = useAsyncData(fetchAnalytics)

const filteredTeams = computed(() => {
  if (!selectedLeague.value) return allTeams.value
  return leagueTeams.value
})

async function reload() {
  if (!selectedTeam.value) return
  router.replace({ query: { team: selectedTeam.value, league: selectedLeague.value || undefined } })
  await load(selectedTeam.value)
}

async function onLeagueChange() {
  selectedLeague.value ? (leagueTeams.value = await fetchTeamsByLeague(selectedLeague.value)) : (leagueTeams.value = allTeams.value)
  if (leagueTeams.value.length && !leagueTeams.value.includes(selectedTeam.value)) {
    selectedTeam.value = leagueTeams.value[0]
  }
}

async function fetchTeamsByLeague(leagueCode) {
  try {
    const res = await fetchTeams(leagueCode)
    return (res.teams || []).map((x) => x.name)
  } catch {
    return []
  }
}

watch(selectedTeam, reload)

onMounted(async () => {
  try {
    const [lRes, tRes] = await Promise.all([fetchLeagues(), fetchTeams()])
    leagues.value = Array.isArray(lRes) ? lRes.map((x) => x.id) : (lRes.leagues || [])
    allTeams.value = (tRes.teams || []).map((x) => x.name)
    leagueTeams.value = allTeams.value
  } catch {
    leagues.value = []
    allTeams.value = ['Arsenal', 'Manchester City', 'Real Madrid', 'Inter', 'Bayern Munich']
    leagueTeams.value = allTeams.value
  }

  if (route.query.team) {
    selectedTeam.value = route.query.team
  } else if (!allTeams.value.includes(selectedTeam.value) && allTeams.value.length) {
    selectedTeam.value = allTeams.value[0]
  }
  await reload()
})
</script>

<template>
  <div class="space-y-5">
    <!-- Header & Two-Tier Filters -->
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <div class="label-caps text-sky-400/90">Tactical Scouting</div>
        <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-50">Analitik Klub</h1>
        <p class="mt-1 text-sm text-slate-400">
          Laporan pemantauan taktis, matriks kendali teritorial, dan proyeksi jadwal.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <!-- 1. Tier 1: League Filter -->
        <select
          v-model="selectedLeague"
          class="rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none focus:border-sky-500/60"
          @change="onLeagueChange"
        >
          <option value="">Semua Liga</option>
          <option v-for="l in leagues" :key="l" :value="l">{{ LEAGUE_LABELS[l] || l }}</option>
        </select>

        <!-- 2. Tier 2: Team Filter -->
        <select
          v-model="selectedTeam"
          class="rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none focus:border-sky-500/60"
        >
          <option v-for="t in filteredTeams" :key="t" :value="t">{{ t }}</option>
        </select>

        <button class="btn-ghost" type="button" :disabled="loading" @click="reload">
          <RefreshCw :size="14" :class="loading ? 'animate-spin' : ''" />
          Muat Ulang
        </button>
      </div>
    </div>

    <div v-if="error" class="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
      {{ error }}
    </div>

    <div v-if="loading && !data">
      <SkeletonCard :lines="4" />
      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <SkeletonCard :lines="5" />
        <SkeletonCard :lines="5" />
      </div>
    </div>

    <template v-else-if="data">
      <ClubHeader :data="data" />

      <TacticalBullets :bullets="data.tactical_bullets || []" />

      <div class="grid gap-4 lg:grid-cols-2">
        <TerritorialHeatmap :cells="data.territorial || []" :side="data.profile?.overload_side || 'Kanan'" />

        <div class="panel p-5">
          <div class="label-caps">Tren xG & Hasil</div>
          <h3 class="mb-3 mt-1 text-base font-semibold text-slate-100">10 Laga Terakhir</h3>
          <div class="space-y-2">
            <div
              v-for="(row, i) in data.xg_trend || []"
              :key="i"
              class="flex items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2"
            >
              <div class="min-w-0">
                <div class="truncate text-xs font-medium text-slate-200">{{ row.opponent }}</div>
                <div class="num text-[10px] text-slate-500">{{ row.date }}</div>
              </div>
              <div class="num shrink-0 text-right text-xs">
                <span class="text-sky-400">{{ row.xg_for }}</span>
                <span class="mx-1 text-slate-600">xG</span>
                <span class="text-rose-400">{{ row.xg_against }}</span>
              </div>
            </div>
            <div v-if="!(data.xg_trend || []).length" class="text-sm text-slate-500">
              Belum ada data tren xG.
            </div>
          </div>

          <div class="mt-5">
            <FormHistoryTable :history="data.form || []" />
          </div>

          <div class="mt-5 rounded-lg border border-slate-800 bg-slate-950/40 p-3">
            <div class="label-caps">Ringkasan Shot Metrics</div>
            <div class="num mt-2 grid grid-cols-2 gap-2 text-xs text-slate-300 sm:grid-cols-4">
              <div>Shots: <span class="text-slate-100">{{ data.shot_metrics?.shots ?? 0 }}</span></div>
              <div>Goals: <span class="text-emerald-400">{{ data.shot_metrics?.goals ?? 0 }}</span></div>
              <div>xG: <span class="text-sky-400">{{ data.shot_metrics?.xg_total ?? data.shot_metrics?.xg ?? 0 }}</span></div>
              <div>Conv: <span class="text-amber-400">{{ data.shot_metrics?.conversion_pct ?? 0 }}%</span></div>
            </div>
          </div>
        </div>
      </div>

      <UpcomingFixturesTable :fixtures="data.upcoming || []" />
    </template>
  </div>
</template>
