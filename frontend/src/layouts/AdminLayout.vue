<template>
  <div class="flex h-screen bg-background text-foreground overflow-hidden">
    <!-- Global loading bar -->
    <div
      v-if="loading"
      class="fixed top-0 left-0 right-0 z-50 h-0.5 bg-card overflow-hidden"
    >
      <div class="h-full w-full loading-bar-slide" />
    </div>

    <!-- Overlay for mobile -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-10 bg-black/20 lg:hidden"
      @click="sidebarOpen = false"
    />

    <!-- Sidebar -->
    <aside
      :class="[
        'fixed lg:static inset-y-0 left-0 z-20 flex flex-col border-r border-border/50',
        'backdrop-blur-2xl transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] overflow-hidden',
        sidebarOpen ? 'w-60 lg:translate-x-0 translate-x-0' : 'w-60 -translate-x-full lg:w-[56px] lg:translate-x-0',
      ]"
      style="background-color: hsl(var(--sidebar)); color: hsl(var(--sidebar-foreground))"
    >
      <!-- App title -->
      <div
        :class="[
          'flex items-center pt-6 pb-4 gap-3 border-b border-border/30 flex-shrink-0',
          sidebarOpen ? 'px-5' : 'px-[12px] justify-center',
        ]"
      >
        <img :src="isDark ? '/logo-dark.svg' : '/logo-light.svg'" class="w-8 h-8 rounded-lg flex-shrink-0" />
        <span v-show="sidebarOpen" class="font-semibold text-sm tracking-tight whitespace-nowrap">{{ $t('app.title') }}</span>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 space-y-0.5 px-3 py-2">
        <template v-for="item in navItems" :key="item.to">
          <!-- Parent item (with or without children) -->
          <div
            v-if="item.children"
            class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors duration-150 overflow-hidden whitespace-nowrap cursor-pointer"
            :class="isActive(item.to) ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 font-bold shadow-sm' : 'hover:bg-muted/50 text-muted-foreground hover:text-foreground'"
            @click="toggleMenu(item.to)"
            :title="$t(item.label)"
          >
            <component :is="item.icon" class="w-4 h-4 flex-shrink-0" />
            <span>{{ $t(item.label) }}</span>
            <ChevronDown
              v-if="sidebarOpen"
              class="w-3.5 h-3.5 ml-auto flex-shrink-0 transition-transform duration-200"
              :class="{ 'rotate-180': expandedMenus.includes(item.to) }"
            />
          </div>

          <!-- Child items -->
          <template v-if="item.children && expandedMenus.includes(item.to) && sidebarOpen">
            <router-link
              v-for="child in item.children"
              :key="child.to"
              :to="child.to"
              :title="$t(child.label)"
              class="flex items-center gap-3 pl-9 pr-3 py-1.5 rounded-lg text-xs transition-colors duration-150 overflow-hidden whitespace-nowrap"
              :class="route.path === child.to ? 'text-zinc-900 dark:text-zinc-100 font-bold' : 'text-muted-foreground hover:text-foreground'"
            >
              <component :is="child.icon" class="w-3.5 h-3.5 flex-shrink-0" />
              <span>{{ $t(child.label) }}</span>
            </router-link>
          </template>

          <!-- Regular item (no children) -->
          <router-link
            v-if="!item.children"
            :to="item.to"
            :title="$t(item.label)"
            class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors duration-150 overflow-hidden whitespace-nowrap"
            :class="isActive(item.to) ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 font-bold shadow-sm' : 'hover:bg-muted/50 text-muted-foreground hover:text-foreground'"
          >
            <component :is="item.icon" class="w-4 h-4 flex-shrink-0" />
            <span>{{ $t(item.label) }}</span>
          </router-link>
        </template>
      </nav>

      <!-- Logout -->
      <div class="pt-2 border-t border-border/50 px-3 pb-5 mt-2">
        <button
          @click="handleLogout"
          :title="$t('nav.logout')"
          class="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-destructive hover:bg-destructive/5 transition-colors duration-150 overflow-hidden whitespace-nowrap"
        >
          <LogOut class="w-4 h-4 flex-shrink-0" />
          <span>{{ $t('nav.logout') }}</span>
        </button>
      </div>
    </aside>

    <!-- Main area -->
    <main class="flex-1 flex flex-col min-w-0">
      <!-- Header -->
      <header class="flex items-center justify-between px-5 py-3 border-b border-border/40" style="background-color: hsl(var(--card) / 0.6); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px)">
        <button
          @click="sidebarOpen = !sidebarOpen"
          class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-muted transition-colors"
        >
          <PanelLeftOpen v-if="!sidebarOpen" class="w-4 h-4" />
          <PanelLeftClose v-else class="w-4 h-4" />
        </button>

        <div class="flex items-center gap-1.5">
          <!-- Locale toggle -->
          <div class="flex items-center rounded-lg bg-muted/50 p-0.5 mr-2">
            <button
              @click="setLocale('zh')"
              :class="['px-2.5 py-1 rounded-md text-xs font-medium transition-all duration-150', locale === 'zh' ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground']"
            >中</button>
            <button
              @click="setLocale('en')"
              :class="['px-2.5 py-1 rounded-md text-xs font-medium transition-all duration-150', locale === 'en' ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground']"
            >EN</button>
          </div>

          <!-- Dark mode toggle -->
          <button
            @click="toggleDark"
            class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-muted transition-colors"
            :title="isDark ? 'Light mode' : 'Dark mode'"
          >
            <Sun v-if="isDark" class="w-4 h-4" />
            <Moon v-else class="w-4 h-4" />
          </button>
        </div>
      </header>

      <!-- Content -->
      <div class="flex-1 overflow-auto">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { inject, ref, computed, type Ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useLoading } from '@/composables/useLoading'

