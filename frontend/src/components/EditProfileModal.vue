<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/40" @click="$emit('close')" />

    <!-- Modal -->
    <div class="relative w-full max-w-md max-h-[90vh] overflow-auto rounded-2xl shadow-xl p-6 mx-4" style="background-color: hsl(var(--card))">
      <h2 class="text-lg font-semibold mb-5">{{ t('user.editProfile') }}</h2>

      <!-- Avatar preview -->
      <div class="flex items-center gap-4 mb-5">
        <div
          class="w-16 h-16 rounded-full flex items-center justify-center text-xl font-bold select-none flex-shrink-0"
          style="background-color: hsl(var(--foreground) / 0.1); color: hsl(var(--foreground))"
        >
          {{ previewAvatarText }}
        </div>
        <div>
          <p class="text-sm font-medium">{{ authStore.displayName }}</p>
          <p class="text-xs text-muted-foreground">{{ authStore.user?.email }}</p>
        </div>
      </div>

      <!-- Profile form -->
      <div class="space-y-3 mb-5">
        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('user.nickname') }}</label>
          <input
            v-model="form.nickname"
            type="text"
            maxlength="64"
            class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
            style="background-color: hsl(var(--muted) / 0.6)"
            :placeholder="t('user.nickname')"
          />
        </div>
        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('user.avatarText') }}</label>
          <input
            v-model="form.avatar_text"
            type="text"
            maxlength="4"
            class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
            style="background-color: hsl(var(--muted) / 0.6)"
            :placeholder="t('user.avatarTextHint')"
          />
          <p class="text-xs text-muted-foreground mt-1">{{ t('user.avatarTextDesc') }}</p>
        </div>
      </div>

      <div class="border-t border-border/30 pt-4 mb-5 space-y-3">
        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('user.currentPassword') }}</label>
          <input
            v-model="form.current_password"
            type="password"
            class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
            style="background-color: hsl(var(--muted) / 0.6)"
            :placeholder="t('user.currentPassword')"
          />
        </div>
        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('user.newPassword') }} <span class="text-muted-foreground/50">({{ t('user.optional') }})</span></label>
          <input
            v-model="form.new_password"
            type="password"
            class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
            style="background-color: hsl(var(--muted) / 0.6)"
            :placeholder="t('user.newPassword')"
          />
        </div>
        <div v-if="form.new_password">
          <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('user.confirmNewPassword') }}</label>
          <input
            v-model="confirmPassword"
            type="password"
            class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
            style="background-color: hsl(var(--muted) / 0.6)"
            :placeholder="t('user.confirmNewPassword')"
          />
        </div>
      </div>

      <!-- 2FA Section -->
      <div class="border-t border-border/30 pt-4 mb-5">
        <h3 class="text-sm font-medium mb-3">{{ t('user.twoFactorAuth') }}</h3>

        <!-- Not enabled, not setting up -->
        <div v-if="!mfaEnabled && !mfaSettingUp" class="flex items-center justify-between">
          <span class="text-sm text-muted-foreground">{{ t('user.twoFactorDisabled') }}</span>
          <button
            @click="startMfaSetup"
            :disabled="mfaLoading"
            class="px-3 py-1.5 bg-accent text-accent-foreground rounded-lg text-xs font-medium hover:opacity-90 disabled:opacity-50 transition-all"
          >
            {{ t('user.enable2FA') }}
          </button>
        </div>

        <!-- Setting up MFA -->
        <div v-if="mfaSettingUp" class="space-y-3">
          <p class="text-sm text-muted-foreground">{{ t('user.scanQRCode') }}</p>
          <div class="flex justify-center">
            <canvas ref="qrCanvas" class="rounded-lg" width="180" height="180" />
          </div>
          <div>
            <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('user.enterCodeVerify') }}</label>
            <div class="flex gap-2">
              <input
                v-model="mfaCode"
                type="text"
                maxlength="6"
                class="flex-1 px-3 py-2 rounded-lg text-sm text-center tracking-[0.25em] focus:outline-none focus:ring-2 focus:ring-accent/30"
                style="background-color: hsl(var(--muted) / 0.6)"
                placeholder="000000"
                @input="mfaCode = mfaCode.replace(/\D/g, '').slice(0, 6)"
              />
              <button
                @click="confirmMfa"
                :disabled="mfaCode.length !== 6 || mfaLoading"
                class="px-4 py-2 bg-accent text-accent-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all"
              >
                {{ t('user.verify') }}
              </button>
            </div>
          </div>
          <button
            @click="cancelMfaSetup"
            class="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {{ t('common.cancel') }}
          </button>
        </div>

        <!-- Enabled -->
        <div v-if="mfaEnabled" class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-green-600 dark:text-green-400 font-medium flex items-center gap-1.5">
              <ShieldCheck class="w-4 h-4" />{{ t('user.twoFactorEnabled') }}
            </span>
            <button
              @click="showDisableMfa = true"
              class="px-3 py-1.5 rounded-lg text-xs font-medium border border-border hover:bg-muted transition-colors text-destructive"
            >
              {{ t('user.disable2FA') }}
            </button>
          </div>

          <!-- Disable form -->
          <div v-if="showDisableMfa" class="space-y-2 pt-2">
            <input
              v-model="disablePassword"
              type="password"
              class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
              style="background-color: hsl(var(--muted) / 0.6)"
              :placeholder="t('login.password')"
            />
            <div class="flex gap-2">
              <input
                v-model="disableCode"
                type="text"
                maxlength="6"
                class="flex-1 px-3 py-2 rounded-lg text-sm text-center tracking-[0.25em] focus:outline-none focus:ring-2 focus:ring-accent/30"
                style="background-color: hsl(var(--muted) / 0.6)"
                placeholder="000000"
                @input="disableCode = disableCode.replace(/\D/g, '').slice(0, 6)"
              />
              <button
                @click="disableMfa"
                :disabled="disableCode.length !== 6 || !disablePassword || mfaLoading"
                class="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all"
              >
                {{ t('user.disable2FA') }}
              </button>
            </div>
            <button
              @click="showDisableMfa = false; disablePassword = ''; disableCode = ''"
              class="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              {{ t('common.cancel') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Error -->
      <p v-if="error" class="text-destructive text-xs text-center mb-3">{{ error }}</p>
      <p v-if="success" class="text-green-600 dark:text-green-400 text-xs text-center mb-3">{{ success }}</p>

      <!-- Actions -->
      <div class="flex justify-end gap-2 pt-2 border-t border-border/30">
        <button
          @click="$emit('close')"
          class="px-4 py-2 rounded-lg text-sm font-medium border border-border hover:bg-muted transition-colors"
        >
          {{ t('common.cancel') }}
        </button>
        <button
          @click="saveProfile"
          :disabled="profileLoading"
          class="px-5 py-2 bg-accent text-accent-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all"
        >
          {{ profileLoading ? '...' : t('common.save') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { auth } from '@/api'
import { ShieldCheck } from 'lucide-vue-next'

defineEmits<{ close: [] }>()

const { t } = useI18n()
const authStore = useAuthStore()

// Profile form
const form = ref({
  nickname: authStore.user?.nickname || '',
  avatar_text: authStore.user?.avatar_text || '',
  current_password: '',
  new_password: '',
})
const confirmPassword = ref('')
const profileLoading = ref(false)
const error = ref('')
const success = ref('')

const previewAvatarText = computed(() => {
  if (form.value.avatar_text) return form.value.avatar_text.slice(0, 4)
  if (form.value.nickname) return form.value.nickname[0].toUpperCase()
  return authStore.avatarText
})

// MFA state
const mfaEnabled = ref(authStore.user?.mfa_enabled || false)
const mfaSettingUp = ref(false)
const mfaLoading = ref(false)
const mfaCode = ref('')
const mfaSecret = ref('')
const mfaProvisioningUri = ref('')
const showDisableMfa = ref(false)
const disablePassword = ref('')
const disableCode = ref('')
const qrCanvas = ref<HTMLCanvasElement | null>(null)

async function drawQr() {
  await nextTick()
  if (!qrCanvas.value || !mfaProvisioningUri.value) return
  try {
    const QRCode = (await import('qrcode')).default
    QRCode.toCanvas(qrCanvas.value, mfaProvisioningUri.value, { width: 180, margin: 2 })
  } catch (_) { /* qrcode not loaded */ }
}

async function startMfaSetup() {
  mfaLoading.value = true
  error.value = ''
  try {
    const res = await auth.mfaSetup()
    mfaSecret.value = res.data.secret
    mfaProvisioningUri.value = res.data.provisioning_uri
    mfaSettingUp.value = true
    await drawQr()
  } catch (e: any) {
    error.value = parseError(e)
  } finally {
    mfaLoading.value = false
  }
}

async function confirmMfa() {
  mfaLoading.value = true
  error.value = ''
  try {
    await auth.mfaConfirm(mfaCode.value)
    mfaEnabled.value = true
    mfaSettingUp.value = false
    mfaCode.value = ''
    mfaSecret.value = ''
    mfaProvisioningUri.value = ''
    if (authStore.user) {
      authStore.user.mfa_enabled = true
    }
    success.value = t('user.mfaEnabledSuccess')
    setTimeout(() => { success.value = '' }, 3000)
  } catch (e: any) {
    error.value = parseError(e)
  } finally {
    mfaLoading.value = false
  }
}

function cancelMfaSetup() {
  mfaSettingUp.value = false
  mfaCode.value = ''
  mfaSecret.value = ''
  mfaProvisioningUri.value = ''
}

async function disableMfa() {
  mfaLoading.value = true
  error.value = ''
  try {
    await auth.mfaDisable(disablePassword.value, disableCode.value)
    mfaEnabled.value = false
    showDisableMfa.value = false
    disablePassword.value = ''
    disableCode.value = ''
    if (authStore.user) {
      authStore.user.mfa_enabled = false
    }
    success.value = t('user.mfaDisabledSuccess')
    setTimeout(() => { success.value = '' }, 3000)
  } catch (e: any) {
    error.value = parseError(e)
  } finally {
    mfaLoading.value = false
  }
}

async function saveProfile() {
  profileLoading.value = true
  error.value = ''
  try {
    if (form.value.new_password && form.value.new_password !== confirmPassword.value) {
      error.value = t('user.passwordMismatch')
      profileLoading.value = false
      return
    }
    const data: any = {
      current_password: form.value.current_password,
    }
    if (form.value.nickname !== (authStore.user?.nickname || '')) {
      data.nickname = form.value.nickname
    }
    if (form.value.avatar_text !== (authStore.user?.avatar_text || '')) {
      data.avatar_text = form.value.avatar_text
    }
    if (form.value.new_password) {
      data.new_password = form.value.new_password
    }
    const res = await auth.profile(data)
    authStore.setUser(res.data)
    success.value = t('user.profileSaved')
    setTimeout(() => { success.value = '' }, 3000)
    form.value.current_password = ''
    form.value.new_password = ''
    confirmPassword.value = ''
  } catch (e: any) {
    error.value = parseError(e)
  } finally {
    profileLoading.value = false
  }
}

function parseError(e: any): string {
  const d = e.response?.data
  let msg = d?.message
  if (!msg && d?.detail) {
    try { const parsed = typeof d.detail === 'string' ? JSON.parse(d.detail) : d.detail; msg = parsed.message } catch (_) {}
  }
  return msg || 'Operation failed'
}
</script>
