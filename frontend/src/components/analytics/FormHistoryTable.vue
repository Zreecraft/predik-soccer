<script setup>
import { formBadgeClass } from '@/utils/format'

defineProps({
  history: { type: Array, default: () => [] },
})

function formatDate(dateStr) {
  if (!dateStr) return '?'
  return String(dateStr).slice(0, 10)
}
</script>

<template>
  <div class="panel overflow-hidden">
    <div class="border-b border-line px-5 py-4">
      <div class="label-caps">Form History</div>
      <h3 class="mt-1 text-base font-semibold text-ink">Hasil 5 Pertandingan Terakhir</h3>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full min-w-[640px] text-sm">
        <thead>
          <tr class="border-b border-line bg-canvas/40 text-left">
            <th class="label-caps px-4 py-2.5">Tanggal</th>
            <th class="label-caps px-4 py-2.5">Lawan</th>
            <th class="label-caps px-4 py-2.5">Lokasi</th>
            <th class="label-caps px-4 py-2.5 text-right">Skor</th>
            <th class="label-caps px-4 py-2.5 text-right">xG (For vs Against)</th>
            <th class="label-caps px-4 py-2.5 text-right">Hasil</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(m, i) in history"
            :key="i"
            class="border-b border-line/70 transition hover:bg-card/25"
          >
            <td class="num px-4 py-3 text-xs text-mute">{{ formatDate(m.date) }}</td>
            <td class="px-4 py-3 font-medium text-ink">{{ m.opponent }}</td>
            <td class="px-4 py-3">
              <span
                class="chip"
                :class="m.is_home ? 'border-home/30 bg-home/10 text-home' : 'border-line bg-card/40 text-mute'"
              >
                {{ m.is_home ? 'HOME' : 'AWAY' }}
              </span>
            </td>
            <td class="num px-4 py-3 text-right font-bold text-ink">{{ m.score }}</td>
            <td class="num px-4 py-3 text-right text-xs">
              <span class="text-home">{{ m.xg_for ?? '—' }}</span>
              <span class="mx-1 text-mute">/</span>
              <span class="text-bad">{{ m.xg_against ?? '—' }}</span>
            </td>
            <td class="px-4 py-3 text-right">
              <span
                class="inline-flex h-6 w-6 items-center justify-center rounded-md border text-xs font-black"
                :class="formBadgeClass(m.result)"
              >
                {{ m.result }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!history.length" class="px-5 py-6 text-sm text-mute">
        Belum ada riwayat pertandingan.
      </div>
    </div>
  </div>
</template>
