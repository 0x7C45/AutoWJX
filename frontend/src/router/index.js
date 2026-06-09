import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/monitor/:taskId',
    name: 'Monitor',
    component: () => import('../views/Monitor.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
