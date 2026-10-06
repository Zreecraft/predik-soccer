<script setup>
defineProps({
  pots: { type: Object, default: () => ({}) },
})

const potOrder = ['Pot 1', 'Pot 2', 'Pot 3', 'Pot 4']

function statusClass(status) {
  if (status === 'LOLOS') return 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400'
  if (status === 'PLAY-OFF') return 'border-amber-500/40 bg-amber-500/10 text-amber-400'
  return 'border-rose-500/40 bg-rose-500/10 text-rose-400'
}
</script>

<template>
  <div class="panel p-5">
    <div class="label-caps">Fase Liga</div>
    <h3 class="mb-4 mt-1 text-base font-semibold text-slate-100">Alokasi Pot · 36 Tim</h3>

    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div v-for="pot in potOrder" :key="pot">
        <div class="mb-2 flex items-center justify-between">
          <div class="text-sm font-semibold text-slate-200">{{ pot }}</div>
          <span class="num text-[11px] text-slate-500">{{ (pots[pot] || []).length }} tim</span>
        </div>
        <div class="space-y-2">
          <div
            v-for="t in pots[pot] || []"
            :key="t.team"
            class="rounded-lg border border-slate-800 bg-slate-950/40 p-2.5"
          >
            <div class="flex items-center gap-2">
              <img
                v-if="t.logo"
                :src="t.logo"
                :alt="t.team"
                class="h-6 w-6 rounded object-contain"
              />
              <div class="min-w-0 flex-1">
                <div class="truncate text-xs font-semibold text-slate-100">{{ t.team }}</div>
                <div class="num text-[10px] text-slate-500">
                  {{ t.PTS }} pts · xG {{ t.avg_xg }}
                </div>
              </div>
              <span class="chip" :class="statusClass(t.status)">{{ t.status }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
