<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold">{{ t('model.title') }}</h2>
      <button @click="handleTrain" class="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm hover:opacity-90">
        {{ t('model.train') }}
      </button>
    </div>

    <div class="bg-card rounded-lg border border-border overflow-hidden">
      <table class="w-full text-sm">
        <thead class="border-b border-border">
          <tr>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">Model</th>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">{{ t('model.version') }}</th>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">{{ t('model.status') }}</th>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">{{ t('model.dataset') }}</th>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in versions" :key="v.id" class="border-b border-border last:border-0">
            <td class="px-4 py-3">{{ v.model_name }}</td>
            <td class="px-4 py-3">{{ v.version }}</td>
            <td class="px-4 py-3">
              <span :class="['px-2 py-0.5 rounded text-xs', v.status === 'trained' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700']">
                {{ v.status }}
              </span>
            </td>
            <td class="px-4 py-3">{{ v.dataset_size }}</td>
            <td class="px-4 py-3 text-muted-foreground">{{ v.created_at }}</td>
          </tr>
          <tr v-if="!versions.length">
            <td colspan="5" class="px-4 py-8 text-center text-muted-foreground">No model versions</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="trainMsg" class="mt-4 p-3 rounded-md text-sm" :class="trainOk ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'">
      {{ trainMsg }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { recommend } from '@/api'

const { t } = useI18n()
const versions = ref<any[]>([])
const trainMsg = ref('')
const trainOk = ref(true)

const load = async () => {
  try {
    const res = await recommend.modelStatus()
    versions.value = res.data
  } catch (_) {}
}

const handleTrain = async () => {
  trainMsg.value = ''
  const code = prompt('Enter verification code:')
  if (!code) return
  try {
    await recommend.train(code)
    trainOk.value = true
    trainMsg.value = 'Training triggered'
    load()
  } catch (e: any) {
    trainOk.value = false
    trainMsg.value = e.response?.data?.message || 'Training failed'
  }
}

onMounted(load)
</script>
