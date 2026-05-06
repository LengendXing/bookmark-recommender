<template>
  <div class="p-6 lg:p-8">
    <h2 class="text-xl font-semibold tracking-tight mb-6">{{ t('audit.title') }}</h2>

    <!-- Skeleton loading -->
    <div v-if="loading" class="space-y-2">
      <SkeletonTable :rows="8" />
    </div>

    <div v-else class="rounded-xl overflow-hidden" style="background-color: hsl(var(--card)); box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.04)">
      <table class="w-full text-sm">
        <thead>
          <tr style="background-color: hsl(var(--muted) / 0.4)">
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase w-12">#</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase">User</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase">{{ t('audit.action') }}</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden md:table-cell">{{ t('audit.target') }}</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden sm:table-cell">{{ t('audit.time') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in items" :key="log.id" class="border-t border-border/50 hover:bg-muted/30 transition-colors">
            <td class="px-4 py-3 text-muted-foreground text-xs">{{ log.id }}</td>
            <td class="px-4 py-3 font-medium text-xs">user #{{ log.user_id }}</td>
            <td class="px-4 py-3">
              <span class="inline-block px-2.5 py-1 rounded-lg text-xs font-medium" style="background-color: hsl(var(--muted)); color: hsl(var(--muted-foreground))">{{ log.action }}</span>
            </td>
            <td class="px-4 py-3 hidden md:table-cell text-xs text-muted-foreground">{{ log.target_type }} #{{ log.target_id }}</td>
            <td class="px-4 py-3 hidden sm:table-cell text-xs text-muted-foreground">{{ log.created_at }}</td>
          </tr>
          <tr v-if="!items.length">
            <td colspan="5" class="px-4 py-16 text-center">
              <ShieldCheck class="w-8 h-8 text-muted-foreground/30 mx-auto mb-3" />
              <p class="text-muted-foreground text-sm">No audit logs</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="flex items-center justify-end mt-4">
      <div class="flex gap-1.5">
        <button
          @click="page--"
          :disabled="page <= 1"
          class="px-3 py-1.5 rounded-lg text-xs font-medium border border-border/50 hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >Prev</button>
        <button
          @click="page++"
          :disabled="page * 50 >= total"
          class="px-3 py-1.5 rounded-lg text-xs font-medium border border-border/50 hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >Next</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { admin } from '@/api'
import { ShieldCheck } from 'lucide-vue-next'
import SkeletonTable from '@/components/SkeletonTable.vue'

const { t } = useI18n()
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)

const load = async () => {
  loading.value = true
  try {
    const res = await admin.auditLogs({ page: page.value })
    items.value = res.data.items
    total.value = res.data.total
  } catch (_) {}
  loading.value = false
}

onMounted(load)
watch(page, load)
</script>
