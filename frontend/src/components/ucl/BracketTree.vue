<script setup>
defineProps({
  matches: { type: Array, default: () => [] },
  title: { type: String, default: '' },
})

function probBar(homeProb, awayProb) {
  return {
    home: Number(homeProb) || 0,
    away: Number(awayProb) || 0,
  }
}
</script>

<template>
  <div>
    <div v-if="title" class="label-caps mb-2">{{ title }}</div>
    <div class="space-y-2">
      <div
        v-for="(m, i) in matches"
        :key="i"
        class="rounded-lg border border-slate-800 bg-slate-900/50 p-3"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="flex min-w-0 items-center gap-2">
            <img
              v-if="m.logo_home"
              :src="m.logo_home"
              :alt="m.team_home"
              class="h-6 w-6 rounded object-contain"
            />
            <span class="truncate text-xs font-semibold" :class="m.winner === m.team_home ? 'text-emerald-400' : 'text-slate-300'">
              {{ m.team_home }}
            </span>
          </div>

          <div class="num shrink-0 rounded-md border border-slate-700/70 bg-slate-950/70 px-2 py-1 text-[11px] font-bold text-slate-100">
            {{ m.agg_home }} - {{ m.agg_away }}
          </div>

          <div class="flex min-w-0 flex-row-reverse items-center gap-2">
            <img
              v-if="m.logo_away"
              :src="m.logo_away"
              :alt="m.team_away"
              class="h-6 w-6 rounded object-contain"
            />
            <span class="truncate text-right text-xs font-semibold" :class="m.winner === m.team_away ? 'text-emerald-400' : 'text-slate-300'">
              {{ m.team_away }}
            </span>
          </div>
        </div>

        <div class="mt-2">
          <div class="flex h-1 overflow-hidden rounded-full bg-slate-800">
            <div
              class="h-full bg-sky-500/80"
              :style="{ width: probBar(m.win_prob_home, m.win_prob_away).home + '%' }"
            />
            <div
              class="h-full bg-rose-500/80"
              :style="{ width: probBar(m.win_prob_home, m.win_prob_away).away + '%' }"
            />
          </div>
          <div class="num mt-1 flex justify-between text-[10px] text-slate-500">
            <span>{{ m.win_prob_home }}% menang</span>
            <span class="text-emerald-400/90">Winner: {{ m.winner }}</span>
            <span>{{ m.win_prob_away }}% menang</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
