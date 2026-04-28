<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold">{{ t('bookmarks.title') }}</h2>
      <div class="flex gap-2">
        <input v-model="searchQuery" :placeholder="t('bookmarks.search')" class="px-3 py-2 rounded-md border border-border bg-background text-sm" />
        <input v-model="ingestUrl" :placeholder="t('bookmarks.url')" class="px-3 py-2 rounded-md border border-border bg-background text-sm w-64" />
        <button @click="handleIngest" class="px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm hover:opacity-90">{{ t('bookmarks.ingest') }}</button>
      </div>
    </div>

    <div class="overflow-x-auto bg-card rounded-lg border border-border">
      <table class="w-full text-sm">
        <thead class="border-b border-border">
          <tr>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">#</th>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">Title</th>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">{{ t('bookmarks.tags') }}</th>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">Rating</th>
            <th class="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="bm in items" :key="bm.id" class="border-b border-border last:border-0 hover:bg-muted/50">
            <td class="px-4 py-3">{{ bm.id }}</td>
            <td class="px-4 py-3">
              <a :href="bm.url" target="_blank" class="font-medium hover:underline">{{ bm.title }}</a>
              <p class="text-xs text-muted-foreground truncate max-w-xs">{{ bm.description }}</p>
            </td>
            <td class="px-4 py-3">
              <span v-for="tag in bm.tags" :key="tag" class="inline-block px-2 py-0.5 bg-muted rounded text-xs mr-1">{{ tag }}</span>
            </td>
            <td class="px-4 py-3">{{ bm.rating }}</td>
            <td class="px-4 py-3 text-right space-x-2">
              <button @click="handleDelete(bm.id)" class="text-red-500 hover:text-red-700">{{ t('bookmarks.delete') }}</button>
            </td>
          </tr>
          <tr v-if="!items.length">
            <td colspan="5" class="px-4 py-8 text-center text-muted-foreground">No bookmarks yet</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex items-center justify-between mt-4">
      <p class="text-sm text-muted-foreground">Total: {{ total }}</p>
      <div class="flex gap-2">
        <button @click="page--" :disabled="page <= 1" class="px-3 py-1.5 rounded border border-border text-sm hover:bg-muted">Prev</button>
        <button @click="page++" :disabled="page * pageSize >= total" class="px-3 py-1.5 rounded border border-border text-sm hover:bg-muted">Next</button>
      </div>
    </div>

    <div v-if="error" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-600 text-sm">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { bookmarks } from '@/api'

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
