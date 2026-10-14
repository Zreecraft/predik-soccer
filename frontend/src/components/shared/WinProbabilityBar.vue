<script setup>
import { computed } from 'vue'

const props = defineProps({
  homeWin: { type: Number, default: 0 },
  draw: { type: Number, default: 0 },
  awayWin: { type: Number, default: 0 },
  homeLabel: { type: String, default: 'Home' },
  awayLabel: { type: String, default: 'Away' },
})

const homeW = computed(() => props.homeWin || 0)
const drawW = computed(() => props.draw || 0)
const awayW = computed(() => props.awayWin || 0)
</script>

<template>
  <div class="space-y-2">
    <div class="flex h-2.5 w-full overflow-hidden rounded-full" style="background: var(--line)">
      <div class="h-full transition-all" :style="{ width: homeW + '%', background: 'var(--home)' }" />
      <div class="h-full transition-all" :style="{ width: drawW + '%', background: 'var(--draw)' }" />
      <div class="h-full transition-all" :style="{ width: awayW + '%', background: 'var(--away)' }" />
    </div>
    <div class="grid grid-cols-3 gap-2">
      <div>
        <div class="num text-[15px] font-semibold" style="color: var(--home)">{{ homeW.toFixed(1) }}%</div>
        <div class="mt-0.5 truncate text-[13px]" style="color: var(--mute)">{{ homeLabel }}</div>
      </div>
      <div class="text-center">
        <div class="num text-[15px] font-semibold" style="color: var(--ink)">{{ drawW.toFixed(1) }}%</div>
        <div class="mt-0.5 text-[13px]" style="color: var(--mute)">Seri</div>
      </div>
      <div class="text-right">
        <div class="num text-[15px] font-semibold" style="color: var(--away)">{{ awayW.toFixed(1) }}%</div>
        <div class="mt-0.5 truncate text-[13px]" style="color: var(--mute)">{{ awayLabel }}</div>
      </div>
    </div>
  </div>
</template>
