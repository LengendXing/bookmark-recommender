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
      <div class="flex-1 min-w-0 max-w-sm">
        <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.url') }}</label>
        <input
          v-model="ingestUrl"
          :placeholder="t('bookmarks.url')"
          class="w-full px-3.5 py-2 rounded-xl text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent/30"
          style="background-color: hsl(var(--muted) / 0.6)"
        />
      </div>
      <button
        @click="handleIngest"
        class="flex items-center gap-1.5 px-4 py-2 bg-accent text-accent-foreground rounded-xl text-sm font-medium transition-all duration-200 hover:opacity-90 active:scale-[0.98]"
      >
        <Download class="w-4 h-4" />
        {{ t('bookmarks.ingest') }}
      </button>
    </div>

    <!-- Table -->
    <div class="rounded-xl overflow-hidden" style="background-color: hsl(var(--card)); box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.04)">
      <table class="w-full text-sm">
        <thead>
          <tr style="background-color: hsl(var(--muted) / 0.4)">
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase w-12">#</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase">Title</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden md:table-cell">{{ t('bookmarks.tags') }}</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden sm:table-cell w-20">Rating</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-muted-foreground tracking-wide uppercase w-24">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="bm in items" :key="bm.id" class="border-t border-border/50 hover:bg-muted/30 transition-colors">
            <td class="px-4 py-3 text-muted-foreground text-xs">{{ bm.id }}</td>
            <td class="px-4 py-3">
              <a :href="bm.url" target="_blank" class="font-medium hover:text-accent transition-colors line-clamp-1">{{ bm.title }}</a>
              <p class="text-xs text-muted-foreground line-clamp-1 mt-0.5 max-w-xs">{{ bm.description }}</p>
            </td>
            <td class="px-4 py-3 hidden md:table-cell">
              <div class="flex flex-wrap gap-1">
                <span v-for="tag in (bm.tags || [])" :key="tag" class="inline-block px-2 py-0.5 rounded-lg text-xs font-medium" style="background-color: hsl(var(--accent) / 0.08); color: hsl(var(--accent))">{{ tag }}</span>
              </div>
            </td>
            <td class="px-4 py-3 hidden sm:table-cell font-medium">{{ bm.rating }}</td>
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
          <tr v-if="!items.length">
            <td colspan="5" class="px-4 py-16 text-center">
              <Bookmark class="w-8 h-8 text-muted-foreground/30 mx-auto mb-3" />
              <p class="text-muted-foreground text-sm">No bookmarks yet</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="flex items-center justify-between mt-4">
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
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { bookmarks } from '@/api'
import { Search, Download, Trash2, Bookmark } from 'lucide-vue-next'

const { t } = useI18n()
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const searchQuery = ref('')
const ingestUrl = ref('')
const error = ref('')

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

const handleIngest = async () => {
  error.value = ''
  if (!ingestUrl.value) return
  try {
    await bookmarks.ingest(ingestUrl.value)
    ingestUrl.value = ''
    load()
  } catch (e: any) {
    error.value = e.response?.data?.message || 'Ingest failed'
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
