<script setup>
import { RouterView } from 'vue-router'
import Navbar from '@/components/navbar/Navbar.vue'
</script>

<template>
  <div class="flex min-h-screen flex-col bg-canvas">
    <!-- cahaya latar halus -->
    <div class="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <div class="absolute -top-40 left-1/2 h-[26rem] w-[46rem] -translate-x-1/2 rounded-full bg-home/[0.055] blur-3xl" />
      <div class="absolute -right-32 top-[38%] h-96 w-96 rounded-full bg-bad/[0.035] blur-3xl" />
      <div class="absolute -left-32 bottom-[10%] h-80 w-80 rounded-full bg-ok/[0.03] blur-3xl" />
    </div>

    <Navbar />

    <main class="mx-auto w-full max-w-[1400px] flex-1 px-4 pb-16 pt-6 sm:px-6">
      <RouterView />
    </main>

    <footer class="border-t border-line/70 bg-canvas/40">
      <div class="mx-auto flex max-w-[1400px] flex-wrap items-center justify-between gap-x-4 gap-y-2 px-4 py-5 text-[11px] text-mute sm:px-6">
        <span class="inline-flex items-center gap-2">
          <img src="/logo.svg" alt="" class="h-5 w-5 opacity-70" width="20" height="20" />
          <span class="font-semibold tracking-[0.14em] text-mute">ANALYTICA FC</span>
          <span class="text-mute">·</span>
          <span>Telemetri analitik sepakbola</span>
        </span>
        <span>
          Skor &amp; detail laga: ESPN · football-data.org
          <span class="mx-1 text-mute">|</span>
          xG historis: Understat
          <span class="mx-1 text-mute">|</span>
          Simulasi Monte Carlo — bukan taruhan
        </span>
      </div>
    </footer>
  </div>
</template>
