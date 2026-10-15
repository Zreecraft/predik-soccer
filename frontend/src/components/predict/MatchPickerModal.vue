<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { CheckCircle2, CircleAlert, Radio, Search, X, XCircle } from 'lucide-vue-next'
import { fetchModelStats, fetchSchedule } from '@/services/api'
import { formatWibDay, formatWibTime, LEAGUE_LABELS } from '@/utils/format'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  leagues: { type: Array, default: () => [] },
  selected: { type: Object, default: null },
})
const emit = defineEmits(['close', 'select'])

const TABS = [
  { id: 'live', label: 'Live / Hari ini' },
  { id: 'upcoming', label: 'Mendatang' },
  { id: 'finished', label: 'Hasil selesai' },
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
  emit('select', { league: item.league, home: item.home, away: item.away, date: item.date })
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
  exact: 'color: var(--ok)',
  outcome: 'color: var(--ink)',
  miss: 'color: var(--bad)',
}
const verdictLabel = { exact: 'Tepat skor', outcome: 'Tepat hasil', miss: 'Meleset' }

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
          <div class="border-b" style="border-color: var(--line)">
            <div class="px-4 pb-3 pt-4 sm:px-5">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <h2 class="font-display text-lg font-bold" style="color: var(--ink)">Cari laga</h2>
                  <p class="mt-0.5 text-[13px]" style="color: var(--mute)">
                    Pilih laga untuk melihat prediksinya. Laga selesai tetap tersedia untuk perbandingan.
                  </p>
                </div>
                <button
                  type="button"
                  class="rounded-elem border p-1.5 transition"
                  style="border-color: var(--line); color: var(--mute)"
                  aria-label="Tutup"
                  @click="emit('close')"
                >
                  <X :size="16" />
                </button>
              </div>

              <!-- Search -->
              <div class="relative mt-3">
                <Search :size="16" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2" style="color: var(--mute)" />
                <input
                  v-model="q"
                  type="search"
                  placeholder="Cari nama tim… (mis. Arsenal)"
                  class="w-full rounded-elem border bg-transparent py-2.5 pl-9 pr-3 text-[15px] outline-none transition"
                  style="border-color: var(--line); color: var(--ink)"
                />
              </div>

              <!-- League pills -->
              <div class="mt-3 flex flex-wrap gap-1.5">
                <button
                  type="button"
                  class="rounded-full border px-3 py-1 text-[13px] font-medium transition"
                  :style="league === ''
                    ? 'border-color: var(--home); color: var(--home)'
                    : 'border-color: var(--line); color: var(--mute)'"
                  @click="league = ''"
                >
                  Semua
                </button>
                <button
                  v-for="l in allLeagues"
                  :key="l.id"
                  type="button"
                  class="rounded-full border px-3 py-1 text-[13px] font-medium transition"
                  :style="league === l.id
                    ? 'border-color: var(--home); color: var(--home)'
                    : 'border-color: var(--line); color: var(--mute)'"
                  @click="league = league === l.id ? '' : l.id"
                >
                  {{ LEAGUE_LABELS[l.id] || l.name }}
                </button>
              </div>
            </div>

            <!-- Tabs -->
            <div class="flex gap-1 overflow-x-auto px-3">
              <button
                v-for="t in TABS"
                :key="t.id"
                type="button"
                class="relative shrink-0 border-b-2 px-3 py-2 text-[13px] font-medium transition"
                :style="tab === t.id
                  ? 'border-color: var(--home); color: var(--ink)'
                  : 'border-color: transparent; color: var(--mute)'"
                @click="tab = t.id"
              >
                <Radio v-if="t.id === 'live'" :size="13" class="mr-1 inline" />
                {{ t.label }}
                <span class="num ml-1" :style="tab === t.id ? 'color: var(--ink)' : 'color: var(--mute)'">
                  {{ counts[t.id] ?? 0 }}
                </span>
              </button>
            </div>
          </div>

          <!-- Body -->
          <div class="min-h-[220px] max-h-[58vh] overflow-y-auto p-2">
            <div v-if="loading && !items.length">
              <SkeletonCard :lines="5" />
            </div>

            <div
              v-else-if="error"
              class="rounded-elem border px-4 py-3 text-[15px]"
              style="border-color: var(--bad); color: var(--bad)"
            >
              {{ error }}
            </div>

            <div v-else-if="!items.length" class="flex flex-col items-center justify-center gap-2 py-10 text-center">
              <Search :size="26" style="color: var(--mute)" />
              <p class="text-[15px] font-semibold" style="color: var(--ink)">Tidak ada laga cocok</p>
              <p class="text-[13px]" style="color: var(--mute)">Coba ubah kata kunci, liga, atau tab lain.</p>
            </div>

            <div v-else class="flex flex-col">
              <button
                v-for="m in items"
                :key="m.id + m.home"
                type="button"
                class="flex w-full items-center gap-3 rounded-elem px-3 py-2.5 text-left transition"
                :style="selected && selected.home === m.home && selected.away === m.away
                  ? 'background: color-mix(in srgb, var(--home) 12%, transparent)'
                  : ''"
                @click="pick(m)"
              >
                <!-- Tanggal -->
                <span class="w-[86px] shrink-0 text-[13px]" style="color: var(--mute)">
                  {{ formatWibDay(m.date) }}
                </span>

                <!-- Tim A skor Tim B (dengan logo) -->
                <span class="flex min-w-0 flex-1 items-center justify-center gap-2">
                  <span class="min-w-0 flex-1 truncate text-right text-[15px] font-medium" style="color: var(--ink)">
                    {{ m.home }}
                  </span>
                  <img
                    v-if="m.home_logo"
                    :src="m.home_logo"
                    :alt="m.home"
                    class="h-7 w-7 shrink-0 object-contain sm:h-8 sm:w-8"
                  />
                  <span v-if="m.home_score != null && m.away_score != null" class="num shrink-0 text-[15px] font-semibold" style="color: var(--ink)">
                    {{ m.home_score }}<span class="mx-0.5" style="color: var(--mute)">:</span>{{ m.away_score }}
                  </span>
                  <span v-else class="num shrink-0 text-[13px]" style="color: var(--mute)">
                    {{ formatWibTime(m.date) }}
                  </span>
                  <img
                    v-if="m.away_logo"
                    :src="m.away_logo"
                    :alt="m.away"
                    class="h-7 w-7 shrink-0 object-contain sm:h-8 sm:w-8"
                  />
                  <span class="min-w-0 flex-1 truncate text-[15px] font-medium" style="color: var(--ink)">
                    {{ m.away }}
                  </span>
                </span>

                <!-- Ikon hasil / status -->
                <span class="flex w-[92px] shrink-0 items-center justify-end gap-1.5 text-[13px]">
                  <template v-if="m.status === 'live'">
                    <span class="inline-block h-1.5 w-1.5 animate-pulse rounded-full" style="background: var(--away)" />
                    <span class="num font-medium" style="color: var(--away)">
                      {{ m.minute != null ? m.minute + "'" : 'Live' }}
                    </span>
                  </template>
                  <template v-else-if="m.verdict">
                    <CheckCircle2 v-if="m.verdict.label === 'exact'" :size="15" style="color: var(--ok)" />
                    <CircleAlert v-else-if="m.verdict.label === 'outcome'" :size="15" style="color: var(--mute)" />
                    <XCircle v-else :size="15" style="color: var(--bad)" />
                    <span :style="verdictStyle[m.verdict.label]">{{ verdictLabel[m.verdict.label] }}</span>
                  </template>
                  <template v-else-if="m.status === 'finished'">
                    <span style="color: var(--mute)">Selesai</span>
                  </template>
                </span>
              </button>

              <p v-if="total > items.length" class="px-3 pt-2 text-center text-[13px]" style="color: var(--mute)">
                Menampilkan {{ items.length }} dari {{ total }} laga — persempit dengan pencarian atau filter liga.
              </p>
            </div>
          </div>

          <!-- Footer: akurasi model (pembelajaran sistem) -->
          <div class="flex flex-wrap items-center gap-x-4 gap-y-1 border-t px-4 py-2.5 sm:px-5" style="border-color: var(--line)">
            <span class="text-[13px] font-medium" style="color: var(--mute)">Pembelajaran sistem</span>
            <template v-if="modelStats">
              <span class="text-[13px]" style="color: var(--mute)">
                Prediksi <b class="num" style="color: var(--ink)">{{ modelStats.total_predictions }}</b>
                · dievaluasi <b class="num" style="color: var(--ok)">{{ modelStats.evaluated }}</b>
                · menunggu <b class="num" style="color: var(--ink)">{{ modelStats.pending }}</b>
              </span>
              <span v-if="accuracyPct != null" class="text-[13px]" style="color: var(--mute)">
                Akurasi outcome <b class="num" style="color: var(--ink)">{{ accuracyPct }}%</b>
              </span>
              <span v-if="modelStats.recent_metrics?.[0]?.brier_score != null" class="text-[13px]" style="color: var(--mute)">
                Brier <b class="num" style="color: var(--ink)">{{ modelStats.recent_metrics[0].brier_score }}</b>
              </span>
            </template>
            <span v-else class="text-[13px]" style="color: var(--mute)">Memuat statistik model…</span>
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
