<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Download, Radio, RefreshCw } from 'lucide-vue-next'
import { fetchLeagues, fetchLiveStandings, fetchStandings } from '@/services/api'
import { LEAGUE_LABELS } from '@/utils/format'
import { useAsyncData } from '@/composables/useAsyncData'
import KpiCards from '@/components/standings/KpiCards.vue'
import ProjectedPointsChart from '@/components/standings/ProjectedPointsChart.vue'
import TeamTrajectoryGrid from '@/components/standings/TeamTrajectoryGrid.vue'
import TrajectoryChart from '@/components/standings/TrajectoryChart.vue'
import StandingsTable from '@/components/standings/StandingsTable.vue'
import LiveStandingsTable from '@/components/standings/LiveStandingsTable.vue'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'
import PageHeader from '@/components/shared/PageHeader.vue'

const route = useRoute()
const router = useRouter()

const leagues = ref([])
const league = ref(route.query.league || 'EPL')
const { data, loading, error, load } = useAsyncData(fetchStandings)

// Mode: 'projection' (Monte Carlo) | 'live' (klasemen aktual + skor berjalan)
const mode = ref(route.query.mode === 'live' ? 'live' : 'projection')
const liveData = ref(null)
const liveLoading = ref(false)
const liveError = ref(null)
let liveTimer = null

async function loadLive() {
  liveLoading.value = true
  liveError.value = null
  try {
    liveData.value = await fetchLiveStandings(league.value)
  } catch (err) {
    liveError.value = err?.response?.data?.detail || err?.message || 'Gagal memuat klasemen live'
    liveData.value = null
  } finally {
    liveLoading.value = false
  }
}

function setMode(m) {
  mode.value = m
  router.replace({ query: { league: league.value, ...(m === 'live' ? { mode: 'live' } : {}) } })
  if (m === 'live') loadLive()
}

async function reload() {
  router.replace({ query: { league: league.value, ...(mode.value === 'live' ? { mode: 'live' } : {}) } })
  if (mode.value === 'live') {
    await loadLive()
    return
  }
  await load(league.value, 350)
}

