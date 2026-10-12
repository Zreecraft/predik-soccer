<script setup>
defineProps({
  history: { type: Array, default: () => [] },
  selectedSeason: { type: Number, default: null },
})

function posClass(pos) {
  if (pos === 1) return 'text-amber-400 font-semibold'
  if (pos <= 4) return 'text-emerald-400'
  if (pos <= 6) return 'text-sky-400'
  return 'text-slate-300'
}
</script>

<template>
  <div class="panel overflow-hidden">
    <div class="flex items-center justify-between border-b border-slate-800 px-5 py-4">
      <div>
        <div class="label-caps">Statistik per Musim</div>
        <h3 class="mt-1 text-base font-semibold text-slate-100">Rekam Jejak 2020/21 → Sekarang</h3>
      </div>
      <span class="text-[11px] text-slate-500">Sumber: hasil laga Understat</span>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full min-w-[980px] border-collapse text-sm">
        <thead>
          <tr class="border-b border-slate-800 bg-slate-950/40 text-left">
            <th class="label-caps px-4 py-3">Musim</th>
            <th class="label-caps px-3 py-3 text-right">Pos</th>
            <th class="label-caps px-3 py-3 text-right">Main</th>
            <th class="label-caps px-3 py-3 text-right">M</th>
            <th class="label-caps px-3 py-3 text-right">S</th>
            <th class="label-caps px-3 py-3 text-right">K</th>
            <th class="label-caps px-3 py-3 text-right">GM</th>
            <th class="label-caps px-3 py-3 text-right">GK</th>
            <th class="label-caps px-3 py-3 text-right">SG</th>
            <th class="label-caps px-3 py-3 text-right">Poin</th>
            <th class="label-caps px-3 py-3 text-right">PPG</th>
            <th class="label-caps px-3 py-3 text-right">xG ±</th>
            <th class="label-caps px-4 py-3">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in history"
            :key="row.season"
            class="border-b border-slate-800/70 transition"
            :class="[
              selectedSeason === row.season ? 'bg-sky-500/10' : 'hover:bg-slate-800/40',
              row.relegated ? 'bg-rose-500/5' : '',
            ]"
          >
            <td class="num px-4 py-2.5 text-slate-200">{{ row.label }}</td>
            <td class="num px-3 py-2.5 text-right" :class="posClass(row.position)">
              {{ row.position }}
            </td>
            <td class="num px-3 py-2.5 text-right text-slate-400">{{ row.played }}</td>
            <td class="num px-3 py-2.5 text-right text-slate-300">{{ row.w }}</td>
            <td class="num px-3 py-2.5 text-right text-slate-400">{{ row.d }}</td>
            <td class="num px-3 py-2.5 text-right text-slate-400">{{ row.l }}</td>
            <td class="num px-3 py-2.5 text-right text-slate-300">{{ row.gf }}</td>
            <td class="num px-3 py-2.5 text-right text-slate-400">{{ row.ga }}</td>
            <td class="num px-3 py-2.5 text-right" :class="row.gd > 0 ? 'text-emerald-400' : row.gd < 0 ? 'text-rose-400' : 'text-slate-400'">
              {{ row.gd > 0 ? '+' : '' }}{{ row.gd }}
            </td>
            <td class="num px-3 py-2.5 text-right font-semibold text-slate-100">{{ row.points }}</td>
            <td class="num px-3 py-2.5 text-right text-sky-400">{{ row.ppg }}</td>
            <td class="num px-3 py-2.5 text-right text-xs">
              <span class="text-emerald-400">{{ row.xg_for_avg }}</span>
              <span class="mx-0.5 text-slate-600">/</span>
              <span class="text-rose-400">{{ row.xg_ga_avg }}</span>
            </td>
            <td class="px-4 py-2.5">
              <span
                v-if="row.relegated"
                class="chip border-rose-500/40 bg-rose-500/15 text-[10px] font-semibold text-rose-400"
              >
                DEGRADASI
              </span>
              <span
                v-else-if="row.in_progress"
                class="chip border-sky-500/30 bg-sky-500/10 text-[10px] text-sky-400"
              >
                BERLANGSUNG
              </span>
              <span v-else class="text-[11px] text-slate-600">—</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!history.length" class="px-5 py-6 text-sm text-slate-500">
        Belum ada data musiman untuk klub ini.
      </div>
    </div>
  </div>
</template>
