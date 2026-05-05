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
        <div v-else-if="bookmark" class="px-5 py-4 space-y-5">
          <!-- Section: Basic -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">{{ t('bookmarks.title') }}</h4>
            <p class="text-sm font-medium">{{ bookmark.title }}</p>
          </section>

          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">{{ t('bookmarks.url') }}</h4>
            <a :href="bookmark.url" target="_blank" class="text-sm text-accent break-all hover:underline">{{ bookmark.url }}</a>
          </section>

          <section v-if="bookmark.description">
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">{{ t('bookmarks.description') }}</h4>
            <p class="text-sm">{{ bookmark.description }}</p>
          </section>

          <section v-if="bookmark.author">
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">{{ t('bookmarks.author') }}</h4>
            <p class="text-sm">{{ bookmark.author }}</p>
          </section>

          <!-- Section: AI Generated -->
          <section v-if="bookmark.generated_title">
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">{{ t('bookmarks.generatedTitle') }}</h4>
            <p class="text-sm">{{ bookmark.generated_title }}</p>
          </section>

          <section v-if="bookmark.generated_description">
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">{{ t('bookmarks.generatedDescription') }}</h4>
            <p class="text-sm">{{ bookmark.generated_description }}</p>
          </section>

          <!-- Section: Category -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">{{ t('bookmarks.category') }}</h4>
            <span v-if="bookmark.category" class="inline-block px-2.5 py-1 rounded-lg text-xs font-medium" style="background-color: hsl(var(--accent) / 0.08); color: hsl(var(--accent))">{{ bookmark.category }}</span>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Section: Tags -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">{{ t('bookmarks.tags') }}</h4>
            <div v-if="bookmark.tags && bookmark.tags.length" class="flex flex-wrap gap-1.5">
              <span v-for="tag in bookmark.tags" :key="tag" class="inline-block px-2.5 py-1 rounded-lg text-xs font-medium" style="background-color: hsl(var(--accent) / 0.08); color: hsl(var(--accent))">{{ tag }}</span>
            </div>
            <span v-else class="text-sm text-muted-foreground">—</span>
          </section>

          <!-- Section: Rating -->
          <section>
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Rating</h4>
            <div class="flex gap-0.5">
              <Star v-for="i in 5" :key="i" :class="['w-4 h-4', i <= (bookmark.rating || 0) ? 'text-amber-400 fill-amber-400' : 'text-muted-foreground/25']" />
            </div>
          </section>

          <!-- Section: Original Page Data (collapsible) -->
          <details class="group" v-if="bookmark.page_title || bookmark.page_description || bookmark.page_text">
            <summary class="text-xs font-semibold text-muted-foreground uppercase tracking-wide cursor-pointer hover:text-foreground transition-colors select-none">
              {{ t('bookmarks.originalData') }}
            </summary>
            <div class="mt-3 space-y-3 pl-1">
              <div v-if="bookmark.page_title">
                <h4 class="text-xs font-medium text-muted-foreground mb-1">{{ t('bookmarks.pageTitle') }}</h4>
                <p class="text-sm">{{ bookmark.page_title }}</p>
              </div>
              <div v-if="bookmark.page_description">
                <h4 class="text-xs font-medium text-muted-foreground mb-1">{{ t('bookmarks.pageDescription') }}</h4>
                <p class="text-sm">{{ bookmark.page_description }}</p>
              </div>
              <div v-if="bookmark.page_text">
                <h4 class="text-xs font-medium text-muted-foreground mb-1">{{ t('bookmarks.pageText') }}</h4>
                <p class="text-sm max-h-48 overflow-y-auto whitespace-pre-wrap p-2 rounded-lg" style="background-color: hsl(var(--muted) / 0.4)">{{ bookmark.page_text }}</p>
              </div>
            </div>
          </details>

          <!-- Section: Browser Import Data -->
          <section v-if="bookmark.folder_path || bookmark.date_added">
            <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">{{ t('bookmarks.importInfo') }}</h4>
            <div class="space-y-2">
              <div v-if="bookmark.folder_path">
                <span class="text-xs text-muted-foreground">{{ t('bookmarks.folderPath') }}:</span>
                <span class="text-sm ml-2">{{ bookmark.folder_path }}</span>
              </div>
              <div v-if="bookmark.date_added">
                <span class="text-xs text-muted-foreground">{{ t('bookmarks.dateAdded') }}:</span>
                <span class="text-sm ml-2">{{ bookmark.date_added }}</span>
              </div>
            </div>
          </section>

          <!-- Section: Crawl Error -->
          <section v-if="bookmark.crawl_error" class="rounded-xl p-3" style="background-color: hsl(var(--destructive) / 0.06)">
            <h4 class="text-xs font-semibold mb-1" style="color: hsl(var(--destructive))">{{ t('bookmarks.crawlError') }}</h4>
            <p class="text-xs" style="color: hsl(var(--destructive) / 0.8)">{{ bookmark.crawl_error }}</p>
          </section>

          <!-- Section: Timestamps -->
          <section class="border-t border-border/30 pt-4">
            <div class="flex justify-between text-xs text-muted-foreground">
              <span>Created: {{ bookmark.created_at }}</span>
              <span>Updated: {{ bookmark.updated_at }}</span>
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

const props = withDefaults(defineProps<{
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