function exportCsv() {
  if (!data.value?.standings?.length) return
  const cols = [
    'projected_position',
    'team',
    'P',
    'W',
    'D',
    'L',
    'GF',
    'GA',
    'GD',
    'PTS',
    'ppg',
    'avg_xg_for',
    'avg_xg_ga',
    'projected_points',
    'title_pct',
    'top4_pct',
    'relegation_pct',
    'status',
  ]
  const header = [
    'POS', 'TEAM', 'M', 'M', 'S', 'K', 'GM', 'GK', 'SG', 'POIN',
    'PPG', 'XGF', 'XGA', 'PROJECTED', 'TITLE%', 'TOP4%', 'RELEG%', 'STATUS',
  ]
  const lines = [header.join(',')]
  for (const r of data.value.standings) {
    lines.push(cols.map((c) => r[c] ?? '').join(','))
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `proyeksi-${league.value}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

watch(league, reload)
onMounted(async () => {
  leagues.value = await fetchLeagues()
  await reload()
  liveTimer = setInterval(() => {
    if (mode.value === 'live' && !liveLoading.value) loadLive()
  }, 60000)
})
onBeforeUnmount(() => clearInterval(liveTimer))
</script>

<template>
  <div class="space-y-5">
    <PageHeader
      eyebrow="Season Projection Engine"
      title="Proyeksi Liga"
      subtitle="Simulasi Monte Carlo sisa musim — ambang juara, UCL, degradasi, dan dispersi poin."
    >
      <template #actions>
        <span v-if="mode === 'live'" class="chip border-bad/30 bg-bad/10 text-bad">
          <span class="mr-1.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-bad" />
          Klasemen Live · auto 60s
        </span>
        <template v-else>
          <span
            class="chip"
            :class="loading ? 'border-draw/30 bg-draw/10 text-draw' : 'border-ok/30 bg-ok/10 text-ok'"
          >
            <span class="mr-1.5 inline-block h-1.5 w-1.5 rounded-full" :class="loading ? 'bg-draw animate-pulse' : 'bg-ok'" />
            {{ loading ? 'Engine Simulasi…' : 'Engine Siap' }}
          </span>
          <button class="btn-ghost" type="button" :disabled="loading" @click="reload">
            <RefreshCw :size="14" :class="loading ? 'animate-spin' : ''" />
            Hitung Ulang
          </button>
          <button class="btn-ghost" type="button" @click="exportCsv">
            <Download :size="14" />
            Export CSV
          </button>
        </template>
      </template>
    </PageHeader>

    <!-- Mode toggle: Proyeksi vs Live -->
    <div class="flex flex-wrap items-center gap-2">
      <div class="flex rounded-lg border border-line bg-card/50 p-1">
        <button
          type="button"
          class="rounded-md px-3 py-1.5 text-xs font-semibold transition"
          :class="mode === 'projection' ? 'bg-home/15 text-home' : 'text-mute hover:text-ink'"
          @click="setMode('projection')"
        >
          Proyeksi Monte Carlo
        </button>
        <button
          type="button"
          class="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition"
          :class="mode === 'live' ? 'bg-bad/20 text-bad' : 'text-mute hover:text-ink'"
          @click="setMode('live')"
        >
          <Radio :size="13" />
          Klasemen Live
        </button>
      </div>
      <span v-if="mode === 'live'" class="text-[11px] text-mute">
        Poin aktual dari hasil nyata + skor laga yang sedang berjalan
      </span>
    </div>

    <div class="flex flex-wrap gap-2">
      <button
        v-for="l in leagues"
        :key="l.id"
        type="button"
        class="rounded-lg border px-3 py-2 text-xs font-semibold uppercase tracking-wider transition"
        :class="
          league === l.id
            ? 'border-home/50 bg-home/10 text-home'
            : 'border-line bg-card/50 text-mute hover:border-line hover:text-ink'
        "
        @click="league = l.id"
      >
        {{ l.name }}
      </button>
    </div>

    <!-- Klasemen Live -->
    <div
      v-if="mode === 'live' && liveError"
      class="rounded-lg border border-bad/30 bg-bad/10 px-4 py-3 text-sm text-bad"
    >
      {{ liveError }}
    </div>
    <div v-else-if="mode === 'live' && liveLoading && !liveData">
      <SkeletonCard :lines="10" />
    </div>
    <LiveStandingsTable
      v-else-if="mode === 'live' && liveData"
      :rows="liveData.table || []"
      :source="liveData.source"
    />

    <div v-else-if="mode === 'projection' && error" class="rounded-lg border border-bad/30 bg-bad/10 px-4 py-3 text-sm text-bad">
      {{ error }}
    </div>

    <div v-else-if="mode === 'projection' && loading && !data">
      <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SkeletonCard v-for="i in 4" :key="i" :lines="2" />
      </div>
      <div class="mt-4"><SkeletonCard :lines="8" /></div>
    </div>

    <template v-else-if="mode === 'projection' && data">
      <KpiCards :kpi="data.kpi || {}" />

      <TrajectoryChart :trajectory="data.trajectory || {}" :rows="data.standings || []" />

      <TeamTrajectoryGrid
        :trajectory="data.trajectory || {}"
        :rows="data.standings || []"
        :position-history="data.position_history || null"
      />

      <div class="panel flex flex-col gap-5 p-5 lg:flex-row lg:items-center">
        <div class="lg:w-2/5">
          <div class="label-caps">Status Simulasi</div>
          <h3 class="mt-1 text-base font-semibold text-ink">
            {{ data.league_name || LEAGUE_LABELS[league] || league }}
          </h3>
          <p class="mt-2 text-sm leading-relaxed text-mute">
            Model menjalankan <span class="num text-ink">{{ data.n_seasons }}</span> musim paralel
            berdasarkan xG power index, home/away bias, dan hasil aktual musim ini.
            Angka proyeksi adalah rerata statistik — bukan kepastian.
          </p>
        </div>
        <div class="grid flex-1 grid-cols-3 gap-3 text-center">
            <div class="rounded-lg border border-line bg-canvas/40 p-3">
              <div class="label-caps">Juara Teratas</div>
              <div class="mt-1 truncate text-sm font-semibold text-draw">
                {{ data.standings?.[0]?.team || '—' }}
              </div>
              <div class="num mt-0.5 text-xs text-mute">
                {{ data.standings?.[0]?.title_pct ?? 0 }}%
              </div>
            </div>
            <div class="rounded-lg border border-line bg-canvas/40 p-3">
              <div class="label-caps">Zona UCL Teratas</div>
              <div class="mt-1 truncate text-sm font-semibold text-home">
                {{ data.standings?.[0]?.team || '—' }}
              </div>
              <div class="num mt-0.5 text-xs text-mute">
                {{ data.standings?.[0]?.projected_points ?? 0 }} pts
              </div>
            </div>
            <div class="rounded-lg border border-line bg-canvas/40 p-3">
              <div class="label-caps">Risiko Tertinggi</div>
              <div class="mt-1 truncate text-sm font-semibold text-bad">
                {{ [...(data.standings || [])].sort((a, b) => b.relegation_pct - a.relegation_pct)[0]?.team || '—' }}
              </div>
              <div class="num mt-0.5 text-xs text-mute">
                {{ [...(data.standings || [])].sort((a, b) => b.relegation_pct - a.relegation_pct)[0]?.relegation_pct ?? 0 }}%
              </div>
            </div>
          </div>
      </div>

      <ProjectedPointsChart :rows="data.standings || []" :kpi="data.kpi || {}" />

      <StandingsTable :rows="data.standings || []" :position-history="data.position_history || null" />
    </template>
  </div>
</template>
