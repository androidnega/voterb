<template>
  <div class="admin-page">
    <PageHeader
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
        <div class="theme-picker dashboard-picker settings-scroll">
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
        <div v-else-if="featureFlags.length === 0" class="settings-empty">
          No feature flags configured. Run <code>seed_system_defaults</code> on the backend.
        </div>
        <div v-else class="toggle-list settings-scroll">
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

      <DataPanel title="SMS & USSD integrations" subtitle="Arkesel, Moolre, and USSD callback used in production">
        <div v-if="integrationsLoading" class="settings-loading"><i class="fas fa-spinner fa-spin"></i> Loading integrations…</div>
        <div v-else-if="integrationSettings.length === 0" class="settings-empty">
          No integration settings found. Run <code>seed_system_defaults</code> on the backend.
        </div>
        <div v-else class="integration-settings settings-scroll">
          <label v-for="setting in integrationSettings" :key="setting.key" class="integration-row">
            <div>
              <p class="toggle-title">{{ integrationLabel(setting.key) }}</p>
              <p class="toggle-desc">{{ integrationHelp(setting) }}</p>
            </div>
            <input
              v-model="setting.value"
              class="integration-input"
              :type="isSecretKey(setting.key) ? 'password' : 'text'"
              :placeholder="integrationPlaceholder(setting.key)"
              :disabled="integrationSavingKey === setting.key"
              @change="saveIntegrationSetting(setting)"
            />
          </label>
          <p class="integration-hint">
            Arkesel callback (JSON in / JSON out — leave webhook API key blank):
            <code>https://votebridge.online/api/v1/ussd/callback/</code>
          </p>
        </div>
      </DataPanel>

      <DataPanel title="Security & auth" subtitle="OTP, SVT, and session controls used across the platform">
        <div v-if="securityLoading" class="settings-loading"><i class="fas fa-spinner fa-spin"></i> Loading security settings…</div>
        <div v-else-if="securitySettings.length === 0" class="settings-empty">
          No security settings found. Run <code>seed_system_defaults</code> on the backend.
        </div>
        <div v-else class="security-settings settings-scroll">
          <label v-for="setting in securitySettings" :key="setting.key" class="security-row">
            <div>
              <p class="toggle-title">{{ securityLabel(setting.key) }}</p>
              <p class="toggle-desc">{{ setting.description || setting.key }}</p>
            </div>
            <input
              v-model="setting.value"
              class="security-input"
              :class="{ 'is-wide': isTextSecurityKey(setting.key) }"
              :type="isSecretKey(setting.key) ? 'password' : (isTextSecurityKey(setting.key) ? 'text' : 'number')"
              :min="isTextSecurityKey(setting.key) ? undefined : 1"
              :disabled="securitySavingKey === setting.key"
              @change="saveSecuritySetting(setting)"
            />
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

      <DataPanel title="Institution" subtitle="Name and logo shown on ballot boxes and platform branding">
        <div class="inst-editor">
          <div class="inst-logo-block">
            <div class="inst-logo-preview">
              <img
                v-if="institutionLogoPreview"
                :src="institutionLogoPreview"
                alt="Institution logo"
              />
              <span v-else class="inst-logo-empty">No logo</span>
            </div>
            <label class="inst-upload">
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp,image/svg+xml"
                :disabled="institutionSaving"
                @change="onLogoSelected"
              />
              <span>{{ institutionSaving ? 'Saving…' : 'Change logo' }}</span>
            </label>
            <p class="inst-hint">Used next to the EC badge on the sealed ballot box.</p>
          </div>

          <div class="inst-fields">
            <label class="inst-field">
              <span>Institution name</span>
              <input v-model="institutionForm.name" type="text" maxlength="255" />
            </label>
            <label class="inst-field">
              <span>Short name</span>
              <input v-model="institutionForm.short_name" type="text" maxlength="50" />
            </label>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="institutionSaving"
              @click="saveInstitution"
            >
              {{ institutionSaving ? 'Saving…' : 'Save institution' }}
            </button>
          </div>
        </div>
      </DataPanel>
    </div>

    <Transition name="save-toast">
      <p
        v-if="saveMessage"
        class="save-toast"
        :class="{ 'is-error': saveTone === 'error' }"
        role="status"
        aria-live="polite"
      >
        <i :class="saveTone === 'error' ? 'fas fa-exclamation-circle' : 'fas fa-check-circle'"></i>
        {{ saveMessage }}
      </p>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { systemApi } from '@/api/system'
