<template>
  <div class="admin-page">
    <PageHeader
      title="Settings"
      subtitle="Platform appearance, feature flags, and maintenance controls."
      icon="fas fa-sliders-h"
      icon-tone="tone-teal"
      :show-refresh="false"
    >
      <template #actions>
        <button v-if="isSuperAdmin" type="button" class="btn btn-primary" :disabled="saving" @click="saveAppearance">
          <i class="fas fa-save"></i> {{ saving ? 'Saving…' : 'Save appearance' }}
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

      <DataPanel title="Admin dashboard" subtitle="Layout template for staff dashboards">
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

      <DataPanel title="Feature flags" subtitle="Live platform capabilities from the server">
        <div v-if="flagsLoading" class="settings-loading"><i class="fas fa-spinner fa-spin"></i> Loading flags…</div>
        <div v-else-if="featureFlags.length === 0" class="settings-empty">No feature flags configured.</div>
        <div v-else class="toggle-list">
          <label v-for="flag in featureFlags" :key="flag.key" class="toggle-row">
            <div>
              <p class="toggle-title">{{ flagLabel(flag) }}</p>
              <p class="toggle-desc">{{ flag.description || flag.key }}</p>
            </div>
            <button
              type="button"
              class="toggle"
              :class="{ on: flag.is_enabled }"
              :disabled="flagSavingKey === flag.key"
              @click="toggleFlag(flag)"
            >
              <span class="toggle-knob"></span>
            </button>
          </label>
        </div>
      </DataPanel>

      <DataPanel title="Maintenance mode" subtitle="Temporarily block non-admin access">
        <div class="toggle-list">
          <label class="toggle-row">
            <div>
              <p class="toggle-title">Enable maintenance</p>
              <p class="toggle-desc">Shows a maintenance message to regular users.</p>
            </div>
            <button
              type="button"
              class="toggle"
              :class="{ on: maintenance.is_active }"
              :disabled="maintenanceSaving"
              @click="toggleMaintenance"
            >
              <span class="toggle-knob"></span>
            </button>
          </label>
        </div>
        <label class="maint-message">
          <span>Message</span>
          <textarea v-model="maintenance.message" rows="3" @change="saveMaintenanceMessage" />
        </label>
      </DataPanel>

      <DataPanel title="Institution" subtitle="Profile used across the platform">
        <div class="info-grid">
          <div class="info-item"><span>Name</span><strong>{{ institution.name || '—' }}</strong></div>
          <div class="info-item"><span>Short name</span><strong>{{ institution.short_name || '—' }}</strong></div>
          <div class="info-item"><span>Signed in as</span><strong>{{ userLabel }}</strong></div>
          <div class="info-item"><span>Role</span><strong class="capitalize">{{ roleName.replace('_', ' ') }}</strong></div>
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
import { systemApi } from '@/api/system'
import { formatIndexDisplay } from '@/utils/index'
import PageHeader from '@/components/admin/PageHeader.vue'
import DataPanel from '@/components/admin/DataPanel.vue'

const authStore = useAuthStore()
const themeStore = useThemeStore()

const saveMessage = ref('')
const saving = ref(false)
const selectedTheme = ref(themeStore.theme)
const selectedDashboard = ref(themeStore.dashboard)

const featureFlags = ref([])
const flagsLoading = ref(false)
const flagSavingKey = ref('')
const institution = ref({})
const maintenance = ref({ is_active: false, message: '' })
const maintenanceSaving = ref(false)

const THEME_SWATCHES = {
  classic: ['#3d4f44', '#a3b18a', '#f2f1ec', '#1c1c1c'],
  pulse: ['#ff3b5c', '#1a1a1a', '#f3f4f6', '#71717a'],
  amber: ['#e8b92a', '#2d2d2d', '#f8f7f2', '#8a877c'],
}

const FLAG_LABELS = {
  ussd_voting: 'USSD voting',
  web_voting: 'Web voting',
  biometric_auth: 'Biometric auth',
  sms_notifications: 'SMS notifications',
  email_notifications: 'Email notifications',
  student_registration: 'Student self-registration',
  results_auto_generate: 'Auto-generate results',
  strongroom_enabled: 'Strongroom',
  fraud_detection: 'Fraud detection',
  audit_logging: 'Audit logging',
  maintenance_mode: 'Maintenance mode flag',
}

const roleName = computed(() => authStore.roleName)
const isSuperAdmin = computed(() => authStore.isSuperAdmin)
const userLabel = computed(() => {
  const user = authStore.user
  if (!user) return 'Unknown'
  if (user.index_number) return formatIndexDisplay(user.index_number)
  return user.email || 'Unknown'
})

const themeOptions = computed(() => (
  (themeStore.options?.length ? themeStore.options : []).map((option) => ({
    ...option,
    swatches: THEME_SWATCHES[option.id] || THEME_SWATCHES.classic,
  }))
))

