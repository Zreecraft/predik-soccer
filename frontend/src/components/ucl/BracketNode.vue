<script setup>
import { computed } from 'vue'
import { Trophy } from 'lucide-vue-next'

const props = defineProps({
  match: { type: Object, required: true },
  highlight: { type: Boolean, default: false },
  edit: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'edit-score'])

const isR16 = computed(() => String(props.match?.match_id || '').startsWith('r16'))
const isPlayoff = computed(() => String(props.match?.match_id || '').startsWith('playoff'))
const showTag = computed(
  () => props.highlight || ((isR16.value || isPlayoff.value) && !!props.match?.bracket_slot)
)

const homeProb = computed(() => Number(props.match?.win_prob_home) || 50)
const awayProb = computed(() => Number(props.match?.win_prob_away) || 100 - homeProb.value)

function onScoreChange(side, e) {
  const v = Math.max(0, Math.min(20, parseInt(e.target.value, 10) || 0))
  emit('edit-score', { match: props.match, side, value: v })
}
</script>

<template>
  <div
    class="mcard"
    :class="{ 'mcard--final': highlight, 'mcard--tagged': showTag }"
    @click="$emit('select', match)"
  >
    <!-- Tag babak / slot bagan -->
    <div v-if="highlight" class="mcard__tag mcard__tag--final">Grand Final</div>
    <div v-else-if="showTag" class="mcard__tag">{{ match.bracket_slot }}</div>

    <!-- Slot Kandang -->
    <div class="mcard__row" :class="{ 'is-win': match.winner === match.team_home }">
      <img
        v-if="match.logo_home"
        :src="match.logo_home"
        :alt="match.team_home"
        class="mcard__logo"
      />
      <span class="mcard__name">{{ match.team_home || 'TBD' }}</span>
      <input
        v-if="edit"
        class="mcard__score mcard__score--input"
        type="number"
        min="0"
        max="20"
        :value="match.agg_home ?? 0"
        :disabled="!match.team_home"
        title="Ubah skor agregat (kandang)"
        @click.stop
        @change="onScoreChange('home', $event)"
      />
      <span v-else class="mcard__score">{{ match.agg_home ?? '–' }}</span>
      <Trophy v-if="match.winner && match.winner === match.team_home" :size="11" class="mcard__flag" />
    </div>

    <!-- Slot Tandang -->
    <div class="mcard__row mcard__row--b" :class="{ 'is-win': match.winner === match.team_away }">
      <img
        v-if="match.logo_away"
        :src="match.logo_away"
        :alt="match.team_away"
        class="mcard__logo"
      />
      <span class="mcard__name">{{ match.team_away || 'TBD' }}</span>
      <input
        v-if="edit"
        class="mcard__score mcard__score--input"
        type="number"
        min="0"
        max="20"
        :value="match.agg_away ?? 0"
        :disabled="!match.team_away"
        title="Ubah skor agregat (tandang)"
        @click.stop
        @change="onScoreChange('away', $event)"
      />
      <span v-else class="mcard__score">{{ match.agg_away ?? '–' }}</span>
      <Trophy v-if="match.winner && match.winner === match.team_away" :size="11" class="mcard__flag" />
    </div>

    <!-- Bar probabilitas lolos -->
    <div class="mcard__prob" aria-hidden="true">
      <span class="mcard__prob-home" :style="{ width: homeProb + '%' }" />
      <span class="mcard__prob-away" :style="{ width: awayProb + '%' }" />
    </div>
  </div>
</template>

<style scoped>
.mcard {
  position: relative;
  width: 100%;
  cursor: pointer;
  overflow: hidden;
  border: 1px solid #1e293b;
  border-radius: 10px;
  background: linear-gradient(180deg, #111827 0%, #0b1220 100%);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}
.mcard:hover {
  transform: translateY(-2px);
  border-color: #38bdf8;
  box-shadow: 0 10px 24px rgba(56, 189, 248, 0.14), 0 6px 16px rgba(0, 0, 0, 0.45);
}
.mcard:active {
  transform: scale(0.985);
}

/* Kartu ber-tag: margin bawah agar pembatas dua baris tepat di pusat cabang */
.mcard--tagged {
  margin-bottom: 16px;
}

/* Grand Final */
.mcard--final {
  border-color: rgba(245, 158, 11, 0.5);
  background: linear-gradient(180deg, #191307 0%, #0b1220 100%);
}
.mcard--final:hover {
  border-color: #fbbf24;
  box-shadow: 0 10px 26px rgba(245, 158, 11, 0.18), 0 6px 16px rgba(0, 0, 0, 0.45);
}

/* Tag baris atas */
.mcard__tag {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 20px;
  font-size: 8.5px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #64748b;
  background: rgba(2, 6, 23, 0.6);
  border-bottom: 1px solid rgba(30, 41, 59, 0.9);
}
.mcard__tag--final {
  font-size: 9.5px;
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.12);
  border-bottom-color: rgba(245, 158, 11, 0.3);
}

/* Baris tim */
.mcard__row {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 10px 11px;
  transition: background 0.15s ease;
}
.mcard__row--b {
  border-top: 1px solid rgba(30, 41, 59, 0.8);
}
.mcard__row.is-win {
  background: rgba(16, 185, 129, 0.12);
  box-shadow: inset 3px 0 0 #10b981;
}

.mcard__logo {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  object-fit: contain;
}
.mcard__name {
  flex: 1;
  min-width: 0;
  font-size: 12.5px;
  font-weight: 600;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.mcard__row.is-win .mcard__name {
  color: #6ee7b7;
  font-weight: 800;
}

.mcard__score {
  flex-shrink: 0;
  min-width: 24px;
  padding: 2px 7px;
  text-align: center;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-variant-numeric: tabular-nums;
  font-size: 12.5px;
  font-weight: 700;
  color: #e2e8f0;
  background: #020617;
  border: 1px solid #1e293b;
  border-radius: 6px;
}
.mcard__row.is-win .mcard__score {
  color: #34d399;
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.5);
}

/* Input skor What-If */
.mcard__score--input {
  width: 42px;
  padding: 2px 4px;
  cursor: text;
  appearance: textfield;
  -moz-appearance: textfield;
}
.mcard__score--input::-webkit-outer-spin-button,
.mcard__score--input::-webkit-inner-spin-button {
  appearance: none;
  -webkit-appearance: none;
  margin: 0;
}
.mcard__score--input:focus {
  outline: none;
  border-color: #38bdf8;
  box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25);
}
.mcard__score--input:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.mcard__flag {
  flex-shrink: 0;
  color: #34d399;
}

/* Bar probabilitas lolos (Monte Carlo) */
.mcard__prob {
  display: flex;
  height: 4px;
  background: #1e293b;
}
.mcard__prob-home {
  background: #0ea5e9;
  transition: width 0.5s ease;
}
.mcard__prob-away {
  background: #f43f5e;
  opacity: 0.75;
  transition: width 0.5s ease;
}
</style>
