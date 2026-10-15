<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { RefreshCw, Search } from 'lucide-vue-next'
import { fetchFixtures, fetchLeagues, fetchLiveMatches, fetchPredict, fetchSchedule, fetchShots } from '@/services/api'
import { useAsyncData } from '@/composables/useAsyncData'
import MatchHeroCard from '@/components/predict/MatchHeroCard.vue'
import MatchPickerModal from '@/components/predict/MatchPickerModal.vue'
import TacticalCompareTable from '@/components/predict/TacticalCompareTable.vue'
import ShotMap from '@/components/predict/ShotMap.vue'
import SkeletonCard from '@/components/shared/SkeletonCard.vue'
import PageHeader from '@/components/shared/PageHeader.vue'

const route = useRoute()
const router = useRouter()

const leagues = ref([])
const fixtures = ref([])
const league = ref(route.query.league || 'EPL')
const homeTeam = ref(route.query.home || '')
const awayTeam = ref(route.query.away || '')
const shotsData = ref({ home: {}, away: {}, summary: {} })
const shotsLoading = ref(false)

const { data: predict, loading, error, load } = useAsyncData(fetchPredict)

// Live score untuk laga yang sedang dipilih
const liveMatches = ref([])
let liveTimer = null

async function refreshLive() {
  try {
    const d = await fetchLiveMatches()
    liveMatches.value = d.matches || []
  } catch {
    liveMatches.value = []
  }
}

const currentLiveMatch = computed(() => {
  const h = (homeTeam.value || '').toLowerCase()
  const a = (awayTeam.value || '').toLowerCase()
  if (!h || !a) return null
  return (
    liveMatches.value.find(
      (m) => m.live && m.home?.toLowerCase() === h && m.away?.toLowerCase() === a
    ) || null
  )
})

// Laga terpilih di daftar livescore (live > selesai) — tombol menuju Match Centre
const selectedMatch = computed(() => {
  const h = (homeTeam.value || '').toLowerCase()
  const a = (awayTeam.value || '').toLowerCase()
  if (!h || !a) return null
  const exact = liveMatches.value.filter(
    (m) => m.home?.toLowerCase() === h && m.away?.toLowerCase() === a
  )
  return exact.find((m) => m.live) || exact.find((m) => m.status === 'FINISHED') || null
})

// Tanggal laga utk Match Centre — resolusi ESPN lintas jendela waktu (laga
// kapan pun). Prioritas: query URL (awet saat reload) → kickoff livescore →
// pilihan Match Picker → fixture.
const pickedDate = ref(String(route.query.date || ''))
const matchCentreDate = computed(() => {
  const k = selectedMatch.value?.kickoff
  if (k) return String(k).slice(0, 10)
  if (pickedDate.value) return String(pickedDate.value).slice(0, 10)
  const h = (homeTeam.value || '').toLowerCase()
  const a = (awayTeam.value || '').toLowerCase()
  const f = fixtures.value.find(
    (x) => x.home_team?.toLowerCase() === h && x.away_team?.toLowerCase() === a
  )
  return f?.date ? String(f.date).slice(0, 10) : ''
})

// Link menuju halaman Match Centre (data asli, terpisah dari prediksi)
const matchCentreLink = computed(() => ({
  path: '/match',
  query: {
    ...(selectedMatch.value?.id ? { id: String(selectedMatch.value.id) } : {}),
    home: homeTeam.value,
    away: awayTeam.value,
    league: league.value,
    ...(matchCentreDate.value ? { date: matchCentreDate.value } : {}),
  },
}))

// Kickoff laga terpilih dalam WIB (data UTC) — tampil saat tidak sedang live
function formatWib(dateStr) {
  if (!dateStr) return ''
  const d = new Date(String(dateStr).replace(' ', 'T') + 'Z')
  if (isNaN(d.getTime())) return ''
  const wib = new Date(d.getTime() + 7 * 3600 * 1000)
  const days = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab']
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
  const pad = (n) => String(n).padStart(2, '0')
  return `${days[wib.getUTCDay()]}, ${wib.getUTCDate()} ${months[wib.getUTCMonth()]} ${wib.getUTCFullYear()} • ${pad(wib.getUTCHours())}:${pad(wib.getUTCMinutes())} WIB`
}

const kickoffWib = computed(() => {
  const h = (homeTeam.value || '').toLowerCase()
  const a = (awayTeam.value || '').toLowerCase()
  const f = fixtures.value.find(
    (x) => x.home_team?.toLowerCase() === h && x.away_team?.toLowerCase() === a
  )
  return formatWib(f?.date)
})

async function loadFixtures() {
  const data = await fetchFixtures(league.value, 40)
  fixtures.value = data.fixtures || []
}

function applyDefaults() {
  if (fixtures.value.length) {
    const f = fixtures.value[0]
    if (!homeTeam.value) homeTeam.value = f.home_team
    if (!awayTeam.value) awayTeam.value = f.away_team
  }
}

