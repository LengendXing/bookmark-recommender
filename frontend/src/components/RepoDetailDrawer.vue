<template>
  <Teleport to="body">
    <Transition name="drawer-fade">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex justify-end"
        @click.self="close"
      >
        <div class="fixed inset-0 bg-black/50" />
        <div class="relative z-10 w-[480px] max-w-[90vw] h-full bg-card border-l border-border shadow-2xl overflow-y-auto">
          <template v-if="repo">
            <!-- Header -->
            <div class="sticky top-0 bg-card border-b border-border px-5 py-4 flex items-start justify-between gap-3">
              <div class="min-w-0 flex-1">
                <h2 class="text-lg font-semibold truncate">{{ repo.repo_name }}</h2>
                <p class="text-sm text-muted-foreground">{{ repo.owner }}/{{ repo.repo_name }}</p>
              </div>
              <button
                @click="close"
                class="w-7 h-7 flex items-center justify-center rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
              >&times;</button>
            </div>

            <div class="px-5 py-4 space-y-5">
              <!-- Description -->
              <div v-if="repo.description">
                <h3 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">{{ $t('github.description') }}</h3>
                <p class="text-sm text-foreground/80">{{ repo.description }}</p>
              </div>

              <!-- GitHub Stats -->
              <div class="grid grid-cols-4 gap-3">
                <div class="bg-muted/40 rounded-lg px-3 py-2 text-center">
                  <div class="text-sm font-semibold">{{ repo.stars?.toLocaleString() || 0 }}</div>
                  <div class="text-[10px] text-muted-foreground">{{ $t('github.stars') }}</div>
                </div>
                <div class="bg-muted/40 rounded-lg px-3 py-2 text-center">
                  <div class="text-sm font-semibold">{{ repo.forks?.toLocaleString() || 0 }}</div>
                  <div class="text-[10px] text-muted-foreground">{{ $t('github.forks') }}</div>
                </div>
                <div class="bg-muted/40 rounded-lg px-3 py-2 text-center">
                  <div class="text-sm font-semibold">{{ repo.open_issues?.toLocaleString() || 0 }}</div>
                  <div class="text-[10px] text-muted-foreground">Issues</div>
                </div>
                <div class="bg-muted/40 rounded-lg px-3 py-2 text-center">
                  <div class="text-sm font-semibold">{{ repo.size_kb || 0 }}</div>
                  <div class="text-[10px] text-muted-foreground">KB</div>
                </div>
              </div>

              <!-- Meta badges -->
              <div class="flex flex-wrap gap-2">
                <span v-if="repo.language" class="px-2 py-0.5 text-xs rounded-md bg-muted/50">{{ repo.language }}</span>
                <span v-if="repo.license" class="px-2 py-0.5 text-xs rounded-md bg-muted/50">{{ repo.license }}</span>
                <span v-if="repo.default_branch" class="px-2 py-0.5 text-xs rounded-md bg-muted/50">{{ repo.default_branch }}</span>
                <span v-if="repo.archived" class="px-2 py-0.5 text-xs rounded-md bg-destructive/10 text-destructive">Archived</span>
              </div>

              <!-- AI Analysis Section -->
              <div v-if="repo.ai_analyzed_at" class="border border-border rounded-xl p-4 space-y-3">
                <div class="flex items-center gap-2">
                  <h3 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{{ $t('github.aiAnalysis') }}</h3>
                  <span class="text-[10px] text-muted-foreground bg-muted/50 px-1.5 py-0.5 rounded">{{ repo.ai_analyzed_at }}</span>
                </div>

                <div v-if="repo.ai_summary">
                  <div class="text-[10px] font-medium text-muted-foreground mb-1">{{ $t('github.aiSummary') }}</div>
                  <p class="text-sm">{{ repo.ai_summary }}</p>
                </div>

                <div v-if="repo.ai_category">
                  <div class="text-[10px] font-medium text-muted-foreground mb-1">{{ $t('github.aiCategory') }}</div>
                  <span class="px-2 py-0.5 text-xs rounded-md bg-muted/50">{{ repo.ai_category }}</span>
                </div>

                <div v-if="tagsList.length > 0">
                  <div class="text-[10px] font-medium text-muted-foreground mb-1">{{ $t('github.aiTags') }}</div>
                  <div class="flex flex-wrap gap-1.5">
                    <span v-for="t in tagsList" :key="t" class="px-2 py-0.5 text-xs rounded-md bg-accent/10 text-accent">{{ t }}</span>
                  </div>
                </div>

                <div v-if="repo.analyze_error" class="text-xs text-destructive bg-destructive/5 rounded px-2 py-1.5">
                  {{ repo.analyze_error }}
                </div>
              </div>

              <!-- Not analyzed info -->
              <div v-else class="border border-border rounded-xl p-4 text-center">
                <p class="text-sm text-muted-foreground">{{ $t('github.noAIAnalysis') }}</p>
              </div>

              <!-- Topics -->
              <div v-if="githubTopicsList.length > 0">
                <h3 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">{{ $t('github.topics') }}</h3>
                <div class="flex flex-wrap gap-1.5">
                  <span v-for="t in githubTopicsList" :key="t" class="px-2 py-0.5 text-xs rounded-full bg-muted/50 text-muted-foreground">{{ t }}</span>
                </div>
              </div>

              <!-- Homepage -->
              <div v-if="repo.homepage">
                <h3 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">{{ $t('github.homepage') }}</h3>
                <a :href="repo.homepage" target="_blank" class="text-sm text-accent hover:underline break-all">{{ repo.homepage }}</a>
              </div>

              <!-- README -->
              <div v-if="repo.readme_text" class="border-t border-border pt-4">
                <h3 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">{{ $t('github.readme') }}</h3>
                <pre class="text-xs whitespace-pre-wrap font-mono bg-muted/30 rounded-lg p-3 max-h-[300px] overflow-y-auto">{{ repo.readme_text }}</pre>
              </div>
            </div>

            <!-- Footer action bar -->
            <div class="sticky bottom-0 bg-card border-t border-border px-5 py-3">
              <a
                :href="`https://github.com/${repo.repo_full_name}`"
                target="_blank"
                class="flex items-center justify-center gap-2 w-full h-9 text-sm font-medium rounded-lg bg-accent text-accent-foreground hover:opacity-90 transition-opacity"
              >{{ $t('github.openInGitHub') }}</a>
            </div>
          </template>

          <div v-else class="flex items-center justify-center h-full text-muted-foreground text-sm">
            Loading...
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { github } from '@/api'
import { ref, watch } from 'vue'

