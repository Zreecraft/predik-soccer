<script setup>
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { X, Trophy, Swords, Zap, ArrowRight, MapPin } from 'lucide-vue-next'
import PlayerCutout from '@/components/shared/PlayerCutout.vue'
import WinProbabilityBar from '@/components/shared/WinProbabilityBar.vue'
import { useAsyncData } from '@/composables/useAsyncData'
import { fetchPredict } from '@/services/api'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  matchData: { type: Object, default: null },
})

const emit = defineEmits(['close'])

const router = useRouter()

// Prediksi skor laga (fetched saat drawer dibuka)
const { data: prediction, loading: predLoading, load: loadPrediction } = useAsyncData(fetchPredict)

watch(
  () => [props.isOpen, props.matchData],
  ([open]) => {
    if (open && props.matchData?.team_home && props.matchData?.team_away) {
      loadPrediction(props.matchData.team_home, props.matchData.team_away)
    }
  },
  { immediate: true }
)

const predScore = computed(() => prediction.value?.projection?.score || null)
const predVerdict = computed(() => {
  const p = prediction.value
  if (!p) return null
  const probs = [
    { label: `Menang ${homeTeam.value}`, v: p.probabilities.home_win },
    { label: 'Seri', v: p.probabilities.draw },
    { label: `Menang ${awayTeam.value}`, v: p.probabilities.away_win },
  ]
  return probs.sort((a, b) => b.v - a.v)[0]
})

function closeDrawer() {
  emit('close')
}

const homeTeam = computed(() => props.matchData?.team_home || '')
const awayTeam = computed(() => props.matchData?.team_away || '')
const homeLogo = computed(() => props.matchData?.logo_home || '')
const awayLogo = computed(() => props.matchData?.logo_away || '')
const winner = computed(() => props.matchData?.winner || '')
const score = computed(() => props.matchData?.score || `${props.matchData?.agg_home ?? 0} - ${props.matchData?.agg_away ?? 0}`)
const roundName = computed(() => props.matchData?.round_name || props.matchData?.label || 'Babak Gugur UCL')

const homeProb = computed(() => Number(props.matchData?.win_prob_home) || 50)
const awayProb = computed(() => Number(props.matchData?.win_prob_away) || 50)
const winnerProb = computed(() => Number(props.matchData?.winner_prob) || (winner.value === homeTeam.value ? homeProb.value : awayProb.value))

const homeXg = computed(() => Number(props.matchData?.home_xg) || 1.5)
const awayXg = computed(() => Number(props.matchData?.away_xg) || 1.2)
const totalXg = computed(() => homeXg.value + awayXg.value || 1)
const homeXgPercent = computed(() => Math.min(100, Math.max(0, (homeXg.value / totalXg.value) * 100)))

const starPlayerHome = computed(() => props.matchData?.star_player_home || null)
const starPlayerAway = computed(() => props.matchData?.star_player_away || null)

function navigateToPredict() {
  if (!homeTeam.value || !awayTeam.value) return
  closeDrawer()
  router.push({
    path: '/predict',
    query: {
      home: homeTeam.value,
      away: awayTeam.value,
    },
  })
}
</script>

