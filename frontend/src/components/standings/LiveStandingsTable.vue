<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

defineProps({
  rows: { type: Array, default: () => [] },
  source: { type: String, default: 'mock' },
})

function goToAnalytics(team) {
  router.push({ path: '/analytics', query: { team } })
}

function zoneClass(zone) {
  if (zone === 'UCL') return 'border-l-2 border-l-emerald-500'
  if (zone === 'UEL') return 'border-l-2 border-l-sky-500'
  if (zone === 'REL') return 'border-l-2 border-l-rose-500'
  return 'border-l-2 border-l-transparent'
}
</script>

<template>
  <div class="panel overflow-hidden">
    <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 bg-slate-950/40 px-4 py-3">
      <div class="flex items-center gap-2 text-sm font-semibold text-slate-200">
        <span class="inline-block h-2 w-2 animate-pulse rounded-full bg-rose-500" />
        Klasemen Live
        <span class="text-xs font-normal text-slate-500">— aktual + skor berjalan</span>
      </div>
      <span class="text-[10px] uppercase tracking-wider text-slate-500">
        sumber: {{ source === 'api' ? 'football-data.org' : source === 'espn' ? 'ESPN' : 'data lokal + simulasi live' }} · auto 60s
      </span>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full min-w-[720px] border-collapse text-sm">
        <thead>
          <tr class="border-b border-slate-800 bg-slate-950/40 text-left">
            <th class="label-caps px-4 py-3">POS</th>
            <th class="label-caps px-4 py-3">Klub</th>
            <th class="label-caps px-3 py-3 text-right">Main</th>
            <th class="label-caps px-3 py-3 text-right">M</th>
            <th class="label-caps px-3 py-3 text-right">S</th>
            <th class="label-caps px-3 py-3 text-right">K</th>
            <th class="label-caps px-3 py-3 text-right">GM</th>
            <th class="label-caps px-3 py-3 text-right">GK</th>
            <th class="label-caps px-3 py-3 text-right">SG</th>
            <th class="label-caps px-3 py-3 text-right">Poin</th>
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
            <td class="num px-4 py-3 text-slate-400">{{ row.position }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <img
                  v-if="row.logo"
                  :src="row.logo"
                  :alt="row.team"
                  class="h-7 w-7 rounded-md border border-slate-700/50 bg-slate-950/50 object-contain p-0.5"
                />
                <div class="min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="truncate font-medium text-slate-100">{{ row.team }}</span>
                    <span
                      v-if="row.live"
                      class="inline-flex shrink-0 items-center gap-1 rounded bg-rose-600/90 px-1.5 py-0.5 text-[9px] font-bold text-white"
                    >
                      <span class="inline-block h-1 w-1 animate-pulse rounded-full bg-white" />LIVE
                    </span>
                  </div>
                  <div class="truncate text-[11px] text-slate-500">{{ row.star_player?.player_name }}</div>
                </div>
              </div>
            </td>
            <td class="num px-3 py-3 text-right text-slate-300">{{ row.P }}</td>
            <td class="num px-3 py-3 text-right text-slate-400">{{ row.W }}</td>
            <td class="num px-3 py-3 text-right text-slate-400">{{ row.D }}</td>
            <td class="num px-3 py-3 text-right text-slate-400">{{ row.L }}</td>
            <td class="num px-3 py-3 text-right text-slate-400">{{ row.GF }}</td>
            <td class="num px-3 py-3 text-right text-slate-400">{{ row.GA }}</td>
            <td class="num px-3 py-3 text-right" :class="row.GD > 0 ? 'text-emerald-400' : row.GD < 0 ? 'text-rose-400' : 'text-slate-400'">
              {{ row.GD > 0 ? '+' : '' }}{{ row.GD }}
            </td>
            <td class="num px-3 py-3 text-right text-base font-bold text-slate-50">{{ row.PTS }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
