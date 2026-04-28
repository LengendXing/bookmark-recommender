<template>
  <div class="w-full max-w-sm mx-auto p-8">
    <div class="bg-card rounded-lg border border-border p-6 shadow-sm">
      <h2 class="text-2xl font-bold mb-6 text-center">{{ t('login.title') }}</h2>
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="text-sm block mb-1 text-muted-foreground">{{ t('login.username') }}</label>
          <input v-model="form.username" type="text" class="w-full px-3 py-2 rounded-md border border-border bg-background focus:outline-none focus:ring-1 focus:ring-primary" required />
        </div>
        <div>
          <label class="text-sm block mb-1 text-muted-foreground">{{ t('login.password') }}</label>
          <input v-model="form.password" type="password" class="w-full px-3 py-2 rounded-md border border-border bg-background focus:outline-none focus:ring-1 focus:ring-primary" required />
        </div>
        <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
        <button type="submit" class="w-full py-2 bg-primary text-primary-foreground rounded-md hover:opacity-90 transition font-medium" :disabled="loading">
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
