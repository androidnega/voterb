<template>
  <div class="admin-page">
    <PageHeader
      title="Settings"
      subtitle="Configure platform security, voting channels, and appearance."
      icon="fas fa-sliders-h"
      icon-tone="tone-teal"
      :show-refresh="false"
    >
      <template #actions>
        <button v-if="isSuperAdmin" type="button" class="btn btn-ghost" @click="resetSettings">Reset</button>
        <button v-if="isSuperAdmin" type="button" class="btn btn-primary" @click="saveSettings">
          <i class="fas fa-save"></i> Save
        </button>
      </template>
    </PageHeader>

    <div v-if="!isSuperAdmin" class="access-notice">
      <i class="fas fa-lock"></i>
      <span>Only super admins can change system settings.</span>
    </div>

    <div v-else class="settings-grid">
      <DataPanel title="Appearance" subtitle="Platform-wide color theme for all users">
        <div class="theme-picker">
          <button
            v-for="option in themeOptions"
            :key="option.id"
            type="button"
            class="theme-card"
            :class="{ 'is-active': selectedTheme === option.id }"
            @click="selectTheme(option.id)"
          >
            <div class="theme-card__swatches">
              <span
                v-for="swatch in option.swatches"
                :key="swatch"
                class="theme-card__swatch"
                :style="{ background: swatch }"
              ></span>
            </div>
            <div>
              <p class="theme-card__title">{{ option.label }}</p>
              <p class="theme-card__desc">{{ option.description }}</p>
            </div>
          </button>
        </div>
      </DataPanel>

      <DataPanel title="Platform" subtitle="Environment and session context">
        <div class="info-grid">
          <div class="info-item"><span>Application</span><strong>VoterB Election Platform</strong></div>
          <div class="info-item"><span>Environment</span><strong>Development</strong></div>
          <div class="info-item"><span>Signed in as</span><strong>{{ userLabel }}</strong></div>
          <div class="info-item"><span>Role</span><strong class="capitalize">{{ roleName.replace('_', ' ') }}</strong></div>
        </div>
      </DataPanel>

      <DataPanel title="Security" subtitle="Authentication and voting access">
        <div class="toggle-list">
          <label v-for="item in securityToggles" :key="item.key" class="toggle-row">
            <div>
              <p class="toggle-title">{{ item.title }}</p>
              <p class="toggle-desc">{{ item.description }}</p>
            </div>
            <button type="button" class="toggle" :class="{ on: settings[item.key] }" @click="settings[item.key] = !settings[item.key]">
              <span class="toggle-knob"></span>
            </button>
          </label>
        </div>
      </DataPanel>

      <DataPanel title="Notifications" subtitle="Outbound alert channels">
        <div class="toggle-list">
          <label v-for="item in notificationToggles" :key="item.key" class="toggle-row">
            <div>
              <p class="toggle-title">{{ item.title }}</p>
              <p class="toggle-desc">{{ item.description }}</p>
            </div>
            <button type="button" class="toggle" :class="{ on: settings[item.key] }" @click="settings[item.key] = !settings[item.key]">
              <span class="toggle-knob"></span>
            </button>
          </label>
        </div>
      </DataPanel>
    </div>

    <p v-if="saveMessage" class="save-toast"><i class="fas fa-check-circle"></i> {{ saveMessage }}</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { formatIndexDisplay } from '@/utils/index'
import PageHeader from '@/components/admin/PageHeader.vue'
import DataPanel from '@/components/admin/DataPanel.vue'

const authStore = useAuthStore()
const themeStore = useThemeStore()
const saveMessage = ref('')
const selectedTheme = ref(themeStore.theme)

const THEME_SWATCHES = {
  classic: ['#0f766e', '#ecfdf5', '#0f172a', '#f8fafc'],
  pulse: ['#ff3b5c', '#1a1a1a', '#f3f4f6', '#71717a'],
}

const defaultSettings = {
  requireOtp: true,
  webVoting: true,
  ussdVoting: false,
  smsNotifications: true,
  emailNotifications: false,
}

const settings = ref({ ...defaultSettings })

const roleName = computed(() => authStore.roleName)
const isSuperAdmin = computed(() => authStore.isSuperAdmin)
const userLabel = computed(() => {
  const user = authStore.user
  if (!user) return 'Unknown'
  if (user.index_number) return formatIndexDisplay(user.index_number)
  return user.email || 'Unknown'
})

const themeOptions = computed(() => {
  const apiOptions = themeStore.options?.length
    ? themeStore.options
    : [
        { id: 'classic', label: 'Classic', description: 'Teal admin theme' },
        { id: 'pulse', label: 'Pulse', description: 'Coral accent on light surfaces' },
      ]

  return apiOptions.map((option) => ({
    ...option,
    swatches: THEME_SWATCHES[option.id] || THEME_SWATCHES.classic,
  }))
})

const securityToggles = [
  { key: 'requireOtp', title: 'Require OTP for login', description: 'All users verify OTP before signing in.' },
  { key: 'webVoting', title: 'Enable web voting', description: 'Allow ballots through the web application.' },
  { key: 'ussdVoting', title: 'Enable USSD voting', description: 'Allow voting through USSD channels.' },
]

const notificationToggles = [
  { key: 'smsNotifications', title: 'SMS notifications', description: 'Send OTP and election alerts via SMS.' },
  { key: 'emailNotifications', title: 'Email notifications', description: 'Send admin alerts and updates by email.' },
]

const loadSettings = () => {
  try {
    const saved = localStorage.getItem('voterb_settings')
    if (saved) settings.value = { ...defaultSettings, ...JSON.parse(saved) }
  } catch {
    settings.value = { ...defaultSettings }
  }
  selectedTheme.value = themeStore.theme
}

const selectTheme = (themeId) => {
  selectedTheme.value = themeId
  themeStore.setTheme(themeId)
}

const saveSettings = async () => {
  localStorage.setItem('voterb_settings', JSON.stringify(settings.value))
  try {
    await themeStore.setTheme(selectedTheme.value, { persistRemote: true })
    saveMessage.value = 'Settings saved. Theme applied for all users.'
  } catch (error) {
    console.error('Failed to save theme:', error)
    saveMessage.value = 'Local settings saved, but theme could not be synced to the server.'
  }
  setTimeout(() => { saveMessage.value = '' }, 3000)
}

const resetSettings = async () => {
  settings.value = { ...defaultSettings }
  localStorage.removeItem('voterb_settings')
  selectedTheme.value = 'classic'
  try {
    await themeStore.setTheme('classic', { persistRemote: true })
  } catch (error) {
    console.error('Failed to reset theme:', error)
  }
  saveMessage.value = 'Settings reset to defaults.'
  setTimeout(() => { saveMessage.value = '' }, 3000)
}

onMounted(loadSettings)
</script>