const { loading } = useLoading()
import {
  LayoutDashboard,
  Bookmark,
  Github,
  Code2,
  ShieldCheck,
  Cpu,
  Settings,
  LogOut,
  Sun,
  Moon,
  PanelLeftOpen,
  PanelLeftClose,
  Route,
  ExternalLink,
  ChevronDown,
} from 'lucide-vue-next'

const sidebarOpen = ref(true)
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { locale } = inject('i18n', { locale: ref('zh') }) as { locale: Ref<string> }
const isDark = ref(localStorage.getItem('dark') === 'true')

const expandedMenus = ref<string[]>([])

const toggleMenu = (path: string) => {
  const idx = expandedMenus.value.indexOf(path)
  if (idx >= 0) expandedMenus.value.splice(idx, 1)
  else expandedMenus.value.push(path)
}

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'nav.dashboard' },
  { to: '/bookmarks', icon: Bookmark, label: 'nav.bookmarks' },
  {
    to: '/api-management', icon: Code2, label: 'nav.apiManagement',
    children: [
      { to: '/api-management/index', icon: LayoutDashboard, label: 'nav.apiOverview' },
      { to: '/api-management/internal', icon: Route, label: 'nav.internalApis' },
      { to: '/api-management/external', icon: ExternalLink, label: 'nav.externalApis' },
    ],
  },
  { to: '/github', icon: Github, label: 'nav.github' },
  { to: '/audit', icon: ShieldCheck, label: 'nav.audit' },
  { to: '/model', icon: Cpu, label: 'nav.model' },
  { to: '/settings', icon: Settings, label: 'nav.settings' },
]

const isActive = (path: string) => route.path === path || route.path.startsWith(path + '/')

const toggleDark = () => {
  isDark.value = !isDark.value
  localStorage.setItem('dark', String(isDark.value))
  document.documentElement.classList.toggle('dark')
}

const setLocale = (lang: string) => {
  locale.value = lang
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>
