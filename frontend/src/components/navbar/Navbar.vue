<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Activity, BarChart3, GitBranch, LineChart, Menu, X } from 'lucide-vue-next'
import { fetchTicker } from '@/services/api'
import { abbrTeam } from '@/utils/format'

const route = useRoute()
const tickerItems = ref([])
const tickerLoading = ref(false)
const mobileOpen = ref(false)

const links = [
  { to: '/predict', label: 'Prediksi Laga', icon: Activity },
  { to: '/standings', label: 'Proyeksi Liga', icon: LineChart },
  { to: '/ucl', label: 'Bagan UCL', icon: GitBranch },
  { to: '/analytics', label: 'Analitik Klub', icon: BarChart3 },
]

onMounted(async () => {
  tickerLoading.value = true
  try {
    const data = await fetchTicker(18)
    tickerItems.value = data.items || []
  } catch {
    tickerItems.value = []
  } finally {
    tickerLoading.value = false
  }
})
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-slate-800 bg-canvas/95 backdrop-blur">
    <div class="mx-auto flex h-14 max-w-[1400px] items-center justify-between gap-4 px-4 sm:px-6">
      <RouterLink to="/predict" class="flex items-center gap-3">
        <span class="flex h-8 w-8 items-center justify-center rounded-lg border border-sky-500/40 bg-sky-500/10">
          <Activity class="h-4 w-4 text-sky-400" :size="16" />
        </span>
        <span class="flex flex-col leading-none">
          <span class="text-sm font-extrabold tracking-[0.18em] text-slate-50">ANALYTICA FC</span>
          <span class="mt-0.5 text-[10px] font-semibold tracking-[0.22em] text-sky-400/90">TELEMETRI</span>
        </span>
      </RouterLink>

      <nav class="hidden items-center gap-1 lg:flex">
        <RouterLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="rounded-lg px-3 py-2 text-sm font-medium transition"
          :class="
            route.path.startsWith(link.to)
              ? 'bg-slate-800/80 text-slate-50'
              : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
          "
        >
          {{ link.label }}
        </RouterLink>
      </nav>

      <button
        class="btn-ghost lg:hidden"
        type="button"
        @click="mobileOpen = !mobileOpen"
      >
        <Menu v-if="!mobileOpen" :size="16" />
        <X v-else :size="16" />
      </button>
    </div>

    <!-- Mobile nav -->
    <nav v-if="mobileOpen" class="border-t border-slate-800 bg-slate-950/95 px-4 py-3 lg:hidden">
      <RouterLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        class="mb-1 flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-slate-800"
        @click="mobileOpen = false"
      >
        <component :is="link.icon" :size="15" class="text-slate-500" />
        {{ link.label }}
      </RouterLink>
    </nav>

    <!-- Fixture ticker -->
    <div class="border-t border-slate-800/80 bg-slate-950/60">
      <div class="relative mx-auto flex h-9 max-w-[1400px] items-center overflow-hidden px-4 sm:px-6">
        <span class="label-caps mr-3 shrink-0 text-sky-400/90">Pekan</span>
        <div v-if="tickerLoading" class="skeleton h-4 flex-1" />
        <div v-else-if="tickerItems.length" class="ticker-track gap-6">
          <div v-for="(item, i) in [...tickerItems, ...tickerItems]" :key="i" class="flex shrink-0 items-center gap-2 text-[11px]">
            <span class="num font-semibold text-slate-200">{{ item.home_short || abbrTeam(item.home) }}</span>
            <span class="text-slate-600">vs</span>
            <span class="num font-semibold text-slate-200">{{ item.away_short || abbrTeam(item.away) }}</span>
            <span class="text-slate-600">·</span>
            <span class="num text-slate-500">{{ item.date?.slice(5, 16) || '' }}</span>
          </div>
        </div>
        <div v-else class="text-xs text-slate-500">Jadwal pekan ini tidak tersedia</div>
      </div>
    </div>
  </header>
</template>
