<template>
  <div class="p-6">
    <h2 class="text-xl font-bold mb-6">{{ t('audit.title') }}</h2>
    <div class="overflow-x-auto bg-card rounded-lg border border-border">
      <table class="w-full text-sm">
        <thead class="border-b border-border">
          <tr>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">#</th>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">User</th>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">{{ t('audit.action') }}</th>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">{{ t('audit.target') }}</th>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">{{ t('audit.time') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in items" :key="log.id" class="border-b border-border last:border-0 hover:bg-muted/50">
            <td class="px-4 py-3">{{ log.id }}</td>
            <td class="px-4 py-3">user #{{ log.user_id }}</td>
            <td class="px-4 py-3"><span class="px-2 py-0.5 bg-muted rounded text-xs">{{ log.action }}</span></td>
            <td class="px-4 py-3">{{ log.target_type }} #{{ log.target_id }}</td>
            <td class="px-4 py-3 text-muted-foreground">{{ log.created_at }}</td>
          </tr>
          <tr v-if="!items.length">
            <td colspan="5" class="px-4 py-8 text-center text-muted-foreground">No audit logs</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="flex justify-end mt-4 gap-2">
      <button @click="page--" :disabled="page <= 1" class="px-3 py-1.5 rounded border border-border text-sm hover:bg-muted">Prev</button>
      <button @click="page++" :disabled="page * 50 >= total" class="px-3 py-1.5 rounded border border-border text-sm hover:bg-muted">Next</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { admin } from '@/api'

const { t } = useI18n()
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)

onMounted(async () => {
  try {
    const res = await admin.auditLogs({ page: page.value })
    items.value = res.data.items
    total.value = res.data.total
  } catch (_) {}
})
</script>
