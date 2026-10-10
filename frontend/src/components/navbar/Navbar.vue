<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { BarChart3, Crosshair, GitBranch, LineChart, Menu, MonitorPlay, X } from 'lucide-vue-next'
import { fetchTicker } from '@/services/api'
import { abbrTeam } from '@/utils/format'
import LiveTicker from '@/components/shared/LiveTicker.vue'

const route = useRoute()
const tickerItems = ref([])
const tickerLoading = ref(false)
const mobileOpen = ref(false)

const links = [
  { to: '/predict', label: 'Prediksi Laga', icon: Crosshair },
  { to: '/match', label: 'Match Centre', icon: MonitorPlay },
  { to: '/standings', label: 'Proyeksi Liga', icon: LineChart },
  { to: '/ucl', label: 'Bagan UCL', icon: GitBranch },
  { to: '/analytics', label: 'Analitik Klub', icon: BarChart3 },
]

// Parse tanggal ISO → DD MMM HH:mm (local time friendly)
function formatDate(dateStr) {
  if (!dateStr || typeof dateStr !== 'string') return '?'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return '?'
    const days = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab']
    const day = days[d.getDay()]
    const date = String(d.getDate()).padStart(2, '0')
    const month = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'][d.getMonth()]
    const hours = String(d.getHours()).padStart(2, '0')
    const mins = String(d.getMinutes()).padStart(2, '0')
    return `${day} ${date} ${month} • ${hours}:${mins}`
  } catch {
    return '?'
  }
}

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
      <RouterLink to="/predict" class="group flex items-center gap-3">
        <img
          src="/logo.svg"
          alt=""
          class="h-9 w-9 rounded-xl border border-slate-700/70 bg-slate-950/60 p-1 transition group-hover:border-sky-500/50"
          width="36"
          height="36"
        />
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

    <!-- Live score ticker -->
    <LiveTicker />

    <!-- Fixture ticker -->
    <div class="border-t border-slate-800/80 bg-slate-950/60">
      <div class="relative mx-auto flex h-9 max-w-[1400px] items-center overflow-hidden px-4 sm:px-6">
        <span class="label-caps relative z-10 mr-3 shrink-0 bg-slate-950/60 pr-1 text-sky-400/90">Pekan</span>
        <div v-if="tickerLoading" class="skeleton h-4 flex-1" />
        <div v-else-if="tickerItems.length" class="min-w-0 flex-1 overflow-hidden">
          <div class="ticker-track gap-6 pr-8">
            <div
              v-for="(item, i) in tickerItems"
              :key="i"
              class="flex shrink-0 items-center gap-2 whitespace-nowrap text-[11px]"
            >
              <span class="num font-semibold text-slate-200">{{ item.home_short || abbrTeam(item.home) }}</span>
              <span class="text-slate-600">×</span>
              <span class="num font-semibold text-slate-200">{{ item.away_short || abbrTeam(item.away) }}</span>
              <span class="hidden sm:inline text-slate-600">|</span>
              <span class="num text-slate-500">{{ formatDate(item.date) }}</span>
            </div>
          </div>
        </div>
        <div v-else class="text-xs text-slate-500">Jadwal pekan ini tidak tersedia</div>
      </div>
    </div>
  </header>
</template>
