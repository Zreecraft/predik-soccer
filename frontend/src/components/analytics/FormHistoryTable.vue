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
    <div class="border-b border-slate-800 px-5 py-4">
      <div class="label-caps">Form History</div>
      <h3 class="mt-1 text-base font-semibold text-slate-100">Hasil 5 Pertandingan Terakhir</h3>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full min-w-[640px] text-sm">
        <thead>
          <tr class="border-b border-slate-800 bg-slate-950/40 text-left">
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
            class="border-b border-slate-800/70 transition hover:bg-slate-800/25"
          >
            <td class="num px-4 py-3 text-xs text-slate-400">{{ formatDate(m.date) }}</td>
            <td class="px-4 py-3 font-medium text-slate-100">{{ m.opponent }}</td>
            <td class="px-4 py-3">
              <span
                class="chip"
                :class="m.is_home ? 'border-sky-500/30 bg-sky-500/10 text-sky-400' : 'border-slate-600 bg-slate-800/40 text-slate-300'"
              >
                {{ m.is_home ? 'HOME' : 'AWAY' }}
              </span>
            </td>
            <td class="num px-4 py-3 text-right font-bold text-slate-100">{{ m.score }}</td>
            <td class="num px-4 py-3 text-right text-xs">
              <span class="text-sky-400">{{ m.xg_for ?? '—' }}</span>
              <span class="mx-1 text-slate-600">/</span>
              <span class="text-rose-400">{{ m.xg_against ?? '—' }}</span>
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
      <div v-if="!history.length" class="px-5 py-6 text-sm text-slate-500">
        Belum ada riwayat pertandingan.
      </div>
    </div>
  </div>
</template>
