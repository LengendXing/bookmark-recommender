<template>
  <div class="flex h-[calc(100vh-4rem)]">
    <!-- Collections Sidebar -->
    <aside class="w-56 flex-shrink-0 border-r border-border/50 flex flex-col" style="background-color: hsl(var(--card))">
      <div class="flex items-center justify-between px-4 py-3 border-b border-border/50">
        <h3 class="text-sm font-semibold text-muted-foreground">{{ t('collections.title') }}</h3>
        <button
          @click="openCollectionCreate"
          class="w-6 h-6 flex items-center justify-center rounded-lg hover:bg-muted transition-colors"
        >
          <Plus class="w-3.5 h-3.5 text-muted-foreground" />
        </button>
      </div>
      <div class="flex-1 overflow-y-auto py-1">
        <!-- All Bookmarks -->
        <button
          @click="selectCollection(null)"
          class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm transition-colors hover:bg-muted/50"
          :class="selectedCollectionId === null ? 'bg-accent/10 text-accent font-medium' : 'text-muted-foreground'"
        >
          <Folder class="w-4 h-4 flex-shrink-0" />
          <span class="truncate">{{ t('collections.allBookmarks') }}</span>
        </button>
        <!-- Collection Items -->
        <button
          v-for="col in collections"
          :key="col.id"
          @click="selectCollection(col.id)"
          class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm transition-colors hover:bg-muted/50 group relative"
          :class="selectedCollectionId === col.id ? 'bg-accent/10 text-accent font-medium' : 'text-muted-foreground'"
        >
          <Folder class="w-4 h-4 flex-shrink-0" />
          <span class="truncate flex-1 text-left">{{ col.name }}</span>
          <span class="text-xs text-muted-foreground/60">{{ col.bookmark_count }}</span>
          <!-- Hover Actions -->
          <div class="hidden group-hover:flex absolute right-2 top-1/2 -translate-y-1/2 gap-0.5 bg-card/90 backdrop-blur rounded-lg px-0.5 py-0.5">
            <button @click.stop="openCollectionEdit(col)" class="w-5 h-5 flex items-center justify-center rounded hover:bg-muted transition-colors">
              <Pencil class="w-3 h-3 text-muted-foreground" />
            </button>
            <button @click.stop="handleCollectionDelete(col.id)" class="w-5 h-5 flex items-center justify-center rounded hover:bg-destructive/10 transition-colors">
              <Trash2 class="w-3 h-3 text-destructive/70" />
            </button>
          </div>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 overflow-auto p-6 lg:p-8">
      <h2 class="text-xl font-semibold tracking-tight mb-6">{{ t('bookmarks.title') }}</h2>

      <!-- Toolbar -->
      <div class="flex flex-wrap items-end gap-3 mb-6">
        <div class="flex-1 min-w-0 max-w-sm">
          <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.search') }}</label>
          <div class="flex gap-1.5">
            <select
              v-model="searchMode"
              class="px-2.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 flex-shrink-0"
              style="background-color: hsl(var(--muted) / 0.6)"
            >
              <option value="normal">{{ t('bookmarks.searchNormal') }}</option>
              <option value="semantic">{{ t('bookmarks.searchSemantic') }}</option>
            </select>
            <div class="relative flex-1">
              <Search v-if="searchMode === 'normal'" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground/50" />
              <Sparkles v-else class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-accent/60" />
              <input
                v-model="searchQuery"
                :placeholder="searchMode === 'normal' ? t('bookmarks.search') : t('bookmarks.semanticPlaceholder')"
                @keyup.enter="searchMode === 'semantic' && handleSemanticSearch()"
                class="w-full pl-9 pr-3 py-2 rounded-xl text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent/30"
                style="background-color: hsl(var(--muted) / 0.6)"
              />
            </div>
          </div>
        </div>
        <button
          v-if="searchMode === 'semantic'"
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
        <button
          @click="showAddModal = true"
          class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 hover:opacity-90 active:scale-[0.98]"
          style="background-color: hsl(var(--muted) / 0.6); color: hsl(var(--foreground))"
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
        <button
          v-if="!analyzeLoading"
          @click="handleAnalyzeAll"
          class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 hover:opacity-90 active:scale-[0.98]"
          style="background-color: hsl(var(--muted) / 0.6); color: hsl(var(--foreground))"
        >
          <Sparkles class="w-4 h-4" />
          {{ t('bookmarks.analyzeAll') }}
        </button>
        <div
          v-else
          class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium min-w-[140px]"
          style="background-color: hsl(var(--muted) / 0.6); color: hsl(var(--foreground))"
        >
          <Sparkles class="w-4 h-4 flex-shrink-0" />
          <div class="flex-1 h-2 rounded-full overflow-hidden" style="background-color: hsl(var(--muted))">
            <div
              class="h-full transition-all duration-300 rounded-full"
              style="background-color: hsl(var(--accent))"
              :style="{ width: analyzePercent + '%' }"
            ></div>
          </div>
          <span class="text-xs flex-shrink-0">{{ analyzeProgress.completed }}/{{ analyzeProgress.total }}</span>
        </div>
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

      <!-- Collection CRUD Modal -->
      <div
        v-if="showCollectionModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
        @click.self="closeCollectionModal"
      >
        <div class="rounded-2xl p-6 w-full max-w-sm mx-4 shadow-xl" style="background-color: hsl(var(--card))">
          <h3 class="text-lg font-semibold mb-4">{{ editingCollection ? t('collections.edit') : t('collections.create') }}</h3>
          <form @submit.prevent="handleCollectionSave" class="space-y-4">
            <div>
              <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('collections.name') }}</label>
              <input v-model="collectionForm.name" type="text" required class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
            </div>
            <div>
              <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('collections.description') }}</label>
              <input v-model="collectionForm.description" type="text" class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
            </div>
            <div class="flex gap-3 pt-2">
              <button type="button" @click="closeCollectionModal" class="flex-1 py-2 rounded-xl text-sm font-medium border border-border/50 hover:bg-muted transition-colors">{{ t('common.cancel') }}</button>
              <button type="submit" :disabled="collectionLoading" class="flex-1 py-2 bg-accent text-accent-foreground rounded-xl text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all">{{ collectionLoading ? '...' : t('common.save') }}</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Move to Collection Modal -->
      <div
        v-if="showMoveModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
        @click.self="showMoveModal = false"
      >
        <div class="rounded-2xl p-6 w-full max-w-xs mx-4 shadow-xl" style="background-color: hsl(var(--card))">
          <h3 class="text-lg font-semibold mb-4">{{ t('collections.moveTo') }}</h3>
          <div class="space-y-2 max-h-60 overflow-y-auto">
            <button
              @click="handleMoveFromModal(null)"
              class="w-full text-left px-4 py-2.5 rounded-xl text-sm transition-colors flex items-center gap-3"
              :class="movingBookmark?.collectionId === null ? 'bg-accent/10 text-accent font-medium' : 'text-muted-foreground hover:bg-muted/50'"
            >
              <Folder class="w-4 h-4 flex-shrink-0" />
              <span>{{ t('collections.noCollection') }}</span>
            </button>
            <button
              v-for="col in collections"
              :key="col.id"
              @click="handleMoveFromModal(col.id)"
              class="w-full text-left px-4 py-2.5 rounded-xl text-sm transition-colors flex items-center gap-3"
              :class="movingBookmark?.collectionId === col.id ? 'bg-accent/10 text-accent font-medium' : 'text-muted-foreground hover:bg-muted/50'"
            >
              <Folder class="w-4 h-4 flex-shrink-0" />
              <span class="flex-1 truncate">{{ col.name }}</span>
              <span class="text-xs text-muted-foreground/50">{{ col.bookmark_count }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Edit Bookmark Modal -->
      <div
        v-if="showEditModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
        @click.self="showEditModal = false"
      >
        <div class="rounded-2xl p-6 w-full max-w-md mx-4 shadow-xl" style="background-color: hsl(var(--card))">
          <h3 class="text-lg font-semibold mb-4">{{ t('bookmarks.edit') }}</h3>
          <form @submit.prevent="handleEditSave" class="space-y-4">
            <div>
              <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.url') }}</label>
              <input v-model="editForm.url" type="url" required class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
            </div>
            <div>
              <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.titleLabel') }}</label>
              <input v-model="editForm.title" type="text" required class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
            </div>
            <div>
              <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.description') }}</label>
              <input v-model="editForm.description" type="text" class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.author') }}</label>
                <input v-model="editForm.author" type="text" class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
              </div>
              <div>
                <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.category') }}</label>
                <input v-model="editForm.category" type="text" class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
              </div>
            </div>
            <div>
              <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('bookmarks.tags') }}</label>
              <input v-model="editForm.tagsStr" :placeholder="t('bookmarks.tagsHint')" type="text" class="w-full px-3.5 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30" style="background-color: hsl(var(--muted) / 0.6)" />
            </div>
            <div class="flex gap-3 pt-2">
              <button type="button" @click="showEditModal = false" class="flex-1 py-2 rounded-xl text-sm font-medium border border-border/50 hover:bg-muted transition-colors">{{ t('common.cancel') }}</button>
              <button type="submit" :disabled="editLoading" class="flex-1 py-2 bg-accent text-accent-foreground rounded-xl text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all">{{ editLoading ? '...' : t('common.save') }}</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Semantic Error -->
      <div v-if="semanticError" class="mb-4 px-4 py-3 rounded-xl text-sm font-medium" style="background-color: hsl(var(--destructive) / 0.08); color: hsl(var(--destructive))">
        {{ semanticError }}
      </div>

      <!-- Analyze Result -->
      <div v-if="analyzeMsg" class="mb-4 px-4 py-3 rounded-xl text-sm font-medium" :style="analyzeMsg.includes('failed') ? 'background-color: hsl(var(--destructive) / 0.08); color: hsl(var(--destructive))' : 'background-color: hsl(var(--success) / 0.08); color: hsl(var(--success))'">
        {{ analyzeMsg }}
      </div>

      <!-- Table Skeleton -->
      <div v-if="listLoading" class="space-y-2">
        <SkeletonTable :rows="8" />
      </div>

      <!-- Table -->
      <div v-else class="rounded-xl overflow-hidden" style="background-color: hsl(var(--card)); box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.04)">
        <table class="w-full text-sm">
          <thead>
            <tr style="background-color: hsl(var(--muted) / 0.4)">
              <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase" style="width: 4em">#</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase" style="max-width: 8em">Title</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden md:table-cell">{{ t('bookmarks.tags') }}</th>
              <th v-if="semanticMode" class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden sm:table-cell w-20">{{ t('bookmarks.relevance') }}</th>
              <th v-else class="px-4 py-3 text-left text-xs font-semibold text-muted-foreground tracking-wide uppercase hidden sm:table-cell w-20">Rating</th>
              <th class="px-4 py-3 text-center text-xs font-semibold text-muted-foreground tracking-wide uppercase w-14"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="bm in displayItems" :key="bm.id" class="border-t border-border/50 hover:bg-muted/30 transition-colors">
              <td class="px-4 py-3 text-muted-foreground text-xs whitespace-nowrap">{{ bm.id }}</td>
              <td class="px-4 py-3">
                <button @click="openDrawer(bm.id)" class="font-medium hover:text-accent transition-colors text-left block whitespace-nowrap" :title="bm.title">{{ truncateTitle(bm.title) }}</button>
                <p class="text-xs text-muted-foreground whitespace-nowrap mt-0.5" :title="bm.description" v-if="bm.description">{{ truncateTitle(bm.description) }}</p>
              </td>
              <td class="px-4 py-3 hidden md:table-cell">
                <div class="flex flex-wrap gap-1 max-w-[160px]">
                  <span v-for="tag in (bm.tags || [])" :key="tag" class="inline-block px-2 py-0.5 rounded-lg text-xs font-medium truncate max-w-[120px]" style="background-color: hsl(var(--accent) / 0.08); color: hsl(var(--accent))">{{ tag }}</span>
                </div>
              </td>
              <td v-if="semanticMode" class="px-4 py-3 hidden sm:table-cell">
                <span class="inline-block px-2 py-0.5 rounded-lg text-xs font-medium" :style="{ backgroundColor: `hsl(var(--accent) / ${(bm.score || 0) * 0.12})`, color: 'hsl(var(--accent))' }">{{ ((bm.score || 0) * 100).toFixed(0) }}%</span>
              </td>
              <td v-else class="px-4 py-3 hidden sm:table-cell font-medium">{{ bm.rating }}</td>
              <td class="px-4 py-3 text-center relative">
                <button
                  data-menu-toggle
                  @click.stop="toggleMenu(bm.id)"
                  class="w-7 h-7 inline-flex items-center justify-center rounded-lg hover:bg-muted transition-colors"
                >
                  <MoreVertical class="w-4 h-4 text-muted-foreground" />
                </button>
                <!-- Dropdown Menu -->
                <div
                  v-if="openMenuId === bm.id"
                  data-menu-dropdown
                  class="absolute right-2 top-full mt-1 z-40 min-w-[140px] rounded-xl py-1.5 shadow-lg border border-border/50"
                  style="background-color: hsl(var(--card))"
                  @click.stop
                >
                  <button
                    @click="openMoveModal(bm.id, bm.collection_id); openMenuId = null"
                    class="w-full text-left px-4 py-2 text-sm text-muted-foreground hover:bg-muted/50 transition-colors flex items-center gap-2"
                  >
                    <Folder class="w-3.5 h-3.5" />
                    {{ t('collections.moveTo') }}
                  </button>
                  <button
                    @click="openEditBookmark(bm); openMenuId = null"
                    class="w-full text-left px-4 py-2 text-sm text-muted-foreground hover:bg-muted/50 transition-colors flex items-center gap-2"
                  >
                    <Pencil class="w-3.5 h-3.5" />
                    {{ t('bookmarks.edit') }}
                  </button>
                  <button
                    @click="handleDelete(bm.id); openMenuId = null"
                    class="w-full text-left px-4 py-2 text-sm text-muted-foreground hover:bg-destructive/5 hover:text-destructive transition-colors flex items-center gap-2"
                  >
                    <Trash2 class="w-3.5 h-3.5" />
                    {{ t('bookmarks.delete') }}
                  </button>
                </div>
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
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { bookmarks, collections as collectionsApi, recommend } from '@/api'
import { Search, Plus, Upload, FileDown, Trash2, Bookmark, Sparkles, Folder, Pencil, MoreVertical } from 'lucide-vue-next'
import BookmarkDrawer from '@/components/BookmarkDrawer.vue'
import SkeletonTable from '@/components/SkeletonTable.vue'

