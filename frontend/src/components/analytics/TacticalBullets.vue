<script setup>
import { Boxes, Goal, Gauge } from 'lucide-vue-next'

defineProps({
  bullets: { type: Array, default: () => [] },
})

const icons = {
  overload: Boxes,
  set_piece: Goal,
  ppda: Gauge,
}

const toneMap = {
  sky: 'border-sky-500/25 text-sky-400',
  amber: 'border-amber-500/25 text-amber-400',
  emerald: 'border-emerald-500/25 text-emerald-400',
}
</script>

<template>
  <div class="grid gap-3 sm:grid-cols-3">
    <div
      v-for="b in bullets"
      :key="b.key"
      class="panel p-4"
      :class="toneMap[b.tone] || toneMap.sky"
    >
      <div class="flex items-center gap-2">
        <component
          :is="icons[b.key] || Boxes"
          :size="15"
          :class="toneMap[b.tone]?.split(' ')[1] || 'text-sky-400'"
        />
        <div class="label-caps">{{ b.title }}</div>
      </div>
      <div class="num mt-3 text-2xl font-bold text-slate-50">{{ b.value }}</div>
      <p class="mt-2 text-xs leading-relaxed text-slate-400">{{ b.detail }}</p>
    </div>
  </div>
</template>
