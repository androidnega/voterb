<template>
  <form class="create-election-form" @submit.prevent="handleSubmit">
    <div class="form-body">
      <div class="field">
        <label for="election-title">Title <span class="req">*</span></label>
        <InputText
          id="election-title"
          v-model="form.title"
          class="w-full"
          placeholder="e.g. SRC General Elections 2026"
          required
          autofocus
        />
      </div>

      <div class="field">
        <label for="election-description">Description</label>
        <Textarea
          id="election-description"
          v-model="form.description"
          rows="2"
          class="w-full"
          autoResize
          placeholder="Optional overview for voters and staff"
        />
      </div>

      <div class="field">
        <div class="field-head">
          <label for="election-register">Voter register <span class="req">*</span></label>
          <span class="field-hint-inline">Who can vote</span>
        </div>

        <div v-if="!loadingRegisters && !registerOptions.length" class="register-empty">
          <p class="register-empty__title">No voter registers available for your scope.</p>
          <p class="register-empty__copy">
            <template v-if="isSubEC">
              Ask Main EC to create and approve a register for your faculty or department
              categories, then return here to create the election.
            </template>
            <template v-else>
              Create a Main EC institution register under Register, get approval, then return here.
            </template>
          </p>
          <router-link
            v-if="!isSubEC"
            to="/register"
            class="btn btn-primary"
            @click="$emit('cancel')"
          >
            <i class="fas fa-book" aria-hidden="true"></i>
            Go to Register
          </router-link>
        </div>

        <template v-else>
          <div v-if="registerOptions.length === 1 && selectedRegister" class="register-auto">
            <span class="register-auto__icon" aria-hidden="true">
              <i class="fas fa-users"></i>
            </span>
            <span class="register-auto__copy">
              <strong>{{ selectedRegister.name }}</strong>
              <small>
                {{ selectedRegister.entry_count || 0 }} voters
                <template v-if="selectedRegister.category_count">
                  · {{ selectedRegister.category_count }}
                  {{ selectedRegister.category_count === 1 ? 'category' : 'categories' }}
                </template>
              </small>
            </span>
            <span class="register-auto__status">
              <i class="fas fa-check" aria-hidden="true"></i>
              Selected
            </span>
          </div>
          <select
            v-else
            id="election-register"
            v-model="form.register_uuid"
            class="register-select"
            :disabled="loadingRegisters || !registerOptions.length"
            required
          >
            <option value="">{{ loadingRegisters ? 'Loading registers…' : 'Select a voter register' }}</option>
            <option v-for="register in registerOptions" :key="register.uuid" :value="register.uuid">
              {{ register.name }}
              ({{ register.category_count || 0 }} categories · {{ register.entry_count || 0 }} voters)
            </option>
          </select>
        </template>
      </div>

      <div class="field">
        <div class="field-head">
          <label>Schedule <span class="req">*</span></label>
          <span class="field-hint-inline">Opens and closes</span>
        </div>
        <div class="schedule-grid">
          <div class="schedule-field">
            <label class="schedule-field__label" for="election-start">Starts</label>
            <DatePicker
              id="election-start"
              v-model="form.start_date"
              showTime
              hourFormat="24"
              dateFormat="dd M yy"
              class="schedule-picker"
              inputClass="schedule-picker__input"
              panelClass="schedule-datepicker-panel"
              placeholder="Date & time"
              :manualInput="false"
              :showSeconds="false"
              :showIcon="true"
              iconDisplay="input"
              :hideOnDateTimeSelect="true"
              appendTo="body"
            />
            <p v-if="form.start_date" class="schedule-field__value">{{ formatSchedule(form.start_date) }}</p>
          </div>
          <div class="schedule-field">
            <label class="schedule-field__label" for="election-end">Ends</label>
            <DatePicker
              id="election-end"
              v-model="form.end_date"
              showTime
              hourFormat="24"
              dateFormat="dd M yy"
              class="schedule-picker"
              inputClass="schedule-picker__input"
              panelClass="schedule-datepicker-panel"
              placeholder="Date & time"
              :manualInput="false"
              :showSeconds="false"
              :showIcon="true"
              iconDisplay="input"
              :hideOnDateTimeSelect="true"
              appendTo="body"
            />
            <p v-if="form.end_date" class="schedule-field__value">{{ formatSchedule(form.end_date) }}</p>
          </div>
        </div>
      </div>

      <div class="field">
        <div class="field-head">
          <label>Voting channels</label>
          <span class="field-hint-inline">How voters take part</span>
        </div>
        <div class="channel-checks" role="group" aria-label="Voting channels">
          <label
            v-for="channel in channelOptions"
            :key="channel.key"
            class="channel-check"
            :class="{ 'is-selected': form[channel.key], 'is-disabled': channel.disabled }"
          >
            <input
              type="checkbox"
              :checked="form[channel.key]"
              :disabled="channel.disabled"
              @change="toggleChannel(channel.key)"
            />
            <span class="channel-check__box" aria-hidden="true">
              <i class="fas fa-check"></i>
            </span>
            <span class="channel-check__icon" aria-hidden="true">
              <i :class="channel.icon"></i>
            </span>
            <span class="channel-check__copy">
              <span class="channel-check__label">{{ channel.label }}</span>
              <small>{{ channel.hint }}</small>
            </span>
          </label>
        </div>
      </div>

      <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>
    </div>

    <div class="form-actions">
      <button type="button" class="btn btn-ghost" :disabled="loading" @click="$emit('cancel')">
        Cancel
      </button>
      <button type="submit" class="btn btn-primary" :disabled="loading || (!loadingRegisters && !registerOptions.length)">
        <i v-if="loading" class="fas fa-spinner fa-spin" aria-hidden="true"></i>
        {{ loading ? 'Creating…' : 'Create election' }}
      </button>
    </div>
  </form>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { electionApi } from '@/api/elections'
