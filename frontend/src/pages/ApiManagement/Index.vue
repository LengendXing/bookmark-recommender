<template>
  <div class="p-6 space-y-6">
    <h2 class="text-lg font-semibold">{{ $t('apiManagement.overview') }}</h2>

    <!-- Stats Cards -->
    <div class="grid grid-cols-3 gap-4">
      <div class="rounded-xl border border-border/60 bg-card p-5">
        <div class="text-sm text-muted-foreground">{{ $t('apiManagement.internalInterface') }}</div>
        <div class="mt-2 text-3xl font-bold">{{ stats.internal_count }}</div>
      </div>
      <div class="rounded-xl border border-border/60 bg-card p-5">
        <div class="text-sm text-muted-foreground">{{ $t('apiManagement.externalInterface') }}</div>
        <div class="mt-2 text-3xl font-bold">{{ stats.external_count }}</div>
      </div>
      <div class="rounded-xl border border-border/60 bg-card p-5">
        <div class="text-sm text-muted-foreground">{{ $t('apiManagement.totalCalls') }}</div>
        <div class="mt-2 text-3xl font-bold">{{ stats.calls_today }}</div>
      </div>
    </div>

    <!-- Recent Calls -->
    <div>
      <h3 class="text-sm font-medium mb-3">{{ $t('apiManagement.recentCalls') }}</h3>
      <div v-if="recentCalls.length === 0" class="text-sm text-muted-foreground text-center py-10">
        {{ $t('apiManagement.noCallLogs') }}
      </div>
      <div v-else class="overflow-x-auto rounded-lg border border-border/60">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border/40 bg-muted/40">
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">Time</th>
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.method') }}</th>
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.path') }}</th>
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.statusCode') }}</th>
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.duration') }}</th>
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">Client</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in recentCalls" :key="log.id" class="border-b border-border/30 hover:bg-muted/20">
              <td class="px-4 py-2 whitespace-nowrap text-muted-foreground">{{ fmtTime(log.created_at) }}</td>
              <td class="px-4 py-2">
                <span :class="methodBadgeClass(log.method)" class="px-1.5 py-0.5 rounded text-xs font-medium">
                  {{ log.method }}
                </span>
              </td>
              <td class="px-4 py-2 font-mono text-xs max-w-[300px] truncate">{{ log.path }}</td>
              <td class="px-4 py-2">
                <span :class="statusClass(log.response_status)" class="px-1.5 py-0.5 rounded text-xs font-medium">
                  {{ log.response_status }}
                </span>
              </td>
              <td class="px-4 py-2 whitespace-nowrap text-muted-foreground">{{ log.duration_ms.toFixed(1) }}ms</td>
              <td class="px-4 py-2 text-muted-foreground">{{ log.client_ip }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { admin } from '@/api'

const stats = ref({ internal_count: 0, external_count: 0, calls_today: 0 })
const recentCalls = ref<any[]>([])
let timer: ReturnType<typeof setInterval> | null = null

const fetchData = async () => {
  try {
    const res: any = await admin.apiRoutesStats()
    if (res?.data) {
      stats.value = {
        internal_count: res.data.internal_count || 0,
        external_count: res.data.external_count || 0,
        calls_today: res.data.calls_today || 0,
      }
      recentCalls.value = res.data.recent_calls || []
    }
  } catch (_) { /* ignore */ }
}

const fmtTime = (ts: string) => {
  if (!ts) return '-'
  try { return new Date(ts).toLocaleString() } catch { return ts }
}

const methodBadgeClass = (m: string) => {
  const map: Record<string, string> = {
    GET: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    POST: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    PUT: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    DELETE: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    PATCH: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  }
  return map[m] || 'bg-muted text-muted-foreground'
}

const statusClass = (s: number) => {
  if (s >= 500) return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
  if (s >= 400) return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
  if (s >= 200) return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
  return 'bg-muted text-muted-foreground'
}

onMounted(() => {
  fetchData()
  timer = setInterval(fetchData, 30000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
