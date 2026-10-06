<script setup>
defineProps({
  title: { type: String, default: '' },
  value: { type: [String, Number], default: '' },
  sub: { type: String, default: '' },
  tone: { type: String, default: 'sky' },
})

const tones = {
  sky: 'border-sky-500/25 bg-sky-500/5 text-sky-400',
  emerald: 'border-emerald-500/25 bg-emerald-500/5 text-emerald-400',
  rose: 'border-rose-500/25 bg-rose-500/5 text-rose-400',
  amber: 'border-amber-500/25 bg-amber-500/5 text-amber-400',
  slate: 'border-slate-700 bg-slate-900/60 text-slate-200',
}
</script>

<template>
  <div class="panel p-4" :class="tones[tone] || tones.sky">
    <div class="label-caps">{{ title }}</div>
    <div class="num mt-2 text-2xl font-bold text-slate-50">{{ value }}</div>
    <div v-if="sub" class="mt-1 text-xs text-slate-400">{{ sub }}</div>
  </div>
</template>
