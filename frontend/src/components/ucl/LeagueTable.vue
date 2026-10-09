<script setup>
defineProps({
  rows: { type: Array, default: () => [] },
})

const legend = [
  { dot: 'bg-emerald-400', text: '1–8 · Lolos 16 Besar' },
  { dot: 'bg-amber-400', text: '9–24 · Babak Play-off' },
  { dot: 'bg-rose-400', text: '25–36 · Tereliminasi' },
]

// Divider zona di antara baris (key = index baris pertama zona berikutnya)
const dividers = {
  8: { label: 'Babak Play-off · posisi 9–24', cls: 'text-amber-400' },
  24: { label: 'Tereliminasi · posisi 25–36', cls: 'text-rose-400' },
}

function zoneOf(pos) {
  if (pos <= 8) return 'r16'
  if (pos <= 24) return 'po'
  return 'out'
}

const zoneBorder = {
  r16: 'border-l-emerald-500/70',
  po: 'border-l-amber-500/70',
  out: 'border-l-rose-500/70',
}
const posCls = {
  r16: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
  po: 'border-amber-500/40 bg-amber-500/10 text-amber-400',
  out: 'border-rose-500/40 bg-rose-500/10 text-rose-400',
}
const chipCls = posCls
const zoneLabel = { r16: '16 Besar', po: 'Play-off', out: 'Gugur' }
</script>

<template>
  <div class="panel overflow-hidden">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 p-5">
      <div>
        <div class="label-caps text-sky-400">Fase Liga · Klasemen</div>
        <h3 class="mt-1 text-base font-semibold text-slate-100">Klasemen Akhir · 36 Tim</h3>
      </div>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="z in legend"
          :key="z.text"
          class="inline-flex items-center gap-1.5 rounded-full border border-slate-700 bg-slate-950/60 px-2.5 py-1 text-[11px] text-slate-400"
        >
          <span class="h-1.5 w-1.5 rounded-full" :class="z.dot" />
          {{ z.text }}
        </span>
      </div>
    </div>

    <!-- Tabel -->
    <div class="max-h-[620px] overflow-y-auto overflow-x-auto">
      <table class="w-full text-left text-xs">
        <thead class="league-thead">
          <tr class="text-[10px] uppercase tracking-wider text-slate-500">
            <th class="w-12 px-4 py-2.5 font-semibold">#</th>
            <th class="px-2 py-2.5 font-semibold">Tim</th>
            <th class="w-10 px-2 py-2.5 text-center font-semibold">P</th>
            <th class="hidden w-10 px-2 py-2.5 text-center font-semibold sm:table-cell">M</th>
            <th class="hidden w-10 px-2 py-2.5 text-center font-semibold sm:table-cell">S</th>
            <th class="hidden w-10 px-2 py-2.5 text-center font-semibold sm:table-cell">K</th>
            <th class="hidden w-10 px-2 py-2.5 text-center font-semibold md:table-cell">GM</th>
            <th class="hidden w-10 px-2 py-2.5 text-center font-semibold md:table-cell">GK</th>
            <th class="hidden w-12 px-2 py-2.5 text-center font-semibold md:table-cell">SG</th>
            <th class="w-12 px-2 py-2.5 text-center font-semibold text-slate-300">PTS</th>
            <th class="w-24 px-4 py-2.5 text-right font-semibold">Status</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(r, i) in rows" :key="r.team">
            <!-- Divider zona -->
            <tr v-if="dividers[i]">
              <td colspan="11" class="px-4 py-2">
                <div class="flex items-center gap-3" :class="dividers[i].cls">
                  <span class="text-[10px] font-bold uppercase tracking-[0.14em]">
                    {{ dividers[i].label }}
                  </span>
                  <span class="h-px flex-1 bg-slate-800" />
                </div>
              </td>
            </tr>

            <tr
              class="border-t border-slate-800/60 transition hover:bg-slate-800/30"
            >
              <td class="border-l-2 px-4 py-2" :class="zoneBorder[zoneOf(r.position)]">
                <span
                  class="num inline-flex h-6 w-7 items-center justify-center rounded border text-[11px] font-bold"
                  :class="posCls[zoneOf(r.position)]"
                >
                  {{ r.position }}
                </span>
              </td>
              <td class="px-2 py-2">
                <div class="flex min-w-0 items-center gap-2">
                  <img
                    v-if="r.logo"
                    :src="r.logo"
                    :alt="r.team"
                    class="h-6 w-6 shrink-0 object-contain"
                  />
                  <span
                    class="truncate font-semibold"
                    :class="r.position <= 8 ? 'text-slate-100' : 'text-slate-300'"
                  >
                    {{ r.team }}
                  </span>
                </div>
              </td>
              <td class="num px-2 py-2 text-center text-slate-400">{{ r.P }}</td>
              <td class="num hidden px-2 py-2 text-center text-slate-400 sm:table-cell">{{ r.W }}</td>
              <td class="num hidden px-2 py-2 text-center text-slate-400 sm:table-cell">{{ r.D }}</td>
              <td class="num hidden px-2 py-2 text-center text-slate-400 sm:table-cell">{{ r.L }}</td>
              <td class="num hidden px-2 py-2 text-center text-slate-400 md:table-cell">{{ r.GF }}</td>
              <td class="num hidden px-2 py-2 text-center text-slate-400 md:table-cell">{{ r.GA }}</td>
              <td
                class="num hidden px-2 py-2 text-center font-semibold md:table-cell"
                :class="r.GD > 0 ? 'text-emerald-400' : r.GD < 0 ? 'text-rose-400' : 'text-slate-400'"
              >
                {{ r.GD > 0 ? '+' : '' }}{{ r.GD }}
              </td>
              <td class="num px-2 py-2 text-center text-sm font-black text-slate-100">
                {{ r.PTS }}
              </td>
              <td class="px-4 py-2 text-right">
                <span class="chip" :class="chipCls[zoneOf(r.position)]">
                  {{ zoneLabel[zoneOf(r.position)] }}
                </span>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.league-thead th {
  position: sticky;
  top: 0;
  z-index: 5;
  background: #0e1628;
  border-bottom: 1px solid #1e293b;
}
</style>
