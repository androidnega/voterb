<template>
  <div>
    <h2 class="text-lg font-semibold text-gray-900 mb-4">Feature Flags</h2>
    
    <div v-if="loading" class="text-center py-8 text-gray-500">
      <i class="fas fa-spinner fa-spin"></i> Loading...
    </div>

    <div v-else class="space-y-6">
      <div v-for="(group, category) in groupedFlags" :key="category" class="bg-gray-50 rounded-lg border border-gray-200 p-4">
        <h3 class="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">{{ category }}</h3>
        <div class="space-y-2">
          <div v-for="flag in group" :key="flag.key" class="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200 hover:border-emerald-200 transition-colors">
            <div>
              <p class="font-medium text-gray-900">{{ formatKey(flag.key) }}</p>
              <p class="text-sm text-gray-500">{{ flag.description || 'No description' }}</p>
            </div>
            <div class="flex items-center gap-3 ml-4">
              <span class="text-sm font-medium" :class="flag.is_enabled ? 'text-emerald-600' : 'text-gray-400'">
                {{ flag.is_enabled ? 'ON' : 'OFF' }}
              </span>
              <button 
                @click="toggleFlag(flag)"
                class="relative inline-flex items-center h-6 rounded-full w-11 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500"
                :class="flag.is_enabled ? 'bg-emerald-600' : 'bg-gray-300'"
              >
                <span 
                  class="inline-block w-4 h-4 transform bg-white rounded-full transition-transform duration-200 shadow-sm"
                  :class="flag.is_enabled ? 'translate-x-6' : 'translate-x-1'"
                />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="saveMessage" class="mt-4 p-4 rounded-lg" :class="saveSuccess ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'">
      {{ saveMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { systemApi } from '@/api/system'

const flags = ref([])
const loading = ref(true)
const saveMessage = ref('')
const saveSuccess = ref(false)

const groupedFlags = computed(() => {
  const groups = {}
  flags.value.forEach(flag => {
    const category = flag.category || 'general'
    if (!groups[category]) groups[category] = []
    groups[category].push(flag)
  })
  return groups
})

const formatKey = (key) => {
  return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

const fetchFlags = async () => {
  loading.value = true
  try {
    const response = await systemApi.listFeatureFlags()
    flags.value = response.data
  } catch (error) {
    console.error('Failed to fetch feature flags:', error)
  } finally {
    loading.value = false
  }
}

const toggleFlag = async (flag) => {
  const newValue = !flag.is_enabled
  try {
    await systemApi.updateFeatureFlag(flag.key, newValue)
    flag.is_enabled = newValue
    saveSuccess.value = true
    saveMessage.value = `${formatKey(flag.key)} ${newValue ? 'enabled' : 'disabled'} successfully!`
  } catch (error) {
    console.error('Failed to update flag:', error)
    saveSuccess.value = false
    saveMessage.value = 'Failed to update flag. Please try again.'
  } finally {
    setTimeout(() => { saveMessage.value = '' }, 3000)
  }
}

onMounted(fetchFlags)
</script>
