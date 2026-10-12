<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Radio, Search, X } from 'lucide-vue-next'
import { fetchModelStats, fetchSchedule } from '@/services/api'
import { formatWib, formatWibDay, formatWibTime, leagueAccent, LEAGUE_LABELS } from '@/utils/format'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  leagues: { type: Array, default: () => [] },
  selected: { type: Object, default: null },
})
const emit = defineEmits(['close', 'select'])

const TABS = [
  { id: 'live', label: 'Live / Hari Ini', badge: 'text-rose-400' },
  { id: 'upcoming', label: 'Mendatang', badge: 'text-sky-400' },
  { id: 'finished', label: 'Hasil Selesai', badge: 'text-emerald-400' },
]

const tab = ref('live')
const league = ref('')
const q = ref('')
const items = ref([])
const counts = ref({ upcoming: 0, live: 0, finished: 0 })
const total = ref(0)
const loading = ref(false)
const error = ref('')
const modelStats = ref(null)
let qTimer = null

const allLeagues = computed(() => {
  if (props.leagues.length) return props.leagues
  return Object.entries(LEAGUE_LABELS).map(([id, name]) => ({ id, name }))
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchSchedule({
      tab: tab.value,
      league: league.value || null,
      q: q.value.trim() || null,
      limit: 80,
    })
    items.value = data.items || []
    counts.value = data.counts || { upcoming: 0, live: 0, finished: 0 }
    total.value = data.total || 0
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Gagal memuat jadwal'
    items.value = []
  } finally {
    loading.value = false
  }
}

async function loadModelStats() {
  try {
    modelStats.value = await fetchModelStats()
  } catch {
    modelStats.value = null
  }
}

function pick(item) {
  emit('select', { league: item.league, home: item.home, away: item.away })
  emit('close')
}

function onKey(e) {
  if (e.key === 'Escape') emit('close')
}

watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      window.addEventListener('keydown', onKey)
      load()
      if (!modelStats.value) loadModelStats()
    } else {
      window.removeEventListener('keydown', onKey)
    }
  },
  { immediate: true }
)
watch([tab, league], load)
watch(q, () => {
  clearTimeout(qTimer)
  qTimer = setTimeout(load, 300)
})
onBeforeUnmount(() => {
  clearTimeout(qTimer)
  window.removeEventListener('keydown', onKey)
})

const verdictStyle = {
  exact: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
  outcome: 'border-sky-500/40 bg-sky-500/10 text-sky-400',
  miss: 'border-rose-500/40 bg-rose-500/10 text-rose-400',
}
const verdictLabel = { exact: 'TEPAT SKOR', outcome: 'TEPAT HASIL', miss: 'MELESET' }