const dashboardOptions = computed(() => (
  themeStore.dashboardOptions?.length
    ? themeStore.dashboardOptions
    : [
        { id: 'atelier', label: 'Atelier Soft', description: 'Soft-UI mosaic dashboard' },
        { id: 'operations', label: 'Operations', description: 'Compact ops layout' },
        { id: 'lumen', label: 'Lumen', description: 'Warm soft-UI workspace dashboard' },
      ]
))

const flagLabel = (flag) => FLAG_LABELS[flag.key] || flag.key.replaceAll('_', ' ')

const flash = (message) => {
  saveMessage.value = message
  setTimeout(() => { saveMessage.value = '' }, 3000)
}

const selectTheme = (themeId) => {
  selectedTheme.value = themeId
  themeStore.setTheme(themeId)
}

const selectDashboard = (dashboardId) => {
  selectedDashboard.value = dashboardId
  themeStore.setDashboard(dashboardId)
}

const saveAppearance = async () => {
  saving.value = true
  try {
    await themeStore.setTheme(selectedTheme.value)
    await themeStore.setDashboard(selectedDashboard.value, { persistRemote: true })
    flash('Appearance saved for all users.')
  } catch (error) {
    console.error(error)
    flash('Could not sync appearance to the server.')
  } finally {
    saving.value = false
  }
}

const loadFlags = async () => {
  flagsLoading.value = true
  try {
    const { data } = await systemApi.listFeatureFlags()
    featureFlags.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error(error)
    featureFlags.value = []
  } finally {
    flagsLoading.value = false
  }
}

const toggleFlag = async (flag) => {
  flagSavingKey.value = flag.key
  try {
    const { data } = await systemApi.updateFeatureFlag(flag.key, !flag.is_enabled)
    const idx = featureFlags.value.findIndex((f) => f.key === flag.key)
    if (idx >= 0) featureFlags.value[idx] = data
    flash(`${flagLabel(flag)} ${data.is_enabled ? 'enabled' : 'disabled'}.`)
  } catch (error) {
    console.error(error)
    flash('Failed to update feature flag.')
  } finally {
    flagSavingKey.value = ''
  }
}

const loadInstitution = async () => {
  try {
    const { data } = await systemApi.getInstitution()
    institution.value = data || {}
  } catch (error) {
    console.error(error)
  }
}

const loadMaintenance = async () => {
  try {
    const { data } = await systemApi.getMaintenance()
    maintenance.value = {
      is_active: !!data?.is_active,
      message: data?.message || '',
    }
  } catch (error) {
    console.error(error)
  }
}

const toggleMaintenance = async () => {
  maintenanceSaving.value = true
  try {
    const { data } = await systemApi.setMaintenance({
      is_active: !maintenance.value.is_active,
      message: maintenance.value.message,
    })
    maintenance.value = {
      is_active: !!data.is_active,
      message: data.message || maintenance.value.message,
    }
    flash(maintenance.value.is_active ? 'Maintenance mode enabled.' : 'Maintenance mode disabled.')
  } catch (error) {
    console.error(error)
    flash('Failed to update maintenance mode.')
  } finally {
    maintenanceSaving.value = false
  }
}

const saveMaintenanceMessage = async () => {
  try {
    await systemApi.setMaintenance({
      is_active: maintenance.value.is_active,
      message: maintenance.value.message,
    })
    flash('Maintenance message saved.')
  } catch (error) {
    console.error(error)
  }
}

onMounted(async () => {
  selectedTheme.value = themeStore.theme
  selectedDashboard.value = themeStore.dashboard
  if (!isSuperAdmin.value) return
  await Promise.all([loadFlags(), loadInstitution(), loadMaintenance()])
})
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

@media (min-width: 1100px) {
  .dashboard-picker {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
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

.preview--atelier span:nth-child(4) { background: #3d4f44; }
.preview--operations { grid-template-columns: 1fr 1fr; }
.preview--operations span:nth-child(3) {
  grid-column: 1 / -1;
  min-height: 1.8rem;
  background: #e8efe6;
}
.preview--operations span:nth-child(4) { display: none; }
.preview--lumen {
  background: #f8f7f2;
  grid-template-columns: 1.2fr 1fr 0.8fr;
}
.preview--lumen span:nth-child(1) {
  grid-row: 1 / 3;
  background: linear-gradient(180deg, #fbf3d6, #fff);
}
.preview--lumen span:nth-child(2) { background: #fff; }
.preview--lumen span:nth-child(3) { background: #2d2d2d; }
.preview--lumen span:nth-child(4) {
  grid-column: 2 / 4;
  background: #e8b92a;
}

.settings-loading,
.settings-empty {
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.85rem;
  padding: 0.5rem 0;
}

.maint-message {
  display: grid;
  gap: 0.45rem;
  margin-top: 1rem;
  font-size: 0.8rem;
  color: var(--vb-muted, #8a8a8a);
}

.maint-message textarea {
  width: 100%;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 0.75rem;
  padding: 0.75rem 0.85rem;
  font: inherit;
  color: var(--vb-ink, #1c1c1c);
  resize: vertical;
}
</style>
