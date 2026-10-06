<script setup>
import { computed } from 'vue'
import { Target, Crosshair, ShieldAlert } from 'lucide-vue-next'

const props = defineProps({
  summary: { type: String, default: '' },
  homeName: { type: String, default: 'Home' },
  awayName: { type: String, default: 'Away' },
  shots: { type: Object, default: () => ({ home: {}, away: {} }) },
})

const bullets = computed(() => {
  const h = props.shots.home || {}
  const a = props.shots.away || {}
  return [
    {
      icon: Target,
      title: 'Dominasi Zona 14',
      value: `${h.zone14_shots ?? 0} vs ${a.zone14_shots ?? 0}`,
      detail: `Temukan area kunci di luar kotak penalti — ${props.homeName} vs ${props.awayName}.`,
      tone: 'sky',
    },
    {
      icon: Crosshair,
      title: 'Efisiensi Konversi',
      value: `${h.conversion_pct ?? 0}% vs ${a.conversion_pct ?? 0}%`,
      detail: 'Rasio gol terhadap total tembakan tercatat.',
      tone: 'emerald',
    },
    {
      icon: ShieldAlert,
      title: 'Supresi Tembakan',
      value: `${h.shots ?? 0} vs ${a.shots ?? 0}`,
      detail: 'Volume tembakan kandang/tandang dalam dataset analitik.',
      tone: 'amber',
    },
  ]
})
</script>

<template>
  <div class="mt-4 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
    <div class="label-caps mb-2">Rangkuman Diferensial Taktis</div>
    <p class="text-sm leading-relaxed text-slate-300">
      {{ summary || 'Belum cukup data untuk merangkum diferensial taktis.' }}
    </p>

    <div class="mt-4 grid gap-3 sm:grid-cols-3">
      <div
        v-for="b in bullets"
        :key="b.title"
        class="rounded-lg border border-slate-800 bg-slate-900/50 p-3"
      >
        <div class="flex items-center gap-2">
          <component
            :is="b.icon"
            :size="14"
            :class="{
              'text-sky-400': b.tone === 'sky',
              'text-emerald-400': b.tone === 'emerald',
              'text-amber-400': b.tone === 'amber',
            }"
          />
          <div class="text-xs font-medium text-slate-400">{{ b.title }}</div>
        </div>
        <div class="num mt-2 text-lg font-bold text-slate-100">{{ b.value }}</div>
        <p class="mt-1 text-[11px] leading-snug text-slate-500">{{ b.detail }}</p>
      </div>
    </div>
  </div>
</template>
