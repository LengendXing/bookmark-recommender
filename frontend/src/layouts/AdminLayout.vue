<template>
  <div class="flex h-screen bg-background text-foreground">
    <aside :class="['w-64 bg-card border-r border-border flex flex-col transition-all', props.sidebarOpen ? 'translate-x-0' : '-translate-x-64 absolute h-full z-10']">
      <div class="p-4 border-b border-border">
        <h1 class="text-lg font-bold">Bookmark Recommender</h1>
      </div>
      <nav class="flex-1 p-2 space-y-1">
        <router-link to="/dashboard" class="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted transition-colors">
          <span class="text-lg">&#9632;</span> {{ $t('nav.dashboard') }}
        </router-link>
        <router-link to="/bookmarks" class="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted transition-colors">
          <span class="text-lg">&#9733;</span> {{ $t('nav.bookmarks') }}
        </router-link>
        <router-link to="/audit" class="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted transition-colors">
          <span class="text-lg">&#9673;</span> {{ $t('nav.audit') }}
        </router-link>
        <router-link to="/model" class="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted transition-colors">
          <span class="text-lg">&#9675;</span> {{ $t('nav.model') }}
        </router-link>
      </nav>
      <div class="p-2 border-t border-border">
        <button @click="handleLogout" class="w-full px-3 py-2 rounded-md hover:bg-muted text-sm transition-colors">
          {{ $t('nav.logout') }}
        </button>
      </div>
    </aside>
    <main class="flex-1 overflow-auto">
      <header class="flex items-center justify-between px-6 py-3 border-b border-border bg-card">
        <button @click="sidebarOpen = !sidebarOpen" class="text-foreground hover:text-foreground/80">
          &#9776;
        </button>
        <div class="flex items-center gap-3">
          <button @click="toggleLocale" class="px-2 py-1 text-xs rounded border border-border">
            {{ locale === 'zh' ? '中' : 'EN' }}
          </button>
          <button @click="toggleDark" class="px-2 py-1 text-xs rounded border border-border">
            {{ isDark ? '☀' : '☾' }}
          </button>
        </div>
      </header>
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { inject, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ sidebarOpen: boolean }>()
const router = useRouter()
const authStore = useAuthStore()
const { locale } = inject('i18n', { locale: ref('zh') }) as { locale: Ref<string> }
const isDark = ref(localStorage.getItem('dark') === 'true')

const toggleDark = () => {
  isDark.value = !isDark.value
  localStorage.setItem('dark', String(isDark.value))
  document.documentElement.classList.toggle('dark')
}

const toggleLocale = () => {
  locale.value = locale.value === 'zh' ? 'en' : 'zh'
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>
