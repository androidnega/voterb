<template>
  <div>
      <div class="mb-6">
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">Settings</h1>
        <p class="text-gray-500 text-sm mt-1">Super admin configuration for the VoterB platform.</p>
      </div>

      <div v-if="!isSuperAdmin" class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
        Only super admins can change system settings.
      </div>

      <div v-else class="space-y-6">
        <section class="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h2 class="text-sm font-semibold text-gray-900 mb-4">Platform</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p class="text-gray-500">Application</p>
              <p class="font-medium text-gray-900 mt-1">VoterB Election Platform</p>
            </div>
            <div>
              <p class="text-gray-500">Environment</p>
              <p class="font-medium text-gray-900 mt-1">Development</p>
            </div>
            <div>
              <p class="text-gray-500">Signed in as</p>
              <p class="font-medium text-gray-900 mt-1">{{ userEmail }}</p>
            </div>
            <div>
              <p class="text-gray-500">Role</p>
              <p class="font-medium text-gray-900 mt-1 capitalize">{{ roleName }}</p>
            </div>
          </div>
        </section>

        <section class="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h2 class="text-sm font-semibold text-gray-900 mb-4">Security</h2>
          <div class="space-y-4">
            <label class="flex items-center justify-between gap-4">
              <div>
                <p class="text-sm font-medium text-gray-900">Require OTP for login</p>
                <p class="text-xs text-gray-500">All users must verify OTP before signing in.</p>
              </div>
              <input v-model="settings.requireOtp" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-emerald-600" />
            </label>
            <label class="flex items-center justify-between gap-4">
              <div>
                <p class="text-sm font-medium text-gray-900">Enable web voting</p>
                <p class="text-xs text-gray-500">Allow voters to cast ballots through the web app.</p>
              </div>
              <input v-model="settings.webVoting" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-emerald-600" />
            </label>
            <label class="flex items-center justify-between gap-4">
              <div>
                <p class="text-sm font-medium text-gray-900">Enable USSD voting</p>
                <p class="text-xs text-gray-500">Allow voting through USSD channels.</p>
              </div>
              <input v-model="settings.ussdVoting" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-emerald-600" />
            </label>
          </div>
        </section>

        <section class="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h2 class="text-sm font-semibold text-gray-900 mb-4">Notifications</h2>
          <div class="space-y-4">
            <label class="flex items-center justify-between gap-4">
              <div>
                <p class="text-sm font-medium text-gray-900">SMS notifications</p>
                <p class="text-xs text-gray-500">Send OTP and election alerts via SMS.</p>
              </div>
              <input v-model="settings.smsNotifications" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-emerald-600" />
            </label>
            <label class="flex items-center justify-between gap-4">
              <div>
                <p class="text-sm font-medium text-gray-900">Email notifications</p>
                <p class="text-xs text-gray-500">Send admin alerts and result updates by email.</p>
              </div>
              <input v-model="settings.emailNotifications" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-emerald-600" />
            </label>
          </div>
        </section>

        <div class="flex items-center justify-between gap-4">
          <p v-if="saveMessage" class="text-sm text-emerald-700">{{ saveMessage }}</p>
          <div class="ml-auto flex gap-3">
            <button
              type="button"
              @click="resetSettings"
              class="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
            >
              Reset
            </button>
            <button
              type="button"
              @click="saveSettings"
              class="px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700"
            >
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const saveMessage = ref('')

const defaultSettings = {
  requireOtp: true,
  webVoting: true,
  ussdVoting: false,
  smsNotifications: true,
  emailNotifications: false,
}

const settings = ref({ ...defaultSettings })

const roleName = computed(() => {
  const user = authStore.user
  if (!user) return ''
  if (typeof user.role_name === 'string' && user.role_name) return user.role_name
  if (typeof user.role === 'object' && user.role?.name) return user.role.name
  if (user.is_superuser) return 'super_admin'
  if (user.is_staff) return 'admin'
  return ''
})

const isSuperAdmin = computed(() => roleName.value === 'super_admin' || !!authStore.user?.is_superuser)
const userEmail = computed(() => authStore.user?.email || authStore.user?.index_number || 'Unknown')

const loadSettings = () => {
  try {
    const saved = localStorage.getItem('voterb_settings')
    if (saved) {
      settings.value = { ...defaultSettings, ...JSON.parse(saved) }
    }
  } catch {
    settings.value = { ...defaultSettings }
  }
}

const saveSettings = () => {
  localStorage.setItem('voterb_settings', JSON.stringify(settings.value))
  saveMessage.value = 'Settings saved locally.'
  setTimeout(() => {
    saveMessage.value = ''
  }, 3000)
}

const resetSettings = () => {
  settings.value = { ...defaultSettings }
  localStorage.removeItem('voterb_settings')
  saveMessage.value = 'Settings reset to defaults.'
  setTimeout(() => {
    saveMessage.value = ''
  }, 3000)
}

onMounted(() => {
  loadSettings()
})
</script>
