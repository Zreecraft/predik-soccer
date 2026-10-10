<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { RefreshCw, Zap, RotateCcw } from 'lucide-vue-next'
import { extractError, fetchLiveUcl, fetchUcl, postUclWhatIf } from '@/services/api'
import { useAsyncData } from '@/composables/useAsyncData'
import PotGrid from '@/components/ucl/PotGrid.vue'
import LeagueTable from '@/components/ucl/LeagueTable.vue'
import BracketTree from '@/components/ucl/BracketTree.vue'
import ChampionCard from '@/components/ucl/ChampionCard.vue'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'
import UclDrawer from '@/components/ucl/UclDrawer.vue'
import WhatIfFixtures from '@/components/ucl/WhatIfFixtures.vue'
import PageHeader from '@/components/shared/PageHeader.vue'
import MatchDetailModal from '@/components/shared/MatchDetailModal.vue'

const tabs = [
  { id: 'all', label: 'Bagan & Semua Babak' },
  { id: 'bracket', label: 'Bagan Visual Gugur' },
  { id: 'fase', label: 'Fase Liga & Play-off' },
]

const active = ref('all')
const { data, loading, error, load } = useAsyncData(fetchUcl)

// What-If Interactive Simulator
const whatIf = ref(false)
const overrides = reactive({ knockout: {}, league_fixtures: {} })
const recomputing = ref(false)
let recomputeTimer = null

const activeKoIds = computed(() => overrides.knockout)
const activeLpIds = computed(() => overrides.league_fixtures)
const overrideCount = computed(
  () => Object.keys(overrides.knockout).length + Object.keys(overrides.league_fixtures).length
)

function scheduleRecompute() {
  clearTimeout(recomputeTimer)
  recomputeTimer = setTimeout(recompute, 500)
}

async function recompute() {
  if (!whatIf.value) return
  recomputing.value = true
  try {
    const res = await postUclWhatIf(JSON.parse(JSON.stringify(overrides)))
    data.value = res
    error.value = null
  } catch (err) {
    error.value = extractError(err)
  } finally {
    recomputing.value = false
  }
}

function onKoEdit({ match, side, value }) {
  const id = match.match_id
  if (!id) return
  const cur = overrides.knockout[id] || {
    agg_home: match.agg_home ?? 0,
    agg_away: match.agg_away ?? 0,
  }
  if (side === 'home') cur.agg_home = value
  else cur.agg_away = value
  overrides.knockout[id] = { ...cur }
  scheduleRecompute()
}

function onLpUpdate({ match_id, side, value }) {
  const base = data.value?.league_fixtures?.find((f) => f.match_id === match_id)
  if (!base) return
  const cur = overrides.league_fixtures[match_id] || {
    goals_home: base.goals_home,
    goals_away: base.goals_away,
  }
  if (side === 'home') cur.goals_home = value
  else cur.goals_away = value
  overrides.league_fixtures[match_id] = { ...cur }
  scheduleRecompute()
}

function toggleWhatIf() {
  whatIf.value = !whatIf.value
  if (!whatIf.value) resetWhatIf()
}

function resetWhatIf() {
  clearTimeout(recomputeTimer)
  overrides.knockout = {}
  overrides.league_fixtures = {}
  scheduleRecompute()
}

// Drawer State Management
const selectedMatch = ref(null)
const isDrawerOpen = ref(false)

function openDrawer(match) {
  selectedMatch.value = match
  isDrawerOpen.value = true
}

function closeDrawer() {
  isDrawerOpen.value = false
}

// Live UCL matches
const uclLive = ref([])
const uclLiveSource = ref('mock')
const openLiveMatch = ref(null)
let uclLiveTimer = null

const uclLiveSourceLabel = computed(
  () => (uclLiveSource.value === 'api' ? 'football-data.org' : uclLiveSource.value === 'espn' ? 'ESPN' : 'demo')
)

async function refreshUclLive() {
  try {
    const d = await fetchLiveUcl()
    uclLive.value = d.matches || []
    uclLiveSource.value = d.source
  } catch {
    uclLive.value = []
  }
}

const showBracket = computed(() => active.value === 'all' || active.value === 'bracket')
const showFase = computed(() => active.value === 'all' || active.value === 'fase')

onMounted(() => {
  load()
  refreshUclLive()
  uclLiveTimer = setInterval(refreshUclLive, 60000)
})
onBeforeUnmount(() => clearInterval(uclLiveTimer))
</script>

