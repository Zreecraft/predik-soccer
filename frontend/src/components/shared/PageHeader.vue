<script setup>
defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <header class="flex flex-wrap items-end justify-between gap-x-4 gap-y-3 border-b border-slate-800/70 pb-4">
    <div class="min-w-0">
      <div v-if="eyebrow || $slots.eyebrow" class="eyebrow flex items-center gap-2">
        <span class="text-sky-500/50">//</span>
        <slot name="eyebrow">{{ eyebrow }}</slot>
      </div>
      <h1 class="mt-1.5 text-[1.65rem] font-extrabold leading-none tracking-tight text-slate-50 sm:text-[1.9rem]">
        {{ title }}
      </h1>
      <p v-if="subtitle || $slots.subtitle" class="mt-2 max-w-xl text-sm leading-relaxed text-slate-400">
        <slot name="subtitle">{{ subtitle }}</slot>
      </p>
    </div>
    <div v-if="$slots.actions" class="flex shrink-0 flex-wrap items-center gap-2">
      <slot name="actions" />
    </div>
  </header>
</template>
