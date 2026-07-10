<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-white rounded-xl shadow-sm border border-gray-200 p-8">
      <div class="text-center mb-6">
        <i class="fas fa-shield-alt text-4xl text-emerald-600"></i>
        <h1 class="text-2xl font-bold text-gray-900 mt-2">Verify Seal</h1>
        <p class="text-sm text-gray-500">Enter a seal hash to verify its authenticity.</p>
      </div>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Seal Hash</label>
          <input 
            v-model="sealHash" 
            type="text" 
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent font-mono text-sm"
            placeholder="Paste seal hash here..."
          />
        </div>

        <button 
          @click="verify" 
          :disabled="!sealHash || loading"
          class="w-full py-2 px-4 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
        >
          <i v-if="loading" class="fas fa-spinner fa-spin mr-2"></i>
          {{ loading ? 'Verifying...' : 'Verify' }}
        </button>
      </div>

      <div v-if="result" class="mt-6 p-4 rounded-lg" :class="result.valid ? 'bg-emerald-50 border border-emerald-200' : 'bg-red-50 border border-red-200'">
        <div class="flex items-center gap-2">
          <i :class="result.valid ? 'fas fa-check-circle text-emerald-600' : 'fas fa-times-circle text-red-600'"></i>
          <span class="font-medium" :class="result.valid ? 'text-emerald-700' : 'text-red-700'">
            {{ result.valid ? 'Valid Seal' : 'Invalid Seal' }}
          </span>
        </div>
        <div v-if="result.valid" class="mt-2 text-sm text-gray-700 space-y-1">
          <p><span class="font-semibold">Type:</span> {{ result.type }}</p>
          <p><span class="font-semibold">Election:</span> {{ result.election }}</p>
          <p><span class="font-semibold">Created:</span> {{ formatDate(result.created_at) }}</p>
          <p><span class="font-semibold">Status:</span> {{ result.status }}</p>
        </div>
        <div v-else class="mt-2 text-sm text-red-600">
          {{ result.message || 'No matching seal found.' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { strongroomApi } from '@/api/strongroom'

const sealHash = ref('')
const loading = ref(false)
const result = ref(null)

const verify = async () => {
  if (!sealHash.value) return
  loading.value = true
  result.value = null
  try {
    const response = await strongroomApi.verifySeal(sealHash.value)
    result.value = response.data
  } catch (error) {
    alert('Verification failed. Please try again.')
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  return new Date(date).toLocaleString()
}
</script>