const { t } = useI18n()

const props = defineProps<{
  open: boolean
  repoId: number | null
  isRecommended?: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const repo = ref<any>(null)
const loading = ref(false)

const tagsList = computed(() => {
  if (!repo.value?.ai_tags) return []
  const raw = repo.value.ai_tags
  if (raw.startsWith('[')) {
    try { return JSON.parse(raw) } catch { return [] }
  }
  return raw.split(',').map((t: string) => t.trim()).filter(Boolean)
})

const githubTopicsList = computed(() => {
  if (!repo.value?.topics) return []
  const raw = repo.value.topics
  if (raw.startsWith('[')) {
    try { return JSON.parse(raw) } catch { return [] }
  }
  return raw.split(',').map((t: string) => t.trim()).filter(Boolean)
})

const close = () => emit('close')

watch(() => props.open, async (val) => {
  if (val && props.repoId) {
    loading.value = true
    try {
      const res: any = await github.getRepo(props.repoId)
      repo.value = res.data
    } catch {
      repo.value = null
    }
    loading.value = false
  } else if (!val) {
    repo.value = null
  }
})
</script>

<style scoped>
.drawer-fade-enter-active,
.drawer-fade-leave-active {
  transition: opacity 0.2s ease;
}
.drawer-fade-enter-active > div:last-child,
.drawer-fade-leave-active > div:last-child {
  transition: transform 0.25s ease;
}
.drawer-fade-enter-from,
.drawer-fade-leave-to {
  opacity: 0;
}
.drawer-fade-enter-from > div:last-child {
  transform: translateX(100%);
}
.drawer-fade-leave-to > div:last-child {
  transform: translateX(100%);
}
</style>
