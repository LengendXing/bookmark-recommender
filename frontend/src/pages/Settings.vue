<template>
  <div class="p-6 lg:p-8">
    <h2 class="text-xl font-semibold tracking-tight mb-6">{{ t('settings.title') }}</h2>

    <!-- Skeleton loading -->
    <div v-if="pageLoading" class="max-w-lg rounded-2xl p-6 shadow-sm space-y-5" style="background-color: hsl(var(--card))">
      <div class="space-y-3">
        <SkeletonBox width="60px" height="12px" />
        <SkeletonBox width="100%" height="38px" />
      </div>
      <div class="space-y-3">
        <SkeletonBox width="50px" height="12px" />
        <SkeletonBox width="100%" height="38px" />
      </div>
      <div class="space-y-3">
        <SkeletonBox width="70px" height="12px" />
        <SkeletonBox width="100%" height="38px" />
      </div>
      <div class="space-y-3">
        <SkeletonBox width="40px" height="12px" />
        <SkeletonBox width="100%" height="38px" />
      </div>
      <SkeletonBox width="100%" height="42px" />
    </div>

    <div v-else class="max-w-lg rounded-2xl p-6 shadow-sm space-y-6" style="background-color: hsl(var(--card))">
      <!-- Config Form -->
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
        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1.5 block">{{ t('settings.apiProvider') }}</label>
          <select
            v-model="form.api_provider"
            class="w-full px-3.5 py-2.5 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 transition-all"
            style="background-color: hsl(var(--muted) / 0.6)"
          >
            <option value="openai">{{ t('settings.providerOpenAI') }}</option>
            <option value="anthropic">{{ t('settings.providerAnthropic') }}</option>
          </select>
        </div>
        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1.5 block">{{ t('settings.model') }}</label>
          <input
            v-model="form.ai_model"
            type="text"
            :placeholder="form.api_provider === 'anthropic' ? 'claude-sonnet-4-6-20250514' : 'gpt-4o'"
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

      <!-- Divider -->
      <div class="border-t border-border/50"></div>

      <!-- Test Connection Section -->
      <div class="space-y-4">
        <h3 class="text-sm font-medium">{{ t('settings.testConnection') }}</h3>

        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1.5 block">{{ t('settings.selectModel') }}</label>
          <select
            v-model="testModel"
            class="w-full px-3.5 py-2.5 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 transition-all"
            style="background-color: hsl(var(--muted) / 0.6)"
            @focus="fetchModels"
          >
            <option v-if="models.length === 0" value="">{{ testLoading ? '...' : '--' }}</option>
            <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>

        <!-- Test Result -->
        <div v-if="testResult" :class="testResult.success ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'" class="rounded-xl p-3 border text-xs space-y-1.5">
          <p :class="testResult.success ? 'text-emerald-700' : 'text-red-700'" class="font-medium">
            {{ testResult.success ? t('settings.testSuccess') : t('settings.testFailed') }}
          </p>
          <p v-if="testResult.success" class="text-muted-foreground">
            {{ t('settings.response') }}: <span class="text-foreground">{{ testResult.response }}</span>
          </p>
          <p v-if="testResult.success && testResult.tokens" class="text-muted-foreground">
            {{ t('settings.tokens') }}: input={{ testResult.tokens.input_tokens }}, output={{ testResult.tokens.output_tokens }}
          </p>
          <p v-if="!testResult.success" class="text-red-600">{{ testResult.error }}</p>
        </div>

        <button
          type="button"
          :disabled="testLoading || !testModel"
          @click="handleTest"
          class="w-full py-2.5 rounded-xl text-sm font-medium transition-all disabled:opacity-50"
          :class="testResult?.success ? 'bg-emerald-500 text-white hover:bg-emerald-600' : 'bg-muted text-muted-foreground hover:bg-muted/80'"
        >
          {{ testLoading ? '...' : t('settings.test') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { settings } from '@/api'
import SkeletonBox from '@/components/SkeletonBox.vue'

const { t } = useI18n()
const form = ref({ api_endpoint: '', api_key: '', api_provider: 'openai', ai_model: '' })
const loading = ref(false)
const pageLoading = ref(true)
const statusMsg = ref('')
const statusOk = ref(true)

const testModel = ref('')
const testLoading = ref(false)
const models = ref<string[]>([])
const testResult = ref<{ success: boolean; response?: string; model?: string; tokens?: any; error?: string } | null>(null)

onMounted(async () => {
  try {
    const res = await settings.get()
    form.value.api_endpoint = res.data.api_endpoint || ''
    form.value.api_key = res.data.api_key || ''
    form.value.api_provider = res.data.api_provider || 'openai'
    form.value.ai_model = res.data.ai_model || ''
  } catch (_) {} finally {
    pageLoading.value = false
  }
})

const handleSave = async () => {
  loading.value = true
  statusMsg.value = ''
  try {
    await settings.update({
      api_endpoint: form.value.api_endpoint,
      api_key: form.value.api_key,
      api_provider: form.value.api_provider,
      ai_model: form.value.ai_model,
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

const fetchModels = async () => {
  if (models.value.length > 0) return
  testLoading.value = true
  try {
    const res = await settings.listModels({
      api_endpoint: form.value.api_endpoint,
      api_key: form.value.api_key,
      api_provider: form.value.api_provider,
      model: form.value.ai_model || 'default',
    })
    models.value = res.data.models || []
    if (models.value.length > 0 && !testModel.value) {
      testModel.value = models.value[0]
    }
  } catch (_) {} finally {
    testLoading.value = false
  }
}

const handleTest = async () => {
  testLoading.value = true
  testResult.value = null
  try {
    const res = await settings.test({
      api_endpoint: form.value.api_endpoint,
      api_key: form.value.api_key,
      api_provider: form.value.api_provider,
      model: testModel.value,
    })
    testResult.value = res.data
  } catch (e: any) {
    testResult.value = {
      success: false,
      error: e.response?.data?.message || 'Test failed',
    }
  } finally {
    testLoading.value = false
  }
}
</script>