import { resolveMediaUrl } from '@/utils/media'
import PageHeader from '@/components/admin/PageHeader.vue'
import DataPanel from '@/components/admin/DataPanel.vue'

const authStore = useAuthStore()
const themeStore = useThemeStore()
const toast = useToast()

const saveMessage = ref('')
const saveTone = ref('success')
const saving = ref(false)
const selectedTheme = ref(themeStore.theme)
const selectedDashboard = ref(themeStore.dashboard)

const featureFlags = ref([])
const flagsLoading = ref(false)
const flagSavingKey = ref('')
const securitySettings = ref([])
const securityLoading = ref(false)
const securitySavingKey = ref('')
const integrationSettings = ref([])
const integrationsLoading = ref(false)
const integrationSavingKey = ref('')
const institution = ref({})
const institutionForm = ref({ name: '', short_name: '' })
const institutionSaving = ref(false)
const logoObjectUrl = ref('')
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

const SECURITY_LABELS = {
  otp_length: 'OTP digits',
  otp_expiry_minutes: 'OTP expiry (minutes)',
  staff_master_otp: 'Staff master OTP',
  staff_master_otp_aliases: 'Staff master OTP aliases',
  staff_otp_phone: 'Staff OTP SMS phone',
  staff_master_emails: 'Staff master OTP emails',
  svt_expiry_minutes: 'SVT lifetime (minutes)',
  svt_max_requests_total: 'SVT max requests / voter',
  svt_resend_cooldown_seconds: 'SVT resend cooldown (seconds)',
  svt_max_validation_attempts: 'SVT max failed attempts',
  svt_cross_user_block_minutes: 'SVT cross-user block (minutes)',
  session_timeout_minutes: 'Session timeout (minutes)',
  max_login_attempts: 'Max login attempts',
}

const SECURITY_KEYS = Object.keys(SECURITY_LABELS)
const TEXT_SECURITY_KEYS = new Set([
  'staff_master_otp',
  'staff_master_otp_aliases',
  'staff_otp_phone',
  'staff_master_emails',
])

const INTEGRATION_LABELS = {
  sms_enabled: 'SMS enabled',
  sms_provider_primary: 'Primary SMS provider',
  sms_provider_fallback: 'Fallback SMS provider',
  sms_arkesel_api_key: 'Arkesel API key',
  sms_arkesel_sender_id: 'Arkesel sender ID',
  sms_arkesel_url: 'Arkesel SMS URL',
  sms_moolre_api_key: 'Moolre API key',
  sms_moolre_sender_id: 'Moolre sender ID',
  sms_moolre_url: 'Moolre SMS URL',
  ussd_enabled: 'USSD enabled',
  ussd_service_code: 'USSD service code',
  ussd_callback_url: 'USSD callback URL',
  ussd_api_key: 'USSD webhook API key (leave blank)',
  ussd_session_timeout: 'USSD session timeout (seconds)',
  ussd_svt_resume_seconds: 'USSD SVT resume window (seconds)',
  ussd_retry_attempts: 'USSD retry attempts',
  ussd_rate_limit_per_minute: 'USSD rate limit / minute',
  email_enabled: 'Email enabled',
  email_from_address: 'Email from address',
  email_smtp_host: 'SMTP host',
  email_smtp_port: 'SMTP port',
  email_smtp_username: 'SMTP username',
  email_smtp_password: 'SMTP password',
}

