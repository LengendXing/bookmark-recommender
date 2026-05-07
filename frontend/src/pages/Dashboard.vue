<template>
  <div class="p-6 lg:p-8">
    <h2 class="text-xl font-semibold tracking-tight mb-8">{{ t('dashboard.title') }}</h2>

    <!-- Skeleton loading -->
    <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="i in 4" :key="i" class="rounded-xl p-5 space-y-4" style="background-color: hsl(var(--card))">
        <div class="flex items-center gap-3">
          <SkeletonBox width="40px" height="40px" borderRadius="12px" />
          <SkeletonBox width="80px" height="14px" />
        </div>
        <SkeletonBox width="60%" height="32px" />
        <SkeletonBox width="40%" height="12px" />
      </div>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Bookmarks -->
      <div class="rounded-xl p-5 transition-all duration-200 hover:shadow-md cursor-default" style="background-color: hsl(var(--card)); box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
            <Bookmark class="w-5 h-5 text-zinc-700 dark:text-zinc-300" />
          </div>
          <p class="text-sm text-muted-foreground font-medium">{{ t('dashboard.bookmarks') }}</p>
        </div>
        <p class="text-3xl font-bold tracking-tight">{{ stats.bookmarks || 0 }}</p>
      </div>

      <!-- Users -->
      <div class="rounded-xl p-5 transition-all duration-200 hover:shadow-md cursor-default" style="background-color: hsl(var(--card)); box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
            <Users class="w-5 h-5 text-zinc-700 dark:text-zinc-300" />
          </div>
          <p class="text-sm text-muted-foreground font-medium">{{ t('dashboard.users') }}</p>
        </div>
        <p class="text-3xl font-bold tracking-tight">{{ stats.users || 0 }}</p>
      </div>

      <!-- Audit Logs -->
      <div class="rounded-xl p-5 transition-all duration-200 hover:shadow-md cursor-default" style="background-color: hsl(var(--card)); box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-xl bg-muted flex items-center justify-center">
            <ScrollText class="w-5 h-5 text-muted-foreground" />
          </div>
          <p class="text-sm text-muted-foreground font-medium">{{ t('dashboard.logs') }}</p>
        </div>
        <p class="text-3xl font-bold tracking-tight">{{ stats.audit_logs || 0 }}</p>
      </div>

      <!-- Model -->
      <div class="rounded-xl p-5 transition-all duration-200 hover:shadow-md cursor-default" style="background-color: hsl(var(--card)); box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
            <Cpu class="w-5 h-5 text-zinc-700 dark:text-zinc-300" />
          </div>
          <p class="text-sm text-muted-foreground font-medium">{{ t('dashboard.model') }}</p>
        </div>
        <p class="text-lg font-bold tracking-tight">{{ stats.latest_model?.version || '-' }}</p>
        <p class="text-xs text-muted-foreground mt-0.5">{{ stats.latest_model?.status }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { admin } from '@/api'
import { Bookmark, Users, ScrollText, Cpu } from 'lucide-vue-next'
import SkeletonBox from '@/components/SkeletonBox.vue'

const { t } = useI18n()
const stats = ref<any>({})
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await admin.stats()
    stats.value = res.data
  } catch (_) {}
  loading.value = false
})
</script>