<template>
  <div class="space-y-5">
    <!-- Top Header -->
    <PageHeader
      eyebrow="UEFA Champions League"
      title="Bagan & Simulasi UCL"
      subtitle="Klasemen 36 tim, babak Play-off, dan knockout bracket simetris dengan probabilitas pemenang."
    >
      <template #actions>
        <button
          class="rounded-lg border px-3 py-2 text-sm font-semibold transition"
          :class="
            whatIf
              ? 'border-amber-500/60 bg-amber-500/15 text-amber-300 shadow-lg shadow-amber-500/10'
              : 'border-slate-700 bg-slate-900/50 text-slate-400 hover:border-amber-500/50 hover:text-amber-300'
          "
          type="button"
          title="Ubah skor laga secara manual → seluruh bagan & peluang dihitung ulang"
          @click="toggleWhatIf"
        >
          <Zap :size="14" class="mr-1.5 inline-block" />
          {{ whatIf ? 'Tutup What-If' : 'What-If Simulator' }}
        </button>
        <button class="btn-ghost" type="button" :disabled="loading" @click="load">
          <RefreshCw :size="14" :class="loading ? 'animate-spin' : ''" />
          Simulasi Ulang
        </button>
      </template>
    </PageHeader>

    <!-- Live UCL -->
    <div class="panel overflow-hidden border-rose-500/30">
      <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 bg-slate-950/40 px-4 py-3">
        <div class="flex items-center gap-2 text-sm font-semibold text-slate-200">
          <span class="flex items-center gap-1.5 rounded bg-rose-600 px-1.5 py-0.5 text-[10px] font-extrabold tracking-widest text-white">
            <span class="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-white" />
            LIVE
          </span>
          Laga Champions League
        </div>
        <span class="text-[10px] uppercase tracking-wider text-slate-500">
          {{ uclLiveSourceLabel }} · auto 60s · klik laga untuk detail
        </span>
      </div>
      <div v-if="uclLive.length" class="divide-y divide-slate-800/70">
        <button
          v-for="m in uclLive"
          :key="m.id"
          type="button"
          class="flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-slate-800/30"
          title="Klik untuk lihat timeline, kartu & line-up"
          @click="openLiveMatch = m"
        >
          <span class="num w-8 shrink-0 text-right text-xs font-bold text-rose-400">
            {{ m.status === 'PAUSED' ? 'HT' : m.minute != null ? `${m.minute}'` : '—' }}
          </span>
          <img v-if="m.crest_home" :src="m.crest_home" :alt="m.home" class="h-6 w-6 shrink-0 object-contain" />
          <span class="flex-1 truncate text-right text-sm font-medium text-slate-200">{{ m.home }}</span>
          <span class="num shrink-0 rounded bg-slate-900 px-2 py-1 text-sm font-bold text-slate-50 ring-1 ring-rose-500/40">
            {{ m.home_score ?? 0 }}<span class="mx-0.5 text-slate-600">-</span>{{ m.away_score ?? 0 }}
          </span>
          <span class="flex-1 truncate text-sm font-medium text-slate-200">{{ m.away }}</span>
          <img v-if="m.crest_away" :src="m.crest_away" :alt="m.away" class="h-6 w-6 shrink-0 object-contain" />
        </button>
      </div>
      <div v-else class="px-4 py-4 text-sm text-slate-500">
        Tidak ada laga UCL yang sedang berlangsung — panel update otomatis tiap 60 detik.
      </div>
    </div>

    <!-- Tab navigation -->
    <div class="flex flex-wrap gap-2">
      <button
        v-for="t in tabs"
        :key="t.id"
        type="button"
        class="rounded-lg border px-3 py-2 text-xs font-semibold uppercase tracking-wider transition"
        :class="
          active === t.id
            ? 'border-sky-500/50 bg-sky-500/10 text-sky-400'
            : 'border-slate-700 bg-slate-900/50 text-slate-400 hover:border-slate-600 hover:text-slate-200'
        "
        @click="active = t.id"
      >
        {{ t.label }}
      </button>
    </div>

    <!-- What-If status bar -->
    <div
      v-if="whatIf"
      class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-500/40 bg-[#1c1508]/70 px-4 py-3"
    >
      <div class="flex items-center gap-2.5 text-sm text-amber-200">
        <span class="inline-block h-2 w-2 shrink-0 animate-pulse rounded-full bg-amber-400" />
        <span>
          <strong class="font-bold">Mode What-If aktif</strong>
          — {{ overrideCount }} override · edit skor pada kartu bagan (agregat) atau daftar Fase Liga.
        </span>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="recomputing" class="num text-xs text-amber-400">Menghitung ulang…</span>
        <button
          class="rounded-lg border border-slate-600 bg-slate-900/60 px-3 py-1.5 text-xs font-semibold text-slate-300 transition hover:border-slate-500 hover:text-slate-100"
          type="button"
          @click="resetWhatIf"
        >
          <RotateCcw :size="12" class="mr-1 inline-block" />
          Reset
        </button>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
      {{ error }}
    </div>

    <!-- Skeleton Loading -->
    <div v-if="loading && !data">
      <div class="grid gap-4 lg:grid-cols-3">
        <div class="lg:col-span-2"><SkeletonCard :lines="10" /></div>
        <SkeletonCard :lines="8" />
      </div>
    </div>

    <!-- Main Content -->
    <template v-else-if="data">
      <!-- What-If: editor skor fase liga -->
      <WhatIfFixtures
        v-if="whatIf"
        :fixtures="data.league_fixtures || []"
        :active-ids="activeLpIds"
        @update="onLpUpdate"
      />

      <!-- 1. Full-Width Symmetrical Visual Tournament Bracket -->
      <div v-if="showBracket" class="w-full">
        <BracketTree
          :knockout="data.knockout_stage || {}"
          :champion="data.champion || {}"
          :edit="whatIf"
          @select-match="openDrawer"
          @edit-score="onKoEdit"
        />
      </div>

      <!-- 2. Klasemen Fase Liga (seluruh 36 tim + zona play-off) -->
      <LeagueTable v-if="showFase" :rows="data.league_phase || []" />

      <!-- 3. Alokasi Pot & Champion -->
      <div v-if="showFase" class="grid gap-4 lg:grid-cols-3">
        <div class="lg:col-span-2">
          <PotGrid :pots="data.pots || {}" />
        </div>

        <div>
          <ChampionCard :champion="data.champion || {}" />
        </div>
      </div>
    </template>

    <!-- Side-Over Drawer Modal -->
    <UclDrawer
      :is-open="isDrawerOpen"
      :match-data="selectedMatch"
      @close="closeDrawer"
    />

    <!-- Detail laga UCL live -->
    <MatchDetailModal :is-open="!!openLiveMatch" :match="openLiveMatch" @close="openLiveMatch = null" />
  </div>
</template>
