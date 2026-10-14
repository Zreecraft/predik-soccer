<script setup>
defineProps({
  history: { type: Array, default: () => [] },
  selectedSeason: { type: Number, default: null },
})

function posClass(pos) {
  if (pos === 1) return 'text-draw font-semibold'
  if (pos <= 4) return 'text-ok'
  if (pos <= 6) return 'text-home'
  return 'text-mute'
}
</script>

<template>
  <div class="panel overflow-hidden">
    <div class="flex items-center justify-between border-b border-line px-5 py-4">
      <div>
        <div class="label-caps">Statistik per Musim</div>
        <h3 class="mt-1 text-base font-semibold text-ink">Rekam Jejak 2020/21 → Sekarang</h3>
      </div>
      <span class="text-[11px] text-mute">Sumber: hasil laga Understat</span>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full min-w-[980px] border-collapse text-sm">
        <thead>
          <tr class="border-b border-line bg-canvas/40 text-left">
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
            class="border-b border-line/70 transition"
            :class="[
              selectedSeason === row.season ? 'bg-home/10' : 'hover:bg-card/40',
              row.relegated ? 'bg-bad/5' : '',
            ]"
          >
            <td class="num px-4 py-2.5 text-ink">{{ row.label }}</td>
            <td class="num px-3 py-2.5 text-right" :class="posClass(row.position)">
              {{ row.position }}
            </td>
            <td class="num px-3 py-2.5 text-right text-mute">{{ row.played }}</td>
            <td class="num px-3 py-2.5 text-right text-mute">{{ row.w }}</td>
            <td class="num px-3 py-2.5 text-right text-mute">{{ row.d }}</td>
            <td class="num px-3 py-2.5 text-right text-mute">{{ row.l }}</td>
            <td class="num px-3 py-2.5 text-right text-mute">{{ row.gf }}</td>
            <td class="num px-3 py-2.5 text-right text-mute">{{ row.ga }}</td>
            <td class="num px-3 py-2.5 text-right" :class="row.gd > 0 ? 'text-ok' : row.gd < 0 ? 'text-bad' : 'text-mute'">
              {{ row.gd > 0 ? '+' : '' }}{{ row.gd }}
            </td>
            <td class="num px-3 py-2.5 text-right font-semibold text-ink">{{ row.points }}</td>
            <td class="num px-3 py-2.5 text-right text-home">{{ row.ppg }}</td>
            <td class="num px-3 py-2.5 text-right text-xs">
              <span class="text-ok">{{ row.xg_for_avg }}</span>
              <span class="mx-0.5 text-mute">/</span>
              <span class="text-bad">{{ row.xg_ga_avg }}</span>
            </td>
            <td class="px-4 py-2.5">
              <span
                v-if="row.relegated"
                class="chip border-bad/40 bg-bad/15 text-[10px] font-semibold text-bad"
              >
                DEGRADASI
              </span>
              <span
                v-else-if="row.in_progress"
                class="chip border-home/30 bg-home/10 text-[10px] text-home"
              >
                BERLANGSUNG
              </span>
              <span v-else class="text-[11px] text-mute">—</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!history.length" class="px-5 py-6 text-sm text-mute">
        Belum ada data musiman untuk klub ini.
      </div>
    </div>
  </div>
</template>