// Match pembuka saat halaman baru dibuka: laga MENDATANG dengan kickoff terdekat
// (lintas liga, bukan selalu fixtures[0] EPL yang bisa sudah lewat).
async function pickNearestKickoff() {
  if (homeTeam.value && awayTeam.value) return false
  try {
    const [live, upcoming] = await Promise.all([
      fetchSchedule({ tab: 'live', limit: 200 }),
      fetchSchedule({ tab: 'upcoming', limit: 200 }),
    ])
    const candidates = [...(live.items || []), ...(upcoming.items || [])]
      .filter((i) => i.status === 'upcoming')
      .sort((a, b) => String(a.date).localeCompare(String(b.date)))
    const next = candidates[0]
    if (next) {
      league.value = next.league || league.value
      if (!homeTeam.value) homeTeam.value = next.home
      if (!awayTeam.value) awayTeam.value = next.away
      pickedDate.value = String(next.date || '')
      await loadFixtures() // muat ulang fixtures liga terpilih (lookup kickoff)
      return true
    }
  } catch {
    /* jatuh ke fallback fixtures di bawah */
  }
  return false
}

async function runPredict() {
  if (!homeTeam.value || !awayTeam.value) return
  router.replace({
    query: {
      league: league.value,
      home: homeTeam.value,
      away: awayTeam.value,
      // date dipertahankan agar link Match Centre tetap presisi setelah reload
      ...(matchCentreDate.value ? { date: matchCentreDate.value } : {}),
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

// Match Picker: pilih laga dari modal (termasuk hasil selesai), lalu langsung prediksi
const showPicker = ref(false)

async function onPickMatch(sel) {
  showPicker.value = false
  pickedDate.value = sel.date || ''
  if (sel.league && sel.league !== league.value) {
    league.value = sel.league
    await loadFixtures()
  }
  homeTeam.value = sel.home
  awayTeam.value = sel.away
  await runPredict()
}

onMounted(async () => {
  leagues.value = await fetchLeagues()
  await loadFixtures()
  const picked = await pickNearestKickoff()
  if (!picked) applyDefaults()
  await runPredict()
  await refreshLive()
  liveTimer = setInterval(refreshLive, 60000)
})
onBeforeUnmount(() => clearInterval(liveTimer))
</script>

<template>
  <div class="space-y-8">
    <PageHeader
      title="Prediksi Laga"
      subtitle="Simulasi Monte Carlo 10.000 iterasi minute-by-minute dengan model xG."
    >
      <template #actions>
        <button class="btn-ghost" type="button" :disabled="loading" @click="runPredict">
          <RefreshCw :size="16" :class="loading ? 'animate-spin' : ''" />
          {{ loading ? 'Menghitung…' : 'Jalankan prediksi' }}
        </button>
      </template>
    </PageHeader>

    <!-- Cari laga: tombol biasa, tanpa chip POP-UP -->
    <button
      type="button"
      class="flex w-full items-center gap-3 rounded-block border px-4 py-3 text-left text-[15px] transition"
      style="border-color: var(--line); background: var(--card); color: var(--mute)"
      @click="showPicker = true"
    >
      <Search :size="18" class="shrink-0" />
      <span class="truncate">
        {{ homeTeam && awayTeam ? `${homeTeam} vs ${awayTeam}` : 'Cari laga… (Live / Mendatang / Hasil selesai)' }}
      </span>
    </button>

    <MatchPickerModal
      :is-open="showPicker"
      :leagues="leagues"
      :selected="{ home: homeTeam, away: awayTeam }"
      @close="showPicker = false"
      @select="onPickMatch"
    />

    <div
      v-if="error"
      class="rounded-block border px-4 py-3 text-[15px]"
      style="border-color: var(--bad); color: var(--bad)"
    >
      {{ error }}
    </div>

    <div v-if="loading && !predict">
      <SkeletonCard :lines="4" />
      <div class="mt-8 grid gap-8 lg:grid-cols-2">
        <SkeletonCard :lines="6" />
        <SkeletonCard :lines="6" />
      </div>
    </div>

    <template v-else-if="predict">
      <!-- Kickoff: satu baris teks kecil, bukan kartu -->
      <p
        v-if="kickoffWib && !currentLiveMatch && predict.result?.status !== 'finished'"
        class="text-[13px]"
        style="color: var(--mute)"
      >
        Kickoff {{ kickoffWib }} · belum dimulai — prediksi = pra-pertandingan
      </p>

      <MatchHeroCard :data="predict" :live-match="currentLiveMatch" />

      <!-- 4. Kenapa model memprediksi ini -->
      <TacticalCompareTable
        :home="predict.tactical?.home || {}"
        :away="predict.tactical?.away || {}"
        :home-name="predict.home_team?.name"
        :away-name="predict.away_team?.name"
        :home-source="predict.home_team?.data_source"
        :away-source="predict.away_team?.data_source"
      />

      <!-- Rangkuman diferensial: satu kalimat, bukan kartu terpisah -->
      <p v-if="predict.differential_summary" class="text-[15px] leading-relaxed" style="color: var(--mute)">
        {{ predict.differential_summary }}
      </p>

      <!-- 5. Peta tembakan -->
      <div v-if="shotsLoading">
        <SkeletonCard :lines="6" />
      </div>
      <ShotMap
        v-else
        :home="shotsData.home || {}"
        :away="shotsData.away || {}"
        :summary="shotsData.summary || {}"
      />

      <!-- 6. Match Centre sebagai teks biasa -->
      <p class="text-[15px]" style="color: var(--mute)">
        Skor asli, pencetak gol, kartu, dan line-up ada di
        <RouterLink
          :to="matchCentreLink"
          class="font-medium underline underline-offset-4"
          style="color: var(--home)"
        >
          Match Centre
        </RouterLink>
        — data asli dari ESPN, tanpa simulasi model.
      </p>
    </template>
  </div>
</template>
