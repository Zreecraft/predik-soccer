<script setup>
defineProps({
  pots: { type: Object, default: () => ({}) },
})

const potOrder = ['Pot 1', 'Pot 2', 'Pot 3', 'Pot 4']

function rangeLabel(rows) {
  if (!rows.length) return 'Kosong'
  return `Pos ${rows[0].position}–${rows[rows.length - 1].position}`
}

function zoneOf(t) {
  if (t.status === 'LOLOS') return 'r16'
  if (t.status === 'PLAY-OFF') return t.is_seeded ? 'poS' : 'poU'
  return 'out'
}

const zone = {
  r16: {
    pos: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
    chip: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
    name: 'text-slate-100',
    label: '16 Besar',
    tip: 'Lolos langsung ke 16 Besar',
  },
  poS: {
    pos: 'border-amber-500/40 bg-amber-500/10 text-amber-400',
    chip: 'border-amber-500/40 bg-amber-500/10 text-amber-400',
    name: 'text-slate-200',
    label: 'Play-off',
    tip: 'Play-off (Seeded)',
  },
  poU: {
    pos: 'border-amber-500/40 bg-amber-500/10 text-amber-400',
    chip: 'border-amber-500/30 bg-transparent text-amber-400/90',
    name: 'text-slate-300',
    label: 'Play-off',
    tip: 'Play-off (Unseeded)',
  },
  out: {
    pos: 'border-rose-500/40 bg-rose-500/10 text-rose-400',
    chip: 'border-rose-500/40 bg-rose-500/10 text-rose-400',
    name: 'text-slate-400',
    label: 'Gugur',
    tip: 'Tereliminasi dari fase liga',
  },
}
</script>

<template>
  <div class="panel overflow-hidden">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 p-5 pb-4">
      <div>
        <div class="label-caps text-sky-400">Fase Liga · Undian</div>
        <h3 class="mt-1 text-base font-semibold text-slate-100">Alokasi Pot · 36 Tim</h3>
      </div>
      <div class="num text-[11px] text-slate-500">4 pot × 9 tim</div>
    </div>

    <!-- Grid Pot -->
    <div class="grid gap-4 p-5 pt-4 md:grid-cols-2">
      <div
        v-for="pot in potOrder"
        :key="pot"
        class="overflow-hidden rounded-lg border border-slate-800 bg-slate-950/30"
      >
        <!-- Bar judul pot -->
        <div class="flex items-center justify-between border-b border-slate-800 bg-slate-900/70 px-3 py-2">
          <div class="flex items-center gap-2">
            <span class="h-4 w-1 rounded-full bg-sky-500/70" />
            <span class="text-xs font-bold uppercase tracking-wider text-slate-200">{{ pot }}</span>
          </div>
          <span class="num text-[10px] text-slate-500">
            {{ rangeLabel(pots[pot] || []) }} · {{ (pots[pot] || []).length }} tim
          </span>
        </div>

        <!-- Baris tim -->
        <ul class="divide-y divide-slate-800/70">
          <li
            v-for="t in pots[pot] || []"
            :key="t.team"
            class="flex items-center gap-2.5 px-3 py-2 transition hover:bg-slate-800/40"
            :title="`${t.team} · ${t.PTS} pts · xG ${t.avg_xg} — ${zone[zoneOf(t)].tip}`"
          >
            <span
              class="num inline-flex h-5 w-5 shrink-0 items-center justify-center rounded border text-[10px] font-bold"
              :class="zone[zoneOf(t)].pos"
            >
              {{ t.position }}
            </span>
            <img
              v-if="t.logo"
              :src="t.logo"
              :alt="t.team"
              class="h-6 w-6 shrink-0 object-contain"
            />
            <span
              class="min-w-0 flex-1 truncate text-xs font-semibold"
              :class="zone[zoneOf(t)].name"
            >
              {{ t.team }}
            </span>
            <span class="num shrink-0 text-[11px] font-bold text-slate-200">
              {{ t.PTS }}<span class="font-normal text-slate-600"> pts</span>
            </span>
            <span
              class="chip shrink-0 text-[10px]"
              :class="zone[zoneOf(t)].chip"
              :title="zone[zoneOf(t)].tip"
            >
              {{ zone[zoneOf(t)].label }}
            </span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
