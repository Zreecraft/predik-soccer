<script setup>
import { formBadgeClass } from '@/utils/format'

defineProps({
  form: { type: Array, default: () => [] },
  label: { type: String, default: 'Form' },
})
</script>

<template>
  <div class="space-y-1.5">
    <div class="label-caps">{{ label }} · 5 Laga</div>
    <div class="flex flex-wrap gap-1.5">
      <span
        v-for="(f, i) in form"
        :key="i"
        class="chip num h-7 w-7 justify-center"
        :class="formBadgeClass(f.result)"
        :title="`${f.result} ${f.score} vs ${f.opponent}`"
      >
        {{ f.result }}
      </span>
      <span v-if="!form.length" class="text-xs text-slate-500">Belum ada data</span>
    </div>
  </div>
</template>
