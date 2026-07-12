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
      <DataPanel title="Color theme" subtitle="Platform-wide accent palette for all users">
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

      <DataPanel title="Admin dashboard" subtitle="Layout template for election committee and super admin dashboards">
        <div class="theme-picker dashboard-picker">
          <button
            v-for="option in dashboardOptions"
            :key="option.id"
            type="button"
            class="theme-card dashboard-card"
            :class="{ 'is-active': selectedDashboard === option.id }"
            @click="selectDashboard(option.id)"
          >
            <div class="dashboard-card__preview" :class="`preview--${option.id}`" aria-hidden="true">
              <span></span><span></span><span></span><span></span>
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
const selectedDashboard = ref(themeStore.dashboard)

const THEME_SWATCHES = {
  classic: ['#3d4f44', '#a3b18a', '#f2f1ec', '#1c1c1c'],
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
  const apiOptions = themeStore.options?.length ? themeStore.options : []
  return apiOptions.map((option) => ({
    ...option,
    swatches: THEME_SWATCHES[option.id] || THEME_SWATCHES.classic,
  }))
})

const dashboardOptions = computed(() => (
  themeStore.dashboardOptions?.length
    ? themeStore.dashboardOptions
    : [
        { id: 'atelier', label: 'Atelier Soft', description: 'Current soft-UI admin dashboard' },
        { id: 'operations', label: 'Operations', description: 'Compact ops layout' },
      ]
))

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
  selectedDashboard.value = themeStore.dashboard
}

const selectTheme = (themeId) => {
  selectedTheme.value = themeId
  themeStore.setTheme(themeId)
}

const selectDashboard = (dashboardId) => {
  selectedDashboard.value = dashboardId
  themeStore.setDashboard(dashboardId)
}

const saveSettings = async () => {
  localStorage.setItem('voterb_settings', JSON.stringify(settings.value))
  try {
    await themeStore.setTheme(selectedTheme.value)
    await themeStore.setDashboard(selectedDashboard.value, { persistRemote: true })
    saveMessage.value = 'Settings saved. Appearance applied for all users.'
  } catch (error) {
    console.error('Failed to save appearance:', error)
    saveMessage.value = 'Local settings saved, but appearance could not be synced to the server.'
  }
  setTimeout(() => { saveMessage.value = '' }, 3000)
}

const resetSettings = async () => {
  settings.value = { ...defaultSettings }
  localStorage.removeItem('voterb_settings')
  selectedTheme.value = 'classic'
  selectedDashboard.value = 'atelier'
  try {
    await themeStore.setTheme('classic')
    await themeStore.setDashboard('atelier', { persistRemote: true })
  } catch (error) {
    console.error('Failed to reset appearance:', error)
  }
  saveMessage.value = 'Settings reset to defaults.'
  setTimeout(() => { saveMessage.value = '' }, 3000)
}

onMounted(loadSettings)
</script>

<style scoped>
.dashboard-picker {
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  .dashboard-picker {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.dashboard-card {
  align-items: stretch;
}

.dashboard-card__preview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.35rem;
  padding: 0.65rem;
  border-radius: 0.85rem;
  background: #f2f1ec;
  min-height: 4.25rem;
}

.dashboard-card__preview span {
  border-radius: 0.45rem;
  background: #fff;
  box-shadow: 0 1px 2px rgba(28, 28, 28, 0.04);
}

.preview--atelier span:nth-child(1) { grid-column: span 1; background: #e8efe6; }
.preview--atelier span:nth-child(2) { grid-column: span 1; }
.preview--atelier span:nth-child(3) { grid-column: span 1; }
.preview--atelier span:nth-child(4) { grid-column: span 1; background: #3d4f44; }

.preview--operations {
  grid-template-columns: 1fr 1fr;
}

.preview--operations span:nth-child(1),
.preview--operations span:nth-child(2) {
  min-height: 1.35rem;
}

.preview--operations span:nth-child(3) {
  grid-column: 1 / -1;
  min-height: 1.8rem;
  background: #e8efe6;
}

.preview--operations span:nth-child(4) {
  display: none;
}
</style>
