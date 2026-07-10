<template>
  <div>
    <h2 class="text-lg font-semibold text-gray-900 mb-4">Integration Settings</h2>
    
    <div class="space-y-6 max-w-2xl">
      <!-- SMS Provider -->
      <div class="bg-gray-50 rounded-lg border border-gray-200 p-6">
        <h3 class="font-medium text-gray-900 mb-3">SMS Provider</h3>
        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Provider</label>
            <select v-model="smsProvider.value" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
              <option value="arkesel">Arkesel</option>
              <option value="twilio">Twilio</option>
              <option value="moolre">Moolre</option>
              <option value="none">None</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
            <input v-model="smsApiKey.value" type="password" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" placeholder="Enter API key..." />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Sender ID</label>
            <input v-model="smsSenderId.value" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" placeholder="VoterB" />
          </div>
        </div>
      </div>

      <!-- Email Provider -->
      <div class="bg-gray-50 rounded-lg border border-gray-200 p-6">
        <h3 class="font-medium text-gray-900 mb-3">Email Settings</h3>
        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">From Address</label>
            <input v-model="emailFrom.value" type="email" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" placeholder="noreply@voterb.com" />
          </div>
        </div>
      </div>

      <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <button @click="saveIntegrations" :disabled="saving" class="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50">
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

const smsProvider = ref({ value: 'arkesel' })
const smsApiKey = ref({ value: '' })
const smsSenderId = ref({ value: 'VoterB' })
const emailFrom = ref({ value: 'noreply@voterb.com' })

const saving = ref(false)
const saveMessage = ref('')
const saveSuccess = ref(false)

const fetchSettings = async () => {
  try {
    const response = await systemApi.getSettingsByCategory('integrations')
    const settings = response.data
    settings.forEach(s => {
      if (s.key === 'sms_provider') smsProvider.value.value = s.value
      if (s.key === 'sms_api_key') smsApiKey.value.value = s.value
      if (s.key === 'sms_sender_id') smsSenderId.value.value = s.value
      if (s.key === 'email_from_address') emailFrom.value.value = s.value
    })
  } catch (error) {
    console.error('Failed to fetch settings:', error)
  }
}

const saveIntegrations = async () => {
  saving.value = true
  saveMessage.value = ''
  try {
    await systemApi.updateSetting('sms_provider', smsProvider.value.value)
    await systemApi.updateSetting('sms_api_key', smsApiKey.value.value)
    await systemApi.updateSetting('sms_sender_id', smsSenderId.value.value)
    await systemApi.updateSetting('email_from_address', emailFrom.value.value)
    saveSuccess.value = true
    saveMessage.value = 'Integration settings saved successfully!'
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