import { systemApi } from '@/api/system'
import { registerApi } from '@/api/registers'
import { useAuthStore } from '@/stores/auth'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import DatePicker from 'primevue/datepicker'

const emit = defineEmits(['success', 'cancel', 'pending-approval'])
const authStore = useAuthStore()
const isSubEC = computed(() => authStore.isSubEC && !authStore.isMainEC)

const form = ref({
  title: '',
  description: '',
  start_date: null,
  end_date: null,
  register_uuid: '',
  allow_web_voting: true,
  allow_ussd_voting: false,
  allow_sms_notifications: false,
})

const loading = ref(false)
const formError = ref('')
const smsEnabled = ref(false)
const registerOptions = ref([])
const loadingRegisters = ref(false)

const selectedRegister = computed(() =>
  registerOptions.value.find((register) => register.uuid === form.value.register_uuid),
)

const channelOptions = computed(() => [
  {
    key: 'allow_web_voting',
    label: 'Web',
    hint: 'Browser ballot',
    icon: 'fas fa-globe',
    disabled: false,
  },
  {
    key: 'allow_ussd_voting',
    label: 'USSD',
    hint: 'Dial short code',
    icon: 'fas fa-mobile-alt',
    disabled: false,
  },
  {
    key: 'allow_sms_notifications',
    label: 'SMS',
    hint: smsEnabled.value ? 'Alerts and tokens' : 'Disabled in Settings',
    icon: 'fas fa-message',
    disabled: !smsEnabled.value,
  },
])