const accuracyPct = computed(() => {
  const m = modelStats.value?.recent_metrics?.[0]
  if (!m?.accuracy && m?.accuracy !== 0) return null
  const acc = Number(m.accuracy)
  return acc <= 1 ? (acc * 100).toFixed(1) : acc.toFixed(1)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="picker-fade">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[60] flex items-start justify-center overflow-y-auto bg-black/70 p-3 backdrop-blur-sm sm:items-center sm:p-4"
        @click.self="emit('close')"
      >
        <div class="panel w-full max-w-3xl overflow-hidden shadow-2xl shadow-black/50">
          <!-- Header -->
          <div class="relative overflow-hidden border-b border-slate-800">
            <div class="absolute inset-0 bg-gradient-to-r from-sky-500/15 via-indigo-500/10 to-emerald-500/10" />
            <div class="relative px-4 pb-3 pt-4 sm:px-5">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <div class="eyebrow text-sky-400">Match Picker</div>
                  <h2 class="mt-1 text-lg font-bold text-slate-50">Cari Laga</h2>
                  <p class="mt-0.5 text-xs text-slate-400">
                    Klik kartu untuk masuk ke prediksi. Laga selesai tetap tersedia untuk perbandingan & pembelajaran model.
                  </p>
                </div>
                <button
                  type="button"
                  class="rounded-lg border border-slate-700 p-1.5 text-slate-400 transition hover:bg-slate-800 hover:text-slate-100"
                  aria-label="Tutup"
                  @click="emit('close')"
                >
                  <X :size="16" />
                </button>
              </div>

              <!-- Search -->
              <div class="relative mt-3">
                <Search :size="15" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  v-model="q"
                  type="search"
                  placeholder="Cari nama tim… (mis. Arsenal)"
                  class="w-full rounded-lg border border-slate-700 bg-slate-950/70 py-2.5 pl-9 pr-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-sky-500/60"
                />
              </div>

              <!-- League pills -->
              <div class="mt-3 flex flex-wrap gap-1.5">
                <button
                  type="button"
                  class="rounded-full border px-3 py-1 text-xs font-semibold transition"
                  :class="
                    league === ''
                      ? 'border-slate-500 bg-slate-700/60 text-slate-50'
                      : 'border-slate-700 bg-slate-900/60 text-slate-400 hover:border-slate-500 hover:text-slate-200'
                  "
                  @click="league = ''"
                >
                  Semua
                </button>
                <button
                  v-for="l in allLeagues"
                  :key="l.id"
                  type="button"
                  class="rounded-full border px-3 py-1 text-xs font-semibold transition"
                  :class="
                    league === l.id
                      ? `${leagueAccent(l.id).chip}`
                      : 'border-slate-700 bg-slate-900/60 text-slate-400 hover:text-slate-200'
                  "
                  @click="league = league === l.id ? '' : l.id"
                >
                  {{ LEAGUE_LABELS[l.id] || l.name }}
                </button>
              </div>
            </div>

            <!-- Tabs -->
            <div class="relative flex gap-1 px-3">
              <button
                v-for="t in TABS"
                :key="t.id"
                type="button"
                class="relative flex items-center gap-1.5 rounded-t-lg border-x border-t px-3 py-2 text-xs font-bold transition"
                :class="
                  tab === t.id
                    ? 'border-slate-700 bg-slate-900 text-slate-50'
                    : 'border-transparent text-slate-500 hover:text-slate-300'
                "
                @click="tab = t.id"
              >
                <Radio v-if="t.id === 'live'" :size="12" :class="tab === t.id ? 'text-rose-400' : ''" />
                {{ t.label }}
                <span
                  class="num rounded px-1.5 py-0.5 text-[10px] font-extrabold"
                  :class="tab === t.id ? `${t.badge} bg-slate-800` : 'bg-slate-800/60 text-slate-500'"
                >
                  {{ counts[t.id] ?? 0 }}
                </span>
              </button>
            </div>
          </div>

          <!-- Body -->
          <div class="min-h-[220px] max-h-[58vh] overflow-y-auto bg-slate-950/40 p-3 sm:p-4">
            <div v-if="loading && !items.length">
              <SkeletonCard :lines="5" />
            </div>

            <div v-else-if="error" class="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
              {{ error }}
            </div>

            <div v-else-if="!items.length" class="flex flex-col items-center justify-center gap-2 py-10 text-center">
              <Search :size="26" class="text-slate-600" />
              <p class="text-sm font-semibold text-slate-400">Tidak ada laga cocok</p>
              <p class="text-xs text-slate-600">Coba ubah kata kunci, liga, atau tab lain.</p>
            </div>

            <div v-else class="grid gap-2">
              <button
                v-for="m in items"
                :key="m.id + m.home"
                type="button"
                class="group relative flex w-full items-stretch overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 text-left transition hover:border-slate-600 hover:bg-slate-800/70"
                :class="
                  selected && selected.home === m.home && selected.away === m.away
                    ? '!border-sky-500/60 ring-1 ring-sky-500/30'
                    : ''
                "
                @click="pick(m)"
              >
                <!-- Bar warna liga -->
                <span class="w-1 shrink-0" :class="leagueAccent(m.league).bar" />

                <div class="min-w-0 flex-1 px-3 py-2.5 sm:px-4">
                  <!-- Liga + tanggal -->
                  <div class="mb-2 flex items-center gap-2">
                    <span class="rounded border px-1.5 py-0.5 text-[9px] font-extrabold tracking-wider" :class="leagueAccent(m.league).chip">
                      {{ LEAGUE_LABELS[m.league] || m.league }}
                    </span>
                    <span class="truncate text-[10px] text-slate-500">{{ formatWibDay(m.date) }}</span>
                    <span
                      v-if="m.status === 'live'"
                      class="ml-auto flex items-center gap-1 rounded bg-rose-600 px-1.5 py-0.5 text-[9px] font-extrabold tracking-widest text-white"
                    >
                      <span class="inline-block h-1 w-1 animate-pulse rounded-full bg-white" />
                      {{ m.minute != null ? m.minute + "'" : 'LIVE' }}
                    </span>
                    <span v-else-if="m.status === 'finished'" class="ml-auto rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[9px] font-extrabold tracking-widest text-slate-400">
                      FT
                    </span>
                  </div>

                  <!-- Tim -->
                  <div class="flex items-center gap-2 sm:gap-3">
                    <div class="flex min-w-0 flex-1 items-center justify-end gap-2 text-right">
                      <span class="truncate text-sm font-bold text-slate-100">{{ m.home }}</span>
                      <img
                        v-if="m.home_logo"
                        :src="m.home_logo"
                        :alt="m.home"
                        class="h-7 w-7 shrink-0 object-contain sm:h-8 sm:w-8"
                      />
                    </div>

                    <div class="shrink-0 text-center">
                      <template v-if="m.home_score != null && m.away_score != null">
                        <div class="num text-lg font-extrabold leading-none">
                          <span class="text-sky-400">{{ m.home_score }}</span>
                          <span class="mx-1 text-slate-600">:</span>
                          <span class="text-rose-400">{{ m.away_score }}</span>
                        </div>
                      </template>
                      <template v-else>
                        <div class="num text-sm font-extrabold text-slate-300">VS</div>
                        <div class="text-[10px] text-slate-500">{{ formatWibTime(m.date) }}</div>
                      </template>
                    </div>

                    <div class="flex min-w-0 flex-1 items-center gap-2">
                      <img
                        v-if="m.away_logo"
                        :src="m.away_logo"
                        :alt="m.away"
                        class="h-7 w-7 shrink-0 object-contain sm:h-8 sm:w-8"
                      />
                      <span class="truncate text-sm font-bold text-slate-100">{{ m.away }}</span>
                    </div>
                  </div>

                  <!-- Perbandingan prediksi vs aktual (laga selesai) -->
                  <div
                    v-if="m.status === 'finished' && (m.prediction || m.verdict)"
                    class="mt-2 flex flex-wrap items-center justify-center gap-1.5"
                  >
                    <span
                      v-if="m.prediction && m.prediction.home != null"
                      class="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[10px] font-semibold text-slate-300"
                    >
                      Prediksi {{ m.prediction.home }}-{{ m.prediction.away }}
                    </span>
                    <span
                      v-if="m.home_score != null"
                      class="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[10px] font-semibold text-slate-300"
                    >
                      Aktual {{ m.home_score }}-{{ m.away_score }}
                    </span>
                    <span
                      v-if="m.verdict"
                      class="rounded border px-1.5 py-0.5 text-[10px] font-extrabold tracking-wide"
                      :class="verdictStyle[m.verdict.label]"
                    >
                      {{ verdictLabel[m.verdict.label] }}
                    </span>
                  </div>

                  <!-- Prediksi tersimpan (belum main / live) -->
                  <div
                    v-else-if="m.prediction && m.prediction.home != null"
                    class="mt-2 flex justify-center"
                  >
                    <span class="rounded border border-slate-700/80 bg-slate-800/60 px-1.5 py-0.5 text-[10px] font-semibold text-slate-400">
                      Prediksi tersimpan {{ m.prediction.home }}-{{ m.prediction.away }}
                    </span>
                  </div>
                </div>
              </button>

              <p v-if="total > items.length" class="pt-1 text-center text-[11px] text-slate-500">
                Menampilkan {{ items.length }} dari {{ total }} laga — persempit dengan pencarian atau filter liga.
              </p>
            </div>
          </div>

          <!-- Footer: akurasi model (pembelajaran sistem) -->
          <div class="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-slate-800 bg-slate-950/70 px-4 py-2.5 sm:px-5">
            <span class="label-caps text-slate-500">Pembelajaran Sistem</span>
            <template v-if="modelStats">
              <span class="text-[11px] text-slate-400">
                Prediksi <b class="num text-slate-200">{{ modelStats.total_predictions }}</b>
                · dievaluasi <b class="num text-emerald-400">{{ modelStats.evaluated }}</b>
                · menunggu <b class="num text-slate-300">{{ modelStats.pending }}</b>
              </span>
              <span v-if="accuracyPct != null" class="text-[11px] text-slate-400">
                Akurasi outcome <b class="num text-sky-400">{{ accuracyPct }}%</b>
              </span>
              <span v-if="modelStats.recent_metrics?.[0]?.brier_score != null" class="text-[11px] text-slate-400">
                Brier <b class="num text-slate-200">{{ modelStats.recent_metrics[0].brier_score }}</b>
              </span>
            </template>
            <span v-else class="text-[11px] text-slate-600">Memuat statistik model…</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.picker-fade-enter-active,
.picker-fade-leave-active {
  transition: opacity 0.18s ease;
}
.picker-fade-enter-active > div,
.picker-fade-leave-active > div {
  transition: transform 0.18s ease;
}
.picker-fade-enter-from,
.picker-fade-leave-to {
  opacity: 0;
}
.picker-fade-enter-from > div,
.picker-fade-leave-to > div {
  transform: translateY(12px) scale(0.98);
}
</style>
