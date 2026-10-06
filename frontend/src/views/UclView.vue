<script setup>
import { computed, onMounted, ref } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import { fetchUcl } from '@/services/api'
import { useAsyncData } from '@/composables/useAsyncData'
import PotGrid from '@/components/ucl/PotGrid.vue'
import BracketTree from '@/components/ucl/BracketTree.vue'
import ChampionCard from '@/components/ucl/ChampionCard.vue'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'

const tabs = [
  { id: 'all', label: 'Semua Babak' },
  { id: 'pots', label: 'Fase Liga (Pot)' },
  { id: 'r16', label: '16 Besar' },
  { id: 'sf', label: 'Semifinal' },
  { id: 'final', label: 'Final' },
]

const active = ref('all')
const { data, loading, error, load } = useAsyncData(fetchUcl)

const showPots = computed(() => active.value === 'all' || active.value === 'pots')
const showR16 = computed(() => active.value === 'all' || active.value === 'r16')
const showSf = computed(() => active.value === 'all' || active.value === 'sf')
const showFinal = computed(() => active.value === 'all' || active.value === 'final')

onMounted(load)
</script>

<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <div class="label-caps text-sky-400/90">UEFA Champions League</div>
        <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-50">Bagan & Simulasi UCL</h1>
        <p class="mt-1 text-sm text-slate-400">
          League Phase 36 tim, alokasi pot, dan knockout bracket dengan probabilitas pemenang.
        </p>
      </div>
      <button class="btn-ghost" type="button" :disabled="loading" @click="load">
        <RefreshCw :size="14" :class="loading ? 'animate-spin' : ''" />
        Simulasi Ulang
      </button>
    </div>

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

    <div v-if="error" class="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
      {{ error }}
    </div>

    <div v-if="loading && !data">
      <div class="grid gap-4 lg:grid-cols-3">
        <div class="lg:col-span-2"><SkeletonCard :lines="10" /></div>
        <SkeletonCard :lines="8" />
      </div>
    </div>

    <template v-else-if="data">
      <div class="grid gap-4 lg:grid-cols-3">
        <div class="space-y-4 lg:col-span-2">
          <PotGrid v-if="showPots" :pots="data.pots || {}" />

          <div v-if="showR16" class="grid gap-4 xl:grid-cols-2">
            <div class="panel p-4">
              <BracketTree
                :matches="data.knockout_stage?.playoffs || []"
                title="Play-off Knockout"
              />
            </div>
            <div class="panel p-4">
              <BracketTree
                :matches="data.knockout_stage?.round_of_16 || []"
                title="Babak 16 Besar"
              />
            </div>
          </div>

          <div v-if="showSf" class="grid gap-4 xl:grid-cols-2">
            <div class="panel p-4">
              <BracketTree
                :matches="data.knockout_stage?.quarter_finals || []"
                title="Perempat Final"
              />
            </div>
            <div class="panel p-4">
              <BracketTree
                :matches="data.knockout_stage?.semi_finals || []"
                title="Semifinal"
              />
            </div>
          </div>

          <div v-if="showFinal" class="panel p-4">
            <BracketTree
              :matches="[data.knockout_stage?.final].filter(Boolean)"
              title="Grand Final"
            />
          </div>
        </div>

        <div class="space-y-4">
          <ChampionCard :champion="data.champion || {}" />

          <div class="panel p-5">
            <div class="label-caps">League Phase Snapshot</div>
            <div class="mt-3 space-y-2">
              <div
                v-for="row in (data.league_phase || []).slice(0, 8)"
                :key="row.team"
                class="flex items-center justify-between gap-2 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2"
              >
                <div class="flex min-w-0 items-center gap-2">
                  <span class="num w-6 text-[11px] text-slate-500">{{ row.position }}</span>
                  <img v-if="row.logo" :src="row.logo" class="h-5 w-5 object-contain" :alt="row.team" />
                  <span class="truncate text-xs font-medium text-slate-200">{{ row.team }}</span>
                </div>
                <div class="num shrink-0 text-[11px] text-sky-400">{{ row.PTS }} pts</div>
              </div>
            </div>
            <p class="mt-3 text-[11px] leading-relaxed text-slate-500">
              8 teratas lolos langsung ke 16 besar. Posisi 9–24 melalui play-off knockout.
            </p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
