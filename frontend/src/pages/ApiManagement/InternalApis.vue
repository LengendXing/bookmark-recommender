<template>
  <div class="h-[calc(100vh-4rem)] overflow-auto p-6 lg:p-8">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-semibold tracking-tight">{{ t('apiManagement.title') }}</h2>
      <div class="flex items-center gap-2">
        <button
          class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-medium transition-colors"
          style="background-color: hsl(var(--muted) / 0.6)"
          @click="syncRoutes"
          :disabled="syncing"
        >
          <span v-if="syncing" class="inline-block w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
          {{ t('apiManagement.sync') }}
        </button>
        <button
          class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-medium text-white transition-colors"
          style="background-color: hsl(217 91% 60%)"
          @click="openAdd"
        >+ {{ t('apiManagement.add') }}</button>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="flex flex-wrap items-center gap-3 mb-6">
      <div class="flex-1 min-w-0 max-w-sm">
        <input
          v-model="searchQuery"
          :placeholder="t('apiManagement.search')"
          class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
          style="background-color: hsl(var(--muted) / 0.6)"
          @input="onSearchInput"
        />
      </div>
      <select
        v-model="methodFilter"
        class="px-3 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
        style="background-color: hsl(var(--muted) / 0.6)"
        @change="loadPage(1)"
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
        @change="loadPage(1)"
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
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden md:table-cell w-28">{{ t('apiManagement.tags') }}</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-muted-foreground tracking-wide uppercase w-16">{{ t('apiManagement.enabled') }}</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-muted-foreground tracking-wide uppercase w-20">{{ t('apiManagement.source') }}</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-muted-foreground tracking-wide uppercase w-24">{{ t('common.save') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="route in routes"
            :key="route.id"
            class="border-t border-border/50 hover:bg-muted/30 transition-colors"
          >
            <td class="px-4 py-3">
              <span
                class="inline-block px-2.5 py-0.5 rounded-lg text-xs font-semibold"
                :style="methodStyle(route.method)"
              >{{ route.method }}</span>
            </td>
            <td class="px-4 py-3 font-mono text-xs">{{ route.path }}</td>
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
            <td class="px-4 py-3 text-center">
              <button
                class="w-10 h-5 rounded-full relative transition-colors"
                :style="{ backgroundColor: route.enabled ? 'hsl(142 76% 36%)' : 'hsl(var(--muted))' }"
                @click="toggleEnabled(route)"
              >
                <span
                  class="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-transform"
                  :style="{ left: route.enabled ? '22px' : '2px' }"
                />
              </button>
            </td>
            <td class="px-4 py-3 text-center">
              <span
                class="inline-block px-2 py-0.5 rounded-lg text-xs"
                :style="{ backgroundColor: route.source === 'manual' ? 'hsl(45 93% 47% / 0.15)' : 'hsl(var(--muted) / 0.5)', color: route.source === 'manual' ? 'hsl(45 93% 25%)' : 'hsl(var(--muted-foreground))' }"
              >{{ route.source === 'manual' ? t('apiManagement.sourceManual') : t('apiManagement.sourceAuto') }}</span>
            </td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1">
                <button
                  class="px-2.5 py-1 rounded-lg text-xs hover:bg-muted/50 transition-colors"
                  @click="openEdit(route)"
                >{{ t('common.save') }}</button>
                <button
                  class="px-2.5 py-1 rounded-lg text-xs text-red-500 hover:bg-red-50 transition-colors"
                  @click="confirmDelete(route)"
                >{{ t('apiManagement.delete') }}</button>
              </div>
            </td>
          </tr>
          <tr v-if="!routes.length">
            <td :colspan="7" class="px-4 py-16 text-center">
              <p class="text-muted-foreground text-sm">{{ t('apiManagement.noData') }}</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="total > 0" class="flex items-center justify-between mt-4">
      <div class="flex items-center gap-1 text-xs text-muted-foreground">
        <select
          v-model.number="pageSize"
          class="px-2 py-1 rounded-lg text-xs focus:outline-none"
          style="background-color: hsl(var(--muted) / 0.4)"
          @change="loadPage(1)"
        >
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
      </div>
      <div class="flex items-center gap-1">
        <button
          class="px-2.5 py-1 rounded-lg text-xs transition-colors hover:bg-muted/50"
          :disabled="page <= 1"
          @click="loadPage(page - 1)"
        >{{ t('pagination.prev') }}</button>
        <span class="text-xs text-muted-foreground px-2">{{ t('pagination.pageOf', { current: page, total: totalPages }) }}</span>
        <button
          class="px-2.5 py-1 rounded-lg text-xs transition-colors hover:bg-muted/50"
          :disabled="page >= totalPages"
          @click="loadPage(page + 1)"
        >{{ t('pagination.next') }}</button>
        <input
          v-model="jumpPage"
          class="w-10 px-1.5 py-1 rounded-lg text-xs text-center focus:outline-none"
          style="background-color: hsl(var(--muted) / 0.4)"
          @keyup.enter="jumpToPage"
        />
        <button
          class="px-2 py-1 rounded-lg text-xs transition-colors hover:bg-muted/50"
          @click="jumpToPage"
        >{{ t('pagination.jumpTo') }}</button>
      </div>
    </div>

    <!-- Add/Edit Dialog -->
    <Teleport to="body">
      <div
        v-if="showDialog"
        class="fixed inset-0 z-50 flex items-center justify-center"
        style="background-color: rgb(0 0 0 / 0.3)"
        @click.self="showDialog = false"
      >
        <div class="w-full max-w-lg mx-4 rounded-2xl p-6 shadow-xl" style="background-color: hsl(var(--card))">
          <h3 class="text-lg font-semibold mb-5">{{ editingId ? t('apiManagement.edit') : t('apiManagement.add') }}</h3>
          <div class="space-y-4">
            <div class="flex gap-3">
              <div class="w-28">
                <label class="block text-xs font-medium text-muted-foreground mb-1">{{ t('apiManagement.method') }}</label>
                <select
                  v-model="form.method"
                  class="w-full px-3 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
                  style="background-color: hsl(var(--muted) / 0.4)"
                >
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="DELETE">DELETE</option>
                  <option value="PATCH">PATCH</option>
                </select>
              </div>
              <div class="flex-1">
                <label class="block text-xs font-medium text-muted-foreground mb-1">{{ t('apiManagement.path') }}</label>
                <input
                  v-model="form.path"
                  class="w-full px-3 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
                  style="background-color: hsl(var(--muted) / 0.4)"
                  placeholder="/api/example"
                />
              </div>
            </div>
            <div>
              <label class="block text-xs font-medium text-muted-foreground mb-1">{{ t('apiManagement.summary') }}</label>
              <input
                v-model="form.summary"
                class="w-full px-3 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
                style="background-color: hsl(var(--muted) / 0.4)"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-muted-foreground mb-1">{{ t('apiManagement.tags') }} <span class="font-normal opacity-60">({{ t('apiManagement.tagsHint') }})</span></label>
              <input
                v-model="form.tagsStr"
                class="w-full px-3 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
                style="background-color: hsl(var(--muted) / 0.4)"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-muted-foreground mb-1">{{ t('apiManagement.description') }}</label>
              <textarea
                v-model="form.description"
                rows="3"
                class="w-full px-3 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 resize-none"
                style="background-color: hsl(var(--muted) / 0.4)"
              />
            </div>
            <label class="flex items-center gap-2 text-sm cursor-pointer">
              <input v-model="form.enabled" type="checkbox" class="rounded" />
              {{ t('apiManagement.enable') }}
            </label>
          </div>
          <div class="flex justify-end gap-2 mt-6">
            <button
              class="px-4 py-2 rounded-xl text-sm transition-colors"
              style="background-color: hsl(var(--muted) / 0.4)"
              @click="showDialog = false"
            >{{ t('common.cancel') }}</button>
            <button
              class="px-4 py-2 rounded-xl text-sm text-white transition-colors"
              style="background-color: hsl(217 91% 60%)"
              @click="saveRoute"
              :disabled="saving"
            >{{ t('common.save') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete Confirm Dialog -->
    <Teleport to="body">
      <div
        v-if="deleteTarget"
        class="fixed inset-0 z-50 flex items-center justify-center"
        style="background-color: rgb(0 0 0 / 0.3)"
        @click.self="deleteTarget = null"
      >
        <div class="w-full max-w-sm mx-4 rounded-2xl p-6 shadow-xl" style="background-color: hsl(var(--card))">
          <h3 class="text-lg font-semibold mb-2">{{ t('apiManagement.delete') }}</h3>
          <p class="text-sm text-muted-foreground mb-6">{{ t('apiManagement.deleteConfirm', { method: deleteTarget.method, path: deleteTarget.path }) }}</p>
          <div class="flex justify-end gap-2">
            <button
              class="px-4 py-2 rounded-xl text-sm transition-colors"
              style="background-color: hsl(var(--muted) / 0.4)"
              @click="deleteTarget = null"
            >{{ t('common.cancel') }}</button>
            <button
              class="px-4 py-2 rounded-xl text-sm text-white transition-colors"
              style="background-color: hsl(0 72% 51%)"
              @click="doDelete"
              :disabled="deleting"
            >{{ t('apiManagement.delete') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { admin } from '@/api'

const { t } = useI18n()

const loading = ref(true)
const syncing = ref(false)
const saving = ref(false)
const deleting = ref(false)
const routes = ref<any[]>([])
const searchQuery = ref('')
const methodFilter = ref('')
const tagFilter = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const jumpPage = ref('')

const showDialog = ref(false)
const editingId = ref<number | null>(null)
const form = ref({ method: 'GET', path: '', summary: '', tagsStr: '', description: '', enabled: true })

const deleteTarget = ref<any>(null)

let searchTimer: ReturnType<typeof setTimeout> | null = null

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const allTags = computed(() => {
  const tags = new Set<string>()
  routes.value.forEach((r: any) => r.tags?.forEach((t: string) => tags.add(t)))
  return Array.from(tags).sort()
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

async function loadPage(p: number) {
  page.value = p
  loading.value = true
  try {
    const res = await admin.apiRoutes({
      page: p,
      page_size: pageSize.value,
      method: methodFilter.value,
      tag: tagFilter.value,
      search: searchQuery.value,
    })
    const d = res.data
    routes.value = d.items || []
    total.value = d.total || 0
  } catch (_) {} finally {
    loading.value = false
  }
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadPage(1), 300)
}

async function syncRoutes() {
  syncing.value = true
  try {
    await admin.apiRoutesSync()
    await loadPage(1)
  } catch (_) {} finally {
    syncing.value = false
  }
}

function openAdd() {
  editingId.value = null
  form.value = { method: 'GET', path: '', summary: '', tagsStr: '', description: '', enabled: true }
  showDialog.value = true
}

function openEdit(route: any) {
  editingId.value = route.id
  form.value = {
    method: route.method,
    path: route.path,
    summary: route.summary || '',
    tagsStr: (route.tags || []).join(', '),
    description: route.description || '',
    enabled: route.enabled,
  }
  showDialog.value = true
}

async function saveRoute() {
  saving.value = true
  try {
    const tags = form.value.tagsStr
      .split(',')
      .map((t: string) => t.trim())
      .filter(Boolean)

    if (editingId.value) {
      await admin.apiRouteUpdate(editingId.value, {
        summary: form.value.summary,
        tags,
        description: form.value.description,
        enabled: form.value.enabled,
      })
    } else {
      await admin.apiRouteCreate({
        method: form.value.method,
        path: form.value.path,
        summary: form.value.summary,
        tags,
        description: form.value.description,
        enabled: form.value.enabled,
      })
    }
    showDialog.value = false
    await loadPage(page.value)
  } catch (_) {} finally {
    saving.value = false
  }
}

async function toggleEnabled(route: any) {
  try {
    await admin.apiRouteUpdate(route.id, { enabled: !route.enabled })
    route.enabled = !route.enabled
  } catch (_) {}
}

function confirmDelete(route: any) {
  deleteTarget.value = route
}

async function doDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await admin.apiRouteDelete(deleteTarget.value.id)
    deleteTarget.value = null
    await loadPage(page.value)
  } catch (_) {} finally {
    deleting.value = false
  }
}

function jumpToPage() {
  const n = parseInt(jumpPage.value, 10)
  if (n >= 1 && n <= totalPages.value) {
    loadPage(n)
    jumpPage.value = ''
  }
}

onMounted(() => loadPage(1))
</script>
