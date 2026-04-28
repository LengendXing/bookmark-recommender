<template>
  <div class="p-6">
    <h2 class="text-xl font-bold mb-6">{{ t('dashboard.title') }}</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-card rounded-lg border border-border p-5">
        <p class="text-sm text-muted-foreground">{{ t('dashboard.bookmarks') }}</p>
        <p class="text-3xl font-bold mt-1">{{ stats.bookmarks || 0 }}</p>
      </div>
      <div class="bg-card rounded-lg border border-border p-5">
        <p class="text-sm text-muted-foreground">{{ t('dashboard.users') }}</p>
        <p class="text-3xl font-bold mt-1">{{ stats.users || 0 }}</p>
      </div>
      <div class="bg-card rounded-lg border border-border p-5">
        <p class="text-sm text-muted-foreground">{{ t('dashboard.logs') }}</p>
        <p class="text-3xl font-bold mt-1">{{ stats.audit_logs || 0 }}</p>
      </div>
      <div class="bg-card rounded-lg border border-border p-5">
        <p class="text-sm text-muted-foreground">{{ t('dashboard.model') }}</p>
        <p class="text-lg font-bold mt-1">{{ stats.latest_model?.version || '-' }}</p>
        <p class="text-xs text-muted-foreground">{{ stats.latest_model?.status }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { admin } from '@/api'

const { t } = useI18n()
const stats = ref<any>({})

onMounted(async () => {
  try {
    const res = await admin.stats()
    stats.value = res.data
  } catch (_) {}
})
</script>