const formatSchedule = (value) => {
  if (!value) return ''
  return new Date(value).toLocaleString(undefined, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const toggleChannel = (key) => {
  const channel = channelOptions.value.find((item) => item.key === key)
  if (channel?.disabled) return
  form.value[key] = !form.value[key]
  formError.value = ''
}

const loadFeatureFlags = async () => {
  try {
    const { data } = await systemApi.listFeatureFlags()
    const flags = Array.isArray(data) ? data : []
    const smsFlag = flags.find((f) => f.key === 'sms_notifications')
    smsEnabled.value = Boolean(smsFlag?.is_enabled)
    if (!smsEnabled.value) {
      form.value.allow_sms_notifications = false
    }
  } catch {
    smsEnabled.value = false
    form.value.allow_sms_notifications = false
  }
}

const loadRegisters = async () => {
  loadingRegisters.value = true
  try {
    const { data } = await registerApi.available()
    registerOptions.value = Array.isArray(data) ? data : (data.results || [])
    if (registerOptions.value.length === 1) {
      form.value.register_uuid = registerOptions.value[0].uuid
    }
  } catch (error) {
    console.error('Failed to load registers:', error)
    registerOptions.value = []
  } finally {
    loadingRegisters.value = false
  }
}

const handleSubmit = async () => {
  formError.value = ''
  const title = (form.value.title || '').trim()
  if (!title) {
    formError.value = 'Enter an election title.'
    return
  }
  if (!registerOptions.value.length) {
    formError.value = 'Create a voter register first, then return here.'
    return
  }
  if (!form.value.register_uuid) {
    formError.value = 'Select the voter register for this election.'
    return
  }
  if (!form.value.start_date || !form.value.end_date) {
    formError.value = 'Set both start and end dates.'
    return
  }
  if (new Date(form.value.end_date) <= new Date(form.value.start_date)) {
    formError.value = 'End must be after the start date.'
    return
  }
  if (!form.value.allow_web_voting && !form.value.allow_ussd_voting) {
    formError.value = 'Enable Web and/or USSD so students can cast ballots.'
    return
  }

  loading.value = true
  try {
    const { data, status } = await electionApi.create({
      title,
      description: (form.value.description || '').trim(),
      start_date: new Date(form.value.start_date).toISOString(),
      end_date: new Date(form.value.end_date).toISOString(),
      register_uuid: form.value.register_uuid,
      clone_register: false,
      allow_web_voting: form.value.allow_web_voting,
      allow_ussd_voting: form.value.allow_ussd_voting,
      allow_sms_notifications: smsEnabled.value ? form.value.allow_sms_notifications : false,
    })
    if (status === 202 || data?.status === 'pending') {
      emit('pending-approval', data)
      return
    }
    emit('success', data)
  } catch (error) {
    console.error('Failed to create election:', error)
    const data = error.response?.data
    formError.value =
      data?.title?.[0] ||
      data?.detail ||
      data?.error ||
      data?.register_uuid?.[0] ||
      data?.clone_register?.[0] ||
      data?.allow_web_voting?.[0] ||
      'Could not create election. Check the form and try again.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadFeatureFlags()
  loadRegisters()
})
</script>

<style scoped>
.create-election-form {
  display: flex;
  flex-direction: column;
  margin: -0.25rem -0.15rem 0;
  max-height: min(72vh, 40rem);
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 0.95rem;
  padding: 0.15rem 0.15rem 0.25rem;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.field {
  min-width: 0;
}

.field label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.78rem;
  font-weight: 750;
  letter-spacing: -0.01em;
  color: var(--vb-ink, #1c1c1c);
}

.field-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.4rem;
}

.field-head label {
  margin-bottom: 0;
}

.field-hint-inline {
  font-size: 0.7rem;
  color: var(--vb-muted, #8a8a8a);
  white-space: nowrap;
}

.req {
  color: #b45309;
}

.schedule-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
}

@media (max-width: 480px) {
  .schedule-grid {
    grid-template-columns: 1fr;
  }
}

.schedule-field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  min-width: 0;
}

.schedule-field__label {
  margin: 0;
  font-size: 0.7rem;
  font-weight: 650;
  color: var(--vb-muted, #8a8a8a);
}

.schedule-field__value {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--vb-ink, #1c1c1c);
  letter-spacing: -0.01em;
}

.register-select {
  width: 100%;
  padding: 0.58rem 0.75rem;
  border-radius: 0.7rem;
  border: 1px solid var(--vb-line, #ebeae4);
  background: #fff;
  color: var(--vb-ink, #1c1c1c);
  font-size: 0.88rem;
}

.register-select:focus {
  outline: none;
  border-color: var(--vb-accent-border, #c5d4bc);
  box-shadow: 0 0 0 3px var(--vb-focus-ring, rgba(61, 79, 68, 0.14));
}

.register-select:disabled {
  color: var(--vb-muted, #8a8a8a);
  background: var(--vb-panel, #f7f6f2);
}

.register-auto {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.7rem;
  padding: 0.7rem 0.8rem;
  border-radius: 0.7rem;
  background: var(--vb-panel, #f7f6f2);
  border: 1px solid var(--vb-line, #ebeae4);
  color: var(--vb-ink, #1c1c1c);
}

.register-auto__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.85rem;
  height: 1.85rem;
  border-radius: 0.5rem;
  background: var(--vb-accent, #3d4f44);
  color: #fff;
  font-size: 0.7rem;
}

.register-auto__copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 0.1rem;
}

.register-auto__copy strong {
  overflow: hidden;
  font-size: 0.82rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.register-auto__copy small {
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.7rem;
}

.register-auto__status {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  color: var(--vb-accent, #3d4f44);
  font-size: 0.68rem;
  font-weight: 750;
}

.register-empty {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  padding: 0.9rem 1rem;
  border-radius: 0.85rem;
  border: 1px dashed var(--vb-line, #ebeae4);
  background: var(--vb-panel, #f7f6f2);
}

.register-empty__title {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 750;
  color: var(--vb-ink, #1c1c1c);
}

.register-empty__copy {
  margin: 0;
  font-size: 0.78rem;
  line-height: 1.4;
  color: var(--vb-muted, #8a8a8a);
}

.register-empty .btn {
  align-self: flex-start;
  margin-top: 0.2rem;
}

.channel-checks {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.55rem;
}

@media (max-width: 520px) {
  .channel-checks {
    grid-template-columns: 1fr;
  }
}

.channel-check {
  position: relative;
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr);
  align-items: center;
  gap: 0.5rem;
  min-height: 3.2rem;
  padding: 0.62rem 0.7rem;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 0.8rem;
  background: #fff;
  cursor: pointer;
  user-select: none;
  color: var(--vb-ink, #1c1c1c);
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.channel-check:hover:not(.is-disabled) {
  border-color: #d6d3d1;
  background: #fcfcfb;
}

.channel-check.is-selected {
  border-color: rgba(61, 79, 68, 0.3);
  background: #f8faf7;
  box-shadow: inset 0 0 0 1px rgba(61, 79, 68, 0.08);
}

.channel-check input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.channel-check__box {
  width: 1rem;
  height: 1rem;
  border-radius: 0.32rem;
  border: 1.5px solid #d6d3d1;
  background: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: transparent;
  font-size: 0.55rem;
  transition: border-color 0.12s ease, background 0.12s ease, color 0.12s ease;
}

.channel-check input:checked + .channel-check__box {
  border-color: var(--vb-accent, #3d4f44);
  background: var(--vb-accent, #3d4f44);
  color: #fff;
}

.channel-check__icon {
  width: 1.75rem;
  height: 1.75rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.55rem;
  background: #f7f6f2;
  color: #8a8a8a;
  font-size: 0.72rem;
}

.channel-check.is-selected .channel-check__icon {
  background: #e8efe6;
  color: var(--vb-accent, #3d4f44);
}

.channel-check input:focus-visible + .channel-check__box {
  box-shadow: 0 0 0 3px var(--vb-focus-ring, rgba(61, 79, 68, 0.14));
}

.channel-check.is-disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.channel-check__label {
  display: block;
  font-size: 0.82rem;
  font-weight: 750;
  letter-spacing: -0.01em;
}

.channel-check__copy {
  min-width: 0;
}

.channel-check__copy small {
  display: block;
  margin-top: 0.08rem;
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.66rem;
  line-height: 1.2;
}

.form-error {
  margin: 0;
  padding: 0.65rem 0.75rem;
  border-radius: 0.7rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #be123c;
  font-size: 0.8rem;
  line-height: 1.4;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  flex-shrink: 0;
  margin-top: 1rem;
  padding-top: 0.95rem;
  border-top: 1px solid var(--vb-line, #ebeae4);
}

:deep(.p-inputtext),
:deep(.p-inputtextarea),
:deep(.p-datepicker),
:deep(.p-datepicker .p-inputtext) {
  width: 100%;
}

:deep(.p-inputtext),
:deep(.p-inputtextarea) {
  border-radius: 0.7rem;
  border-color: var(--vb-line, #ebeae4);
  padding: 0.58rem 0.75rem;
  font-size: 0.88rem;
  background: #fff;
}

:deep(.p-inputtext:enabled:focus),
:deep(.p-inputtextarea:enabled:focus) {
  border-color: var(--vb-accent-border, #c5d4bc);
  box-shadow: 0 0 0 3px var(--vb-focus-ring, rgba(61, 79, 68, 0.14));
}

:deep(.p-datepicker) {
  display: block;
}

:deep(.schedule-picker) {
  width: 100%;
}

:deep(.schedule-picker .p-inputtext),
:deep(.schedule-picker__input) {
  width: 100%;
  min-width: 0;
  padding: 0.5rem 2rem 0.5rem 0.7rem;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 0.65rem;
  background: #fff;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--vb-ink, #1c1c1c);
  box-shadow: none;
}

:deep(.schedule-picker .p-inputtext:enabled:focus),
:deep(.schedule-picker__input:enabled:focus) {
  border-color: var(--vb-accent-border, #c5d4bc);
  box-shadow: 0 0 0 3px var(--vb-focus-ring, rgba(61, 79, 68, 0.12));
}

:deep(.schedule-picker .p-datepicker-input-icon-container),
:deep(.schedule-picker .p-datepicker-trigger),
:deep(.schedule-picker .p-datepicker-input-icon) {
  color: var(--vb-muted, #8a8a8a);
  right: 0.5rem;
}

:deep(.schedule-picker .p-icon) {
  width: 0.8rem;
  height: 0.8rem;
}
</style>

<style>
/* DatePicker panel is teleported to body */
.schedule-datepicker-panel.p-datepicker-panel,
.p-datepicker-panel.schedule-datepicker-panel {
  width: min(17.5rem, calc(100vw - 1.5rem)) !important;
  min-width: 0 !important;
  padding: 0.55rem !important;
  border-radius: 0.85rem !important;
  border: 1px solid #ebeae4 !important;
  box-shadow: 0 14px 36px rgba(28, 28, 28, 0.14) !important;
  font-size: 0.8rem !important;
}

.schedule-datepicker-panel .p-datepicker-header {
  padding: 0.15rem 0.2rem 0.45rem !important;
}

.schedule-datepicker-panel .p-datepicker-title {
  font-size: 0.82rem !important;
  font-weight: 700 !important;
}

.schedule-datepicker-panel .p-datepicker-calendar th,
.schedule-datepicker-panel .p-datepicker-calendar td {
  padding: 0.1rem !important;
}

.schedule-datepicker-panel .p-datepicker-day,
.schedule-datepicker-panel .p-datepicker-weekday {
  width: 1.85rem !important;
  height: 1.85rem !important;
  font-size: 0.75rem !important;
}

.schedule-datepicker-panel .p-timepicker,
.schedule-datepicker-panel .p-datepicker-time-picker {
  padding: 0.4rem 0.2rem 0.15rem !important;
  border-top: 1px solid #ebeae4 !important;
  gap: 0.35rem !important;
}

.schedule-datepicker-panel .p-timepicker span,
.schedule-datepicker-panel .p-datepicker-time-picker span {
  font-size: 0.9rem !important;
  font-weight: 700 !important;
}

.schedule-datepicker-panel .p-timepicker button,
.schedule-datepicker-panel .p-datepicker-time-picker button {
  width: 1.5rem !important;
  height: 1.5rem !important;
}
</style>
