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
    <div class="flex flex-wrap items-center justify-between gap-2 border-b border-line bg-canvas/40 px-4 py-3">
      <div class="flex items-center gap-2 text-sm font-semibold text-ink">
        <span class="inline-block h-2 w-2 animate-pulse rounded-full bg-bad" />
        Klasemen Live
        <span class="text-xs font-normal text-mute">— aktual + skor berjalan</span>
      </div>
      <span class="text-[10px] uppercase tracking-wider text-mute">
        sumber: {{ source === 'api' ? 'football-data.org' : source === 'espn' ? 'ESPN' : 'data lokal + simulasi live' }} · auto 60s
      </span>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full min-w-[720px] border-collapse text-sm">
        <thead>
          <tr class="border-b border-line bg-canvas/40 text-left">
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
            class="cursor-pointer border-b border-line/70 transition hover:bg-card/50"
            :class="zoneClass(row.zone)"
            @click="goToAnalytics(row.team)"
          >
            <td class="num px-4 py-3 text-mute">{{ row.position }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <img
                  v-if="row.logo"
                  :src="row.logo"
                  :alt="row.team"
                  class="h-7 w-7 rounded-md border border-line/50 bg-canvas/50 object-contain p-0.5"
                />
                <div class="min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="truncate font-medium text-ink">{{ row.team }}</span>
                    <span
                      v-if="row.live"
                      class="inline-flex shrink-0 items-center gap-1 rounded bg-bad/90 px-1.5 py-0.5 text-[9px] font-bold text-ink"
                    >
                      <span class="inline-block h-1 w-1 animate-pulse rounded-full bg-canvas" />LIVE
                    </span>
                  </div>
                  <div class="truncate text-[11px] text-mute">{{ row.star_player?.player_name }}</div>
                </div>
              </div>
            </td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.P }}</td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.W }}</td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.D }}</td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.L }}</td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.GF }}</td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.GA }}</td>
            <td class="num px-3 py-3 text-right" :class="row.GD > 0 ? 'text-ok' : row.GD < 0 ? 'text-bad' : 'text-mute'">
              {{ row.GD > 0 ? '+' : '' }}{{ row.GD }}
            </td>
            <td class="num px-3 py-3 text-right text-base font-bold text-ink">{{ row.PTS }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
