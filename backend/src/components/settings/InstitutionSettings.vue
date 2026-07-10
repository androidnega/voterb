<template>
  <div>
    <h2 class="text-lg font-semibold text-gray-900 mb-4">Institution Settings</h2>
    
    <div v-if="loading" class="text-center py-8 text-gray-500">
      <i class="fas fa-spinner fa-spin"></i> Loading...
    </div>

    <form v-else @submit.prevent="saveInstitution" class="space-y-6 max-w-2xl">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Institution Name</label>
          <input v-model="form.name" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Short Name</label>
          <input v-model="form.short_name" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Primary Color</label>
          <div class="flex items-center gap-3">
            <input v-model="form.primary_color" type="color" class="w-12 h-12 rounded-lg border border-gray-300 cursor-pointer" />
            <input v-model="form.primary_color" type="text" class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Secondary Color</label>
          <div class="flex items-center gap-3">
            <input v-model="form.secondary_color" type="color" class="w-12 h-12 rounded-lg border border-gray-300 cursor-pointer" />
            <input v-model="form.secondary_color" type="text" class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Contact Email</label>
          <input v-model="form.contact_email" type="email" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Contact Phone</label>
          <input v-model="form.contact_phone" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Address</label>
        <textarea v-model="form.address" rows="2" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"></textarea>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Logo</label>
        <div class="flex items-center gap-4">
          <div class="w-20 h-20 bg-gray-100 rounded-lg border border-gray-300 flex items-center justify-center overflow-hidden">
            <img v-if="form.logo" :src="form.logo" alt="Logo" class="w-full h-full object-cover" />
            <i v-else class="fas fa-image text-gray-300 text-2xl"></i>
          </div>
          <input type="file" accept="image/*" @change="handleLogoUpload" class="text-sm text-gray-500" />
        </div>
      </div>

      <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <button type="button" @click="resetForm" class="px-4 py-2 text-gray-600 hover:text-gray-800">Reset</button>
        <button type="submit" :disabled="saving" class="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50">
          <i v-if="saving" class="fas fa-spinner fa-spin mr-2"></i>
          {{ saving ? 'Saving...' : 'Save Changes' }}
        </button>
      </div>

      <div v-if="saveMessage" class="p-4 rounded-lg" :class="saveSuccess ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'">
        {{ saveMessage }}
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { systemApi } from '@/api/system'

const form = ref({
  name: '',
  short_name: '',
  primary_color: '#1e5f46',
  secondary_color: '#0f7d3e',
  contact_email: '',
  contact_phone: '',
  address: '',
  logo: null
})

const originalForm = ref({})
const loading = ref(true)
const saving = ref(false)
const saveMessage = ref('')
const saveSuccess = ref(false)

const fetchInstitution = async () => {
  loading.value = true
  try {
    const response = await systemApi.getInstitution()
    if (response.data && Object.keys(response.data).length > 0) {
      form.value = response.data
      originalForm.value = JSON.parse(JSON.stringify(response.data))
    }
  } catch (error) {
    console.error('Failed to fetch institution:', error)
  } finally {
    loading.value = false
  }
}

const handleLogoUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      form.value.logo = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const saveInstitution = async () => {
  saving.value = true
  saveMessage.value = ''
  try {
    await systemApi.updateInstitution(form.value)
    saveSuccess.value = true
    saveMessage.value = 'Settings saved successfully!'
    originalForm.value = JSON.parse(JSON.stringify(form.value))
  } catch (error) {
    console.error('Failed to save:', error)
    saveSuccess.value = false
    saveMessage.value = 'Failed to save settings. Please try again.'
  } finally {
    saving.value = false
    setTimeout(() => { saveMessage.value = '' }, 5000)
  }
}

const resetForm = () => {
  form.value = JSON.parse(JSON.stringify(originalForm.value))
}

onMounted(() => {
  fetchInstitution()
})
</script>
