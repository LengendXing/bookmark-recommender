<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex"
      @click.self="$emit('close')"
    >
      <!-- Overlay -->
      <div class="absolute inset-0 bg-black/20 backdrop-blur-sm" />

      <!-- Drawer panel -->
      <div
        class="absolute right-0 top-0 bottom-0 w-full max-w-[420px] shadow-2xl overflow-y-auto animate-slide-in"
        style="background-color: hsl(var(--card))"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-border/50 sticky top-0 z-10 backdrop-blur-md" style="background-color: hsl(var(--card) / 0.9)">
          <h3 class="font-semibold text-sm">{{ t('bookmarks.detail') }}</h3>
          <button
            @click="$emit('close')"
            class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-muted transition-colors"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="px-5 py-12 text-center text-muted-foreground text-sm">
          Loading...
        </div>

        <!-- Content -->
        <div v-else-if="bookmark" class="px-5 py-4 space-y-4">
          <!-- ID -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.id') }}</h4>
            <p class="text-sm">{{ bookmark.id }}</p>
          </section>

          <!-- Title -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.titleLabel') }}</h4>
            <p v-if="bookmark.title" class="text-sm">{{ bookmark.title }}</p>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- URL -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.url') }}</h4>
            <a v-if="bookmark.url" :href="bookmark.url" target="_blank" class="text-sm text-blue-600 dark:text-blue-400 break-all hover:underline">{{ bookmark.url }}</a>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Description -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.description') }}</h4>
            <p v-if="bookmark.description" class="text-sm">{{ bookmark.description }}</p>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Author -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.author') }}</h4>
            <p v-if="bookmark.author" class="text-sm">{{ bookmark.author }}</p>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Category -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.category') }}</h4>
            <span v-if="bookmark.category" class="inline-block px-2.5 py-1 rounded-lg text-xs font-medium" style="background-color: hsl(var(--foreground) / 0.06); color: hsl(var(--foreground))">{{ bookmark.category }}</span>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Tags -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.tags') }}</h4>
            <div v-if="bookmark.tags && bookmark.tags.length" class="flex flex-wrap gap-1.5">
              <span v-for="tag in bookmark.tags" :key="tag" class="inline-block px-2.5 py-1 rounded-lg text-xs font-medium" style="background-color: hsl(var(--foreground) / 0.06); color: hsl(var(--foreground))">{{ tag }}</span>
            </div>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Rating -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.rating') }}</h4>
            <div class="flex gap-0.5">
              <Star v-for="i in 5" :key="i" :class="['w-4 h-4', i <= (bookmark.rating || 0) ? 'text-amber-400 fill-amber-400' : 'text-muted-foreground/25']" />
            </div>
          </section>

          <!-- AI Generated Title -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.generatedTitle') }}</h4>
            <p v-if="bookmark.generated_title" class="text-sm">{{ bookmark.generated_title }}</p>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- AI Generated Description -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.generatedDescription') }}</h4>
            <p v-if="bookmark.generated_description" class="text-sm">{{ bookmark.generated_description }}</p>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Page Title -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.pageTitle') }}</h4>
            <p v-if="bookmark.page_title" class="text-sm">{{ bookmark.page_title }}</p>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Page Description -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.pageDescription') }}</h4>
            <p v-if="bookmark.page_description" class="text-sm">{{ bookmark.page_description }}</p>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Page Text -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.pageText') }}</h4>
            <p v-if="bookmark.page_text" class="text-sm max-h-48 overflow-y-auto whitespace-pre-wrap p-2 rounded-lg" style="background-color: hsl(var(--muted) / 0.4)">{{ bookmark.page_text }}</p>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Folder Path -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.folderPath') }}</h4>
            <p v-if="bookmark.folder_path" class="text-sm">{{ bookmark.folder_path }}</p>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Date Added -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ t('bookmarks.dateAdded') }}</h4>
            <p v-if="bookmark.date_added" class="text-sm">{{ bookmark.date_added }}</p>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Crawl Error -->
          <section>
            <h4 class="text-xs font-semibold uppercase tracking-wide mb-1.5" :style="{ color: bookmark.crawl_error ? 'hsl(var(--destructive))' : 'hsl(var(--muted-foreground))' }">{{ t('bookmarks.crawlError') }}</h4>
            <p v-if="bookmark.crawl_error" class="text-xs rounded-lg p-2" style="background-color: hsl(var(--destructive) / 0.06); color: hsl(var(--destructive))">{{ bookmark.crawl_error }}</p>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Timestamps -->
          <section class="border-t border-border/30 pt-4">
            <div class="flex justify-between text-xs text-muted-foreground">
              <span>{{ t('bookmarks.createdAt') }}: {{ bookmark.created_at }}</span>
              <span>{{ t('bookmarks.updatedAt') }}: {{ bookmark.updated_at }}</span>
            </div>
          </section>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { X, Star } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'

withDefaults(defineProps<{
  visible: boolean
  loading: boolean
  bookmark?: Record<string, any> | null
}>(), {
  bookmark: null
})

defineEmits<{
  close: []
}>()

const { t } = useI18n()
</script>

<style scoped>
.animate-slide-in {
  animation: slideIn 0.25s ease-out;
}
@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}
</style>
