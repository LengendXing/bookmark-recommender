<template>
  <div class="p-6 lg:p-8">
    <h2 class="text-xl font-semibold tracking-tight mb-6">{{ t('settings.title') }}</h2>

    <div class="max-w-lg rounded-2xl p-6 shadow-sm" style="background-color: hsl(var(--card))">
      <form @submit.prevent="handleSave" class="space-y-5">
        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1.5 block">{{ t('settings.apiEndpoint') }}</label>
          <input
            v-model="form.api_endpoint"
            type="url"
            :placeholder="'https://api.openai.com/v1'"
            class="w-full px-3.5 py-2.5 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 transition-all"
            style="background-color: hsl(var(--muted) / 0.6)"
          />
        </div>
        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1.5 block">{{ t('settings.apiKey') }}</label>
          <input
            v-model="form.api_key"
            type="password"
            placeholder="sk-..."
            class="w-full px-3.5 py-2.5 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 transition-all"
            style="background-color: hsl(var(--muted) / 0.6)"
          />
        </div>

        <p v-if="statusMsg" class="text-xs" :class="statusOk ? 'text-emerald-500' : 'text-destructive'">{{ statusMsg }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2.5 bg-accent text-accent-foreground rounded-xl text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all"
        >
          {{ loading ? '...' : t('settings.save') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { settings } from '@/api'

const { t } = useI18n()
const form = ref({ api_endpoint: '', api_key: '' })
const loading = ref(false)
const statusMsg = ref('')
const statusOk = ref(true)

onMounted(async () => {
  try {
    const res = await settings.get()
    form.value.api_endpoint = res.data.data.api_endpoint || ''
    form.value.api_key = res.data.data.api_key || ''
  } catch (_) {}
})

const handleSave = async () => {
  loading.value = true
  statusMsg.value = ''
  try {
    await settings.update({
      api_endpoint: form.value.api_endpoint,
      api_key: form.value.api_key,
    })
    statusOk.value = true
    statusMsg.value = 'Saved'
  } catch (e: any) {
    statusOk.value = false
    statusMsg.value = e.response?.data?.message || 'Save failed'
  } finally {
    loading.value = false
  }
}
</script>
