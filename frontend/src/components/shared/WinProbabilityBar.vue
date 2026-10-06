<script setup>
import { computed } from 'vue'

const props = defineProps({
  homeWin: { type: Number, default: 0 },
  draw: { type: Number, default: 0 },
  awayWin: { type: Number, default: 0 },
  homeLabel: { type: String, default: 'HOME' },
  awayLabel: { type: String, default: 'AWAY' },
})

const homeW = computed(() => props.homeWin || 0)
const drawW = computed(() => props.draw || 0)
const awayW = computed(() => props.awayWin || 0)
</script>

<template>
  <div class="space-y-2">
    <div class="flex h-3 w-full overflow-hidden rounded-full bg-slate-800">
      <div
        class="h-full bg-gradient-to-r from-sky-500 to-sky-400 transition-all duration-700"
        :style="{ width: homeW + '%' }"
      />
      <div
        class="h-full bg-slate-600 transition-all duration-700"
        :style="{ width: drawW + '%' }"
      />
      <div
        class="h-full bg-gradient-to-r from-rose-500 to-rose-400 transition-all duration-700"
        :style="{ width: awayW + '%' }"
      />
    </div>
    <div class="grid grid-cols-3 gap-2 text-center">
      <div>
        <div class="num text-sm font-bold text-sky-400">{{ homeW.toFixed(1) }}%</div>
        <div class="label-caps mt-0.5 truncate">{{ homeLabel }}</div>
      </div>
      <div>
        <div class="num text-sm font-bold text-slate-300">{{ drawW.toFixed(1) }}%</div>
        <div class="label-caps mt-0.5">Draw</div>
      </div>
      <div>
        <div class="num text-sm font-bold text-rose-400">{{ awayW.toFixed(1) }}%</div>
        <div class="label-caps mt-0.5 truncate">{{ awayLabel }}</div>
      </div>
    </div>
  </div>
</template>
