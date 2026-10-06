<script setup>
import { ref } from 'vue'
import { playerImageSrc, teamInitial } from '@/utils/format'

const props = defineProps({
  image: { type: String, default: null },
  name: { type: String, default: '' },
  side: { type: String, default: 'left' },
  size: { type: String, default: 'md' },
})

const failed = ref(false)
const src = playerImageSrc(props.image)

const sizeClass = {
  sm: 'h-16 w-16',
  md: 'h-24 w-24',
  lg: 'h-32 w-32',
  xl: 'h-40 w-40',
}[props.size] || 'h-24 w-24'
</script>

<template>
  <div class="relative shrink-0" :class="[sizeClass, side === 'right' ? 'scale-x-[-1]' : '']">
    <template v-if="src && !failed">
      <img
        :src="src"
        :alt="name"
        class="h-full w-full object-contain opacity-90 drop-shadow-[0_10px_20px_rgba(0,0,0,0.45)]"
        loading="lazy"
        @error="failed = true"
      />
    </template>
    <div
      v-else
      class="flex h-full w-full items-center justify-center rounded-full border border-slate-700/80 bg-gradient-to-b from-slate-800 to-slate-900"
    >
      <span class="num text-lg font-bold text-slate-400">{{ teamInitial(name) }}</span>
    </div>
  </div>
</template>
