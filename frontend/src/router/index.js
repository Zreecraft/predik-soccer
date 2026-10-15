import { createRouter, createWebHistory } from 'vue-router'

// Dynamic import → code-split per rute (bundle utama tak lagi membawa semua view
// + chart.js; rute yang dibuka hanya mengunduh chunk-nya sendiri).
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/predict' },
    {
      path: '/predict',
      name: 'predict',
      component: () => import('@/views/PredictView.vue'),
      meta: { title: 'Prediksi Laga' },
    },
    {
      path: '/match',
      name: 'match',
      component: () => import('@/views/MatchDetailView.vue'),
      meta: { title: 'Detail Laga' },
    },
    {
      path: '/standings',
      name: 'standings',
      component: () => import('@/views/StandingsView.vue'),
      meta: { title: 'Proyeksi Liga' },
    },
    {
      path: '/ucl',
      name: 'ucl',
      component: () => import('@/views/UclView.vue'),
      meta: { title: 'Bagan UCL' },
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: () => import('@/views/AnalyticsView.vue'),
      meta: { title: 'Analitik Klub' },
    },
  ],
})

router.afterEach((to) => {
  document.title = to.meta?.title ? `${to.meta.title} · Analytica FC` : 'Analytica FC'
})

export default router
