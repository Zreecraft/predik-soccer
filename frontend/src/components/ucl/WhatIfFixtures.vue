<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  fixtures: { type: Array, default: () => [] },
  activeIds: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update'])

const filterTeam = ref('')

const teams = computed(() => {
  const set = new Set()
  for (const f of props.fixtures) {
    set.add(f.home)
    set.add(f.away)
  }
  return [...set].sort()
})

const visible = computed(() => {
  if (!filterTeam.value) return props.fixtures
  return props.fixtures.filter(
    (f) => f.home === filterTeam.value || f.away === filterTeam.value
  )
})

function clamp(v) {
  return Math.max(0, Math.min(20, parseInt(v, 10) || 0))
}

function onChange(f, side, e) {
  emit('update', {
    match_id: f.match_id,
    side,
    value: clamp(e.target.value),
  })
}
</script>

<template>
  <div class="panel overflow-hidden">
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4">
      <div>
        <div class="label-caps text-draw">What-If · Fase Liga</div>
        <h3 class="mt-1 text-base font-semibold text-ink">Edit Skor Fase Liga (144 Laga)</h3>
        <p class="mt-0.5 text-xs text-mute">
          Ubah skor laga → klasemen, seeding, bracket, dan peluang juara dihitung ulang otomatis.
        </p>
      </div>
      <select
        v-model="filterTeam"
        class="rounded-lg border border-line bg-canvas/70 px-3 py-2 text-sm text-ink outline-none focus:border-home/60"
      >
        <option value="">Semua tim</option>
        <option v-for="t in teams" :key="t" :value="t">{{ t }}</option>
      </select>
    </div>

    <div class="max-h-[420px] overflow-y-auto">
      <div
        v-for="f in visible"
        :key="f.match_id"
        class="flex items-center gap-3 border-b border-line/60 px-5 py-2.5 transition hover:bg-card/25"
        :class="{ 'bg-draw/5': activeIds[f.match_id] }"
      >
        <span
          class="num w-16 shrink-0 text-[10px] uppercase tracking-wider"
          :class="activeIds[f.match_id] ? 'text-draw' : 'text-mute'"
        >
          {{ f.match_id }}
        </span>
        <span class="min-w-0 flex-1 truncate text-right text-sm font-medium text-ink">
          {{ f.home }}
        </span>
        <input
          class="num h-8 w-12 shrink-0 rounded-md border border-line bg-canvas text-center text-sm font-bold text-ink outline-none focus:border-home/60"
          type="number"
          min="0"
          max="20"
          :value="f.goals_home"
          @change="onChange(f, 'home', $event)"
        />
        <span class="shrink-0 text-xs text-mute">vs</span>
        <input
          class="num h-8 w-12 shrink-0 rounded-md border border-line bg-canvas text-center text-sm font-bold text-ink outline-none focus:border-home/60"
          type="number"
          min="0"
          max="20"
          :value="f.goals_away"
          @change="onChange(f, 'away', $event)"
        />
        <span class="min-w-0 flex-1 truncate text-sm font-medium text-ink">
          {{ f.away }}
        </span>
      </div>
      <div v-if="!visible.length" class="px-5 py-6 text-sm text-mute">
        Tidak ada laga pada filter ini.
      </div>
    </div>
  </div>
</template>
