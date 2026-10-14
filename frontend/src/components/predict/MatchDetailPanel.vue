<script setup>
import { computed, ref, watch } from 'vue'
import { ArrowLeftRight, Flag, ListOrdered, RefreshCw, Shirt, Square, Users } from 'lucide-vue-next'

const props = defineProps({
  detail: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

const tabs = [
  { id: 'timeline', label: 'Timeline', icon: ListOrdered },
  { id: 'lineup', label: 'Line-up', icon: Users },
  { id: 'stats', label: 'Statistik', icon: Flag },
]
const activeTab = ref('timeline')

const EVENT_META = {
  goal: { label: 'Gol', icon: Shirt, cls: 'border-ok/50 bg-ok/15 text-ok' },
  own_goal: { label: 'Gol Bunuh Diri', icon: Shirt, cls: 'border-ok/40 bg-ok/10 text-ok/80' },
  yellow: { label: 'Kartu Kuning', icon: Square, cls: 'border-draw/50 bg-draw/15 text-draw' },
  second_yellow: { label: 'Kuning-Merah', icon: Square, cls: 'border-away/50 bg-away/15 text-away' },
  red: { label: 'Kartu Merah', icon: Square, cls: 'border-bad/50 bg-bad/15 text-bad' },
  sub: { label: 'Pergantian', icon: ArrowLeftRight, cls: 'border-home/40 bg-home/10 text-home' },
}

const available = computed(() => !!props.detail?.available)
const sourceLabel = computed(() => {
  switch (props.detail?.source) {
    case 'espn': return 'Data asli • ESPN'
    case 'api': return 'Data asli • football-data.org'
    default: return null
  }
})
const unavailableMsg = computed(() => {
  switch (props.detail?.reason) {
    case 'mock': return 'Rincian laga tidak tersedia pada mode demo — data simulasi tidak menampilkan event palsu.'
    case 'not_found': return 'Laga tidak ditemukan di daftar skor aktif.'
    default: return props.detail?.reason?.startsWith('fetch_error')
      ? 'Gagal memuat detail dari sumber data. Coba lagi sebentar lagi.'
      : 'Detail laga belum tersedia.'
  }
})

const timeline = computed(() => props.detail?.timeline || [])
const goalCount = computed(() => timeline.value.filter((e) => e.type === 'goal' || e.type === 'own_goal').length)
const lineups = computed(() => props.detail?.lineups || null)
const stats = computed(() => props.detail?.stats || null)

const STAT_ROWS = [
  { key: 'possession', label: 'Possession', suffix: '%' },
  { key: 'shots', label: 'Tembakan' },
  { key: 'shots_on_target', label: 'Tepat Sasaran' },
  { key: 'corners', label: 'Corner' },
  { key: 'fouls', label: 'Pelanggaran' },
  { key: 'offsides', label: 'Offside' },
  { key: 'yellow_cards', label: 'Kartu Kuning' },
  { key: 'red_cards', label: 'Kartu Merah' },
  { key: 'saves', label: 'Penyelamatan' },
]

const statBars = computed(() => {
  if (!stats.value) return []
  return STAT_ROWS.map((r) => {
    const h = Number(stats.value.home?.[r.key] ?? 0)
    const a = Number(stats.value.away?.[r.key] ?? 0)
    const total = h + a
    const hp = total > 0 ? (h / total) * 100 : 50
    return { ...r, h, a, homePct: hp, awayPct: 100 - hp, equal: total === 0 }
  })
})

const POS_SHORT = {
  Goalkeeper: 'GK',
  'Center Defender': 'CB',
  'Center Left Defender': 'LCB',
  'Center Right Defender': 'RCB',
  'Left Back': 'LB',
  'Right Back': 'RB',
  'Defensive Midfield': 'DM',
  'Central Midfield': 'CM',
  'Left Midfield': 'LM',
  'Right Midfield': 'RM',
  'Attacking Midfield': 'AM',
  'Left Wing': 'LW',
  'Right Wing': 'RW',
  Striker: 'ST',
  'Centre-Forward': 'CF',
}
const posShort = (p) => POS_SHORT[p] || (p ? p.split(' ').map((w) => w[0]).join('').slice(0, 3).toUpperCase() : '—')

function sideName(side) {
  return side === 'home' ? props.detail?.home : props.detail?.away
}

watch(
  () => props.detail?.timeline,
  (tl) => {
    // default tab paling informatif: kalau belum ada momen, buka line-up
    if (activeTab.value === 'timeline' && !(tl || []).length && props.detail?.lineups) {
      activeTab.value = 'lineup'
    }
  },
  { immediate: true }
)
</script>

<template>
  <section class="panel overflow-hidden">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-3">
      <div class="flex items-center gap-3">
        <h3 class="text-sm font-bold tracking-tight text-ink">Detail Laga</h3>
        <span v-if="sourceLabel" class="chip border-ok/40 bg-ok/10 text-ok">
          {{ sourceLabel }}
        </span>
        <span v-if="detail?.minute != null && (detail?.status === 'IN_PLAY' || detail?.status === 'PAUSED')" class="num text-xs font-bold text-bad">
          {{ detail.status === 'PAUSED' ? 'HT' : `${detail.minute}'` }}
        </span>
      </div>
      <div class="flex items-center gap-1">
        <button
          v-for="t in tabs"
          :key="t.id"
          type="button"
          class="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold transition"
          :class="activeTab === t.id ? 'bg-card text-ink' : 'text-mute hover:bg-card/50 hover:text-ink'"
          @click="activeTab = t.id"
        >
          <component :is="t.icon" :size="13" />
          {{ t.label }}
          <span v-if="t.id === 'timeline' && goalCount" class="num rounded bg-ok/15 px-1 text-[10px] text-ok">
            {{ goalCount }}
          </span>
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading && !detail" class="px-5 py-8">
      <div class="skeleton mx-auto h-4 w-2/3" />
      <div class="skeleton mx-auto mt-3 h-4 w-1/2" />
      <div class="skeleton mx-auto mt-3 h-4 w-3/5" />
    </div>

    <!-- Unavailable -->
    <div v-else-if="!available" class="px-5 py-8 text-center">
      <div class="label-caps text-mute">Tidak tersedia</div>
      <p class="mx-auto mt-2 max-w-md text-sm text-mute">{{ unavailableMsg }}</p>
    </div>

    <template v-else>
      <!-- ============ TIMELINE ============ -->
      <div v-show="activeTab === 'timeline'" class="px-3 py-4 sm:px-4">
        <div v-if="!timeline.length" class="py-6 text-center text-sm text-mute">
          Belum ada momen tercatat (gol / kartu / pergantian).
        </div>
        <div v-else class="space-y-1">
          <div
            v-for="(ev, i) in timeline"
            :key="i"
            class="grid grid-cols-[1fr_auto_1fr] items-center gap-2 rounded-lg px-1 py-1.5 transition hover:bg-card/30"
          >
            <!-- home side -->
            <div class="min-w-0 text-right">
              <template v-if="ev.side === 'home'">
                <div class="truncate text-sm font-semibold" :class="ev.type === 'goal' || ev.type === 'own_goal' ? 'text-ok' : 'text-ink'">
                  {{ ev.player || '—' }}
                </div>
                <div class="text-[11px] text-mute">
                  <template v-if="ev.type === 'sub'">keluar: {{ ev.player_out || '—' }}</template>
                  <template v-else-if="ev.assist">assist: {{ ev.assist }}</template>
                  <template v-else>{{ ev.team }}</template>
                </div>
              </template>
            </div>

            <!-- center: minute + icon -->
            <div class="flex w-16 flex-col items-center gap-1">
              <span class="num text-[11px] font-bold text-mute">{{ ev.minute || '—' }}</span>
              <span
                class="inline-flex h-7 w-7 items-center justify-center rounded-full border"
                :class="(EVENT_META[ev.type] || {}).cls || 'border-line bg-card text-mute'"
                :title="(EVENT_META[ev.type] || {}).label"
              >
                <component :is="(EVENT_META[ev.type] || {}).icon || Square" :size="13" />
              </span>
            </div>

            <!-- away side -->
            <div class="min-w-0">
              <template v-if="ev.side === 'away' || (ev.side !== 'home' && ev.side !== 'away')">
                <div class="truncate text-sm font-semibold" :class="ev.type === 'goal' || ev.type === 'own_goal' ? 'text-ok' : 'text-ink'">
                  {{ ev.player || '—' }}
                </div>
                <div class="text-[11px] text-mute">
                  <template v-if="ev.type === 'sub'">keluar: {{ ev.player_out || '—' }}</template>
                  <template v-else-if="ev.assist">assist: {{ ev.assist }}</template>
                  <template v-else>{{ ev.team }}</template>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- ============ LINE-UP ============ -->
      <div v-show="activeTab === 'lineup'" class="px-4 py-4">
        <div v-if="!lineups?.home && !lineups?.away" class="py-6 text-center text-sm text-mute">
          Line-up diumumkan saat pertandingan dimulai.
        </div>
        <div v-else class="grid gap-5 lg:grid-cols-2">
          <div v-for="side in ['home', 'away']" :key="side">
            <div v-if="lineups?.[side]" class="rounded-xl border border-line bg-canvas/40 p-3">
              <div class="mb-3 flex items-center justify-between gap-2">
                <div class="min-w-0">
                  <div class="truncate text-sm font-bold text-ink">{{ sideName(side) }}</div>
                  <div class="mt-0.5 text-[11px] text-mute">
                    <span class="num font-semibold text-home">{{ lineups[side].formation || '—' }}</span>
                    <span v-if="lineups[side].coach" class="ml-2">Pelatih: {{ lineups[side].coach }}</span>
                  </div>
                </div>
                <span class="chip border-line bg-card/60 text-mute">Starting XI</span>
              </div>
              <ul class="space-y-1">
                <li
                  v-for="(p, i) in lineups[side].starters"
                  :key="i"
                  class="flex items-center gap-2.5 rounded-lg px-1.5 py-1 hover:bg-card/40"
                >
                  <span class="num flex h-6 w-6 shrink-0 items-center justify-center rounded-md border border-line bg-card text-[11px] font-bold text-mute">
                    {{ p.number || '–' }}
                  </span>
                  <span class="min-w-0 flex-1 truncate text-sm text-ink">{{ p.name }}</span>
                  <span class="label-caps shrink-0 text-[10px] text-mute">{{ posShort(p.position) }}</span>
                </li>
              </ul>
              <template v-if="lineups[side].substitutes?.length">
                <div class="label-caps mt-4 border-t border-line pt-3 text-[10px] text-mute">Cadangan</div>
                <ul class="mt-2 space-y-1">
                  <li
                    v-for="(p, i) in lineups[side].substitutes"
                    :key="i"
                    class="flex items-center gap-2.5 rounded-lg px-1.5 py-0.5"
                  >
                    <span class="num w-6 shrink-0 text-right text-[11px] font-semibold text-mute">{{ p.number || '–' }}</span>
                    <span class="min-w-0 flex-1 truncate text-xs text-mute">{{ p.name }}</span>
                    <span class="label-caps shrink-0 text-[10px] text-mute">{{ posShort(p.position) }}</span>
                  </li>
                </ul>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- ============ STATISTIK ============ -->
      <div v-show="activeTab === 'stats'" class="px-4 py-4">
        <div class="mb-3 grid grid-cols-[1fr_auto_1fr] items-center gap-2 text-xs font-bold">
          <div class="truncate text-home">{{ detail.home }}</div>
          <div class="label-caps text-mute">Statistik</div>
          <div class="truncate text-right text-bad">{{ detail.away }}</div>
        </div>
        <div v-if="!statBars.length" class="py-6 text-center text-sm text-mute">Statistik belum tersedia.</div>
        <div v-else class="space-y-2.5">
          <div v-for="row in statBars" :key="row.key" class="grid grid-cols-[3rem_1fr_3rem] items-center gap-2 sm:grid-cols-[4rem_1fr_4rem]">
            <span class="num text-right text-sm font-bold" :class="row.h > row.a ? 'text-ink' : 'text-mute'">
              {{ row.h }}{{ row.suffix || '' }}
            </span>
            <div class="flex h-2 overflow-hidden rounded-full bg-card">
              <div class="h-full rounded-l-full bg-home/80 transition-all" :style="{ width: row.homePct + '%' }" />
              <div class="h-full rounded-r-full bg-bad/80 transition-all" :style="{ width: row.awayPct + '%' }" />
            </div>
            <span class="num text-sm font-bold" :class="row.a > row.h ? 'text-ink' : 'text-mute'">
              {{ row.a }}{{ row.suffix || '' }}
            </span>
            <div class="col-span-3 -mt-1.5 text-center text-[10px] font-semibold uppercase tracking-wider text-mute">
              {{ row.label }}
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Footer -->
    <div v-if="available && detail?.fetched_at" class="flex items-center justify-between border-t border-line px-5 py-2 text-[10px] text-mute">
      <span>Diperbarui {{ new Date(detail.fetched_at).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) }} (server)</span>
      <span class="inline-flex items-center gap-1"><RefreshCw :size="10" /> auto 60s saat live</span>
    </div>
  </section>
</template>
