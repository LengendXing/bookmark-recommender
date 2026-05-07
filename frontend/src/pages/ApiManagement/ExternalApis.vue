<template>
  <div class="p-6 space-y-4">
    <h2 class="text-lg font-semibold">{{ $t('apiManagement.externalInterface') }}</h2>

    <!-- Toolbar -->
    <div class="flex items-center gap-3 flex-wrap">
      <button @click="openCreate" class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-accent text-accent-foreground hover:opacity-90 transition-opacity">
        <Plus class="w-3.5 h-3.5" /> {{ $t('apiManagement.createExternalApi') }}
      </button>
      <div class="flex items-center gap-2 ml-auto">
        <select v-model="filterMethod" class="px-2 py-1.5 text-sm rounded-lg border border-border/60 bg-card">
          <option value="">{{ $t('apiManagement.all') }}</option>
          <option v-for="m in methods" :key="m" :value="m">{{ m }}</option>
        </select>
        <input
          v-model="filterSearch"
          :placeholder="$t('apiManagement.search')"
          class="px-3 py-1.5 text-sm rounded-lg border border-border/60 bg-card w-56"
        />
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto rounded-lg border border-border/60">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-border/40 bg-muted/40">
            <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.name') }}</th>
            <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.method') }} + {{ $t('apiManagement.path') }}</th>
            <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.description') }}</th>
            <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.enabled') }}</th>
            <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('apiManagement.source') }}</th>
            <th class="px-4 py-2 text-left font-medium text-muted-foreground">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="items.length === 0">
            <td colspan="6" class="px-4 py-10 text-center text-muted-foreground">{{ $t('apiManagement.noData') }}</td>
          </tr>
          <tr v-for="api in items" :key="api.id" class="border-b border-border/30 hover:bg-muted/20">
            <td class="px-4 py-2">{{ api.name }}</td>
            <td class="px-4 py-2">
              <span :class="methodBadge(api.method)" class="px-1.5 py-0.5 rounded text-xs font-medium mr-1.5">{{ api.method }}</span>
              <span class="font-mono text-xs">{{ api.path }}</span>
            </td>
            <td class="px-4 py-2 text-muted-foreground max-w-[200px] truncate">{{ api.description }}</td>
            <td class="px-4 py-2">
              <button
                @click="toggleEnabled(api)"
                :class="api.enabled ? 'bg-accent/15 text-accent' : 'bg-muted text-muted-foreground'"
                class="px-2 py-0.5 rounded text-xs font-medium transition-colors"
              >{{ api.enabled ? $t('apiManagement.enable') : $t('apiManagement.disable') }}</button>
            </td>
            <td class="px-4 py-2">
              <span :class="api.is_native ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' : 'bg-muted text-muted-foreground'" class="px-1.5 py-0.5 rounded text-xs">
                {{ api.is_native ? $t('apiManagement.nativeEndpoint') : $t('apiManagement.sourceManual') }}
              </span>
            </td>
            <td class="px-4 py-2">
              <div class="flex items-center gap-1">
                <button @click="openEdit(api)" :disabled="api.is_native && !api.script" :title="api.is_native ? $t('apiManagement.edit') : $t('apiManagement.edit')" class="w-7 h-7 flex items-center justify-center rounded hover:bg-muted transition-colors disabled:opacity-30">
                  <Pencil class="w-3.5 h-3.5" />
                </button>
                <button v-if="api.script" @click="openTest(api)" :title="$t('apiManagement.testApi')" class="w-7 h-7 flex items-center justify-center rounded hover:bg-muted transition-colors">
                  <Play class="w-3.5 h-3.5" />
                </button>
                <button @click="confirmDelete(api)" :disabled="api.is_native" :title="$t('apiManagement.delete')" class="w-7 h-7 flex items-center justify-center rounded hover:bg-destructive/10 hover:text-destructive transition-colors disabled:opacity-30">
                  <Trash class="w-3.5 h-3.5" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="total > pageSize" class="flex items-center justify-between">
      <span class="text-xs text-muted-foreground">{{ $t('pagination.pageOf', { current: page, total: Math.ceil(total / pageSize) }) }}</span>
      <div class="flex items-center gap-1">
        <button :disabled="page <= 1" @click="page--; load()" class="px-2 py-1 text-xs rounded border border-border/40 hover:bg-muted disabled:opacity-30">{{ $t('pagination.prev') }}</button>
        <button :disabled="page >= Math.ceil(total / pageSize)" @click="page++; load()" class="px-2 py-1 text-xs rounded border border-border/40 hover:bg-muted disabled:opacity-30">{{ $t('pagination.next') }}</button>
      </div>
    </div>

    <!-- Create / Edit Modal -->
    <Teleport to="body">
      <div v-if="modalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="modalOpen = false">
        <div class="bg-card rounded-xl border border-border/60 shadow-xl w-[720px] max-h-[85vh] overflow-y-auto p-6 space-y-4">
          <h3 class="text-base font-semibold">{{ editingId ? $t('apiManagement.editExternal') : $t('apiManagement.createExternalApi') }}</h3>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-muted-foreground block mb-1">{{ $t('apiManagement.name') }} *</label>
              <input v-model="form.name" class="w-full px-3 py-1.5 text-sm rounded-lg border border-border/60 bg-card" />
            </div>
            <div class="flex gap-2">
              <div class="w-24">
                <label class="text-xs text-muted-foreground block mb-1">{{ $t('apiManagement.method') }} *</label>
                <select v-model="form.method" class="w-full px-2 py-1.5 text-sm rounded-lg border border-border/60 bg-card">
                  <option v-for="m in methods" :key="m" :value="m">{{ m }}</option>
                </select>
              </div>
              <div class="flex-1">
                <label class="text-xs text-muted-foreground block mb-1">{{ $t('apiManagement.path') }} *</label>
                <input v-model="form.path" class="w-full px-3 py-1.5 text-sm font-mono rounded-lg border border-border/60 bg-card" placeholder="/api/custom/endpoint" />
              </div>
            </div>
          </div>

          <div>
            <label class="text-xs text-muted-foreground block mb-1">{{ $t('apiManagement.description') }}</label>
            <textarea v-model="form.description" rows="2" class="w-full px-3 py-1.5 text-sm rounded-lg border border-border/60 bg-card" />
          </div>

          <!-- Headers -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs text-muted-foreground">{{ $t('apiManagement.headers') }}</label>
              <button @click="form.headers.push({key:'',value:'',required:false})" class="text-xs text-accent hover:underline">{{ $t('apiManagement.addHeader') }}</button>
            </div>
            <div v-for="(h, i) in form.headers" :key="'h'+i" class="flex items-center gap-2 mb-1.5">
              <input v-model="h.key" placeholder="Key" class="flex-1 px-2 py-1 text-xs rounded border border-border/60 bg-card" />
              <input v-model="h.value" placeholder="Value" class="flex-1 px-2 py-1 text-xs rounded border border-border/60 bg-card" />
              <label class="flex items-center gap-1 text-xs text-muted-foreground">
                <input type="checkbox" v-model="h.required" /> {{ $t('apiManagement.required') }}
              </label>
              <button @click="form.headers.splice(i,1)" class="text-muted-foreground hover:text-destructive">&times;</button>
            </div>
          </div>

          <!-- Params -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs text-muted-foreground">{{ $t('apiManagement.params') }}</label>
              <button @click="form.params.push({key:'',type:'string',required:false})" class="text-xs text-accent hover:underline">{{ $t('apiManagement.addParam') }}</button>
            </div>
            <div v-for="(p, i) in form.params" :key="'p'+i" class="flex items-center gap-2 mb-1.5">
              <input v-model="p.key" placeholder="Key" class="flex-1 px-2 py-1 text-xs rounded border border-border/60 bg-card" />
              <select v-model="p.type" class="w-24 px-2 py-1 text-xs rounded border border-border/60 bg-card">
                <option value="string">string</option>
                <option value="number">number</option>
                <option value="boolean">boolean</option>
              </select>
              <label class="flex items-center gap-1 text-xs text-muted-foreground">
                <input type="checkbox" v-model="p.required" /> {{ $t('apiManagement.required') }}
              </label>
              <button @click="form.params.splice(i,1)" class="text-muted-foreground hover:text-destructive">&times;</button>
            </div>
          </div>

          <!-- Script -->
          <div>
            <label class="text-xs text-muted-foreground block mb-1">{{ $t('apiManagement.script') }}</label>
            <textarea
              v-model="form.script"
              rows="12"
              class="w-full px-3 py-2 text-sm font-mono rounded-lg border border-border/60 bg-[#1e1e2e] text-[#cdd6f4]"
              spellcheck="false"
              :placeholder="`# Python script\n# Inject: request_data, request_headers, request_params\n# Output: response dict\nresponse['message'] = f'Hello {request_data.get(&quot;name&quot;, &quot;World&quot;)}'`"
            />
            <p class="text-xs text-muted-foreground mt-1">{{ $t('apiManagement.scriptHint') }}</p>
          </div>

          <!-- Enabled -->
          <label class="flex items-center gap-2 text-sm">
            <input type="checkbox" v-model="form.enabled" />
            {{ $t('apiManagement.enabled') }}
          </label>

          <div class="flex justify-end gap-2 pt-2">
            <button @click="modalOpen = false" class="px-3 py-1.5 text-sm rounded-lg border border-border/40 hover:bg-muted">{{ $t('common.cancel') }}</button>
            <button @click="save" :disabled="saving" class="px-3 py-1.5 text-sm rounded-lg bg-accent text-accent-foreground hover:opacity-90 disabled:opacity-50">{{ $t('common.save') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Test Modal -->
    <Teleport to="body">
      <div v-if="testModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="testModalOpen = false">
        <div class="bg-card rounded-xl border border-border/60 shadow-xl w-[800px] h-[500px] flex flex-col p-6 space-y-4">
          <h3 class="text-base font-semibold">{{ $t('apiManagement.testApi') }}: {{ testApi?.name }}</h3>
          <div class="flex-1 grid grid-cols-2 gap-4 min-h-0">
            <!-- Request -->
            <div class="flex flex-col">
              <label class="text-xs text-muted-foreground mb-1">{{ $t('apiManagement.testRequest') }}</label>
              <textarea
                v-model="testBody"
                rows="6"
                class="flex-1 px-3 py-2 text-sm font-mono rounded-lg border border-border/60 bg-[#1e1e2e] text-[#cdd6f4]"
                spellcheck="false"
                placeholder='{"key": "value"}'
              />
              <div class="mt-2 grid grid-cols-2 gap-2">
                <div>
                  <label class="text-xs text-muted-foreground block mb-1">Headers (JSON)</label>
                  <textarea v-model="testHeaders" rows="2" class="w-full px-3 py-1 text-xs font-mono rounded-lg border border-border/60 bg-card" placeholder='{"Authorization":"Bearer x"}' />
                </div>
                <div>
                  <label class="text-xs text-muted-foreground block mb-1">Params (JSON)</label>
                  <textarea v-model="testParams" rows="2" class="w-full px-3 py-1 text-xs font-mono rounded-lg border border-border/60 bg-card" placeholder='{"id":"123"}' />
                </div>
              </div>
              <button @click="runTest" :disabled="testing" class="mt-3 px-3 py-1.5 text-sm rounded-lg bg-accent text-accent-foreground hover:opacity-90 disabled:opacity-50 self-start">
                {{ testing ? '...' : $t('apiManagement.testApi') }}
              </button>
            </div>
            <!-- Result -->
            <div class="flex flex-col">
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs text-muted-foreground">{{ $t('apiManagement.testResult') }}</label>
                <span v-if="testDuration !== null" class="text-xs text-muted-foreground">{{ testDuration }}ms</span>
              </div>
              <pre class="flex-1 px-3 py-2 text-sm font-mono rounded-lg border border-border/60 bg-muted/20 overflow-auto whitespace-pre-wrap">{{ testResult }}</pre>
            </div>
          </div>
          <div class="flex justify-end">
            <button @click="testModalOpen = false" class="px-3 py-1.5 text-sm rounded-lg border border-border/40 hover:bg-muted">{{ $t('common.cancel') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete Confirm -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="deleteTarget = null">
        <div class="bg-card rounded-xl border border-border/60 shadow-xl p-6 max-w-sm w-full space-y-4">
          <p class="text-sm">{{ $t('apiManagement.deleteExternalConfirm', { name: deleteTarget.name, method: deleteTarget.method, path: deleteTarget.path }) }}</p>
          <div class="flex justify-end gap-2">
            <button @click="deleteTarget = null" class="px-3 py-1.5 text-sm rounded-lg border border-border/40 hover:bg-muted">{{ $t('common.cancel') }}</button>
            <button @click="doDelete" :disabled="deleting" class="px-3 py-1.5 text-sm rounded-lg bg-destructive text-destructive-foreground hover:opacity-90 disabled:opacity-50">{{ $t('common.delete') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { admin } from '@/api'
import { Plus, Pencil, Play, Trash } from 'lucide-vue-next'

const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']

const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterMethod = ref('')
const filterSearch = ref('')

// Modal state
const modalOpen = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = ref({
  name: '', method: 'POST', path: '', description: '',
  headers: [] as any[], params: [] as any[], script: '', enabled: true,
})

const testModalOpen = ref(false)
const testApi = ref<any>(null)
const testBody = ref('')
const testHeaders = ref('')
const testParams = ref('')
const testing = ref(false)
const testResult = ref('')
const testDuration = ref<number | null>(null)

const deleteTarget = ref<any>(null)
const deleting = ref(false)

const methodBadge = (m: string) => {
  const map: Record<string, string> = {
    GET: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    POST: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    PUT: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    DELETE: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    PATCH: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  }
  return map[m] || 'bg-muted text-muted-foreground'
}

const load = async () => {
  try {
    const res: any = await admin.externalApis({
      page: page.value, page_size: pageSize.value,
      method: filterMethod.value, search: filterSearch.value,
    })
    if (res?.data) {
      items.value = res.data.items || []
      total.value = res.data.total || 0
    }
  } catch (_) { /* ignore */ }
}

watch([filterMethod, filterSearch], () => { page.value = 1; load() })

const openCreate = () => {
  editingId.value = null
  form.value = { name: '', method: 'POST', path: '', description: '', headers: [], params: [], script: '', enabled: true }
  modalOpen.value = true
}

const openEdit = (api: any) => {
  editingId.value = api.id
  form.value = {
    name: api.name, method: api.method, path: api.path,
    description: api.description,
    headers: (api.headers || []).map((h: any) => ({ key: h.key || '', value: h.value || '', required: !!h.required })),
    params: (api.params || []).map((p: any) => ({ key: p.key || '', type: p.type || 'string', required: !!p.required })),
    script: api.script || '',
    enabled: api.enabled,
  }
  modalOpen.value = true
}

const save = async () => {
  saving.value = true
  try {
    const data = {
      name: form.value.name,
      method: form.value.method,
      path: form.value.path,
      description: form.value.description,
      headers: form.value.headers,
      params: form.value.params,
      script: form.value.script,
      enabled: form.value.enabled,
    }
    if (editingId.value) {
      await admin.externalApiUpdate(editingId.value, data)
    } else {
      await admin.externalApiCreate(data)
    }
    modalOpen.value = false
    load()
  } catch (_) { /* ignore */ }
  finally { saving.value = false }
}

const toggleEnabled = async (api: any) => {
  try {
    await admin.externalApiUpdate(api.id, { enabled: !api.enabled })
    api.enabled = !api.enabled
  } catch (_) { /* ignore */ }
}

const openTest = (api: any) => {
  testApi.value = api
  testBody.value = ''
  testHeaders.value = ''
  testParams.value = ''
  testResult.value = ''
  testDuration.value = null
  testModalOpen.value = true
}

const runTest = async () => {
  if (!testApi.value) return
  testing.value = true
  try {
    let headers = {}
    let params = {}
    let data = {}
    try { headers = JSON.parse(testHeaders.value) } catch {}
    try { params = JSON.parse(testParams.value) } catch {}
    try { data = JSON.parse(testBody.value) } catch {}
    const res: any = await admin.externalApiTest(testApi.value.id, { data, headers, params })
    if (res?.data) {
      testDuration.value = res.data.duration_ms
      testResult.value = JSON.stringify(res.data.result, null, 2)
    }
  } catch (e: any) {
    testResult.value = `Error: ${e?.message || e}`
  } finally { testing.value = false }
}

const confirmDelete = (api: any) => {
  deleteTarget.value = api
}

const doDelete = async () => {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await admin.externalApiDelete(deleteTarget.value.id)
    deleteTarget.value = null
    load()
  } catch (_) { /* ignore */ }
  finally { deleting.value = false }
}

onMounted(load)
</script>
