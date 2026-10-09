<script setup>
import { computed, ref } from 'vue'
import { Trophy, ChevronRight } from 'lucide-vue-next'
import BracketNode from '@/components/ucl/BracketNode.vue'
import PlayerCutout from '@/components/shared/PlayerCutout.vue'

const props = defineProps({
  knockout: { type: Object, default: () => ({}) },
  champion: { type: Object, default: () => ({}) },
  edit: { type: Boolean, default: false },
})

const emit = defineEmits(['select-match', 'edit-score'])

const activeTab = ref('po')

const poMatches = computed(() => props.knockout?.playoffs || [])
const r16Matches = computed(() => props.knockout?.round_of_16 || [])
const qfMatches = computed(() => props.knockout?.quarter_finals || [])
const sfMatches = computed(() => props.knockout?.semi_finals || [])
const finalMatch = computed(() => props.knockout?.final || null)

const r16Left = computed(() => r16Matches.value.slice(0, 4))
const r16Right = computed(() => r16Matches.value.slice(4, 8))

const qfLeft = computed(() => qfMatches.value.slice(0, 2))
const qfRight = computed(() => qfMatches.value.slice(2, 4))

// Pasangan play-off yang memberi makan tiap laga 16 besar (diurutkan sejajar cabang R16)
function feedOf(r16m) {
  if (!r16m?.team_home) return null
  return (
    poMatches.value.find(
      (p) => p.winner && (p.winner === r16m.team_home || p.winner === r16m.team_away)
    ) || null
  )
}
const poLeft = computed(() => r16Left.value.map(feedOf))
const poRight = computed(() => r16Right.value.map(feedOf))

const champProb = computed(() => {
  const v = Number(props.champion?.win_prob)
  return Number.isFinite(v) ? Math.round(v) : null
})

function handleSelectMatch(match) {
  if (!match || !match.team_home) return
  emit('select-match', match)
}
</script>

