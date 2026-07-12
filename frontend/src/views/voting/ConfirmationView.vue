<template>
  <div class="max-w-md w-full mx-auto bg-white rounded-xl border border-gray-200 p-8 text-center">
    <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
      <i class="pi pi-check-circle text-green-600 text-4xl"></i>
    </div>
    <h2 class="text-2xl font-bold text-gray-900">Vote Confirmed!</h2>
    <p class="text-gray-600 mt-2">Your vote has been successfully recorded.</p>

    <div class="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <p class="text-sm text-gray-500">Confirmation Code</p>
      <p class="text-lg font-mono font-bold text-gray-900">{{ confirmationCode }}</p>
    </div>

    <p class="text-xs text-gray-400 mt-4">You can verify your vote using this code.</p>

    <router-link
      to="/student"
      class="mt-6 block w-full py-3 px-4 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors text-center"
    >
      Back to My Elections
    </router-link>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const confirmationCode = ref('VTB-2026-000001')

onMounted(() => {
  confirmationCode.value = route.query.code || 'VTB-2026-000001'
})
</script>
