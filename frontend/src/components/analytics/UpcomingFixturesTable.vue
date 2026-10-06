<script setup>
defineProps({
  fixtures: { type: Array, default: () => [] },
})

function miniBar(p) {
  const home = Number(p.prob_home) || 0
  const draw = Number(p.prob_draw) || 0
  const away = Number(p.prob_away) || 0
  return { home, draw, away }
}
</script>

<template>
  <div class="panel overflow-hidden">
    <div class="border-b border-slate-800 px-5 py-4">
      <div class="label-caps">Proyeksi Algoritmik</div>
      <h3 class="mt-1 text-base font-semibold text-slate-100">Jadwal Mendatang & Peluang</h3>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full min-w-[720px] text-sm">
        <thead>
          <tr class="border-b border-slate-800 bg-slate-950/40 text-left">
            <th class="label-caps px-4 py-2.5">Tanggal</th>
            <th class="label-caps px-4 py-2.5">Lawan</th>
            <th class="label-caps px-4 py-2.5">Kandang/Tandang</th>
            <th class="label-caps px-4 py-2.5">1X2</th>
            <th class="label-caps px-4 py-2.5 text-right">Menang</th>
            <th class="label-caps px-4 py-2.5 text-right">Kesulitan</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(f, i) in fixtures"
            :key="i"
            class="border-b border-slate-800/70 hover:bg-slate-800/25"
          >
            <td class="num px-4 py-3 text-xs text-slate-400">{{ (f.date || '').slice(0, 16) }}</td>
            <td class="px-4 py-3">
              <div class="font-medium text-slate-100">{{ f.opponent }}</div>
              <div class="text-[11px] text-slate-500">{{ f.home_team }} vs {{ f.away_team }}</div>
            </td>
            <td class="px-4 py-3">
              <span class="chip" :class="f.is_home ? 'border-sky-500/30 bg-sky-500/10 text-sky-400' : 'border-slate-600 bg-slate-800/40 text-slate-300'">
                {{ f.is_home ? 'HOME' : 'AWAY' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <div class="flex h-1.5 w-32 overflow-hidden rounded-full bg-slate-800">
                <div class="h-full bg-sky-500" :style="{ width: miniBar(f).home + '%' }" />
                <div class="h-full bg-slate-500" :style="{ width: miniBar(f).draw + '%' }" />
                <div class="h-full bg-rose-500" :style="{ width: miniBar(f).away + '%' }" />
              </div>
              <div class="num mt-1 text-[10px] text-slate-500">
                {{ miniBar(f).home }}% · {{ miniBar(f).draw }}% · {{ miniBar(f).away }}%
              </div>
            </td>
            <td class="num px-4 py-3 text-right font-semibold" :class="f.team_win_pct >= 50 ? 'text-emerald-400' : f.team_win_pct >= 35 ? 'text-amber-400' : 'text-rose-400'">
              {{ f.team_win_pct }}%
            </td>
            <td class="px-4 py-3 text-right">
              <span class="chip" :class="f.difficulty_cls || 'border-slate-600 text-slate-300'">
                {{ f.difficulty }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