<template>
  <div class="relative w-full overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/60 p-4 sm:p-6">
    <!-- Header Title -->
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
      <div>
        <div class="label-caps text-sky-400">Diagram Babak Gugur</div>
        <h3 class="text-lg font-bold text-slate-100">Bagan Turnamen Visual UCL (Simetris)</h3>
        <p class="mt-1 text-xs text-slate-500">
          Play-off → 16 Besar → Perempat Final → Grand Final · ketuk kartu untuk drawer telemetri
        </p>
      </div>
      <div class="flex items-center gap-2 text-xs text-slate-400">
        <span class="inline-block h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
        <span>Simulasi Monte Carlo</span>
      </div>
    </div>

    <!-- ========================================================= -->
    <!-- DESKTOP: 7-COLUMN SYMMETRICAL BRACKET TREE (>= 1024px)    -->
    <!-- ========================================================= -->
    <div class="hidden lg:block overflow-x-auto pb-4">
      <div class="mx-auto min-w-[1400px] max-w-[1600px] select-none">
        <!-- Headers -->
        <div class="mb-3 grid grid-cols-[1fr_1fr_1fr_1.35fr_1fr_1fr_1fr] gap-5 text-center">
          <div class="label-caps text-amber-400/90">Play-off</div>
          <div class="label-caps text-slate-400">16 Besar</div>
          <div class="label-caps text-slate-400">Perempat Final</div>
          <div class="label-caps text-amber-400">Grand Final</div>
          <div class="label-caps text-slate-400">Perempat Final</div>
          <div class="label-caps text-slate-400">16 Besar</div>
          <div class="label-caps text-amber-400/90">Play-off</div>
        </div>

        <!-- 7-Column Body -->
        <div class="grid h-[700px] grid-cols-[1fr_1fr_1fr_1.35fr_1fr_1fr_1fr] items-stretch gap-5">
          <!-- ============ KOLOM 1: PLAY-OFF KIRI (lurus ke R16) ============ -->
          <div class="col-po-left flex h-full flex-col">
            <div
              v-for="(m, i) in poLeft"
              :key="'po-l-' + (m?.match_id || i)"
              class="branch flex flex-1 items-center"
            >
              <BracketNode v-if="m" :match="m" :edit="edit" @select="handleSelectMatch" @edit-score="emit('edit-score', $event)" />
            </div>
          </div>

          <!-- ============ KOLOM 2: 16 BESAR KIRI (4 branches) ============ -->
          <div class="col-r16-left flex h-full flex-col">
            <div
              v-for="(m, i) in r16Left"
              :key="m.match_id || i"
              class="branch flex flex-1 items-center"
            >
              <BracketNode :match="m" :edit="edit" @select="handleSelectMatch" @edit-score="emit('edit-score', $event)" />
            </div>
          </div>

          <!-- ============ KOLOM 3: QF KIRI (2 branches) ============ -->
          <div class="col-qf-left flex h-full flex-col">
            <div
              v-for="(m, i) in qfLeft"
              :key="m.match_id || i"
              class="branch flex flex-1 items-center"
            >
              <BracketNode :match="m" :edit="edit" @select="handleSelectMatch" @edit-score="emit('edit-score', $event)" />
            </div>
          </div>

          <!-- ============ KOLOM 4: GRAND FINAL & CHAMPION ============ -->
          <div class="col-center relative h-full">
            <!-- Rail vertikal kiri/kanan: menghubungkan QF (25%/75%) ke final (50%) -->
            <span v-if="qfMatches.length" class="conn-rail conn-rail--l" aria-hidden="true" />
            <span v-if="qfMatches.length" class="conn-rail conn-rail--r" aria-hidden="true" />
            <!-- Garis champion -> final -->
            <span v-if="finalMatch" class="conn-line" aria-hidden="true" />

            <!-- Champion Card -->
            <div
              class="champ-card relative mx-auto mt-4 w-[calc(100%-32px)] max-w-[250px] rounded-2xl border border-amber-500/40 bg-gradient-to-b from-[#1c1508] via-[#0f172a] to-[#0b1220] p-4 text-center shadow-xl shadow-amber-500/10"
            >
              <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-amber-500/40 bg-amber-500/15 text-amber-400">
                <Trophy :size="24" />
              </div>
              <div class="mt-2 text-[10px] font-black uppercase tracking-[0.22em] text-amber-400">
                UCL Champion
              </div>
              <div class="mt-2 flex items-center justify-center gap-2">
                <img
                  v-if="champion.logo"
                  :src="champion.logo"
                  :alt="champion.team"
                  class="h-7 w-7 shrink-0 object-contain"
                />
                <span class="truncate text-base font-black text-slate-50">
                  {{ champion.team || finalMatch?.winner || '—' }}
                </span>
              </div>
              <div class="mt-2 inline-flex items-center gap-1.5 rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1">
                <span class="num text-xs font-black text-amber-300">
                  {{ champProb != null ? champProb + '%' : '—' }}
                </span>
                <span class="text-[9px] font-bold uppercase tracking-wider text-amber-500/80">
                  Peluang juara
                </span>
              </div>
              <div
                v-if="champion.star_player?.player_name"
                class="mt-2.5 flex items-center gap-2 border-t border-slate-800 pt-2.5"
              >
                <PlayerCutout
                  :image="champion.star_player?.image"
                  :name="champion.star_player?.player_name"
                  size="sm"
                />
                <div class="min-w-0 text-left">
                  <div class="truncate text-[11px] font-bold text-slate-200">
                    {{ champion.star_player?.player_name }}
                  </div>
                  <div class="num text-[10px] text-amber-400">
                    {{ champion.star_player?.position }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Grand Final Match (di-center vertikal 50% kolom) -->
            <div v-if="finalMatch" class="absolute left-0 right-0 top-1/2 -translate-y-1/2">
              <BracketNode :match="finalMatch" :highlight="true" :edit="edit" @select="handleSelectMatch" @edit-score="emit('edit-score', $event)" />
            </div>
          </div>

          <!-- ============ KOLOM 5: QF KANAN (2 branches) ============ -->
          <div class="col-qf-right flex h-full flex-col">
            <div
              v-for="(m, i) in qfRight"
              :key="m.match_id || i"
              class="branch flex flex-1 items-center"
            >
              <BracketNode :match="m" :edit="edit" @select="handleSelectMatch" @edit-score="emit('edit-score', $event)" />
            </div>
          </div>

          <!-- ============ KOLOM 6: 16 BESAR KANAN (4 branches) ============ -->
          <div class="col-r16-right flex h-full flex-col">
            <div
              v-for="(m, i) in r16Right"
              :key="m.match_id || i"
              class="branch flex flex-1 items-center"
            >
              <BracketNode :match="m" :edit="edit" @select="handleSelectMatch" @edit-score="emit('edit-score', $event)" />
            </div>
          </div>

          <!-- ============ KOLOM 7: PLAY-OFF KANAN (lurus ke R16) ============ -->
          <div class="col-po-right flex h-full flex-col">
            <div
              v-for="(m, i) in poRight"
              :key="'po-r-' + (m?.match_id || i)"
              class="branch flex flex-1 items-center"
            >
              <BracketNode v-if="m" :match="m" :edit="edit" @select="handleSelectMatch" @edit-score="emit('edit-score', $event)" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========================================================= -->
    <!-- MOBILE FALLBACK: VERTICAL TABBED LIST (< 1024px)          -->
    <!-- ========================================================= -->
    <div class="lg:hidden space-y-4">
      <div class="flex flex-wrap gap-1.5 border-b border-slate-800 pb-3">
        <button
          v-for="tab in [
            { id: 'po', label: 'Play-off' },
            { id: 'r16', label: '16 Besar' },
            { id: 'qf', label: 'Perempat Final' },
            { id: 'sf', label: 'Semifinal' },
            { id: 'final', label: 'Grand Final' },
          ]"
          :key="tab.id"
          type="button"
          class="rounded-lg px-3 py-1.5 text-xs font-semibold uppercase tracking-wider transition"
          :class="
            activeTab === tab.id
              ? 'bg-sky-500/25 text-sky-400 border border-sky-500/40'
              : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
          "
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="space-y-2.5">
        <div
          v-for="m in (
            activeTab === 'po' ? poMatches :
            activeTab === 'r16' ? r16Matches :
            activeTab === 'qf' ? qfMatches :
            activeTab === 'sf' ? sfMatches :
            [finalMatch].filter(Boolean)
          )"
          :key="m.match_id || m.label"
          class="flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/90 p-3.5 transition hover:border-sky-500 active:scale-[0.99]"
          @click="handleSelectMatch(m)"
        >
          <div class="flex min-w-0 flex-1 items-center gap-2.5">
            <img v-if="m.logo_home" :src="m.logo_home" class="h-8 w-8 shrink-0 object-contain" :alt="m.team_home" />
            <span class="truncate text-sm font-semibold" :class="m.winner === m.team_home ? 'text-emerald-400 font-bold' : 'text-slate-200'">
              {{ m.team_home }}
            </span>
          </div>
          <div class="num shrink-0 rounded-md border border-slate-800 bg-slate-950 px-3 py-1.5 text-sm font-bold text-slate-100">
            {{ m.agg_home ?? '-' }} - {{ m.agg_away ?? '-' }}
          </div>
          <div class="flex min-w-0 flex-1 flex-row-reverse items-center gap-2.5">
            <img v-if="m.logo_away" :src="m.logo_away" class="h-8 w-8 shrink-0 object-contain" :alt="m.team_away" />
            <span class="truncate text-right text-sm font-semibold" :class="m.winner === m.team_away ? 'text-emerald-400 font-bold' : 'text-slate-200'">
              {{ m.team_away }}
            </span>
          </div>
          <ChevronRight :size="18" class="shrink-0 text-slate-600" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* =============================================================
   GEOMETRI CONNECTOR (gap antar kolom = 20px, 7 kolom)
   - Play-off : garis lurus horizontal ke R16 (sejajar cabang)
   - R16      : elbow di dalam kolom (padding 16px) -> 25%/75%
   - QF       : stub masuk (-24px/48px), stub keluar ke rail
   - Rail     : vertikal di tepi kolom center (25% -> 75%)
   - Final    : full-width, menutup rail di 50%
   ============================================================= */

