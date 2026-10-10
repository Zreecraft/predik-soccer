<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ExternalLink, X } from 'lucide-vue-next'
import { fetchMatchDetail } from '@/services/api'
import MatchDetailPanel from '@/components/predict/MatchDetailPanel.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  match: { type: Object, default: null },
})
const emit = defineEmits(['close'])

const router = useRouter()

const detail = ref(null)
const loading = ref(false)
let timer = null

function openFullPage() {
  const m = props.match
  if (!m) return
  emit('close')
  router.push({
    path: '/match',
    query: {
      ...(m.id ? { id: String(m.id) } : {}),
      home: m.home,
      away: m.away,
      ...(m.league ? { league: m.league } : {}),
    },
  })
}

async function load(force = false) {
  if (!props.match?.id) return
  loading.value = true
  try {
    detail.value = await fetchMatchDetail(props.match.id, force)
  } catch {
    detail.value = { available: false, reason: 'fetch_error' }
  } finally {
    loading.value = false
  }
}

function onKey(e) {
  if (e.key === 'Escape') emit('close')
}

watch(
  () => [props.isOpen, props.match?.id],
  ([open]) => {
    clearInterval(timer)
    if (open) {
      detail.value = null
      load(true)
      timer = setInterval(() => load(true), 60000)
      window.addEventListener('keydown', onKey)
    } else {
      window.removeEventListener('keydown', onKey)
    }
  },
  { immediate: true }
)
onBeforeUnmount(() => {
  clearInterval(timer)
  window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="isOpen && match"
        class="fixed inset-0 z-[60] flex items-start justify-center overflow-y-auto bg-black/70 p-4 backdrop-blur-sm sm:items-center"
        @click.self="emit('close')"
      >
        <div class="panel w-full max-w-2xl overflow-hidden shadow-2xl shadow-black/50">
          <!-- Header -->
          <div class="flex items-center justify-between gap-3 border-b border-slate-800 px-5 py-3">
            <div class="flex min-w-0 items-center gap-3">
              <span
                v-if="match.live"
                class="flex items-center gap-1.5 rounded bg-rose-600 px-2 py-0.5 text-[10px] font-extrabold tracking-widest text-white"
              >
                <span class="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-white" />
                LIVE
              </span>
              <div class="min-w-0">
                <div class="truncate text-sm font-bold text-slate-50">
                  {{ match.home }} <span class="num text-slate-400">vs</span> {{ match.away }}
                </div>
                <div class="text-[11px] text-slate-500">{{ match.competition_name }}</div>
              </div>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <div v-if="match.home_score != null" class="num text-lg font-bold">
                <span class="text-sky-400">{{ match.home_score }}</span>
                <span class="mx-1 text-slate-600">-</span>
                <span class="text-rose-400">{{ match.away_score }}</span>
              </div>
              <button
                type="button"
                class="btn-ghost !px-2 !py-1.5 !text-xs"
                title="Buka Match Centre (halaman penuh)"
                @click="openFullPage"
              >
                <ExternalLink :size="12" />
                Halaman Penuh
              </button>
              <button
                type="button"
                class="rounded-lg border border-slate-700 p-1.5 text-slate-400 transition hover:bg-slate-800 hover:text-slate-100"
                aria-label="Tutup"
                @click="emit('close')"
              >
                <X :size="16" />
              </button>
            </div>
          </div>

          <!-- Body -->
          <div class="p-3 sm:p-4">
            <MatchDetailPanel :detail="detail" :loading="loading" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.18s ease;
}
.modal-fade-enter-active > div,
.modal-fade-leave-active > div {
  transition: transform 0.18s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-from > div,
.modal-fade-leave-to > div {
  transform: translateY(12px) scale(0.98);
}
</style>
