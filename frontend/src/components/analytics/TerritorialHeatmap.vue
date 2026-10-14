<script setup>
import { computed } from 'vue'

const props = defineProps({
  cells: { type: Array, default: () => [] },
  side: { type: String, default: 'Kanan' },
})

const rows = 5
const cols = 6

function valueAt(r, c) {
  const cell = props.cells.find((x) => x.row === r && x.col === c)
  return cell ? cell.value : 0
}

function colorFor(v) {
  if (v >= 70) return '#6aa0ff'
  if (v >= 50) return '#4a78d6'
  if (v >= 35) return '#3a5fa8'
  if (v >= 20) return '#24406e'
  return '#16241d'
}

function opacityFor(v) {
  return 0.25 + Math.min(0.75, (v / 100) * 0.85)
}

const grid = computed(() => {
  const out = []
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const v = valueAt(r, c)
      out.push({ r, c, v })
    }
  }
  return out
})
</script>

<template>
  <div class="panel p-5">
    <div class="mb-3 flex items-start justify-between">
      <div>
        <div class="label-caps">Kendali Teritorial</div>
        <h3 class="mt-1 text-base font-semibold text-ink">Matriks Densitas Half-Space</h3>
      </div>
      <span class="chip border-home/30 bg-home/10 text-home">Overload {{ side }}</span>
    </div>

    <div class="relative overflow-hidden rounded-xl border border-ok/40 bg-[#0B1F1A] p-2">
      <div class="grid gap-1" :style="{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }">
        <div
          v-for="cell in grid"
          :key="`${cell.r}-${cell.c}`"
          class="aspect-[4/3] rounded-md border"
          :style="{
            backgroundColor: colorFor(cell.v),
            opacity: opacityFor(cell.v),
            borderColor: 'rgba(30,41,59,0.5)',
          }"
          :title="`Zona ${cell.r + 1}-${cell.c + 1}: ${cell.v}`"
        />
      </div>
      <div class="mt-2 flex items-center justify-between px-1 text-[10px] text-mute">
        <span>Build-up / Lini Belakang</span>
        <span>Sepertiga Akhir · Serangan</span>
      </div>
    </div>

    <div class="mt-3 flex items-center gap-2 text-[11px] text-mute">
      <span>Rendah</span>
      <div class="h-2 flex-1 rounded-full" style="background: linear-gradient(90deg, #16241d, #24406e, #3a5fa8, #4a78d6, #6aa0ff)" />
      <span>Tinggi</span>
    </div>
  </div>
</template>
