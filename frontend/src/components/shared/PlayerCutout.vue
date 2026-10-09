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
      <!-- Backdrop glow: pendaran terang di belakang subjek agar kulit gelap terpisah dari kanvas -->
      <div
        class="absolute inset-0"
        style="
          background:
            radial-gradient(circle at 50% 42%,
              rgba(148, 163, 184, 0.30) 0%,
              rgba(71, 85, 105, 0.22) 38%,
              rgba(30, 41, 59, 0.12) 58%,
              transparent 74%);
        "
      />
      <!-- Cahaya bawah (ground light) -->
      <div
        class="absolute inset-x-[12%] bottom-0 h-[26%]"
        style="background: radial-gradient(ellipse at 50% 100%, rgba(56, 189, 248, 0.28) 0%, transparent 70%)"
      />
      <img
        :src="src"
        :alt="name"
        class="relative h-full w-full object-contain"
        style="
          filter:
            drop-shadow(0 12px 22px rgba(0, 0, 0, 0.5))
            drop-shadow(0 0 12px rgba(56, 189, 248, 0.45))
            drop-shadow(0 0 28px rgba(226, 232, 240, 0.22))
            brightness(1.14)
            contrast(1.06);
        "
        loading="lazy"
        @error="failed = true"
      />
    </template>
    <div
      v-else
      class="flex h-full w-full items-center justify-center rounded-full border border-slate-700/80 bg-gradient-to-b from-slate-800 to-slate-900"
    >
      <div
        class="absolute inset-0"
        style="background: radial-gradient(circle, rgba(148, 163, 184, 0.18) 0%, transparent 70%)"
      />
      <span class="relative num text-lg font-bold text-slate-300">{{ teamInitial(name) }}</span>
    </div>
  </div>
</template>
