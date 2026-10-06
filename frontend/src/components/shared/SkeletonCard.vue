<script setup>
defineProps({
  label: { type: String, default: '' },
  lines: { type: Number, default: 3 },
})
</script>

<template>
  <div class="panel space-y-3 p-5">
    <div v-if="label" class="skeleton h-3 w-24" />
    <div v-for="i in lines" :key="i" class="skeleton h-4" :class="i === lines ? 'w-2/3' : 'w-full'" />
  </div>
</template>
