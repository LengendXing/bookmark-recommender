<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/40" @click="$emit('close')" />

    <!-- Modal -->
    <div class="relative w-full max-w-md max-h-[90vh] overflow-auto rounded-2xl shadow-xl p-6 mx-4" style="background-color: hsl(var(--card))">
      <!-- Avatar + user info (always visible) -->
      <div class="flex items-center gap-4 mb-5">
        <div
          class="w-14 h-14 rounded-full flex items-center justify-center text-lg font-bold select-none flex-shrink-0"
          style="background-color: hsl(var(--foreground) / 0.1); color: hsl(var(--foreground))"
        >
          {{ previewAvatarText }}
        </div>
        <div>
          <p class="text-sm font-medium">{{ authStore.displayName }}</p>
          <p class="text-xs text-muted-foreground">{{ authStore.user?.email }}</p>
        </div>
      </div>

      <!-- Tab bar -->
      <div class="flex border-b border-border/30 mb-5">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          :class="[
            'flex-1 pb-2.5 text-sm font-medium transition-colors relative',
            activeTab === tab.key ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'
          ]"
        >
          <component :is="tab.icon" class="w-3.5 h-3.5 inline mr-1.5" />
          {{ t(tab.label) }}
          <div
            v-if="activeTab === tab.key"
            class="absolute bottom-0 left-1/4 right-1/4 h-0.5 rounded-full"
            style="background-color: hsl(var(--foreground) / 0.8)"
          />
        </button>
      </div>

      <!-- Error / Success -->
      <p v-if="error" class="text-destructive text-xs text-center mb-3">{{ error }}</p>
      <p v-if="success" class="text-green-600 dark:text-green-400 text-xs text-center mb-3">{{ success }}</p>

      <!-- Tab: Basic Info -->
      <div v-show="activeTab === 'basic'" class="space-y-3">
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

        <div class="flex justify-end gap-2 pt-3">
          <button
            @click="$emit('close')"
            class="px-4 py-2 rounded-lg text-sm font-medium border border-border hover:bg-muted transition-colors"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            @click="saveBasicInfo"
            :disabled="profileLoading"
            class="px-5 py-2 bg-accent text-accent-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all"
          >
            {{ profileLoading ? '...' : t('common.save') }}
          </button>
        </div>
      </div>

      <!-- Tab: Security -->
      <div v-show="activeTab === 'security'" class="space-y-3">
        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('user.currentPassword') }}</label>
          <input
            v-model="securityForm.current_password"
            type="password"
            class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
            style="background-color: hsl(var(--muted) / 0.6)"
            :placeholder="t('user.currentPassword')"
          />
        </div>
        <div>
          <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('user.newPassword') }}</label>
          <input
            v-model="securityForm.new_password"
            type="password"
            class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
            style="background-color: hsl(var(--muted) / 0.6)"
            :placeholder="t('user.newPassword')"
          />
        </div>
        <div v-if="securityForm.new_password">
          <label class="text-xs font-medium text-muted-foreground mb-1 block">{{ t('user.confirmNewPassword') }}</label>
          <input
            v-model="securityForm.confirm_password"
            type="password"
            class="w-full px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
            style="background-color: hsl(var(--muted) / 0.6)"
            :placeholder="t('user.confirmNewPassword')"
          />
        </div>

        <div class="flex justify-end gap-2 pt-3">
          <button
            @click="$emit('close')"
            class="px-4 py-2 rounded-lg text-sm font-medium border border-border hover:bg-muted transition-colors"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            @click="saveSecurity"
            :disabled="securityLoading"
            class="px-5 py-2 bg-accent text-accent-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all"
          >
            {{ securityLoading ? '...' : t('common.save') }}
          </button>
        </div>
      </div>

      <!-- Tab: 2FA -->
      <div v-show="activeTab === '2fa'">
        <!-- Not enabled -->
        <template v-if="!mfaEnabled && !mfaSettingUp">
          <div class="text-center py-4">
            <ShieldOff class="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
            <p class="text-sm text-muted-foreground mb-4">{{ t('user.twoFactorDisabled') }}</p>
            <button
              @click="startMfaSetup"
              :disabled="mfaLoading"
              class="px-4 py-2 bg-accent text-accent-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all"
            >
              {{ t('user.enable2FA') }}
            </button>
          </div>
        </template>

        <!-- Setting up -->
        <div v-if="mfaSettingUp" class="space-y-3">
          <p class="text-sm text-muted-foreground text-center">{{ t('user.scanQRCode') }}</p>
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
          <div class="text-center py-2">
            <ShieldCheck class="w-10 h-10 mx-auto mb-3 text-green-600 dark:text-green-400" />
            <p class="text-sm text-green-600 dark:text-green-400 font-medium mb-4">{{ t('user.twoFactorEnabled') }}</p>
            <button
              v-if="!showDisableMfa"
              @click="showDisableMfa = true"
              class="px-4 py-2 rounded-lg text-sm font-medium border border-border hover:bg-muted transition-colors text-destructive"
            >
              {{ t('user.disable2FA') }}
            </button>
          </div>

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

          <!-- Trusted devices -->
          <div class="border-t border-border/30 pt-3 mt-3">
            <div class="flex items-center justify-between mb-2">
              <p class="text-xs font-medium text-muted-foreground">{{ t('user.trustedDevices') }}</p>
              <button
                v-if="devices.length > 0"
                @click="clearAllDevices"
                class="text-xs text-destructive hover:underline"
              >
                {{ t('user.clearAllDevices') }}
              </button>
            </div>
            <div v-if="devicesLoading" class="text-center py-2">
              <p class="text-xs text-muted-foreground">...</p>
            </div>
            <div v-else-if="devices.length === 0" class="text-center py-2">
              <p class="text-xs text-muted-foreground">{{ t('user.noTrustedDevices') }}</p>
            </div>
            <div v-else class="space-y-1.5">
              <div
                v-for="device in devices"
                :key="device.id"
                class="flex items-center justify-between px-2.5 py-2 rounded-lg"
                style="background-color: hsl(var(--muted) / 0.3)"
              >
                <div class="flex items-center gap-2 min-w-0">
                  <Laptop class="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                  <div class="min-w-0">
                    <p class="text-xs font-medium truncate">{{ device.device_name }}</p>
                    <p class="text-xs text-muted-foreground truncate">{{ device.ip_address }}</p>
                  </div>
                </div>
                <button
                  @click="removeDevice(device.id)"
                  class="p-1 rounded hover:bg-muted transition-colors flex-shrink-0"
                >
                  <Trash2 class="w-3.5 h-3.5 text-muted-foreground hover:text-destructive" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="flex justify-end pt-3">
          <button
            @click="$emit('close')"
            class="px-4 py-2 rounded-lg text-sm font-medium border border-border hover:bg-muted transition-colors"
          >
            {{ mfaEnabled ? t('common.close') : t('common.cancel') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { auth } from '@/api'
import { ShieldCheck, ShieldOff, User, Lock, Laptop, Trash2 } from 'lucide-vue-next'

defineEmits<{ close: [] }>()

const { t } = useI18n()
const authStore = useAuthStore()

const activeTab = ref<'basic' | 'security' | '2fa'>('basic')
const tabs = [
  { key: 'basic' as const, icon: User, label: 'user.basicInfo' },
  { key: 'security' as const, icon: Lock, label: 'user.securityInfo' },
  { key: '2fa' as const, icon: ShieldCheck, label: 'user.twoFactorAuth' },
]

watch(activeTab, () => {
  error.value = ''
  success.value = ''
})

// --- Basic info ---
const form = ref({
  nickname: authStore.user?.nickname || '',
  avatar_text: authStore.user?.avatar_text || '',
})
const profileLoading = ref(false)

const previewAvatarText = computed(() => {
  if (form.value.avatar_text) return form.value.avatar_text.slice(0, 4)
  if (form.value.nickname) return form.value.nickname[0].toUpperCase()
  return authStore.avatarText
})

async function saveBasicInfo() {
  profileLoading.value = true
  error.value = ''
  try {
    const data: any = {}
    if (form.value.nickname !== (authStore.user?.nickname || '')) {
      data.nickname = form.value.nickname
    }
    if (form.value.avatar_text !== (authStore.user?.avatar_text || '')) {
      data.avatar_text = form.value.avatar_text
    }
    // No changes
    if (Object.keys(data).length === 0) {
      success.value = t('user.profileSaved')
      return
    }
    const res = await auth.profile(data)
    authStore.setUser(res.data)
    success.value = t('user.profileSaved')
    setTimeout(() => { success.value = '' }, 3000)
  } catch (e: any) {
    error.value = parseError(e)
  } finally {
    profileLoading.value = false
  }
}

// --- Security ---
const securityForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: '',
})
const securityLoading = ref(false)

