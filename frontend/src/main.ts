import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import zhCN from './i18n/locales/zh.json'
import enUS from './i18n/locales/en.json'
import { useLoading } from './composables/useLoading'
import './styles/main.css'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: () => import('./pages/Login.vue') },
  { path: '/dashboard', name: 'Dashboard', component: () => import('./pages/Dashboard.vue'), meta: { requiresAuth: true } },
  { path: '/bookmarks', name: 'Bookmarks', component: () => import('./pages/Bookmarks.vue'), meta: { requiresAuth: true } },
  { path: '/github', name: 'GitHubProjects', component: () => import('./pages/GitHubProjects.vue'), meta: { requiresAuth: true } },
  { path: '/audit', name: 'Audit', component: () => import('./pages/Audit.vue'), meta: { requiresAuth: true } },
  { path: '/model', name: 'Model', component: () => import('./pages/Model.vue'), meta: { requiresAuth: true } },
  { path: '/settings', name: 'Settings', component: () => import('./pages/Settings.vue'), meta: { requiresAuth: true } },
]

const router = createRouter({ history: createWebHistory(), routes })
const i18n = createI18n({ legacy: false, locale: 'zh', fallbackLocale: 'en', messages: { zh: zhCN, en: enUS } })
const { start, done } = useLoading()

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) next('/login')
  else {
    if (to.name !== _from.name) start()
    next()
  }
})

router.afterEach(() => {
  setTimeout(done, 200)
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)
app.mount('#app')