const INTEGRATION_HELP = {
  sms_arkesel_api_key: 'Your Arkesel dashboard API key — used only to send SMS/OTP, not for USSD callbacks.',
  ussd_api_key: 'Leave empty for Arkesel. Arkesel does not send an API key on USSD callbacks; filling this will block dialing.',
  ussd_callback_url: 'Must match the callback URL configured in the Arkesel USSD dashboard.',
  ussd_service_code: 'Short code users dial, e.g. *928*013#',
  ussd_enabled: 'Master switch for USSD voting flows.',
}

const INTEGRATION_KEYS = Object.keys(INTEGRATION_LABELS)
const SECRET_KEYS = new Set([
  'sms_arkesel_api_key',
  'sms_moolre_api_key',
  'ussd_api_key',
  'sms_api_key',
  'email_smtp_password',
  'staff_master_otp',
])

const isSuperAdmin = computed(() => authStore.isSuperAdmin)

const institutionLogoPreview = computed(() => {
  if (logoObjectUrl.value) return logoObjectUrl.value
  return resolveMediaUrl(institution.value?.logo) || '/images/institution-logo.png'
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
const securityLabel = (key) => SECURITY_LABELS[key] || key.replaceAll('_', ' ')
const integrationLabel = (key) => INTEGRATION_LABELS[key] || key.replaceAll('_', ' ')
const integrationHelp = (setting) => INTEGRATION_HELP[setting.key] || setting.description || setting.key
const integrationPlaceholder = (key) => {
  if (key === 'ussd_api_key') return 'Leave blank for Arkesel'
  if (isSecretKey(key)) return 'Enter API key…'
  return ''
}
const isSecretKey = (key) => SECRET_KEYS.has(key)
const isTextSecurityKey = (key) => TEXT_SECURITY_KEYS.has(key)

const flash = (message, tone = 'success') => {
  saveTone.value = tone
  saveMessage.value = message
  window.clearTimeout(flash._timer)
  flash._timer = window.setTimeout(() => { saveMessage.value = '' }, 3200)

  toast.add({
    severity: tone === 'error' ? 'error' : 'success',
    summary: tone === 'error' ? 'Could not save' : 'Saved',
    detail: message,
    life: 3200,
  })
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
    // Apply locally first, then persist both keys in one request
    await themeStore.setTheme(selectedTheme.value)
    await themeStore.setDashboard(selectedDashboard.value)
    await themeStore.saveAppearance()
    const themeLabel = themeOptions.value.find((o) => o.id === selectedTheme.value)?.label || selectedTheme.value
    const dashLabel = dashboardOptions.value.find((o) => o.id === selectedDashboard.value)?.label || selectedDashboard.value
    flash(`${themeLabel} · ${dashLabel} applied for all users.`)
  } catch (error) {
    console.error(error)
    flash('Could not sync appearance to the server.', 'error')
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
    institutionForm.value = {
      name: data?.name || '',
      short_name: data?.short_name || '',
    }
  } catch (error) {
    console.error(error)
  }
}

const saveInstitution = async () => {
  institutionSaving.value = true
  try {
    const { data } = await systemApi.updateInstitution({
      name: institutionForm.value.name.trim() || 'VoterB',
      short_name: institutionForm.value.short_name.trim() || 'VoterB',
    })
    institution.value = data || {}
    institutionForm.value = {
      name: data?.name || institutionForm.value.name,
      short_name: data?.short_name || institutionForm.value.short_name,
    }
    flash('Institution profile saved.')
  } catch (error) {
    console.error(error)
    flash('Failed to save institution profile.')
  } finally {
    institutionSaving.value = false
  }
}

const onLogoSelected = async (event) => {
  const file = event.target?.files?.[0]
  event.target.value = ''
  if (!file) return

  if (logoObjectUrl.value) URL.revokeObjectURL(logoObjectUrl.value)
  logoObjectUrl.value = URL.createObjectURL(file)

  institutionSaving.value = true
  try {
    const { data } = await systemApi.updateInstitutionLogo(file, {
      name: institutionForm.value.name.trim() || institution.value.name || 'VoterB',
      short_name: institutionForm.value.short_name.trim() || institution.value.short_name || 'VoterB',
    })
    institution.value = data || {}
    flash('Institution logo updated.')
  } catch (error) {
    console.error(error)
    flash('Failed to upload logo.')
    if (logoObjectUrl.value) {
      URL.revokeObjectURL(logoObjectUrl.value)
      logoObjectUrl.value = ''
    }
  } finally {
    institutionSaving.value = false
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

const loadSecuritySettings = async () => {
  securityLoading.value = true
  try {
    const { data } = await systemApi.listSettings('security')
    const rows = Array.isArray(data) ? data : []
    securitySettings.value = rows
      .filter((row) => SECURITY_KEYS.includes(row.key))
      .sort((a, b) => SECURITY_KEYS.indexOf(a.key) - SECURITY_KEYS.indexOf(b.key))
      .map((row) => ({ ...row, value: String(row.value ?? '') }))
  } catch (error) {
    console.error(error)
    securitySettings.value = []
  } finally {
    securityLoading.value = false
  }
}

const loadIntegrationSettings = async () => {
  integrationsLoading.value = true
  try {
    const { data } = await systemApi.listSettings('integrations')
    const rows = Array.isArray(data) ? data : []
    integrationSettings.value = rows
      .filter((row) => INTEGRATION_KEYS.includes(row.key))
      .sort((a, b) => INTEGRATION_KEYS.indexOf(a.key) - INTEGRATION_KEYS.indexOf(b.key))
      .map((row) => ({ ...row, value: String(row.value ?? '') }))
  } catch (error) {
    console.error(error)
    integrationSettings.value = []
  } finally {
    integrationsLoading.value = false
  }
}

const saveIntegrationSetting = async (setting) => {
  integrationSavingKey.value = setting.key
  try {
    const { data } = await systemApi.updateSetting(setting.key, String(setting.value ?? ''))
    const idx = integrationSettings.value.findIndex((s) => s.key === setting.key)
    if (idx >= 0) {
      integrationSettings.value[idx] = {
        ...integrationSettings.value[idx],
        ...data,
        value: String(data.value ?? ''),
      }
    }
    flash(`${integrationLabel(setting.key)} saved.`)
  } catch (error) {
    console.error(error)
    flash('Failed to save integration setting.', 'error')
    await loadIntegrationSettings()
  } finally {
    integrationSavingKey.value = ''
  }
}

const saveSecuritySetting = async (setting) => {
  const value = String(setting.value ?? '').trim()
  if (isTextSecurityKey(setting.key)) {
    // Allow empty for optional lists (emails/aliases); require a value for phone/OTP.
    if (!value && setting.key !== 'staff_master_emails' && setting.key !== 'staff_master_otp_aliases') {
      flash('Enter a value for this setting.', 'error')
      await loadSecuritySettings()
      return
    }
  } else if (!value || Number(value) < 1) {
    flash('Enter a positive number.', 'error')
    await loadSecuritySettings()
    return
  }
  securitySavingKey.value = setting.key
  try {
    const { data } = await systemApi.updateSetting(setting.key, value)
    const idx = securitySettings.value.findIndex((s) => s.key === setting.key)
    if (idx >= 0) securitySettings.value[idx] = { ...securitySettings.value[idx], ...data, value: String(data.value ?? '') }
    flash(`${securityLabel(setting.key)} saved.`)
  } catch (error) {
    console.error(error)
    flash('Failed to save security setting.', 'error')
    await loadSecuritySettings()
  } finally {
    securitySavingKey.value = ''
  }
}

onMounted(async () => {
  selectedTheme.value = themeStore.theme
  selectedDashboard.value = themeStore.dashboard
  if (!isSuperAdmin.value) return
  await Promise.all([
    loadFlags(),
    loadSecuritySettings(),
    loadIntegrationSettings(),
    loadInstitution(),
    loadMaintenance(),
  ])
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
  gap: 0.28rem;
  padding: 0.45rem;
  border-radius: 0.7rem;
  background: #f2f1ec;
  min-height: 2.6rem;
}

.settings-scroll {
  max-height: 14.5rem;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding-right: 0.25rem;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.settings-scroll::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.dashboard-picker.settings-scroll {
  max-height: 12.5rem;
}

.toggle-list.settings-scroll,
.security-settings.settings-scroll,
.integration-settings.settings-scroll {
  max-height: 15.5rem;
}

.security-input.is-wide {
  width: min(100%, 14rem);
  text-align: left;
  font-weight: 600;
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

.settings-empty code {
  font-size: 0.78rem;
}

.security-settings {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.security-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--vb-line, #ebeae4);
}

.security-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.security-input {
  width: 5.5rem;
  flex-shrink: 0;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 0.7rem;
  padding: 0.55rem 0.65rem;
  font: inherit;
  font-weight: 700;
  color: var(--vb-ink, #1c1c1c);
  text-align: center;
  background: #fafaf9;
}

.integration-settings {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.integration-row {
  display: grid;
  gap: 0.55rem;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid var(--vb-line, #ebeae4);
}

@media (min-width: 720px) {
  .integration-row {
    grid-template-columns: minmax(0, 1.1fr) minmax(12rem, 1fr);
    align-items: center;
  }
}

.integration-row:last-of-type {
  border-bottom: none;
  padding-bottom: 0;
}

.integration-input {
  width: 100%;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 0.7rem;
  padding: 0.65rem 0.8rem;
  font: inherit;
  font-weight: 600;
  color: var(--vb-ink, #1c1c1c);
  background: #fafaf9;
}

.integration-hint {
  margin: 0.35rem 0 0;
  font-size: 0.75rem;
  color: var(--vb-muted, #8a8a8a);
  line-height: 1.45;
}

.integration-hint code {
  font-size: 0.72rem;
  word-break: break-all;
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

.inst-editor {
  display: grid;
  gap: 1.25rem;
}

@media (min-width: 720px) {
  .inst-editor {
    grid-template-columns: auto 1fr;
    align-items: start;
  }
}

.inst-logo-block {
  display: grid;
  gap: 0.65rem;
  justify-items: start;
}

.inst-logo-preview {
  width: 5.5rem;
  height: 5.5rem;
  border-radius: 1rem;
  border: 1px solid var(--vb-line, #ebeae4);
  background: #fafaf9;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.inst-logo-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 0.45rem;
}

.inst-logo-empty {
  font-size: 0.75rem;
  color: var(--vb-muted, #8a8a8a);
}

.inst-upload {
  position: relative;
  display: inline-flex;
  cursor: pointer;
}

.inst-upload input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.inst-upload span {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.45rem 0.85rem;
  background: #1c1917;
  color: #fff;
  font-size: 0.78rem;
  font-weight: 700;
}

.inst-upload input:disabled + span {
  opacity: 0.6;
  cursor: not-allowed;
}

.inst-hint {
  margin: 0;
  font-size: 0.72rem;
  color: var(--vb-muted, #8a8a8a);
  max-width: 14rem;
  line-height: 1.4;
}

.inst-fields {
  display: grid;
  gap: 0.85rem;
}

.inst-field {
  display: grid;
  gap: 0.35rem;
  font-size: 0.78rem;
  color: var(--vb-muted, #8a8a8a);
}

.inst-field input {
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 0.7rem;
  padding: 0.65rem 0.8rem;
  font: inherit;
  font-weight: 650;
  color: var(--vb-ink, #1c1c1c);
  background: #fafaf9;
}

.save-toast {
  position: fixed;
  right: 1.25rem;
  bottom: 1.25rem;
  z-index: 80;
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  max-width: min(24rem, calc(100vw - 2rem));
  margin: 0;
  padding: 0.85rem 1.05rem;
  border-radius: 1rem;
  background: var(--vb-ink, #1c1c1c);
  color: #fff;
  font-size: 0.84rem;
  font-weight: 650;
  box-shadow: 0 16px 40px rgba(28, 28, 28, 0.22);
}

.save-toast i {
  color: #9fdfb3;
}

.save-toast.is-error i {
  color: #f5b5b5;
}

.save-toast-enter-active,
.save-toast-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.save-toast-enter-from,
.save-toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
