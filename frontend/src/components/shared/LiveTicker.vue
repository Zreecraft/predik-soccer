<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { fetchLiveMatches } from '@/services/api'
import MatchDetailModal from '@/components/shared/MatchDetailModal.vue'

const matches = ref([])
const source = ref('mock')
const openMatch = ref(null)
let timer = null

async function refresh() {
  try {
    const data = await fetchLiveMatches()
    matches.value = (data.matches || []).filter((m) => m.live)
    source.value = data.source
  } catch {
    matches.value = []
  }
}

const sourceLabel = computed(() => (source.value === 'api' ? 'football-data.org' : source.value === 'espn' ? 'ESPN' : 'demo'))

function minuteText(m) {
  if (m.status === 'PAUSED') return 'HT'
  if (m.minute != null) return `${m.minute}'`
  return ''
}

function target(m) {
  if (m.league === 'UCL') return { path: '/ucl' }
  return { path: '/predict', query: { league: m.league, home: m.home, away: m.away } }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 60000)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div v-if="matches.length" class="border-t border-bad/25 bg-bad/25">
    <div class="mx-auto flex h-8 max-w-[1400px] items-center gap-3 overflow-hidden px-4 sm:px-6">
      <span
        class="flex shrink-0 items-center gap-1.5 rounded bg-bad px-1.5 py-0.5 text-[10px] font-extrabold tracking-widest text-ink"
      >
        <span class="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-canvas" />
        LIVE
      </span>
      <div class="min-w-0 flex-1 overflow-hidden">
        <div class="ticker-track gap-5">
          <RouterLink
            v-for="m in matches"
            :key="m.id"
            :to="target(m)"
            class="flex shrink-0 items-center gap-2 whitespace-nowrap text-[11px] text-mute transition hover:text-ink"
            title="Klik untuk lihat detail laga"
            @click.prevent="openMatch = m"
          >
            <span class="font-semibold">{{ m.home_short }}</span>
            <span
              class="num rounded bg-card/90 px-1.5 py-0.5 font-bold text-ink ring-1 ring-bad/40"
            >
              {{ m.home_score ?? 0 }}<span class="mx-0.5 text-mute">-</span>{{ m.away_score ?? 0 }}
            </span>
            <span class="font-semibold">{{ m.away_short }}</span>
            <span class="num font-bold text-bad">{{ minuteText(m) }}</span>
            <span class="text-mute">{{ m.competition_name }}</span>
          </RouterLink>
        </div>
      </div>
      <span class="hidden shrink-0 text-[10px] text-mute sm:block">
        {{ sourceLabel }} · auto 60s
      </span>
    </div>
  </div>

  <MatchDetailModal :is-open="!!openMatch" :match="openMatch" @close="openMatch = null" />
</template>
