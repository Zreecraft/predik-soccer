<script setup>
import { Trophy } from 'lucide-vue-next'
import PlayerCutout from '@/components/shared/PlayerCutout.vue'

defineProps({
  champion: { type: Object, default: () => ({}) },
})
</script>

<template>
  <div
    class="panel relative overflow-hidden p-6"
    style="border-color: rgba(245, 158, 11, 0.35)"
  >
    <div class="pointer-events-none absolute right-0 top-0 h-40 w-40 rounded-full bg-amber-500/10 blur-3xl" />
    <div class="relative">
      <div class="flex items-center gap-2 text-amber-400">
        <Trophy :size="16" />
        <span class="label-caps text-amber-400">Juara Hasil Simulasi</span>
      </div>

      <div class="mt-5 flex items-center gap-4">
        <img
          v-if="champion.logo"
          :src="champion.logo"
          :alt="champion.team"
          class="h-20 w-20 rounded-xl border border-amber-500/30 bg-slate-950/60 object-contain p-2"
        />
        <div class="min-w-0 flex-1">
          <div class="truncate text-2xl font-bold text-slate-50">{{ champion.team || '—' }}</div>
          <div class="mt-1 text-sm text-slate-400">
            {{ champion.star_player?.player_name || 'Key Player' }}
            <span class="text-slate-600">·</span>
            {{ champion.star_player?.position || '' }}
          </div>
          <div class="num mt-3 text-3xl font-bold text-amber-400">
            {{ champion.win_prob ?? '—' }}%
          </div>
          <div class="label-caps mt-1">Peluang Juara (Final Simulasi)</div>
        </div>
        <div class="hidden sm:block">
          <PlayerCutout
            :image="champion.star_player?.image"
            :name="champion.star_player?.player_name || champion.team"
            size="md"
          />
        </div>
      </div>
    </div>
  </div>
</template>
