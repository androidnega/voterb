<template>
  <AdminDashboard v-if="authStore.isAdmin" />
  <div v-else class="text-center py-12 text-gray-500">
    <p class="mb-2">Could not load admin dashboard.</p>
    <p class="text-xs text-gray-400 mb-4">role: {{ authStore.roleName || 'none' }}</p>
    <button
      @click="reload"
      class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
    >
      Retry
    </button>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import AdminDashboard from '@/views/admin/AdminDashboardView.vue'

const authStore = useAuthStore()

const reload = async () => {
  authStore.initialized = false
  authStore.initPromise = null
  await authStore.initialize()
}
</script>