.branch {
  position: relative;
}

/* ================= KOLOM 1: PLAY-OFF KIRI (lurus ke kanan) ================= */
.col-po-left .branch::after {
  content: '';
  position: absolute;
  right: -20px;
  top: 50%;
  width: 20px;
  height: 2px;
  background: #334155;
}

/* ================= KOLOM 2: R16 KIRI (bracket keluar ke kanan) ================= */
.col-r16-left .branch {
  padding-right: 16px;
}
.col-r16-left .branch:nth-child(odd)::after {
  content: '';
  position: absolute;
  top: 50%;
  right: 0;
  width: 16px;
  height: 50%;
  border-right: 2px solid #334155;
  border-top: 2px solid #334155;
  border-top-right-radius: 10px;
}
.col-r16-left .branch:nth-child(even)::after {
  content: '';
  position: absolute;
  bottom: 50%;
  right: 0;
  width: 16px;
  height: 50%;
  border-right: 2px solid #334155;
  border-bottom: 2px solid #334155;
  border-bottom-right-radius: 10px;
}

/* ================= KOLOM 3: QF KIRI ================= */
/* masuk dari R16 (kiri) */
.col-qf-left .branch::before {
  content: '';
  position: absolute;
  left: -24px;
  top: 50%;
  width: 48px;
  height: 2px;
  background: #334155;
}
/* keluar ke rail center (kanan) */
.col-qf-left .branch::after {
  content: '';
  position: absolute;
  right: -22px;
  top: 50%;
  width: 26px;
  height: 2px;
  background: #334155;
}

