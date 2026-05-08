import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface UserInfo {
  id: number
  username: string
  email: string
  nickname?: string
  avatar_text?: string
  mfa_enabled: boolean
  is_active: boolean
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const deviceToken = ref(localStorage.getItem('device_token') || '')
  const user = ref<UserInfo | null>(null)
  const mfaToken = ref('')
  const mfaRequired = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const displayName = computed(() => user.value?.nickname || user.value?.username || '')
  const avatarText = computed(() => {
    if (user.value?.avatar_text) return user.value.avatar_text.slice(0, 4)
    if (user.value?.nickname) return user.value.nickname[0].toUpperCase()
    if (user.value?.username) return user.value.username[0].toUpperCase()
    return '?'
  })

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function setDeviceToken(t: string) {
    deviceToken.value = t
    localStorage.setItem('device_token', t)
  }

  function setUser(u: UserInfo) {
    user.value = u
  }

  function setMfaToken(t: string) {
    mfaToken.value = t
    mfaRequired.value = true
  }

  function clearMfa() {
    mfaToken.value = ''
    mfaRequired.value = false
  }

  function logout() {
    token.value = ''
    deviceToken.value = ''
    user.value = null
    mfaToken.value = ''
    mfaRequired.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('device_token')
  }

  return { token, deviceToken, user, isLoggedIn, mfaToken, mfaRequired, displayName, avatarText, setToken, setDeviceToken, setUser, setMfaToken, clearMfa, logout }
})
