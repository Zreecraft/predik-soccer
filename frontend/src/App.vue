<script setup>
import { RouterView } from 'vue-router'
import Navbar from '@/components/navbar/Navbar.vue'
</script>

<template>
  <div class="min-h-screen bg-canvas">
    <Navbar />
    <main class="mx-auto w-full max-w-[1400px] px-4 pb-16 pt-6 sm:px-6">
      <RouterView />
    </main>
  </div>
</template>