const { t } = useI18n()
const listLoading = ref(true)
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const searchQuery = ref('')
const searchMode = ref<'normal' | 'semantic'>('normal')
const error = ref('')

// Collections
const collections = ref<any[]>([])
const selectedCollectionId = ref<number | null>(null)
const showCollectionModal = ref(false)
const editingCollection = ref<any>(null)
const collectionLoading = ref(false)
const collectionForm = ref({ name: '', description: '' })

// Kebab menu
const openMenuId = ref<number | null>(null)

const toggleMenu = (id: number) => {
  openMenuId.value = openMenuId.value === id ? null : id
}

// Move modal
const showMoveModal = ref(false)
const movingBookmark = ref<{ id: number; collectionId: number | null } | null>(null)

const openMoveModal = (bookmarkId: number, collectionId: number | null) => {
  movingBookmark.value = { id: bookmarkId, collectionId }
  showMoveModal.value = true
}

const handleMoveFromModal = async (colId: number | null) => {
  if (!movingBookmark.value) return
  try {
    await bookmarks.move(movingBookmark.value.id, colId)
    showMoveModal.value = false
    movingBookmark.value = null
    load()
    loadCollections()
  } catch (_) {}
}

// Edit modal
const showEditModal = ref(false)
const editLoading = ref(false)
const editForm = ref({ id: 0, url: '', title: '', description: '', author: '', category: '', tagsStr: '' })