<template>
  <Teleport to="body">
    <Transition name="slide-drawer">
      <div
        v-if="isOpen && matchData"
        class="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm"
      >
        <!-- Backdrop Click to Close -->
        <div class="flex-1 cursor-pointer" @click="closeDrawer" />

        <!-- Right Drawer Content Panel -->
        <div
          class="flex h-full w-full max-w-md flex-col justify-between overflow-y-auto border-l border-line bg-card p-6 shadow-2xl shadow-black/80"
        >
          <div class="space-y-6">
            <!-- Header Drawer -->
            <div class="flex items-center justify-between border-b border-line pb-4">
              <div>
                <span class="text-xs font-bold uppercase tracking-wider text-home">
                  {{ roundName }}
                </span>
                <div class="text-[11px] text-mute">UEFA Champions League Knockout</div>
                <div
                  v-if="matchData.bracket_slot"
                  class="mt-1 inline-flex items-center gap-1 rounded-md border border-home/30 bg-home/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-home"
                >
                  <MapPin :size="10" />
                  {{ matchData.bracket_slot }}
                </div>
              </div>
              <button
                type="button"
                class="rounded-lg bg-card/80 p-2 text-mute transition hover:bg-line hover:text-ink"
                @click="closeDrawer"
              >
                <X :size="16" />
              </button>
            </div>

            <!-- Hero H2H Detail -->
            <div class="rounded-xl border border-line bg-canvas/60 p-4 text-center">
              <div class="flex items-center justify-around gap-2">
                <!-- Home Team -->
                <div class="flex flex-1 flex-col items-center">
                  <div
                    class="relative flex h-16 w-16 items-center justify-center rounded-xl border bg-card/80 p-2"
                    :class="winner === homeTeam ? 'border-ok/50 shadow-lg shadow-ok/10' : 'border-line'"
                  >
                    <img
                      v-if="homeLogo"
                      :src="homeLogo"
                      :alt="homeTeam"
                      class="h-12 w-12 object-contain"
                    />
                    <div
                      v-if="winner === homeTeam"
                      class="absolute -top-2 -right-2 rounded-full bg-ok p-1 text-ink shadow"
                    >
                      <Trophy :size="10" />
                    </div>
                  </div>
                  <h4
                    class="mt-2 truncate text-xs font-bold max-w-[110px]"
                    :class="winner === homeTeam ? 'text-ok' : 'text-ink'"
                  >
                    {{ homeTeam }}
                  </h4>
                  <span class="num text-[11px] text-mute">{{ homeProb }}%</span>
                </div>

                <!-- Score / VS -->
                <div class="shrink-0 px-2 text-center">
                  <div class="num text-2xl font-black text-ink">
                    {{ matchData.agg_home ?? '-' }} - {{ matchData.agg_away ?? '-' }}
                  </div>
                  <span class="label-caps text-[10px] text-mute">Agregat</span>
                </div>

                <!-- Away Team -->
                <div class="flex flex-1 flex-col items-center">
                  <div
                    class="relative flex h-16 w-16 items-center justify-center rounded-xl border bg-card/80 p-2"
                    :class="winner === awayTeam ? 'border-ok/50 shadow-lg shadow-ok/10' : 'border-line'"
                  >
                    <img
                      v-if="awayLogo"
                      :src="awayLogo"
                      :alt="awayTeam"
                      class="h-12 w-12 object-contain"
                    />
                    <div
                      v-if="winner === awayTeam"
                      class="absolute -top-2 -right-2 rounded-full bg-ok p-1 text-ink shadow"
                    >
                      <Trophy :size="10" />
                    </div>
                  </div>
                  <h4
                    class="mt-2 truncate text-xs font-bold max-w-[110px]"
                    :class="winner === awayTeam ? 'text-ok' : 'text-ink'"
                  >
                    {{ awayTeam }}
                  </h4>
                  <span class="num text-[11px] text-mute">{{ awayProb }}%</span>
                </div>
              </div>

              <!-- Winner Badge -->
              <div class="mt-4 flex items-center justify-center gap-2">
                <div class="inline-flex items-center gap-1.5 rounded-full border border-ok/30 bg-ok/10 px-3 py-1 text-xs font-semibold text-ok">
                  <Trophy :size="12" />
                  <span>Pemenang: <strong>{{ winner }}</strong> ({{ winnerProb }}%)</span>
                </div>
              </div>

              <!-- Legs Breakdown if available -->
              <div v-if="matchData.leg1 && matchData.leg2" class="mt-3 grid grid-cols-2 gap-2 border-t border-line/80 pt-3 text-[11px] text-mute">
                <div class="rounded bg-card/80 p-1.5 text-center">
                  <span class="text-mute block text-[9px] uppercase">Leg 1 (Kandang)</span>
                  <span class="num font-semibold text-ink">{{ matchData.leg1.goals_home }} - {{ matchData.leg1.goals_away }}</span>
                </div>
                <div class="rounded bg-card/80 p-1.5 text-center">
                  <span class="text-mute block text-[9px] uppercase">Leg 2 (Tandang)</span>
                  <span class="num font-semibold text-ink">{{ matchData.leg2.goals_away }} - {{ matchData.leg2.goals_home }}</span>
                </div>
              </div>
            </div>

            <!-- Prediksi Skor (model) -->
            <div class="panel p-4">
              <div class="flex items-center justify-between">
                <span class="label-caps text-mute">Prediksi Skor</span>
                <span v-if="predLoading" class="text-[11px] text-mute">memuat…</span>
              </div>
              <template v-if="prediction">
                <div class="mt-2 flex items-center justify-center gap-3">
                  <span class="num text-3xl font-black" style="color: var(--ink)">{{ predScore }}</span>
                </div>
                <div class="mt-1.5 text-center text-xs" style="color: var(--mute)">
                  {{ predVerdict.label }} <span class="num font-bold">{{ predVerdict.v }}%</span>
                  <span class="mx-1">·</span>
                  xG <span class="num">{{ prediction.analytics.home_xg }}</span> -
                  <span class="num">{{ prediction.analytics.away_xg }}</span>
                </div>
                <div class="mt-2">
                  <WinProbabilityBar
                    :home-win="prediction.probabilities.home_win"
                    :draw="prediction.probabilities.draw"
                    :away-win="prediction.probabilities.away_win"
                    :home-label="homeTeam"
                    :away-label="awayTeam"
                  />
                </div>
              </template>
              <div v-else class="mt-2 text-center text-xs text-mute">
                Prediksi tidak tersedia untuk laga ini.
              </div>
            </div>

            <!-- Probability Bar -->
            <div class="panel p-4">
              <div class="label-caps mb-2 text-mute">Probabilitas Lolos (Monte Carlo)</div>
              <div class="flex h-2.5 w-full overflow-hidden rounded-full bg-card">
                <div
                  class="h-full bg-home transition-all duration-500"
                  :style="{ width: homeProb + '%' }"
                />
                <div
                  class="h-full bg-bad transition-all duration-500"
                  :style="{ width: awayProb + '%' }"
                />
              </div>
              <div class="mt-2 flex justify-between text-xs">
                <span class="font-medium text-home">{{ homeTeam }}: {{ homeProb }}%</span>
                <span class="font-medium text-bad">{{ awayTeam }}: {{ awayProb }}%</span>
              </div>
            </div>

            <!-- xG Projection -->
            <div class="panel p-4">
              <div class="flex items-center justify-between">
                <span class="label-caps text-mute">Simulasi Proyeksi xG</span>
                <span class="text-[11px] text-mute">Per Leg Rata-rata</span>
              </div>
              <div class="mt-2 flex h-2 w-full overflow-hidden rounded-full bg-card">
                <div
                  class="h-full bg-ok transition-all duration-500"
                  :style="{ width: homeXgPercent + '%' }"
                />
                <div
                  class="h-full bg-draw transition-all duration-500"
                  :style="{ width: (100 - homeXgPercent) + '%' }"
                />
              </div>
              <div class="mt-2 flex justify-between font-mono text-xs">
                <span class="text-ok font-bold">{{ homeXg }} xG</span>
                <span class="text-draw font-bold">{{ awayXg }} xG</span>
              </div>
            </div>

            <!-- Star Players Face-Off -->
            <div class="panel p-4">
              <div class="label-caps mb-3 flex items-center gap-1.5 text-mute">
                <Swords :size="13" class="text-home" />
                <span>Head to Head Star Players</span>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <!-- Home Player -->
                <div class="flex flex-col items-center rounded-lg border border-line bg-canvas/40 p-3 text-center">
                  <PlayerCutout
                    :image="starPlayerHome?.image"
                    :name="starPlayerHome?.player_name || homeTeam"
                    size="sm"
                  />
                  <div class="mt-2 truncate text-xs font-bold text-ink max-w-[130px]">
                    {{ starPlayerHome?.player_name || 'Star Player' }}
                  </div>
                  <span class="num text-[10px] text-home">{{ starPlayerHome?.position || 'FWD' }}</span>
                </div>

                <!-- Away Player -->
                <div class="flex flex-col items-center rounded-lg border border-line bg-canvas/40 p-3 text-center">
                  <PlayerCutout
                    :image="starPlayerAway?.image"
                    :name="starPlayerAway?.player_name || awayTeam"
                    size="sm"
                  />
                  <div class="mt-2 truncate text-xs font-bold text-ink max-w-[130px]">
                    {{ starPlayerAway?.player_name || 'Star Player' }}
                  </div>
                  <span class="num text-[10px] text-bad">{{ starPlayerAway?.position || 'FWD' }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Action Button -->
          <div class="pt-6 border-t border-line/80">
            <button
              type="button"
              class="flex w-full items-center justify-center gap-2 rounded-xl bg-ok py-3 text-sm font-bold text-ink shadow-lg shadow-ok/20 transition hover:bg-ok/90 hover:shadow-ok/30 active:scale-[0.99]"
              @click="navigateToPredict"
            >
              <Zap :size="16" />
              <span>Buka Analisis Taktis Penuh</span>
              <ArrowRight :size="16" />
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.slide-drawer-enter-active,
.slide-drawer-leave-active {
  transition: opacity 0.3s ease;
}

.slide-drawer-enter-active > div:last-child,
.slide-drawer-leave-active > div:last-child {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-drawer-enter-from,
.slide-drawer-leave-to {
  opacity: 0;
}

.slide-drawer-enter-from > div:last-child,
.slide-drawer-leave-to > div:last-child {
  transform: translateX(100%);
}
</style>
