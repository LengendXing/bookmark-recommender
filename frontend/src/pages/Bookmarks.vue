<template>
  <div class="p-6 lg:p-8">
    <h2 class="text-xl font-semibold tracking-tight mb-6">{{ t('bookmarks.title') }}</h2>

    <!-- Toolbar -->
    <div class="flex flex-wrap items-end gap-3 mb-6">
      <div class="flex-1 min-w-0 max-w-xs">
        <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.search') }}</label>
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground/50" />
          <input
            v-model="searchQuery"
            :placeholder="t('bookmarks.search')"
            class="w-full pl-9 pr-3 py-2 rounded-xl text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent/30"
            style="background-color: hsl(var(--muted) / 0.6)"
          />
        </div>
      </div>
      <button
        @click="showAddModal = true"
        class="flex items-center gap-1.5 px-4 py-2 bg-accent text-accent-foreground rounded-xl text-sm font-medium transition-all duration-200 hover:opacity-90 active:scale-[0.98]"
      >
        <Plus class="w-4 h-4" />
        {{ t('bookmarks.add') }}
      </button>
      <button
        @click="showImportModal = true"
        class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 hover:opacity-90 active:scale-[0.98]"
        style="background-color: hsl(var(--muted) / 0.6); color: hsl(var(--foreground))"
      >
        <Upload class="w-4 h-4" />
        {{ t('bookmarks.import') }}
      </button>
      <button
        @click="handleExport"
        class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 hover:opacity-90 active:scale-[0.98]"
        style="background-color: hsl(var(--muted) / 0.6); color: hsl(var(--foreground))"
      >
        <FileDown class="w-4 h-4" />
        {{ t('bookmarks.export') }}
      </button>
    </div>

    <!-- Add Bookmark Modal -->
    <div
      v-if="showAddModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
      @click.self="showAddModal = false"
    >
      <div class="rounded-2xl p-6 w-full max-w-md mx-4 shadow-xl" style="background-color: hsl(var(--card))">
        <h3 class="text-lg font-semibold mb-4">{{ t('bookmarks.add') }}</h3>
        <form @submit.prevent="handleAdd" class="space-y-4">
          <div>
            <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.url') }}</label>
            <input v-model="addForm.url" type="url" required class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
          </div>
          <div>
            <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.title') }}</label>
            <input v-model="addForm.title" type="text" required class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
          </div>
          <div>
            <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.description') }}</label>
            <input v-model="addForm.description" type="text" class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.author') }}</label>
              <input v-model="addForm.author" type="text" class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
            </div>
            <div>
              <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.category') }}</label>
              <input v-model="addForm.category" type="text" class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
            </div>
          </div>
          <div>
            <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.tags') }}</label>
            <input v-model="addForm.tagsStr" :placeholder="t('bookmarks.tagsHint')" type="text" class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showAddModal = false" class="flex-1 py-2 rounded-xl text-sm font-medium border border-border/50 hover:bg-muted transition-colors">{{ t('common.cancel') }}</button>
            <button type="submit" :disabled="addLoading" class="flex-1 py-2 bg-accent text-accent-foreground rounded-xl text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all">{{ addLoading ? '...' : t('common.save') }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Import Modal -->
    <div
      v-if="showImportModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
      @click.self="showImportModal = false"
    >
      <div class="rounded-2xl p-6 w-full max-w-md mx-4 shadow-xl" style="background-color: hsl(var(--card))">
        <h3 class="text-lg font-semibold mb-4">{{ t('bookmarks.import') }}</h3>
        <div class="space-y-4">
          <div>
            <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.browserSource') }}</label>
            <select v-model="importBrowser" class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)">
              <option value="">-- {{ t('bookmarks.selectBrowser') }} --</option>
              <option value="chrome">Google Chrome</option>
              <option value="firefox">Mozilla Firefox</option>
              <option value="edge">Microsoft Edge</option>
              <option value="safari">Apple Safari</option>
              <option value="opera">Opera</option>
            </select>
          </div>
          <div v-if="importBrowser">
            <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.selectFile') }}</label>
            <input ref="fileInput" type="file" accept=".html,.htm" @change="handleFileSelect" class="block w-full text-sm file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:text-xs file:font-medium file:border-0 file:bg-accent/10 file:text-accent hover:file:bg-accent/20 transition-all" />
          </div>
          <p v-if="importError" class="text-destructive text-xs text-center">{{ importError }}</p>
          <p v-if="importSuccess" class="text-xs text-center" style="color: hsl(var(--success))">{{ importSuccess }}</p>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showImportModal = false" class="flex-1 py-2 rounded-xl text-sm font-medium border border-border/50 hover:bg-muted transition-colors">{{ t('common.cancel') }}</button>
            <button @click="handleImport" :disabled="!selectedFile || importLoading" class="flex-1 py-2 bg-accent text-accent-foreground rounded-xl text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all">{{ importLoading ? '...' : t('bookmarks.import') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Semantic Search -->
    <div class="flex flex-wrap items-end gap-3 mb-6">
      <div class="flex-1 min-w-0 max-w-xs">
        <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.semanticSearch') }}</label>
        <div class="relative">
          <Sparkles class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-accent/60" />
          <input
            v-model="semanticQuery"
            :placeholder="t('bookmarks.semanticPlaceholder')"
            @keyup.enter="handleSemanticSearch"
            class="w-full pl-9 pr-3 py-2 rounded-xl text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent/30"
            style="background-color: hsl(var(--muted) / 0.6)"
          />
        </div>
      </div>
      <button
        @click="handleSemanticSearch"
        :disabled="semanticLoading"
        class="flex items-center gap-1.5 px-4 py-2 bg-accent text-accent-foreground rounded-xl text-sm font-medium transition-all duration-200 hover:opacity-90 active:scale-[0.98] disabled:opacity-50"
      >
        <Search class="w-4 h-4" />
        {{ semanticLoading ? '...' : t('bookmarks.search') }}
      </button>
      <button
        v-if="semanticMode"
        @click="clearSemanticSearch"
        class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 hover:opacity-90 active:scale-[0.98]"
        style="background-color: hsl(var(--muted) / 0.6); color: hsl(var(--foreground))"
      >
        {{ t('common.cancel') }}
      </button>
    </div>

    <!-- Semantic Error -->
    <div v-if="semanticError" class="mb-4 px-4 py-3 rounded-xl text-sm font-medium" style="background-color: hsl(var(--destructive) / 0.08); color: hsl(var(--destructive))">
      {{ semanticError }}
    </div>

    <!-- Table -->
    <div class="rounded-xl overflow-hidden" style="background-color: hsl(var(--card)); box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.04)">
      <table class="w-full text-sm">
        <thead>
          <tr style="background-color: hsl(var(--muted) / 0.4)">
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase w-12">#</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase">Title</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden md:table-cell">{{ t('bookmarks.tags') }}</th>
            <th v-if="semanticMode" class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden sm:table-cell w-20">{{ t('bookmarks.relevance') }}</th>
            <th v-else class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden sm:table-cell w-20">Rating</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-muted-foreground tracking-wide uppercase w-24">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="bm in displayItems" :key="bm.id" class="border-t border-border/50 hover:bg-muted/30 transition-colors">
            <td class="px-4 py-3 text-muted-foreground text-xs">{{ bm.id }}</td>
            <td class="px-4 py-3">
              <button @click="openDrawer(bm.id)" class="font-medium hover:text-accent transition-colors line-clamp-1 text-left">{{ bm.title }}</button>
              <p class="text-xs text-muted-foreground line-clamp-1 mt-0.5 max-w-xs">{{ bm.description }}</p>
            </td>
            <td class="px-4 py-3 hidden md:table-cell">
              <div class="flex flex-wrap gap-1">
                <span v-for="tag in (bm.tags || [])" :key="tag" class="inline-block px-2 py-0.5 rounded-lg text-xs font-medium" style="background-color: hsl(var(--accent) / 0.08); color: hsl(var(--accent))">{{ tag }}</span>
              </div>
            </td>
            <td v-if="semanticMode" class="px-4 py-3 hidden sm:table-cell">
              <span class="inline-block px-2 py-0.5 rounded-lg text-xs font-medium" :style="{ backgroundColor: `hsl(var(--accent) / ${(bm.score || 0) * 0.12})`, color: 'hsl(var(--accent))' }">{{ ((bm.score || 0) * 100).toFixed(0) }}%</span>
            </td>
            <td v-else class="px-4 py-3 hidden sm:table-cell font-medium">{{ bm.rating }}</td>
            <td class="px-4 py-3 text-right">
              <button
                @click="handleDelete(bm.id)"
                class="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs text-muted-foreground hover:text-destructive hover:bg-destructive/5 transition-all"
              >
                <Trash2 class="w-3.5 h-3.5" />
                <span class="hidden sm:inline">{{ t('bookmarks.delete') }}</span>
              </button>
            </td>
          </tr>
          <tr v-if="!displayItems.length">
            <td colspan="5" class="px-4 py-16 text-center">
              <Bookmark class="w-8 h-8 text-muted-foreground/30 mx-auto mb-3" />
              <p class="text-muted-foreground text-sm">No bookmarks yet</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="!semanticMode" class="flex items-center justify-between mt-4">
      <p class="text-xs text-muted-foreground">Total: {{ total }}</p>
      <div class="flex gap-1.5">
        <button
          @click="page--"
          :disabled="page <= 1"
          class="px-3 py-1.5 rounded-lg text-xs font-medium border border-border/50 hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >Prev</button>
        <button
          @click="page++"
          :disabled="page * pageSize >= total"
          class="px-3 py-1.5 rounded-lg text-xs font-medium border border-border/50 hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >Next</button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mt-4 px-4 py-3 rounded-xl text-sm font-medium" style="background-color: hsl(var(--destructive) / 0.08); color: hsl(var(--destructive))">
      {{ error }}
    </div>

    <!-- Detail Drawer -->
    <BookmarkDrawer
      :visible="showDrawer"
      :loading="drawerLoading"
      :bookmark="selectedBookmark"
      @close="closeDrawer"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { bookmarks, recommend } from '@/api'
import { Search, Plus, Upload, FileDown, Trash2, Bookmark, Sparkles } from 'lucide-vue-next'
import BookmarkDrawer from '@/components/BookmarkDrawer.vue'

const { t } = useI18n()
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const searchQuery = ref('')
const error = ref('')

// Add modal
const showAddModal = ref(false)
const addLoading = ref(false)
const addForm = ref({ url: '', title: '', description: '', author: '', category: '', tagsStr: '' })

// Import modal
const showImportModal = ref(false)
const importBrowser = ref('')
const selectedFile = ref<File | null>(null)
const importLoading = ref(false)
const importError = ref('')
const importSuccess = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

// Drawer
const showDrawer = ref(false)
const drawerLoading = ref(false)
const selectedBookmark = ref<Record<string, any> | null>(null)
const openDrawer = async (id: number) => {
  showDrawer.value = true
  drawerLoading.value = true
  selectedBookmark.value = null
  try {
    const res = await bookmarks.get(id)
    selectedBookmark.value = res.data
  } catch (_) {
    showDrawer.value = false
  } finally {
    drawerLoading.value = false
  }
}
const closeDrawer = () => { showDrawer.value = false }

const semanticMode = ref(false)
const semanticQuery = ref('')
const semanticLoading = ref(false)
const semanticResults = ref<any[]>([])
const semanticError = ref('')

const handleSemanticSearch = async () => {
  if (!semanticQuery.value.trim()) return
  semanticLoading.value = true
  semanticError.value = ''
  try {
    const res = await recommend.search(semanticQuery.value, 20)
    semanticResults.value = res.data || []
    semanticMode.value = true
  } catch (e: any) {
    semanticError.value = e.response?.data?.message || 'Semantic search failed'
  } finally {
    semanticLoading.value = false
  }
}

const clearSemanticSearch = () => {
  semanticMode.value = false
  semanticQuery.value = ''
  semanticResults.value = []
}

const displayItems = computed(() => semanticMode.value ? semanticResults.value : items.value)

const load = async () => {
  error.value = ''
  try {
    const res = await bookmarks.list({ page: page.value, page_size: pageSize, search: searchQuery.value })
    items.value = res.data.items
    total.value = res.data.total
  } catch (e: any) {
    error.value = e.response?.data?.message || 'Failed to load'
  }
}

const resetAddForm = () => {
  addForm.value = { url: '', title: '', description: '', author: '', category: '', tagsStr: '' }
}

const handleAdd = async () => {
  addLoading.value = true
  try {
    const tags = addForm.value.tagsStr.split(',').map(s => s.trim()).filter(Boolean)
    await bookmarks.create({
      url: addForm.value.url,
      title: addForm.value.title,
      description: addForm.value.description || undefined,
      author: addForm.value.author || undefined,
      category: addForm.value.category || undefined,
      tags,
    })
    showAddModal.value = false
    resetAddForm()
    load()
  } catch (e: any) {
    error.value = e.response?.data?.message || 'Add failed'
  } finally {
    addLoading.value = false
  }
}

const handleFileSelect = (e: Event) => {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0]
    importError.value = ''
    importSuccess.value = ''
  }
}

const handleImport = async () => {
  if (!selectedFile.value || !importBrowser.value) return
  importLoading.value = true
  importError.value = ''
  importSuccess.value = ''
  try {
    const res = await bookmarks.importHtml(importBrowser.value, selectedFile.value)
    importSuccess.value = `Imported ${res.data?.count || 0} bookmarks`
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    load()
  } catch (e: any) {
    importError.value = e.response?.data?.message || 'Import failed'
  } finally {
    importLoading.value = false
  }
}

const handleExport = async () => {
  try {
    const res = await bookmarks.export()
    const blob = res.data instanceof Blob ? res.data : new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `bookmarks-export-${new Date().toISOString().slice(0, 10)}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (e: any) {
    error.value = e.response?.data?.message || 'Export failed'
  }
}

const handleDelete = async (id: number) => {
  try {
    await bookmarks.delete(id)
    load()
  } catch (_) {}
}

watch(searchQuery, () => { page.value = 1; load() })
onMounted(load)
</script>