const openEditBookmark = (bm: any) => {
  editForm.value = {
    id: bm.id,
    url: bm.url || '',
    title: bm.title || '',
    description: bm.description || '',
    author: bm.author || '',
    category: bm.category || '',
    tagsStr: (bm.tags || []).join(', '),
  }
  showEditModal.value = true
}

const handleEditSave = async () => {
  editLoading.value = true
  try {
    const tags = editForm.value.tagsStr.split(',').map((s: string) => s.trim()).filter(Boolean)
    await bookmarks.update(editForm.value.id, {
      url: editForm.value.url,
      title: editForm.value.title,
      description: editForm.value.description || undefined,
      author: editForm.value.author || undefined,
      category: editForm.value.category || undefined,
      tags,
    })
    showEditModal.value = false
    load()
  } catch (_) {} finally {
    editLoading.value = false
  }
}

const loadCollections = async () => {
  try {
    const res = await collectionsApi.list()
    collections.value = res.data || []
  } catch (_) {}
}

const selectCollection = (colId: number | null) => {
  selectedCollectionId.value = colId
  page.value = 1
  load()
}

const openCollectionCreate = () => {
  editingCollection.value = null
  collectionForm.value = { name: '', description: '' }
  showCollectionModal.value = true
}

const openCollectionEdit = (col: any) => {
  editingCollection.value = col
  collectionForm.value = { name: col.name, description: col.description }
  showCollectionModal.value = true
}