/* ================= KOLOM 4: GRAND FINAL & CHAMPION ================= */
.conn-rail {
  position: absolute;
  top: 25%;
  height: 50%;
  width: 2px;
  background: #334155;
}
.conn-rail--l {
  left: 0;
}
.conn-rail--r {
  right: 0;
}
/* Garis champion -> final: top = atas kartu champion (mt-4),
   bottom masuk ke dalam kartu final (ditutup kartu final) */
.conn-line {
  position: absolute;
  left: 50%;
  top: 16px;
  bottom: calc(50% + 30px);
  width: 2px;
  transform: translateX(-50%);
  background: #334155;
}

/* ================= KOLOM 5: QF KANAN ================= */
/* masuk dari R16 (kanan) */
.col-qf-right .branch::before {
  content: '';
  position: absolute;
  right: -24px;
  top: 50%;
  width: 48px;
  height: 2px;
  background: #334155;
}
/* keluar ke rail center (kiri) */
.col-qf-right .branch::after {
  content: '';
  position: absolute;
  left: -22px;
  top: 50%;
  width: 26px;
  height: 2px;
  background: #334155;
}

/* ================= KOLOM 6: R16 KANAN (bracket keluar ke kiri) ================= */
.col-r16-right .branch {
  padding-left: 16px;
}
.col-r16-right .branch:nth-child(odd)::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  width: 16px;
  height: 50%;
  border-left: 2px solid #334155;
  border-top: 2px solid #334155;
  border-top-left-radius: 10px;
}
.col-r16-right .branch:nth-child(even)::after {
  content: '';
  position: absolute;
  bottom: 50%;
  left: 0;
  width: 16px;
  height: 50%;
  border-left: 2px solid #334155;
  border-bottom: 2px solid #334155;
  border-bottom-left-radius: 10px;
}

/* ================= KOLOM 7: PLAY-OFF KANAN (lurus ke kiri) ================= */
.col-po-right .branch::after {
  content: '';
  position: absolute;
  left: -20px;
  top: 50%;
  width: 20px;
  height: 2px;
  background: #334155;
}
</style>
