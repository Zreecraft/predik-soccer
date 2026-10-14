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
    <div class="border-b border-line px-5 py-4">
      <div class="label-caps">Proyeksi Algoritmik</div>
      <h3 class="mt-1 text-base font-semibold text-ink">Jadwal Mendatang & Peluang</h3>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full min-w-[720px] text-sm">
        <thead>
          <tr class="border-b border-line bg-canvas/40 text-left">
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
            class="border-b border-line/70 hover:bg-card/25"
          >
            <td class="num px-4 py-3 text-xs text-mute">{{ (f.date || '').slice(0, 16) }}</td>
            <td class="px-4 py-3">
              <div class="font-medium text-ink">{{ f.opponent }}</div>
              <div class="text-[11px] text-mute">{{ f.home_team }} vs {{ f.away_team }}</div>
            </td>
            <td class="px-4 py-3">
              <span class="chip" :class="f.is_home ? 'border-home/30 bg-home/10 text-home' : 'border-line bg-card/40 text-mute'">
                {{ f.is_home ? 'HOME' : 'AWAY' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <div class="flex h-1.5 w-32 overflow-hidden rounded-full bg-card">
                <div class="h-full bg-home" :style="{ width: miniBar(f).home + '%' }" />
                <div class="h-full bg-mute" :style="{ width: miniBar(f).draw + '%' }" />
                <div class="h-full bg-bad" :style="{ width: miniBar(f).away + '%' }" />
              </div>
              <div class="num mt-1 text-[10px] text-mute">
                {{ miniBar(f).home }}% · {{ miniBar(f).draw }}% · {{ miniBar(f).away }}%
              </div>
            </td>
            <td class="num px-4 py-3 text-right font-semibold" :class="f.team_win_pct >= 50 ? 'text-ok' : f.team_win_pct >= 35 ? 'text-draw' : 'text-bad'">
              {{ f.team_win_pct }}%
            </td>
            <td class="px-4 py-3 text-right">
              <span class="chip" :class="f.difficulty_cls || 'border-line text-mute'">
                {{ f.difficulty }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
