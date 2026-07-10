<template>
  <div>
    <h2 class="text-lg font-semibold text-gray-900 mb-4">Maintenance Mode</h2>
    
    <div class="space-y-6 max-w-2xl">
      <div class="bg-gray-50 rounded-lg border border-gray-200 p-6">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="font-medium text-gray-900">Maintenance Mode</h3>
            <p class="text-sm text-gray-500">When enabled, only super admins can access the system.</p>
          </div>
          <button 
            @click="toggleMaintenance"
            class="relative inline-flex items-center h-6 rounded-full w-11 transition-colors duration-200 focus:outline-none"
            :class="maintenance.is_active ? 'bg-red-600' : 'bg-gray-300'"
          >
            <span 
              class="inline-block w-4 h-4 transform bg-white rounded-full transition-transform duration-200"
              :class="maintenance.is_active ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Maintenance Message</label>
        <textarea v-model="maintenance.message" rows="3" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" placeholder="Enter the maintenance message..." />
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Scheduled Start</label>
          <input v-model="maintenance.scheduled_start" type="datetime-local" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Scheduled End</label>
          <input v-model="maintenance.scheduled_end" type="datetime-local" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
        </div>
      </div>

      <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <button @click="saveMaintenance" :disabled="saving" class="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50">
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

const maintenance = ref({
  is_active: false,
  message: 'The system is currently under maintenance. Please check back later.',
  scheduled_start: null,
  scheduled_end: null
})

const saving = ref(false)
const saveMessage = ref('')
const saveSuccess = ref(false)

const fetchMaintenance = async () => {
  try {
    const response = await systemApi.getMaintenance()
    maintenance.value = response.data
  } catch (error) {
    console.error('Failed to fetch maintenance state:', error)
  }
}

const toggleMaintenance = () => {
  maintenance.value.is_active = !maintenance.value.is_active
  saveMaintenance()
}

const saveMaintenance = async () => {
  saving.value = true
  saveMessage.value = ''
  try {
    await systemApi.updateMaintenance(maintenance.value)
    saveSuccess.value = true
    saveMessage.value = 'Maintenance settings saved successfully!'
  } catch (error) {
    console.error('Failed to save:', error)
    saveSuccess.value = false
    saveMessage.value = 'Failed to save settings. Please try again.'
  } finally {
    saving.value = false
    setTimeout(() => { saveMessage.value = '' }, 5000)
  }
}

onMounted(fetchMaintenance)
</script>
