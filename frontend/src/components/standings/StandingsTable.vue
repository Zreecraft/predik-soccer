<script setup>
import { useRouter } from 'vue-router'
import PositionSparkline from '@/components/standings/PositionSparkline.vue'

const router = useRouter()

const props = defineProps({
  rows: { type: Array, default: () => [] },
  positionHistory: { type: Object, default: null },
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
    if (v >= 50) return 'text-bad'
    if (v >= 20) return 'text-draw'
    return 'text-ok'
  }
  if (v >= 40) return 'text-ok'
  if (v >= 15) return 'text-home'
  return 'text-mute'
}

function historyValues(team) {
  return props.positionHistory?.teams?.[team] || []
}

function historyTitle(team) {
  const seasons = props.positionHistory?.seasons || []
  const vals = historyValues(team)
  if (!vals.length) return 'Belum ada riwayat posisi'
  return seasons.map((s, i) => `${s}/${String(s + 1).slice(2)}: ${vals[i] ?? '-'}`).join(' · ')
}
</script>

<template>
  <div class="panel overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full min-w-[1500px] border-collapse text-sm">
        <thead>
          <tr class="border-b border-line bg-canvas/40 text-left">
            <th class="label-caps px-4 py-3">POS</th>
            <th class="label-caps px-4 py-3">Klub</th>
            <th class="label-caps px-3 py-3">Riwayat</th>
            <th class="label-caps px-3 py-3 text-right">Main</th>
            <th class="label-caps px-3 py-3 text-right">M</th>
            <th class="label-caps px-3 py-3 text-right">S</th>
            <th class="label-caps px-3 py-3 text-right">K</th>
            <th class="label-caps px-3 py-3 text-right">GM</th>
            <th class="label-caps px-3 py-3 text-right">GK</th>
            <th class="label-caps px-3 py-3 text-right">SG</th>
            <th class="label-caps px-3 py-3 text-right">Poin</th>
            <th class="label-caps px-3 py-3 text-right">Proyeksi</th>
            <th class="label-caps px-3 py-3 text-right">PPG</th>
            <th class="label-caps px-3 py-3 text-right">xG F/A</th>
            <th class="label-caps px-3 py-3 text-right">Juara</th>
            <th class="label-caps px-3 py-3 text-right">Top 4</th>
            <th class="label-caps px-3 py-3 text-right">Risiko Deg</th>
            <th class="label-caps px-4 py-3">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row.team"
            class="cursor-pointer border-b border-line/70 transition hover:bg-card/50"
            :class="[zoneClass(row.zone), row.status === 'DEGRADASI' ? 'bg-bad/[0.04]' : '']"
            @click="goToAnalytics(row.team)"
          >
            <td class="num px-4 py-3 text-mute">{{ row.projected_position }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <img
                  v-if="row.logo"
                  :src="row.logo"
                  :alt="row.team"
                  class="h-7 w-7 rounded-md border border-line/50 bg-canvas/50 object-contain p-0.5"
                />
                <div class="min-w-0">
                  <div class="truncate font-medium text-ink">{{ row.team }}</div>
                  <div class="truncate text-[11px] text-mute">{{ row.star_player?.player_name }}</div>
                </div>
              </div>
            </td>
            <td class="px-3 py-3" :title="historyTitle(row.team)">
              <PositionSparkline :values="historyValues(row.team)" />
            </td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.P }}</td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.W }}</td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.D }}</td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.L }}</td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.GF }}</td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.GA }}</td>
            <td
              class="num px-3 py-3 text-right"
              :class="row.GD > 0 ? 'text-ok' : row.GD < 0 ? 'text-bad' : 'text-mute'"
            >
              {{ row.GD > 0 ? '+' : '' }}{{ row.GD }}
            </td>
            <td class="num px-3 py-3 text-right font-semibold text-ink">{{ row.PTS }}</td>
            <td class="num px-3 py-3 text-right font-semibold text-home">
              {{ row.projected_points }}
              <span class="ml-1 text-[10px] text-mute">±{{ row.projected_std }}</span>
            </td>
            <td class="num px-3 py-3 text-right text-mute">{{ row.ppg ?? '—' }}</td>
            <td class="num px-3 py-3 text-right text-xs">
              <template v-if="row.avg_xg_for != null">
                <span class="text-ok">{{ row.avg_xg_for }}</span>
                <span class="mx-0.5 text-mute">/</span>
                <span class="text-bad">{{ row.avg_xg_ga }}</span>
              </template>
              <span v-else class="text-mute">—</span>
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
            <td class="px-4 py-3">
              <div class="flex flex-wrap items-center gap-1">
                <span
                  v-if="row.status === 'DEGRADASI'"
                  class="chip border-bad/40 bg-bad/15 text-[10px] font-semibold text-bad"
                >
                  DEGRADASI
                </span>
                <span
                  v-else-if="row.status === 'JUARA'"
                  class="chip border-draw/40 bg-draw/15 text-[10px] font-semibold text-draw"
                >
                  JUARA
                </span>
                <span
                  v-if="row.promoted"
                  class="chip border-home/30 bg-home/10 text-[10px] font-semibold text-home"
                >
                  PROMOSI
                </span>
                <span
                  v-if="row.relegated_last"
                  class="chip border-line bg-card/60 text-[10px] font-semibold text-mute"
                >
                  {{ row.relegated_last }}
                </span>
                <span
                  v-if="row.status !== 'DEGRADASI' && row.status !== 'JUARA' && !row.promoted"
                  class="text-[11px] text-mute"
                >
                  —
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
