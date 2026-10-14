<script setup>
import { Briefcase, Crosshair, MapPin, Shield } from 'lucide-vue-next'

defineProps({
  data: { type: Object, default: () => ({}) },
})
</script>

<template>
  <section class="panel overflow-hidden">
    <div class="flex flex-wrap items-center gap-5 p-6">
      <img
        v-if="data.logo"
        :src="data.logo"
        :alt="data.team"
        class="h-24 w-24 rounded-2xl border border-line/60 bg-canvas/50 object-contain p-2"
      />
      <div class="min-w-0 flex-1">
        <div class="label-caps text-home/90">Club Monitoring</div>
        <h1 class="mt-1 text-2xl font-bold tracking-tight text-ink">{{ data.team }}</h1>
        <div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-mute">
          <span class="inline-flex items-center gap-1.5">
            <Briefcase :size="14" class="text-mute" />
            {{ data.profile?.coach || '—' }}
          </span>
          <span class="inline-flex items-center gap-1.5">
            <Crosshair :size="14" class="text-mute" />
            {{ data.profile?.formation || '—' }}
          </span>
          <span class="inline-flex items-center gap-1.5">
            <MapPin :size="14" class="text-mute" />
            {{ data.profile?.stadium || '—' }}
          </span>
          <span class="inline-flex items-center gap-1.5">
            <Shield :size="14" class="text-mute" />
            {{ data.league_name || data.league || '—' }}
            <template v-if="data.league_position">
              · Posisi <span class="num text-ink">#{{ data.league_position }}</span>
            </template>
          </span>
        </div>
      </div>
      <div class="flex gap-3">
        <div class="rounded-xl border border-line bg-canvas/40 px-4 py-3 text-center">
          <div class="label-caps">Rating</div>
          <div class="num mt-1 text-2xl font-bold text-draw">{{ data.profile?.rating ?? '—' }}</div>
        </div>
        <div class="rounded-xl border border-line bg-canvas/40 px-4 py-3 text-center">
          <div class="label-caps">Power</div>
          <div class="num mt-1 text-2xl font-bold text-home">{{ data.power?.power_score ?? '—' }}</div>
        </div>
        <div class="rounded-xl border border-line bg-canvas/40 px-4 py-3 text-center">
          <div class="label-caps">PPDA</div>
          <div class="num mt-1 text-2xl font-bold text-ok">{{ data.ppda ?? '—' }}</div>
        </div>
        <div class="rounded-xl border border-line bg-canvas/40 px-4 py-3 text-center">
          <div class="label-caps">Avg xG</div>
          <div class="num mt-1 text-2xl font-bold text-draw">{{ data.power?.avg_xg ?? '—' }}</div>
        </div>
      </div>
    </div>
  </section>
</template>