const closeCollectionModal = () => {
  showCollectionModal.value = false
  editingCollection.value = null
}

const handleCollectionSave = async () => {
  collectionLoading.value = true
  try {
    if (editingCollection.value) {
      await collectionsApi.update(editingCollection.value.id, collectionForm.value)
    } else {
      await collectionsApi.create(collectionForm.value)
    }
    closeCollectionModal()
    loadCollections()
  } catch (_) {} finally {
    collectionLoading.value = false
  }
}

const handleCollectionDelete = async (colId: number) => {
  if (!confirm(t('collections.deleteConfirm'))) return
  try {
    await collectionsApi.delete(colId)
    if (selectedCollectionId.value === colId) {
      selectedCollectionId.value = null
    }
    loadCollections()
    load()
  } catch (_) {}
}

const truncateTitle = (text: string): string => {
  if (!text) return ''
  const hasCJK = /[一-鿿㐀-䶿]/.test(text)
  if (hasCJK) {
    return [...text].length <= 6 ? text : [...text].slice(0, 6).join('') + '...'
  }
  const words = text.split(/\s+/)
  if (words.length <= 2) {
    return text.length <= 25 ? text : text.slice(0, 25) + '...'
  }
  return words.slice(0, 2).join(' ') + '...'
}

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
const semanticLoading = ref(false)
const semanticResults = ref<any[]>([])
const semanticError = ref('')

