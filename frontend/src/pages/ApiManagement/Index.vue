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
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.time') }}</th>
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.method') }}</th>
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.path') }}</th>
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.statusCode') }}</th>
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.duration') }}</th>
              <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.client') }}</th>
              <th class="px-4 py-2 text-center font-medium text-muted-foreground w-16">{{ $t('common.action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in recentCalls" :key="log.id" class="border-b border-border/30 hover:bg-muted/20">
              <td class="px-4 py-2 whitespace-nowrap text-muted-foreground">{{ fmtTime(log.created_at) }}</td>
              <td class="px-4 py-2">
                <span class="px-1.5 py-0.5 rounded text-xs font-medium bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
                  {{ log.method }}
                </span>
              </td>
              <td class="px-4 py-2 font-mono text-xs max-w-[300px] truncate">{{ log.path }}</td>
              <td class="px-4 py-2">
                <span :class="statusClass(log.response_status)" class="px-1.5 py-0.5 rounded text-xs font-medium">
                  {{ log.response_status }}
                </span>
              </td>
              <td class="px-4 py-2 whitespace-nowrap text-muted-foreground">{{ log.duration_ms?.toFixed(1) }}ms</td>
              <td class="px-4 py-2 text-muted-foreground">{{ log.client_ip }}</td>
              <td class="px-4 py-2 text-center">
                <button @click="openCallDetail(log)" :title="$t('apiManagement.detail')" class="w-7 h-7 flex items-center justify-center rounded hover:bg-muted transition-colors">
                  <Info class="w-3.5 h-3.5" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Call Log Detail Drawer -->
    <Teleport to="body">
      <div v-if="detailLog" class="fixed inset-0 z-50 flex justify-end" @click.self="detailLog = null">
        <div class="absolute inset-0 bg-black/30" @click="detailLog = null" />
        <div class="relative bg-card border-l border-border/60 shadow-xl w-[480px] h-full overflow-y-auto p-6 space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold">{{ $t('apiManagement.callDetail') }}</h3>
            <button @click="detailLog = null" class="w-7 h-7 flex items-center justify-center rounded hover:bg-muted transition-colors">
              <X class="w-4 h-4" />
            </button>
          </div>

          <div class="space-y-3">
            <div>
              <label class="text-xs text-muted-foreground block mb-0.5">{{ $t('apiManagement.method') }} + {{ $t('apiManagement.path') }}</label>
              <p class="text-sm">
                <span class="px-1.5 py-0.5 rounded text-xs font-medium bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 mr-1.5">{{ detailLog.method }}</span>
                <span class="font-mono text-xs">{{ detailLog.path }}</span>
              </p>
            </div>
            <div>
              <label class="text-xs text-muted-foreground block mb-0.5">{{ $t('apiManagement.time') }}</label>
              <p class="text-sm text-muted-foreground">{{ fmtTime(detailLog.created_at) }}</p>
            </div>
            <div>
              <label class="text-xs text-muted-foreground block mb-0.5">{{ $t('apiManagement.statusCode') }}</label>
              <p class="text-sm">
                <span :class="statusClass(detailLog.response_status)" class="px-1.5 py-0.5 rounded text-xs font-medium">{{ detailLog.response_status }}</span>
              </p>
            </div>
            <div>
              <label class="text-xs text-muted-foreground block mb-0.5">{{ $t('apiManagement.duration') }}</label>
              <p class="text-sm text-muted-foreground">{{ detailLog.duration_ms?.toFixed(1) }}ms</p>
            </div>
            <div>
              <label class="text-xs text-muted-foreground block mb-0.5">{{ $t('apiManagement.client') }}</label>
              <p class="text-sm text-muted-foreground">{{ detailLog.client_ip }}</p>
            </div>
            <div v-if="detailLog.user_id">
              <label class="text-xs text-muted-foreground block mb-0.5">User ID</label>
              <p class="text-sm text-muted-foreground">{{ detailLog.user_id }}</p>
            </div>
            <div v-if="detailLog.error">
              <label class="text-xs text-muted-foreground block mb-0.5">Error</label>
              <p class="text-sm text-red-600 dark:text-red-400">{{ detailLog.error }}</p>
            </div>

            <!-- Request Body -->
            <div>
              <label class="text-xs text-muted-foreground block mb-1">{{ $t('apiManagement.requestBody') }}</label>
              <pre v-if="detailLog.request_body" class="px-3 py-2 text-xs font-mono rounded-lg border border-border/60 bg-zinc-900 text-zinc-100 overflow-auto max-h-[200px] whitespace-pre-wrap">{{ fmtJson(detailLog.request_body) }}</pre>
              <p v-else class="text-xs text-muted-foreground">-</p>
            </div>

            <!-- Response Body -->
            <div>
              <label class="text-xs text-muted-foreground block mb-1">{{ $t('apiManagement.responseBody') }}</label>
              <pre v-if="detailLog.response_body" class="px-3 py-2 text-xs font-mono rounded-lg border border-border/60 bg-zinc-900 text-zinc-100 overflow-auto max-h-[200px] whitespace-pre-wrap">{{ fmtJson(detailLog.response_body) }}</pre>
              <p v-else class="text-xs text-muted-foreground">-</p>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Info, X } from 'lucide-vue-next'
import { admin } from '@/api'

const stats = ref({ internal_count: 0, external_count: 0, calls_today: 0 })
const recentCalls = ref<any[]>([])
const detailLog = ref<any>(null)
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

const fmtJson = (raw: string) => {
  if (!raw) return '-'
  try { return JSON.stringify(JSON.parse(raw), null, 2) } catch { return raw }
}

const statusClass = (s: number) => {
  if (s >= 500) return 'bg-zinc-800 text-zinc-100 dark:bg-zinc-300 dark:text-zinc-900'
  if (s >= 400) return 'bg-zinc-200 text-zinc-700 dark:bg-zinc-700 dark:text-zinc-300'
  if (s >= 200) return 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800/60 dark:text-zinc-400'
  return 'bg-muted text-muted-foreground'
}

const openCallDetail = async (log: any) => {
  try {
    const res: any = await admin.apiCallLogDetail(log.id)
    if (res?.data) {
      detailLog.value = res.data
    } else {
      detailLog.value = log
    }
  } catch {
    detailLog.value = log
  }
}

onMounted(() => {
  fetchData()
  timer = setInterval(fetchData, 30000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
