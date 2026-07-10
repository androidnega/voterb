<template>
  <div>
    <h2 class="text-lg font-semibold text-gray-900 mb-4">Integration Settings</h2>
    
    <div v-if="loading" class="text-center py-8 text-gray-500">
      <i class="fas fa-spinner fa-spin"></i> Loading...
    </div>

    <div v-else class="space-y-6 max-w-3xl">
      <!-- SMS Provider -->
      <div class="bg-gray-50 rounded-lg border border-gray-200 p-6">
        <h3 class="font-medium text-gray-900 mb-4">SMS Provider</h3>
        <div class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Primary Provider</label>
              <select v-model="smsPrimary.value" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
                <option value="arkesel">Arkesel</option>
                <option value="moolre">Moolre</option>
                <option value="twilio">Twilio</option>
                <option value="none">None</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Fallback Provider</label>
              <select v-model="smsFallback.value" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
                <option value="moolre">Moolre</option>
                <option value="arkesel">Arkesel</option>
                <option value="twilio">Twilio</option>
                <option value="none">None</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Sender ID</label>
            <input v-model="smsSenderId.value" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" placeholder="VoterB" />
          </div>
          <div class="border-t border-gray-200 pt-4">
            <p class="text-sm font-medium text-gray-700 mb-2">Arkesel Configuration</p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                <div class="relative">
                  <input :type="showArkeselKey ? 'text' : 'password'" v-model="smsArkeselKey.value" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent pr-10" placeholder="Enter API key" />
                  <button @click="showArkeselKey = !showArkeselKey" class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600">
                    <i :class="showArkeselKey ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                  </button>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">API URL</label>
                <input v-model="smsArkeselUrl.value" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" placeholder="https://sms.arkesel.com/api/v2/sms/send" />
              </div>
            </div>
          </div>
          <div class="border-t border-gray-200 pt-4">
            <p class="text-sm font-medium text-gray-700 mb-2">Moolre Configuration (Fallback)</p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                <div class="relative">
                  <input :type="showMoolreKey ? 'text' : 'password'" v-model="smsMoolreKey.value" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent pr-10" placeholder="Enter API key" />
                  <button @click="showMoolreKey = !showMoolreKey" class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600">
                    <i :class="showMoolreKey ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                  </button>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">API URL</label>
                <input v-model="smsMoolreUrl.value" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" placeholder="https://api.moolre.com/v1/sms/send" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- USSD Settings -->
      <div class="bg-gray-50 rounded-lg border border-gray-200 p-6">
        <h3 class="font-medium text-gray-900 mb-4">USSD Settings</h3>
        <div class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Service Code</label>
              <input v-model="ussdServiceCode.value" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" placeholder="*920#" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Session Timeout (seconds)</label>
              <input v-model="ussdTimeout.value" type="number" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Callback URL</label>
            <input v-model="ussdCallbackUrl.value" type="url" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" placeholder="https://your-domain.com/api/v1/ussd/callback/" />
            <p class="text-xs text-gray-400 mt-1">This URL will be configured in Arkesel USSD gateway</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Webhook Secret (for authentication)</label>
            <div class="relative">
              <input :type="showUssdKey ? 'text' : 'password'" v-model="ussdApiKey.value" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent pr-10" placeholder="Enter webhook secret" />
              <button @click="showUssdKey = !showUssdKey" class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600">
                <i :class="showUssdKey ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Save Button -->
      <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <button @click="saveIntegrations" :disabled="saving" class="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors">
          <i v-if="saving" class="fas fa-spinner fa-spin mr-2"></i>
          {{ saving ? 'Saving...' : 'Save Changes' }}
        </button>
      </div>

      <div v-if="saveMessage" class="p-4 rounded-lg" :class="saveSuccess ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'">
        {{ saveMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { systemApi } from '@/api/system'

const loading = ref(true)
const saving = ref(false)
const saveMessage = ref('')
const saveSuccess = ref(false)

// SMS Settings
const smsPrimary = ref({ value: 'arkesel' })
const smsFallback = ref({ value: 'moolre' })
const smsSenderId = ref({ value: 'VoterB' })
const smsArkeselKey = ref({ value: '' })
const smsArkeselUrl = ref({ value: 'https://sms.arkesel.com/api/v2/sms/send' })
const smsMoolreKey = ref({ value: '' })
const smsMoolreUrl = ref({ value: 'https://api.moolre.com/v1/sms/send' })
const showArkeselKey = ref(false)
const showMoolreKey = ref(false)

// USSD Settings
const ussdServiceCode = ref({ value: '*920#' })
const ussdTimeout = ref({ value: '300' })
const ussdCallbackUrl = ref({ value: '' })
const ussdApiKey = ref({ value: '' })
const showUssdKey = ref(false)

const fetchSettings = async () => {
  loading.value = true
  try {
    const response = await systemApi.getSettingsByCategory('integrations')
    const settings = response.data
    settings.forEach(s => {
      if (s.key === 'sms_provider_primary') smsPrimary.value.value = s.value
      if (s.key === 'sms_provider_fallback') smsFallback.value.value = s.value
      if (s.key === 'sms_arkesel_sender_id') smsSenderId.value.value = s.value
      if (s.key === 'sms_arkesel_api_key') smsArkeselKey.value.value = s.value
      if (s.key === 'sms_arkesel_url') smsArkeselUrl.value.value = s.value
      if (s.key === 'sms_moolre_api_key') smsMoolreKey.value.value = s.value
      if (s.key === 'sms_moolre_url') smsMoolreUrl.value.value = s.value
      if (s.key === 'ussd_service_code') ussdServiceCode.value.value = s.value
      if (s.key === 'ussd_session_timeout') ussdTimeout.value.value = s.value
      if (s.key === 'ussd_callback_url') ussdCallbackUrl.value.value = s.value
      if (s.key === 'ussd_api_key') ussdApiKey.value.value = s.value
    })
  } catch (error) {
    console.error('Failed to fetch settings:', error)
  } finally {
    loading.value = false
  }
}

const saveIntegrations = async () => {
  saving.value = true
  saveMessage.value = ''
  try {
    const updates = [
      { key: 'sms_provider_primary', value: smsPrimary.value.value },
      { key: 'sms_provider_fallback', value: smsFallback.value.value },
      { key: 'sms_arkesel_sender_id', value: smsSenderId.value.value },
      { key: 'sms_arkesel_api_key', value: smsArkeselKey.value.value },
      { key: 'sms_arkesel_url', value: smsArkeselUrl.value.value },
      { key: 'sms_moolre_api_key', value: smsMoolreKey.value.value },
      { key: 'sms_moolre_url', value: smsMoolreUrl.value.value },
      { key: 'ussd_service_code', value: ussdServiceCode.value.value },
      { key: 'ussd_session_timeout', value: ussdTimeout.value.value },
      { key: 'ussd_callback_url', value: ussdCallbackUrl.value.value },
      { key: 'ussd_api_key', value: ussdApiKey.value.value },
    ]
    for (const update of updates) {
      await systemApi.updateSetting(update.key, update.value)
    }
    saveSuccess.value = true
    saveMessage.value = 'All integration settings saved successfully!'
  } catch (error) {
    console.error('Failed to save:', error)
    saveSuccess.value = false
    saveMessage.value = 'Failed to save settings. Please try again.'
  } finally {
    saving.value = false
    setTimeout(() => { saveMessage.value = '' }, 5000)
  }
}

onMounted(fetchSettings)
</script>