async function saveSecurity() {
  securityLoading.value = true
  error.value = ''
  try {
    if (!securityForm.value.current_password) {
      error.value = t('user.currentPassword') + ' ' + t('common.required')
      securityLoading.value = false
      return
    }
    if (securityForm.value.new_password && securityForm.value.new_password !== securityForm.value.confirm_password) {
      error.value = t('user.passwordMismatch')
      securityLoading.value = false
      return
    }
    const data: any = {
      current_password: securityForm.value.current_password,
    }
    if (securityForm.value.new_password) {
      data.new_password = securityForm.value.new_password
    }
    await auth.profile(data)
    securityForm.value = { current_password: '', new_password: '', confirm_password: '' }
    success.value = t('user.profileSaved')
    setTimeout(() => { success.value = '' }, 3000)
  } catch (e: any) {
    error.value = parseError(e)
  } finally {
    securityLoading.value = false
  }
}

// --- 2FA (unchanged logic) ---
const mfaEnabled = computed(() => authStore.user?.mfa_enabled || false)
const mfaSettingUp = ref(false)
const mfaLoading = ref(false)
const mfaCode = ref('')
const mfaSecret = ref('')
const mfaProvisioningUri = ref('')
const showDisableMfa = ref(false)
const disablePassword = ref('')
const disableCode = ref('')
const qrCanvas = ref<HTMLCanvasElement | null>(null)

