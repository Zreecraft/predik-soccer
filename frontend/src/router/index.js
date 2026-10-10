import { createRouter, createWebHistory } from 'vue-router'

import PredictView from '@/views/PredictView.vue'
import StandingsView from '@/views/StandingsView.vue'
import UclView from '@/views/UclView.vue'
import AnalyticsView from '@/views/AnalyticsView.vue'
import MatchDetailView from '@/views/MatchDetailView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/predict' },
    { path: '/predict', name: 'predict', component: PredictView, meta: { title: 'Prediksi Laga' } },
    { path: '/match', name: 'match', component: MatchDetailView, meta: { title: 'Detail Laga' } },
    { path: '/standings', name: 'standings', component: StandingsView, meta: { title: 'Proyeksi Liga' } },
    { path: '/ucl', name: 'ucl', component: UclView, meta: { title: 'Bagan UCL' } },
    { path: '/analytics', name: 'analytics', component: AnalyticsView, meta: { title: 'Analitik Klub' } },
  ],
})

router.afterEach((to) => {
  document.title = to.meta?.title ? `${to.meta.title} · Analytica FC` : 'Analytica FC'
})

export default router
