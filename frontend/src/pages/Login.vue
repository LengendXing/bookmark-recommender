<template>
  <div class="w-full max-w-md relative z-10">
    <!-- Card -->
    <div class="rounded-2xl p-8 shadow-lg" style="background-color: hsl(var(--card)); box-shadow: 0 4px 24px -4px rgb(0 0 0 / 0.08), 0 2px 8px -2px rgb(0 0 0 / 0.04)">
      <!-- Logo -->
      <div class="flex flex-col items-center mb-8">
        <img :src="isDark ? '/logo-dark.svg' : '/logo-light.svg'" class="w-12 h-12 rounded-xl mb-4" />
        <h2 class="text-xl font-semibold tracking-tight">{{ t('login.title') }}</h2>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-5">
        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1.5 block tracking-wide uppercase">{{ t('login.username') }}</label>
          <input
            v-model="form.username"
            type="text"
            class="w-full px-3.5 py-2.5 rounded-xl text-sm transition-all duration-200 placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-accent/30"
            style="background-color: hsl(var(--muted) / 0.6)"
            :placeholder="t('login.username')"
            required
            autocomplete="username"
          />
        </div>
        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1.5 block tracking-wide uppercase">{{ t('login.password') }}</label>
          <input
            v-model="form.password"
            type="password"
            class="w-full px-3.5 py-2.5 rounded-xl text-sm transition-all duration-200 placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-accent/30"
            style="background-color: hsl(var(--muted) / 0.6)"
            :placeholder="t('login.password')"
            required
            autocomplete="current-password"
          />
        </div>

        <p v-if="error" class="text-destructive text-xs text-center font-medium">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2.5 bg-accent text-accent-foreground rounded-xl text-sm font-medium transition-all duration-200 hover:opacity-90 active:scale-[0.98] disabled:opacity-50"
        >
          {{ loading ? '...' : t('login.submit') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { auth } from '@/api'


const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const isDark = ref(localStorage.getItem('dark') === 'true')
const form = ref({ username: '', password: '' })
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await auth.login(form.value)
    authStore.setToken(res.data.token)
    authStore.setUser(res.data.user)
    router.push('/dashboard')
  } catch (e: any) {
    error.value = e.response?.data?.message || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
