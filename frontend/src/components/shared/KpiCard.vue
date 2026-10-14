<script setup>
defineProps({
  title: { type: String, default: '' },
  value: { type: [String, Number], default: '' },
  sub: { type: String, default: '' },
  tone: { type: String, default: 'sky' },
})

const tones = {
  sky: 'border-home/25 bg-home/5 text-home',
  emerald: 'border-ok/25 bg-ok/5 text-ok',
  rose: 'border-bad/25 bg-bad/5 text-bad',
  amber: 'border-draw/25 bg-draw/5 text-draw',
  slate: 'border-line bg-card/60 text-ink',
}
</script>

<template>
  <div class="panel p-4" :class="tones[tone] || tones.sky">
    <div class="label-caps">{{ title }}</div>
    <div class="num mt-2 text-2xl font-bold text-ink">{{ value }}</div>
    <div v-if="sub" class="mt-1 text-xs text-mute">{{ sub }}</div>
  </div>
</template>