// --- Trusted devices ---
interface Device {
  id: number
  device_name: string
  ip_address: string
  user_agent: string
  created_at: string
  last_used_at: string
}
const devices = ref<Device[]>([])
const devicesLoading = ref(false)

const error = ref('')
const success = ref('')

async function drawQr() {
  await nextTick()
  if (!qrCanvas.value || !mfaProvisioningUri.value) return
  try {
    const QRCode = (await import('qrcode')).default
    QRCode.toCanvas(qrCanvas.value, mfaProvisioningUri.value, { width: 180, margin: 2 })
  } catch (e) { console.error('Failed to render QR code:', e) }
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

async function fetchDevices() {
  devicesLoading.value = true
  try {
    const res = await auth.devices()
    devices.value = res.data || []
  } catch (_) {
    devices.value = []
  } finally {
    devicesLoading.value = false
  }
}

async function removeDevice(id: number) {
  try {
    await auth.removeDevice(id)
    devices.value = devices.value.filter(d => d.id !== id)
    success.value = t('user.deviceRemoved')
    setTimeout(() => { success.value = '' }, 3000)
  } catch (e: any) {
    error.value = parseError(e)
  }
}

async function clearAllDevices() {
  try {
    await auth.clearDevices()
    devices.value = []
    success.value = t('user.devicesCleared')
    setTimeout(() => { success.value = '' }, 3000)
  } catch (e: any) {
    error.value = parseError(e)
  }
}

// Watch for 2FA tab activation to fetch devices
watch(activeTab, (tab) => {
  if (tab === '2fa' && mfaEnabled.value) {
    fetchDevices()
  }
})

function parseError(e: any): string {
  const d = e.response?.data
  let msg = d?.message
  if (!msg && d?.detail) {
    try { const parsed = typeof d.detail === 'string' ? JSON.parse(d.detail) : d.detail; msg = parsed.message } catch (_) {}
  }
  return msg || 'Operation failed'
}
</script>
