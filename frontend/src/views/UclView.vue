<script setup>
import { computed, onMounted, ref } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import { fetchUcl } from '@/services/api'
import { useAsyncData } from '@/composables/useAsyncData'
import PotGrid from '@/components/ucl/PotGrid.vue'
import LeagueTable from '@/components/ucl/LeagueTable.vue'
import BracketTree from '@/components/ucl/BracketTree.vue'
import ChampionCard from '@/components/ucl/ChampionCard.vue'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'
import UclDrawer from '@/components/ucl/UclDrawer.vue'

const tabs = [
  { id: 'all', label: 'Bagan & Semua Babak' },
  { id: 'bracket', label: 'Bagan Visual Gugur' },
  { id: 'fase', label: 'Fase Liga & Play-off' },
]

const active = ref('all')
const { data, loading, error, load } = useAsyncData(fetchUcl)

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

const showBracket = computed(() => active.value === 'all' || active.value === 'bracket')
const showFase = computed(() => active.value === 'all' || active.value === 'fase')

onMounted(load)
</script>

<template>
  <div class="space-y-5">
    <!-- Top Header -->
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <div class="label-caps text-sky-400/90">UEFA Champions League</div>
        <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-50">Bagan & Simulasi UCL</h1>
        <p class="mt-1 text-sm text-slate-400">
          Klasemen 36 tim, babak Play-off, dan knockout bracket simetris dengan probabilitas pemenang.
        </p>
      </div>
      <button class="btn-ghost" type="button" :disabled="loading" @click="load">
        <RefreshCw :size="14" :class="loading ? 'animate-spin' : ''" />
        Simulasi Ulang
      </button>
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
      <!-- 1. Full-Width Symmetrical Visual Tournament Bracket -->
      <div v-if="showBracket" class="w-full">
        <BracketTree
          :knockout="data.knockout_stage || {}"
          :champion="data.champion || {}"
          @select-match="openDrawer"
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
  </div>
</template>
