<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Download, Radio, RefreshCw } from 'lucide-vue-next'
import { fetchLeagues, fetchLiveStandings, fetchStandings } from '@/services/api'
import { LEAGUE_LABELS } from '@/utils/format'
import { useAsyncData } from '@/composables/useAsyncData'
import KpiCards from '@/components/standings/KpiCards.vue'
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
    'PTS',
    'projected_points',
    'title_pct',
    'top4_pct',
    'relegation_pct',
  ]
  const header = ['POS', 'TEAM', 'P', 'PTS', 'PROJECTED', 'TITLE%', 'TOP4%', 'RELEG%']
  const lines = [header.join(',')]
  for (const r of data.value.standings) {
    lines.push(cols.map((c) => r[c]).join(','))
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
        <span v-if="mode === 'live'" class="chip border-rose-500/30 bg-rose-500/10 text-rose-400">
          <span class="mr-1.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-rose-400" />
          Klasemen Live · auto 60s
        </span>
        <template v-else>
          <span
            class="chip"
            :class="loading ? 'border-amber-500/30 bg-amber-500/10 text-amber-400' : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'"
          >
            <span class="mr-1.5 inline-block h-1.5 w-1.5 rounded-full" :class="loading ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'" />
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
      <div class="flex rounded-lg border border-slate-700 bg-slate-900/50 p-1">
        <button
          type="button"
          class="rounded-md px-3 py-1.5 text-xs font-semibold transition"
          :class="mode === 'projection' ? 'bg-sky-500/15 text-sky-400' : 'text-slate-400 hover:text-slate-200'"
          @click="setMode('projection')"
        >
          Proyeksi Monte Carlo
        </button>
        <button
          type="button"
          class="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition"
          :class="mode === 'live' ? 'bg-rose-500/20 text-rose-300' : 'text-slate-400 hover:text-slate-200'"
          @click="setMode('live')"
        >
          <Radio :size="13" />
          Klasemen Live
        </button>
      </div>
      <span v-if="mode === 'live'" class="text-[11px] text-slate-500">
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
            ? 'border-sky-500/50 bg-sky-500/10 text-sky-400'
            : 'border-slate-700 bg-slate-900/50 text-slate-400 hover:border-slate-600 hover:text-slate-200'
        "
        @click="league = l.id"
      >
        {{ l.name }}
      </button>
    </div>

    <!-- Klasemen Live -->
    <div
      v-if="mode === 'live' && liveError"
      class="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300"
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

    <div v-else-if="mode === 'projection' && error" class="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
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

      <div class="grid gap-4 lg:grid-cols-5">
        <div class="lg:col-span-2">
          <TrajectoryChart :trajectory="data.trajectory || {}" />
        </div>
        <div class="panel flex flex-col justify-between p-5 lg:col-span-3">
          <div>
            <div class="label-caps">Status Simulasi</div>
            <h3 class="mt-1 text-base font-semibold text-slate-100">
              {{ data.league_name || LEAGUE_LABELS[league] || league }}
            </h3>
            <p class="mt-2 text-sm leading-relaxed text-slate-400">
              Model menjalankan <span class="num text-slate-200">{{ data.n_seasons }}</span> musim paralel
              berdasarkan xG power index, home/away bias, dan hasil aktual musim ini.
              Angka proyeksi adalah rerata statistik — bukan kepastian.
            </p>
          </div>
          <div class="mt-4 grid grid-cols-3 gap-3 text-center">
            <div class="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
              <div class="label-caps">Juara Teratas</div>
              <div class="mt-1 truncate text-sm font-semibold text-amber-400">
                {{ data.standings?.[0]?.team || '—' }}
              </div>
              <div class="num mt-0.5 text-xs text-slate-400">
                {{ data.standings?.[0]?.title_pct ?? 0 }}%
              </div>
            </div>
            <div class="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
              <div class="label-caps">Zona UCL Teratas</div>
              <div class="mt-1 truncate text-sm font-semibold text-sky-400">
                {{ data.standings?.[0]?.team || '—' }}
              </div>
              <div class="num mt-0.5 text-xs text-slate-400">
                {{ data.standings?.[0]?.projected_points ?? 0 }} pts
              </div>
            </div>
            <div class="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
              <div class="label-caps">Risiko Tertinggi</div>
              <div class="mt-1 truncate text-sm font-semibold text-rose-400">
                {{ [...(data.standings || [])].sort((a, b) => b.relegation_pct - a.relegation_pct)[0]?.team || '—' }}
              </div>
              <div class="num mt-0.5 text-xs text-slate-400">
                {{ [...(data.standings || [])].sort((a, b) => b.relegation_pct - a.relegation_pct)[0]?.relegation_pct ?? 0 }}%
              </div>
            </div>
          </div>
        </div>
      </div>

      <StandingsTable :rows="data.standings || []" />
    </template>
  </div>
</template>
