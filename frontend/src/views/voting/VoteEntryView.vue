<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
    <div class="max-w-2xl mx-auto">
      <!-- Back button -->
      <Button 
        label="← Back to Dashboard" 
        severity="secondary" 
        text 
        @click="$router.push('/student')" 
        class="mb-6"
      />

      <!-- Card -->
      <Card>
        <template #title>
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
            </div>
            <span class="text-xl font-semibold text-gray-900">{{ electionTitle }}</span>
          </div>
        </template>

        <template #content>
          <!-- Step 1: Request SVT -->
          <div v-if="step === 'request'" class="space-y-4">
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
              <p><strong>Secure Voting Token (SVT)</strong></p>
              <p class="mt-1">A 6-digit code will be sent to your registered phone number. Enter it to start voting.</p>
            </div>
            <Button 
              label="Request SVT Code" 
              :loading="requesting" 
              @click="requestSVT" 
              class="w-full"
            />
          </div>

          <!-- Step 2: Validate SVT -->
          <div v-else-if="step === 'validate'" class="space-y-4">
            <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-700">
              <p>✅ SVT code sent to your phone. Enter it below.</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">6-digit code</label>
              <InputText 
                v-model="svtCode" 
                type="text" 
                maxlength="6"
                placeholder="123456" 
                class="w-full text-center text-2xl tracking-widest"
                @keyup.enter="validateSVT"
              />
            </div>
            <div class="flex space-x-3">
              <Button label="Verify" @click="validateSVT" :loading="validating" class="flex-1" />
              <Button label="Resend" severity="secondary" @click="resendSVT" text />
            </div>
            <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {{ errorMessage }}
            </div>
          </div>

          <!-- Step 3: Redirect to ballot -->
          <div v-else-if="step === 'redirecting'" class="text-center py-8">
            <i class="pi pi-spin pi-spinner text-3xl text-green-600"></i>
            <p class="mt-2 text-gray-600">Redirecting to ballot...</p>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { votingApi } from '@/api/voting'
import Card from 'primevue/card'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'

const route = useRoute()
const router = useRouter()
const electionUuid = route.params.uuid

const electionTitle = ref('Loading...')
const step = ref('request') // request | validate | redirecting
const svtCode = ref('')
const requesting = ref(false)
const validating = ref(false)
const errorMessage = ref('')

onMounted(async () => {
  try {
    // Fetch election title (or get from store)
    // For now, we'll just set a placeholder
    electionTitle.value = 'Election'
    // You could fetch election details here
  } catch (error) {
    console.error(error)
  }
})

const requestSVT = async () => {
  requesting.value = true
  errorMessage.value = ''
  try {
    await votingApi.requestSVT(electionUuid)
    step.value = 'validate'
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Failed to send SVT. Please try again.'
  } finally {
    requesting.value = false
  }
}

const validateSVT = async () => {
  if (svtCode.value.length !== 6) {
    errorMessage.value = 'Please enter a valid 6-digit code.'
    return
  }
  validating.value = true
  errorMessage.value = ''
  try {
    await votingApi.validateSVT(electionUuid, svtCode.value)
    step.value = 'redirecting'
    // Redirect to ballot wizard
    router.push(`/vote/${electionUuid}/ballot`)
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Invalid code. Please try again.'
  } finally {
    validating.value = false
  }
}

const resendSVT = async () => {
  try {
    await votingApi.requestSVT(electionUuid)
    alert('New SVT code sent!')
  } catch (error) {
    alert('Failed to resend. Please try again.')
  }
}
</script>
