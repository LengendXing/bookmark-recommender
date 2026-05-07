<template>
  <div class="flex h-full">
    <!-- Left sidebar: account list -->
    <aside class="w-56 flex-shrink-0 border-r border-border/50 flex flex-col" style="background-color: hsl(var(--sidebar)); color: hsl(var(--sidebar-foreground))">
      <div class="flex items-center justify-between px-4 py-3 border-b border-border/30">
        <h3 class="text-sm font-medium">{{ $t('github.accounts') }}</h3>
        <button
          @click="openAddAccount"
          class="w-6 h-6 flex items-center justify-center rounded-md hover:bg-muted/50 transition-colors"
          :title="$t('github.addAccount')"
        >+</button>
      </div>
      <div class="flex-1 overflow-auto py-1">
        <div
          v-for="acc in accounts"
          :key="acc.id"
          @click="selectAccount(acc.id)"
          :class="[
            'flex items-center gap-2.5 px-4 py-2 mx-1 rounded-lg cursor-pointer transition-colors text-sm',
            activeAccountId === acc.id
              ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 font-medium'
              : 'hover:bg-muted/50 text-muted-foreground hover:text-foreground'
          ]"
        >
          <img v-if="acc.avatar_url" :src="acc.avatar_url" class="w-5 h-5 rounded-full flex-shrink-0" />
          <span v-else class="w-5 h-5 rounded-full bg-muted flex-shrink-0" />
          <span class="truncate text-purple-600 dark:text-purple-400">{{ acc.github_login }}</span>
          <button
            @click.stop="confirmDeleteAccount(acc)"
            class="ml-auto w-5 h-5 flex items-center justify-center rounded opacity-0 hover:opacity-100 group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive transition-all"
          >&times;</button>
        </div>
        <div v-if="accounts.length === 0" class="px-4 py-8 text-center text-xs text-muted-foreground">
          {{ $t('github.noAccounts') }}
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <main class="flex-1 flex flex-col min-w-0">
      <!-- Notification banner -->
      <div
        v-if="notify"
        :class="[
          'px-4 py-2 text-sm border-b',
          notify.type === 'error' ? 'bg-destructive/10 text-destructive border-destructive/20' :
          notify.type === 'info' ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border-zinc-200 dark:border-zinc-700' :
          'bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-400 dark:border-green-800'
        ]"
      >{{ notify.msg }}</div>

      <!-- Tab bar -->
      <div v-if="activeAccountId" class="flex items-center border-b border-border/40">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="switchTab(tab.key)"
          :class="[
            'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px',
            activeTab === tab.key
              ? 'border-foreground text-foreground'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          ]"
        >{{ tab.label }}</button>
        <div class="flex-1" />
        <!-- AI buttons (shown only on Starred tab) -->
        <template v-if="activeTab === 'starred'">
          <button
            @click="doRecommend"
            :disabled="recommendRunning"
            class="h-8 px-3 mr-2 text-xs font-medium rounded-lg border border-input bg-card hover:bg-muted transition-colors disabled:opacity-50"
          >{{ recommendRunning ? '...' : $t('github.recommend') }}</button>
          <button
            @click="doAnalyze"
            :disabled="analyzeRunning"
            class="h-8 px-3 mr-3 text-xs font-medium rounded-lg bg-zinc-800 dark:bg-zinc-200 text-zinc-50 dark:text-zinc-900 hover:opacity-90 transition-opacity disabled:opacity-50"
          >{{ analyzeRunning ? '...' : $t('github.analyze') }}</button>
        </template>
      </div>

      <!-- Toolbar -->
      <div class="flex items-center gap-2 px-5 py-3 border-b border-border/40 flex-wrap">
        <!-- Starred tab toolbar -->
        <template v-if="activeTab === 'starred'">
          <select v-model="searchMode" class="h-8 px-2 text-xs rounded-lg border border-input bg-card">
            <option value="normal">{{ $t('github.searchNormal') }}</option>
            <option value="semantic">{{ $t('github.searchSemantic') }}</option>
          </select>

          <input
            v-model="searchQuery"
            :placeholder="searchMode === 'semantic' ? $t('github.semanticSearchPlaceholder') : $t('github.searchPlaceholder')"
            class="h-8 px-3 text-sm rounded-lg border border-input bg-card focus:outline-none focus:ring-1 focus:ring-ring flex-1 min-w-[160px]"
            @keyup.enter="doSearch"
          />

          <button
            @click="doSearch"
            class="h-8 px-3 text-xs font-medium rounded-lg border border-input bg-card hover:bg-muted transition-colors"
          >{{ searchMode === 'semantic' ? $t('github.searchSemantic') : $t('github.searchNormal') }}</button>

          <div class="flex-1" />

          <button
            @click="syncAccount"
            :disabled="syncing"
            class="h-8 px-3 text-xs font-medium rounded-lg border border-input bg-card hover:bg-muted transition-colors"
          >{{ syncing ? '...' : $t('github.sync') }}</button>

          <button
            @click="triggerImport"
            class="h-8 px-3 text-xs font-medium rounded-lg border border-input bg-card hover:bg-muted transition-colors"
          >{{ $t('github.import') }}</button>
          <input ref="importInput" type="file" accept=".json" class="hidden" @change="handleImportFile" />

          <button
            @click="doExport"
            class="h-8 px-3 text-xs font-medium rounded-lg border border-input bg-card hover:bg-muted transition-colors"
          >{{ $t('github.export') }}</button>
        </template>

        <!-- Recommended tab toolbar (search only) -->
        <template v-else>
          <input
            v-model="recSearch"
            placeholder="Search recommendations..."
            class="h-8 px-3 text-sm rounded-lg border border-input bg-card focus:outline-none focus:ring-1 focus:ring-ring flex-1 min-w-[160px]"
            @keyup.enter="loadRecommendations"
          />
          <button
            @click="loadRecommendations"
            class="h-8 px-3 text-xs font-medium rounded-lg border border-input bg-card hover:bg-muted transition-colors"
          >Search</button>
        </template>
      </div>

      <!-- Table -->
      <div class="flex-1 overflow-auto">
        <SkeletonTable v-if="!loaded && listLoading" :rows="5" />
        <div v-else-if="!loaded && !listLoading" class="flex items-center justify-center h-32 text-muted-foreground text-sm">
          {{ $t('github.noAccounts') }}
        </div>

        <!-- Starred repos table -->
        <template v-else-if="activeTab === 'starred'">
          <table v-if="repos.length > 0" class="w-full">
            <thead>
              <tr class="border-b border-border/40 bg-muted/30">
                <th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground w-10">#</th>
                <th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground">{{ $t('github.name') }}</th>
                <th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground hidden md:table-cell">{{ $t('github.description') }}</th>
                <th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground">{{ $t('github.language') }}</th>
                <th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground hidden lg:table-cell">{{ $t('github.aiAnalysis') }}</th>
                <th class="text-right px-4 py-2.5 text-xs font-medium text-muted-foreground">{{ $t('github.stars') }}</th>
                <th class="text-right px-4 py-2.5 text-xs font-medium text-muted-foreground w-16">-</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(repo, idx) in repos"
                :key="repo.id"
                class="border-b border-border/20 hover:bg-muted/20 transition-colors"
              >
                <td class="px-4 py-2.5 text-xs text-muted-foreground">{{ (page - 1) * pageSize + idx + 1 }}</td>
                <td class="px-4 py-2.5 text-sm">
                  <button
                    @click="openDrawer(repo.id)"
                    class="text-foreground hover:underline text-left"
                  >{{ truncateTitle(repo.repo_name) }}</button>
                  <div class="text-[10px] text-muted-foreground">{{ repo.owner }}</div>
                </td>
                <td class="px-4 py-2.5 text-sm text-muted-foreground hidden md:table-cell max-w-[200px] truncate" :title="repo.description">
                  {{ repo.description || '-' }}
                </td>
                <td class="px-4 py-2.5 text-xs">
                  <span v-if="repo.language" class="px-1.5 py-0.5 rounded bg-muted/50">{{ repo.language }}</span>
                  <span v-else class="text-muted-foreground">-</span>
                </td>
                <td class="px-4 py-2.5 text-xs hidden lg:table-cell">
                  <span v-if="repo.ai_summary" class="text-muted-foreground" :title="repo.ai_summary">{{ truncateSummary(repo.ai_summary) }}</span>
                  <span v-else class="text-muted-foreground/50 text-[11px]">{{ $t('github.notAnalyzed') }}</span>
                </td>
                <td class="px-4 py-2.5 text-sm text-right">{{ repo.stars.toLocaleString() }}</td>
                <td class="px-4 py-2.5 text-right">
                  <button
                    @click="confirmDeleteRepo(repo)"
                    class="w-7 h-7 flex items-center justify-center rounded hover:bg-destructive/10 hover:text-destructive transition-colors text-muted-foreground"
                  >&times;</button>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-else class="flex items-center justify-center h-32 text-muted-foreground text-sm">
            {{ $t('github.noRepos') }}
          </div>
        </template>

        <!-- Recommended repos table -->
        <template v-else>
          <table v-if="recommendations.length > 0" class="w-full">
            <thead>
              <tr class="border-b border-border/40 bg-muted/30">
                <th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground w-10">#</th>
                <th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground">{{ $t('github.name') }}</th>
                <th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground hidden md:table-cell">{{ $t('github.aiSummary') }}</th>
                <th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground hidden lg:table-cell">{{ $t('github.aiTags') }}</th>
                <th class="text-right px-4 py-2.5 text-xs font-medium text-muted-foreground">{{ $t('github.stars') }}</th>
                <th class="text-right px-4 py-2.5 text-xs font-medium text-muted-foreground">{{ $t('github.score') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(rec, idx) in recommendations"
                :key="rec.id"
                :class="[
                  'border-b border-border/20 hover:bg-muted/20 transition-colors',
                  !rec.is_read ? 'bg-zinc-100/50 dark:bg-zinc-800/30' : ''
                ]"
              >
                <td class="px-4 py-2.5 text-xs text-muted-foreground">{{ (recPage - 1) * recPageSize + idx + 1 }}</td>
                <td class="px-4 py-2.5 text-sm">
                  <a
                    :href="`https://github.com/${rec.repo_full_name}`"
                    target="_blank"
                    class="text-blue-600 dark:text-blue-400 hover:underline"
                  >{{ truncateTitle(rec.repo_name) }}</a>
                  <div class="text-[10px] text-muted-foreground">{{ rec.owner }}</div>
                </td>
                <td class="px-4 py-2.5 text-sm text-muted-foreground hidden md:table-cell max-w-[220px] truncate" :title="rec.ai_summary">
                  {{ rec.ai_summary || rec.description || '-' }}
                </td>
                <td class="px-4 py-2.5 text-xs hidden lg:table-cell">
                  <div class="flex flex-wrap gap-1 max-w-[200px]">
                    <span v-for="t in recTagList(rec)" :key="t" class="px-1.5 py-0.5 text-[10px] rounded bg-muted/50">{{ t }}</span>
                  </div>
                </td>
                <td class="px-4 py-2.5 text-sm text-right">{{ rec.stars.toLocaleString() }}</td>
                <td class="px-4 py-2.5 text-sm text-right text-foreground font-medium">{{ rec.score.toFixed(1) }}</td>
              </tr>
            </tbody>
          </table>

          <div v-else class="flex items-center justify-center h-32 text-muted-foreground text-sm">
            {{ $t('github.noRecommendations') }}
          </div>
        </template>
      </div>

      <!-- Pagination - Starred -->
      <div v-if="activeTab === 'starred' && repos.length > 0 && searchMode !== 'semantic'" class="flex items-center justify-between px-5 py-3 border-t border-border/40 gap-3 flex-wrap">
        <div class="flex items-center gap-1.5">
          <label class="text-xs text-muted-foreground">{{ $t('pagination.perPage') }}</label>
          <select v-model="pageSize" class="h-8 px-2 text-xs rounded-lg border border-input bg-card">
            <option v-for="n in [10, 20, 50, 100]" :key="n" :value="n">{{ n }}</option>
          </select>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-xs text-muted-foreground">{{ $t('pagination.pageOf', { current: page, total: totalPages || 1 }) }}</span>
          <div class="flex items-center gap-1">
            <input v-model="jumpPage" type="number" :min="1" :max="totalPages" class="w-14 h-8 px-2 text-xs rounded-lg border border-input bg-card text-center" :placeholder="$t('pagination.jumpTo')" @keyup.enter="goToPage" />
            <button @click="goToPage" :disabled="!jumpPage" class="h-8 px-2 text-xs font-medium rounded-lg border border-input bg-card hover:bg-muted disabled:opacity-40">GO</button>
          </div>
        </div>

        <div class="flex gap-1.5">
          <button @click="page--" :disabled="page <= 1" class="h-8 px-3 text-xs font-medium rounded-lg border border-input bg-card hover:bg-muted disabled:opacity-40">{{ $t('pagination.prev') }}</button>
          <button @click="page++" :disabled="page >= totalPages" class="h-8 px-3 text-xs font-medium rounded-lg border border-input bg-card hover:bg-muted disabled:opacity-40">{{ $t('pagination.next') }}</button>
        </div>
      </div>

      <!-- Pagination - Recommended -->
      <div v-if="activeTab === 'recommended' && recommendations.length > 0" class="flex items-center justify-between px-5 py-3 border-t border-border/40 gap-3 flex-wrap">
        <div class="flex items-center gap-1.5">
          <label class="text-xs text-muted-foreground">{{ $t('pagination.perPage') }}</label>
          <select v-model="recPageSize" class="h-8 px-2 text-xs rounded-lg border border-input bg-card">
            <option v-for="n in [10, 20, 50]" :key="n" :value="n">{{ n }}</option>
          </select>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-xs text-muted-foreground">Page {{ recPage }} / {{ recTotalPages || 1 }}</span>
        </div>

        <div class="flex gap-1.5">
          <button @click="recPage--" :disabled="recPage <= 1" class="h-8 px-3 text-xs font-medium rounded-lg border border-input bg-card hover:bg-muted disabled:opacity-40">{{ $t('pagination.prev') }}</button>
          <button @click="recPage++" :disabled="recPage >= recTotalPages" class="h-8 px-3 text-xs font-medium rounded-lg border border-input bg-card hover:bg-muted disabled:opacity-40">{{ $t('pagination.next') }}</button>
        </div>
      </div>
    </main>

    <!-- Add Account Modal -->
    <Teleport to="body">
      <div
        v-if="showAddModal"
        class="fixed inset-0 z-50 flex items-center justify-center"
        @click.self="showAddModal = false"
      >
        <div class="fixed inset-0 bg-black/60" />
        <div class="relative z-10 bg-card rounded-xl border border-border shadow-2xl w-[420px] max-h-[80vh] overflow-auto">
          <div class="flex items-center justify-between px-5 py-3">
            <h3 class="font-semibold text-sm">{{ $t('github.addAccountTitle') }}</h3>
            <button @click="showAddModal = false" class="w-6 h-6 flex items-center justify-center rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors">&times;</button>
          </div>

          <div class="flex gap-1 px-5 pt-4 pb-0">
            <button
              @click="addTab = 'oauth'"
              :class="[
                'flex-1 py-2 text-sm font-medium rounded-lg transition-colors',
                addTab === 'oauth' ? 'bg-zinc-800 dark:bg-zinc-200 text-zinc-50 dark:text-zinc-900' : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              ]"
            >{{ $t('github.oauthTab') }}</button>
            <button
              @click="addTab = 'token'"
              :class="[
                'flex-1 py-2 text-sm font-medium rounded-lg transition-colors',
                addTab === 'token' ? 'bg-zinc-800 dark:bg-zinc-200 text-zinc-50 dark:text-zinc-900' : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              ]"
            >{{ $t('github.tokenTab') }}</button>
          </div>

          <div v-if="addTab === 'oauth'" class="p-5">
            <p class="text-sm text-muted-foreground mb-4">
              OAuth requires a GitHub OAuth App configuration. Please use the Personal Token tab to add an account instead.
            </p>
            <div class="bg-muted/50 rounded-lg p-3 text-xs text-muted-foreground">
              To create a Personal Access Token, go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic). Select <code class="text-foreground">repo</code> and <code class="text-foreground">user:starred</code> scopes.
            </div>
          </div>

          <div v-if="addTab === 'token'" class="p-5 space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1.5">{{ $t('github.tokenLabel') }}</label>
              <input
                v-model="newToken"
                type="password"
                :placeholder="$t('github.tokenPlaceholder')"
                class="w-full h-9 px-3 text-sm rounded-lg border border-input bg-background focus:outline-none focus:ring-1 focus:ring-ring"
              />
              <p class="text-xs text-muted-foreground mt-1.5">{{ $t('github.tokenHint') }}</p>
            </div>
            <div v-if="addError" class="text-sm text-destructive bg-destructive/5 rounded-lg px-3 py-2">{{ addError }}</div>
            <div class="flex justify-end gap-2 pt-2">
              <button @click="showAddModal = false" class="h-9 px-4 text-sm font-medium rounded-lg border border-input bg-card hover:bg-muted">{{ $t('common.cancel') }}</button>
              <button @click="doAddAccount" :disabled="!newToken.trim() || adding" class="h-9 px-4 text-sm font-medium rounded-lg bg-zinc-800 dark:bg-zinc-200 text-zinc-50 dark:text-zinc-900 hover:opacity-90 disabled:opacity-40">{{ adding ? '...' : $t('github.save') }}</button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete account confirm dialog -->
    <Teleport to="body">
      <div
        v-if="deleteAccountTarget"
        class="fixed inset-0 z-50 flex items-center justify-center"
        @click.self="deleteAccountTarget = null"
      >
        <div class="fixed inset-0 bg-black/60" />
        <div class="relative z-10 bg-card rounded-xl border border-border shadow-2xl w-80 p-5">
          <p class="text-sm mb-4">{{ $t('github.deleteAccountConfirm', { name: deleteAccountTarget.github_login }) }}</p>
          <p class="text-xs text-muted-foreground mb-4">{{ $t('github.deleteAccountHint') }}</p>
          <div class="flex justify-end gap-2">
            <button @click="deleteAccountTarget = null" class="h-9 px-4 text-sm font-medium rounded-lg border border-input bg-card hover:bg-muted">{{ $t('common.cancel') }}</button>
            <button @click="doDeleteAccount" class="h-9 px-4 text-sm font-medium rounded-lg bg-destructive text-destructive-foreground hover:opacity-90">{{ $t('github.deleteAccount') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete repo confirm dialog -->
    <Teleport to="body">
      <div
        v-if="deleteRepo"
        class="fixed inset-0 z-50 flex items-center justify-center"
        @click.self="deleteRepo = null"
      >
        <div class="fixed inset-0 bg-black/60" />
        <div class="relative z-10 bg-card rounded-xl border border-border shadow-2xl w-80 p-5">
          <p class="text-sm mb-4">{{ $t('github.deleteRepoConfirm') }}</p>
          <div class="flex justify-end gap-2">
            <button @click="deleteRepo = null" class="h-9 px-4 text-sm font-medium rounded-lg border border-input bg-card hover:bg-muted">{{ $t('common.cancel') }}</button>
            <button @click="doDeleteRepo" class="h-9 px-4 text-sm font-medium rounded-lg bg-destructive text-destructive-foreground hover:opacity-90">{{ $t('common.delete') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Progress modal -->
    <Teleport to="body">
      <div
        v-if="progress.show"
        class="fixed inset-0 z-50 flex items-center justify-center"
      >
        <div class="fixed inset-0 bg-black/50" />
        <div class="relative z-10 bg-card rounded-xl border border-border shadow-2xl w-[400px] max-w-[90vw] p-6">
          <h3 class="font-semibold text-sm mb-4">{{ progress.title }}</h3>
          <!-- Progress bar -->
          <div class="w-full bg-muted rounded-full h-2 mb-3 overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-300"
              :class="progress.done ? 'bg-zinc-700 dark:bg-zinc-300' : 'bg-foreground'"
              :style="{ width: progress.pct + '%' }"
            />
          </div>
          <p class="text-sm text-muted-foreground mb-1">{{ progress.msg }}</p>
          <p v-if="progress.sub" class="text-xs text-muted-foreground/70 mb-3">{{ progress.sub }}</p>
          <div v-if="progress.done" class="text-xs text-green-600 mb-3">{{ progress.doneMsg }}</div>
          <button
            v-if="progress.done"
            @click="progress.show = false"
            class="w-full h-9 text-sm font-medium rounded-lg bg-zinc-800 dark:bg-zinc-200 text-zinc-50 dark:text-zinc-900 hover:opacity-90"
          >{{ $t('common.cancel') }}</button>
        </div>
      </div>
    </Teleport>

    <!-- Repo Detail Drawer -->
    <RepoDetailDrawer
      :open="drawerOpen"
      :repo-id="drawerRepoId"
      @close="drawerOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { github } from '@/api'
import SkeletonTable from '@/components/SkeletonTable.vue'
import RepoDetailDrawer from '@/components/RepoDetailDrawer.vue'

const { t } = useI18n()

// ── Tabs ────────────────────────────────────────────────────────────────────────
const tabs = [
  { key: 'starred', label: t('github.starred') },
  { key: 'recommended', label: t('github.recommended') },
]
const activeTab = ref('starred')

const switchTab = (key: string) => {
  activeTab.value = key
  if (key === 'starred') {
    loadRepos()
  } else {
    loadRecommendations()
  }
}

// ── Sidebar accounts ─────────────────────────────────────────────────────────────
const accounts = ref<any[]>([])
const activeAccountId = ref<number | null>(null)

const showAddModal = ref(false)
const addTab = ref<'oauth' | 'token'>('token')
const newToken = ref('')
const addError = ref('')
const adding = ref(false)
const deleteAccountTarget = ref<any>(null)

const loadAccounts = async () => {
  try {
    const res: any = await github.listAccounts()
    accounts.value = res.data || []
  } catch { /* ignore */ }
}

const selectAccount = (id: number) => {
  activeAccountId.value = id
  activeTab.value = 'starred'
  page.value = 1
  searchMode.value = 'normal'
  searchQuery.value = ''
  loadRepos()
}

const openAddAccount = () => {
  addTab.value = 'token'
  newToken.value = ''
  addError.value = ''
  showAddModal.value = true
}

const doAddAccount = async () => {
  if (!newToken.value.trim()) return
  adding.value = true
  addError.value = ''
  try {
    const res: any = await github.addAccount(newToken.value.trim())
    showAddModal.value = false
    newToken.value = ''
    await loadAccounts()
    const newId = res?.data?.id
    if (newId) {
      activeAccountId.value = newId
      await loadRepos()
    }
    notify.value = { type: 'success', msg: 'Account added' }
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    let msg = ''
    if (typeof detail === 'string') {
      try { msg = JSON.parse(detail).message || detail } catch { msg = detail }
    } else if (detail?.message) {
      msg = detail.message
    }
    addError.value = msg || e?.response?.data?.message || e?.message || 'Failed to add account'
  } finally {
    adding.value = false
  }
}

const confirmDeleteAccount = (acc: any) => {
  deleteAccountTarget.value = acc
}

const doDeleteAccount = async () => {
  const acc = deleteAccountTarget.value
  if (!acc) return
  try {
    await github.deleteAccount(acc.id)
    if (activeAccountId.value === acc.id) activeAccountId.value = null
    deleteAccountTarget.value = null
    await loadAccounts()
    if (activeAccountId.value === null) repos.value = []
  } catch { /* ignore */ }
}

// ── Starred repos ────────────────────────────────────────────────────────────────
const repos = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const searchMode = ref<'normal' | 'semantic'>('normal')
const searchQuery = ref('')
const loaded = ref(false)
const listLoading = ref(true)
const syncing = ref(false)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const jumpPage = ref('')

const goToPage = () => {
  const n = Number(jumpPage.value)
  if (!n || n < 1 || n > totalPages.value) return
  page.value = n
  jumpPage.value = ''
}

watch(pageSize, () => { page.value = 1; loadRepos() })

const loadRepos = async () => {
  if (searchMode.value === 'semantic' && searchQuery.value.trim()) {
    await doSemanticSearch()
    return
  }
  listLoading.value = true
  try {
    const res: any = await github.listRepos({
      q: searchQuery.value,
      page: page.value,
      page_size: pageSize.value,
    })
    repos.value = res.data?.items || []
    total.value = res.data?.total || 0
    loaded.value = true
  } catch { /* ignore */ }
  listLoading.value = false
}

const doSearch = () => {
  page.value = 1
  if (searchMode.value === 'semantic') {
    doSemanticSearch()
  } else {
    loadRepos()
  }
}

const doSemanticSearch = async () => {
  if (!searchQuery.value.trim()) {
    loadRepos()
    return
  }
  listLoading.value = true
  try {
    const res: any = await github.semanticSearch(searchQuery.value.trim())
    repos.value = res.data?.items || []
    total.value = res.data?.total || 0
    loaded.value = true
  } catch { /* ignore */ }
  listLoading.value = false
}

const syncAccount = async () => {
  if (!activeAccountId.value || syncing.value) return
  syncing.value = true
  try {
    const res: any = await github.syncAccount(activeAccountId.value)
    notify.value = { type: 'success', msg: t('github.syncSuccess', { count: res.data?.imported || 0 }) }
    await loadRepos()
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    let msg = ''
    if (typeof detail === 'string') {
      try { msg = JSON.parse(detail).message || detail } catch { msg = detail }
    } else if (detail?.message) {
      msg = detail.message
    }
    notify.value = { type: 'error', msg: msg || e?.response?.data?.message || 'Sync failed' }
  }
  syncing.value = false
}

// ── AI Analyze ───────────────────────────────────────────────────────────────────
const analyzeRunning = ref(false)
let analyzeTimer: ReturnType<typeof setInterval> | null = null

const doAnalyze = async () => {
  if (analyzeRunning.value) return
  analyzeRunning.value = true
  progress.value = { show: true, title: t('github.analyzing'), msg: 'Starting...', sub: '', pct: 0, done: false, doneMsg: '' }
  try {
    await github.analyzeAll()
    analyzeTimer = setInterval(pollAnalyzeProgress, 1500)
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    notify.value = { type: 'error', msg: typeof detail === 'string' ? detail : 'Analysis failed' }
    analyzeRunning.value = false
    progress.value.show = false
  }
}

const pollAnalyzeProgress = async () => {
  try {
    const res: any = await github.analyzeProgress()
    const d = res.data
    const pct = d.total > 0 ? Math.round((d.current / d.total) * 100) : 0
    progress.value = {
      show: true,
      title: t('github.analyzing'),
      msg: `${t('github.analyzeProgress', { current: d.current, total: d.total })}`,
      sub: d.message || '',
      pct,
      done: d.status === 'done',
      doneMsg: d.status === 'done' ? t('github.analyzeComplete', { count: d.total }) : '',
    }
    if (d.status === 'done') {
      if (analyzeTimer) { clearInterval(analyzeTimer); analyzeTimer = null }
      analyzeRunning.value = false
      loadRepos()
    }
  } catch {
    if (analyzeTimer) { clearInterval(analyzeTimer); analyzeTimer = null }
    analyzeRunning.value = false
    progress.value.show = false
  }
}

// ── AI Recommend ─────────────────────────────────────────────────────────────────
const recommendRunning = ref(false)
let recommendTimer: ReturnType<typeof setInterval> | null = null

const doRecommend = async () => {
  if (recommendRunning.value) return
  recommendRunning.value = true
  progress.value = { show: true, title: t('github.recommending'), msg: 'Starting...', sub: '', pct: 0, done: false, doneMsg: '' }
  try {
    await github.generateRecommendations({ top_k_tags: 3 })
    recommendTimer = setInterval(pollRecommendProgress, 1500)
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    notify.value = { type: 'error', msg: typeof detail === 'string' ? detail : 'Recommendation failed' }
    recommendRunning.value = false
    progress.value.show = false
  }
}

const pollRecommendProgress = async () => {
  try {
    const res: any = await github.recommendationsProgress()
    const d = res.data
    const pct = d.total > 0 ? Math.round((d.current / d.total) * 100) : 0
    progress.value = {
      show: true,
      title: t('github.recommending'),
      msg: `${t('github.recommendProgress', { current: d.current, total: d.total })}`,
      sub: d.message || '',
      pct,
      done: d.status === 'done',
      doneMsg: d.status === 'done' ? t('github.recommendComplete', { count: d.found_repos?.length || 0 }) : '',
    }
    if (d.status === 'done') {
      if (recommendTimer) { clearInterval(recommendTimer); recommendTimer = null }
      recommendRunning.value = false
    }
  } catch {
    if (recommendTimer) { clearInterval(recommendTimer); recommendTimer = null }
    recommendRunning.value = false
    progress.value.show = false
  }
}

// ── Recommendations ──────────────────────────────────────────────────────────────
const recommendations = ref<any[]>([])
const recTotal = ref(0)
const recPage = ref(1)
const recPageSize = ref(20)
const recSearch = ref('')

const recTotalPages = computed(() => Math.max(1, Math.ceil(recTotal.value / recPageSize.value)))

watch(recPageSize, () => { recPage.value = 1; loadRecommendations() })

const loadRecommendations = async () => {
  if (activeTab.value !== 'recommended') return
  listLoading.value = true
  try {
    const res: any = await github.listRecommendations({
      page: recPage.value,
      page_size: recPageSize.value,
    })
    recommendations.value = res.data?.items || []
    recTotal.value = res.data?.total || 0
    loaded.value = true
  } catch { /* ignore */ }
  listLoading.value = false
}

const recTagList = (rec: any) => {
  if (!rec.ai_tags) return []
  const raw = rec.ai_tags
  if (raw.startsWith('[')) {
    try { return JSON.parse(raw) } catch { return [] }
  }
  return raw.split(',').map((t: string) => t.trim()).filter(Boolean).slice(0, 4)
}

// ── Import / Export ───────────────────────────────────────────────────────────────
const importInput = ref<HTMLInputElement | null>(null)

const triggerImport = () => {
  importInput.value?.click()
}

const handleImportFile = async (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  try {
    const res: any = await github.importJson(activeAccountId.value || 0, file)
    notify.value = { type: 'success', msg: t('github.importSuccess', { imported: res.data?.imported || 0, skipped: res.data?.skipped || 0 }) }
    loadRepos()
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    let msg = ''
    if (typeof detail === 'string') {
      try { msg = JSON.parse(detail).message || detail } catch { msg = detail }
    } else if (detail?.message) {
      msg = detail.message
    }
    notify.value = { type: 'error', msg: msg || e?.response?.data?.message || 'Import failed' }
  }
  if (importInput.value) importInput.value.value = ''
}

const doExport = async () => {
  try {
    const res: any = await github.exportJson()
    const blob = res.data || res
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'starred_repos.json'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    notify.value = { type: 'error', msg: 'Export failed' }
  }
}

// ── Progress ─────────────────────────────────────────────────────────────────────
const progress = ref<{
  show: boolean
  title: string
  msg: string
  sub: string
  pct: number
  done: boolean
  doneMsg: string
}>({ show: false, title: '', msg: '', sub: '', pct: 0, done: false, doneMsg: '' })

// ── Drawer ────────────────────────────────────────────────────────────────────────
const drawerOpen = ref(false)
const drawerRepoId = ref<number | null>(null)

const openDrawer = (repoId: number) => {
  drawerRepoId.value = repoId
  drawerOpen.value = true
}

// ── Notification ──────────────────────────────────────────────────────────────────
const notify = ref<{ type: string; msg: string } | null>(null)
watch(notify, (val) => {
  if (val) setTimeout(() => { notify.value = null }, 3000)
})

// ── Delete repo ───────────────────────────────────────────────────────────────────
const deleteRepo = ref<any>(null)

const confirmDeleteRepo = (repo: any) => {
  deleteRepo.value = repo
}

const doDeleteRepo = async () => {
  if (!deleteRepo.value) return
  try {
    await github.deleteRepo(deleteRepo.value.id)
    repos.value = repos.value.filter((r: any) => r.id !== deleteRepo.value.id)
    total.value--
    deleteRepo.value = null
  } catch { /* ignore */ }
}

// ── Utils ─────────────────────────────────────────────────────────────────────────
const truncateTitle = (s: string) => {
  if (!s) return ''
  const hasCJK = /[一-鿿]/.test(s)
  if (hasCJK) return s.length > 12 ? s.slice(0, 12) + '...' : s
  return s.length > 25 ? s.slice(0, 25) + '...' : s
}

const truncateSummary = (s: string) => {
  if (!s) return ''
  return s.length > 30 ? s.slice(0, 30) + '...' : s
}

// ── Init ──────────────────────────────────────────────────────────────────────────
onMounted(async () => {
  await loadAccounts()
  listLoading.value = false
  if (accounts.value.length === 0) {
    loaded.value = false
  } else {
    activeAccountId.value = accounts.value[0].id
    await loadRepos()
  }
})

onUnmounted(() => {
  if (analyzeTimer) clearInterval(analyzeTimer)
  if (recommendTimer) clearInterval(recommendTimer)
})
</script>
