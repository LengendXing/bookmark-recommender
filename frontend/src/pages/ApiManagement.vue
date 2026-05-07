<template>
  <div class="h-[calc(100vh-4rem)] overflow-auto p-6 lg:p-8">
    <h2 class="text-xl font-semibold tracking-tight mb-6">{{ t('apiManagement.title') }}</h2>

    <!-- Filter bar -->
    <div class="flex flex-wrap items-center gap-3 mb-6">
      <div class="flex-1 min-w-0 max-w-sm">
        <input
          v-model="searchQuery"
          :placeholder="t('apiManagement.search')"
          class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
          style="background-color: hsl(var(--muted) / 0.6)"
        />
      </div>
      <select
        v-model="methodFilter"
        class="px-3 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
        style="background-color: hsl(var(--muted) / 0.6)"
      >
        <option value="">{{ t('apiManagement.all') }}</option>
        <option value="GET">GET</option>
        <option value="POST">POST</option>
        <option value="PUT">PUT</option>
        <option value="DELETE">DELETE</option>
        <option value="PATCH">PATCH</option>
      </select>
      <select
        v-model="tagFilter"
        class="px-3 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
        style="background-color: hsl(var(--muted) / 0.6)"
      >
        <option value="">{{ t('apiManagement.all') }}</option>
        <option v-for="tag in allTags" :key="tag" :value="tag">{{ tag }}</option>
      </select>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-2">
      <div v-for="i in 8" :key="i" class="h-10 rounded-xl animate-pulse" style="background-color: hsl(var(--muted) / 0.3)" />
    </div>

    <!-- Table -->
    <div v-else class="rounded-xl overflow-hidden" style="background-color: hsl(var(--card)); box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.04)">
      <table class="w-full text-sm">
        <thead>
          <tr style="background-color: hsl(var(--muted) / 0.4)">
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase w-24">{{ t('apiManagement.method') }}</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase">{{ t('apiManagement.path') }}</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase">{{ t('apiManagement.summary') }}</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden md:table-cell w-32">{{ t('apiManagement.tags') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(route, idx) in filteredRoutes"
            :key="idx"
            class="border-t border-border/50 hover:bg-muted/30 transition-colors"
          >
            <td class="px-4 py-3">
              <span
                class="inline-block px-2.5 py-0.5 rounded-lg text-xs font-semibold"
                :style="methodStyle(route.method)"
              >{{ route.method }}</span>
            </td>
            <td class="px-4 py-3 font-mono text-xs whitespace-nowrap">{{ route.path }}</td>
            <td class="px-4 py-3 text-muted-foreground text-xs">{{ route.summary }}</td>
            <td class="px-4 py-3 hidden md:table-cell">
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="tag in route.tags"
                  :key="tag"
                  class="inline-block px-2 py-0.5 rounded-lg text-xs"
                  style="background-color: hsl(var(--muted) / 0.5); color: hsl(var(--muted-foreground))"
                >{{ tag }}</span>
              </div>
            </td>
          </tr>
          <tr v-if="!filteredRoutes.length">
            <td colspan="4" class="px-4 py-16 text-center">
              <p class="text-muted-foreground text-sm">{{ t('dashboard.noData') || 'No results' }}</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Summary footer -->
    <p class="text-xs text-muted-foreground mt-3">{{ filteredRoutes.length }} endpoints</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { admin } from '@/api'

const { t } = useI18n()

const loading = ref(true)
const routes = ref<any[]>([])
const searchQuery = ref('')
const methodFilter = ref('')
const tagFilter = ref('')

const allTags = computed(() => {
  const tags = new Set<string>()
  routes.value.forEach((r: any) => r.tags.forEach((t: string) => tags.add(t)))
  return Array.from(tags).sort()
})

const filteredRoutes = computed(() => {
  return routes.value.filter((r: any) => {
    if (methodFilter.value && r.method !== methodFilter.value) return false
    if (tagFilter.value && !r.tags.includes(tagFilter.value)) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      if (!r.path.toLowerCase().includes(q) && !r.summary.toLowerCase().includes(q)) return false
    }
    return true
  })
})

const methodColors: Record<string, { bg: string; fg: string }> = {
  GET:    { bg: 'hsl(142 76% 36%)',     fg: '#fff' },
  POST:   { bg: 'hsl(217 91% 60%)',     fg: '#fff' },
  PUT:    { bg: 'hsl(45 93% 47%)',      fg: '#fff' },
  DELETE: { bg: 'hsl(0 72% 51%)',       fg: '#fff' },
  PATCH:  { bg: 'hsl(270 60% 50%)',     fg: '#fff' },
}

const methodStyle = (method: string) => {
  const c = methodColors[method] || { bg: 'hsl(var(--muted))', fg: 'hsl(var(--foreground))' }
  return { backgroundColor: c.bg, color: c.fg }
}

onMounted(async () => {
  try {
    const res = await admin.apiList()
    routes.value = res.data.routes || []
  } catch (_) {} finally {
    loading.value = false
  }
})
</script>