const analyzeLoading = ref(false)
const analyzeMsg = ref('')
const analyzeProgress = ref({ total: 0, completed: 0, running: false })
const analyzePercent = computed(() => {
  if (!analyzeProgress.value.total) return 0
  return Math.round((analyzeProgress.value.completed / analyzeProgress.value.total) * 100)
})
let _pollTimer: ReturnType<typeof setInterval> | null = null

const handleSemanticSearch = async () => {
  if (!searchQuery.value.trim()) return
  semanticLoading.value = true
  semanticError.value = ''
  try {
    const res = await recommend.search(searchQuery.value, 20)
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
  searchQuery.value = ''
  semanticResults.value = []
  load()
}

const handleAnalyzeAll = async () => {
  analyzeLoading.value = true
  analyzeMsg.value = ''
  try {
    await bookmarks.analyzeAll()
    _pollTimer = setInterval(async () => {
      try {
        const res = await bookmarks.analyzeProgress()
        const p = res.data
        analyzeProgress.value = p
        if (!p.running) {
          clearInterval(_pollTimer!)
          _pollTimer = null
          analyzeLoading.value = false
          if (p.error) {
            analyzeMsg.value = `Analysis failed: ${p.error}`
          } else {
            analyzeMsg.value = `AI analysis complete: ${p.completed} bookmarks updated`
          }
          load()
        }
      } catch (_) {
        clearInterval(_pollTimer!)
        _pollTimer = null
        analyzeLoading.value = false
        analyzeMsg.value = 'Failed to check progress'
      }
    }, 800)
  } catch (e: any) {
    analyzeLoading.value = false
    analyzeMsg.value = e.response?.data?.message || 'Analysis failed'
  }
}

const displayItems = computed(() => semanticMode.value ? semanticResults.value : items.value)

const load = async () => {
  listLoading.value = true
  error.value = ''
  try {
    const params: any = { page: page.value, page_size: pageSize, search: searchQuery.value }
    if (selectedCollectionId.value !== null) {
      params.collection_id = selectedCollectionId.value
    }
    const res = await bookmarks.list(params)
    items.value = res.data.items
    total.value = res.data.total
  } catch (e: any) {
    error.value = e.response?.data?.message || 'Failed to load'
  } finally {
    listLoading.value = false
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

const closeMenu = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('[data-menu-toggle]') && !target.closest('[data-menu-dropdown]')) {
    openMenuId.value = null
  }
}

watch(searchQuery, () => {
  if (searchMode.value === 'normal') { page.value = 1; load() }
})
watch(searchMode, () => {
  if (semanticMode.value) clearSemanticSearch()
})
watch(page, () => load())
onMounted(() => { load(); loadCollections(); document.addEventListener('click', closeMenu) })
onUnmounted(() => {
  document.removeEventListener('click', closeMenu)
  if (_pollTimer) clearInterval(_pollTimer)
})
</script>
