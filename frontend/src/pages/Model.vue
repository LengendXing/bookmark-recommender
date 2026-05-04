<template>
  <div class="p-6 lg:p-8">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-semibold tracking-tight">{{ t('model.title') }}</h2>
      <button
        @click="showVerify = true"
        class="flex items-center gap-1.5 px-4 py-2 bg-accent text-accent-foreground rounded-xl text-sm font-medium transition-all duration-200 hover:opacity-90 active:scale-[0.98]"
      >
        <Zap class="w-4 h-4" />
        {{ t('model.train') }}
      </button>
    </div>

    <!-- Verification dialog -->
    <div v-if="showVerify" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/20 backdrop-blur-sm" @click="showVerify = false" />
      <div class="relative rounded-2xl p-6 w-full max-w-sm shadow-lg" style="background-color: hsl(var(--card))">
        <h3 class="text-sm font-semibold mb-4">Verification Required</h3>
        <input
          v-model="verifyCode"
          type="text"
          placeholder="Enter verification code"
          class="w-full px-3.5 py-2.5 rounded-xl text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent/30 mb-4"
          style="background-color: hsl(var(--muted) / 0.6)"
          @keyup.enter="confirmTrain"
        />
        <p v-if="verifyError" class="text-xs text-destructive mb-3">{{ verifyError }}</p>
        <div class="flex gap-2 justify-end">
          <button
            @click="showVerify = false; verifyCode = ''; verifyError = ''"
            class="px-4 py-2 rounded-xl text-sm font-medium border border-border/50 hover:bg-muted transition-colors"
          >Cancel</button>
          <button
            @click="confirmTrain"
            :disabled="!verifyCode"
            class="px-4 py-2 rounded-xl text-sm font-medium bg-accent text-accent-foreground hover:opacity-90 transition-all disabled:opacity-50"
          >Confirm</button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="rounded-xl overflow-hidden" style="background-color: hsl(var(--card)); box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.04)">
      <table class="w-full text-sm">
        <thead>
          <tr style="background-color: hsl(var(--muted) / 0.4)">
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase">Model</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase">{{ t('model.version') }}</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase">{{ t('model.status') }}</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden sm:table-cell">{{ t('model.dataset') }}</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden md:table-cell">Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in versions" :key="v.id" class="border-t border-border/50 hover:bg-muted/30 transition-colors">
            <td class="px-4 py-3 font-medium">{{ v.model_name }}</td>
            <td class="px-4 py-3">{{ v.version }}</td>
            <td class="px-4 py-3">
              <span :class="['inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium', v.status === 'trained' ? 'bg-success/10 text-success' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-400/10 dark:text-yellow-400']">
                <span :class="['w-1.5 h-1.5 rounded-full', v.status === 'trained' ? 'bg-success' : 'bg-yellow-500']" />
                {{ v.status }}
              </span>
            </td>
            <td class="px-4 py-3 hidden sm:table-cell">{{ v.dataset_size }}</td>
            <td class="px-4 py-3 hidden md:table-cell text-xs text-muted-foreground">{{ v.created_at }}</td>
          </tr>
          <tr v-if="!versions.length">
            <td colspan="5" class="px-4 py-16 text-center">
              <Cpu class="w-8 h-8 text-muted-foreground/30 mx-auto mb-3" />
              <p class="text-muted-foreground text-sm">No model versions</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Status message -->
    <div v-if="trainMsg" class="mt-4 px-4 py-3 rounded-xl text-sm font-medium" :class="trainOk ? 'bg-success/10 text-success' : 'bg-destructive/10 text-destructive'">
      {{ trainMsg }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { recommend } from '@/api'
import { Zap, Cpu } from 'lucide-vue-next'

const { t } = useI18n()
const versions = ref<any[]>([])
const trainMsg = ref('')
const trainOk = ref(true)
const showVerify = ref(false)
const verifyCode = ref('')
const verifyError = ref('')

const load = async () => {
  try {
    const res = await recommend.modelStatus()
    versions.value = res.data
  } catch (_) {}
}

const confirmTrain = async () => {
  if (!verifyCode.value) return
  verifyError.value = ''
  try {
    await recommend.train(verifyCode.value)
    trainOk.value = true
    trainMsg.value = 'Training triggered'
    showVerify.value = false
    verifyCode.value = ''
    load()
  } catch (e: any) {
    verifyError.value = e.response?.data?.message || 'Verification failed'
  }
}

onMounted(load)
</script>
