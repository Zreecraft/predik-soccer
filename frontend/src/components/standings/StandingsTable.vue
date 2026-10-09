<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

defineProps({
  rows: { type: Array, default: () => [] },
})

function goToAnalytics(team) {
  router.push({ path: '/analytics', query: { team } })
}

function zoneClass(zone) {
  if (zone === 'UCL') return 'border-l-emerald-500'
  if (zone === 'UEL') return 'border-l-sky-500'
  if (zone === 'REL') return 'border-l-rose-500'
  return 'border-l-transparent'
}

function pctColor(pct, inverse = false) {
  const v = Number(pct) || 0
  if (inverse) {
    if (v >= 50) return 'text-rose-400'
    if (v >= 20) return 'text-amber-400'
    return 'text-emerald-400'
  }
  if (v >= 40) return 'text-emerald-400'
  if (v >= 15) return 'text-sky-400'
  return 'text-slate-400'
}
</script>

<template>
  <div class="panel overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full min-w-[900px] border-collapse text-sm">
        <thead>
          <tr class="border-b border-slate-800 bg-slate-950/40 text-left">
            <th class="label-caps px-4 py-3">POS</th>
            <th class="label-caps px-4 py-3">Klub</th>
            <th class="label-caps px-3 py-3 text-right">Main</th>
            <th class="label-caps px-3 py-3 text-right">Poin</th>
            <th class="label-caps px-3 py-3 text-right">Proyeksi</th>
            <th class="label-caps px-3 py-3 text-right">Juara</th>
            <th class="label-caps px-3 py-3 text-right">Top 4</th>
            <th class="label-caps px-3 py-3 text-right">Risiko Deg</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row.team"
            class="cursor-pointer border-b border-slate-800/70 transition hover:bg-slate-800/50"
            :class="zoneClass(row.zone)"
            @click="goToAnalytics(row.team)"
          >
            <td class="num px-4 py-3 text-slate-400">{{ row.projected_position }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <img
                  v-if="row.logo"
                  :src="row.logo"
                  :alt="row.team"
                  class="h-7 w-7 rounded-md border border-slate-700/50 bg-slate-950/50 object-contain p-0.5"
                />
                <div class="min-w-0">
                  <div class="truncate font-medium text-slate-100">{{ row.team }}</div>
                  <div class="truncate text-[11px] text-slate-500">{{ row.star_player?.player_name }}</div>
                </div>
              </div>
            </td>
            <td class="num px-3 py-3 text-right text-slate-300">{{ row.P }}</td>
            <td class="num px-3 py-3 text-right font-semibold text-slate-100">{{ row.PTS }}</td>
            <td class="num px-3 py-3 text-right font-semibold text-sky-400">
              {{ row.projected_points }}
              <span class="ml-1 text-[10px] text-slate-500">±{{ row.projected_std }}</span>
            </td>
            <td class="num px-3 py-3 text-right" :class="pctColor(row.title_pct)">
              {{ row.title_pct }}%
            </td>
            <td class="num px-3 py-3 text-right" :class="pctColor(row.top4_pct)">
              {{ row.top4_pct }}%
            </td>
            <td class="num px-3 py-3 text-right" :class="pctColor(row.relegation_pct, true)">
              {{ row.relegation_pct }}%
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
