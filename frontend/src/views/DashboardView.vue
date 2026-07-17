<template>
  <!-- Router already mounts AdminLayout — do not wrap again -->
  <component :is="activeDashboard" v-if="activeDashboard" />
  <div v-else class="text-center py-12 text-gray-500">
    <i class="fas fa-spinner fa-spin text-3xl"></i>
    <p class="mt-2">Loading dashboard...</p>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AdminDashboard from '@/views/admin/AdminDashboardView.vue'
import AuditorDashboard from '@/views/admin/AuditorDashboardView.vue'
import SuperAdminDashboard from '@/views/admin/SuperAdminDashboardView.vue'

const router = useRouter()
const authStore = useAuthStore()

const activeDashboard = computed(() => {
  if (authStore.isAuditor) return AuditorDashboard
  if (authStore.isSuperAdmin) return SuperAdminDashboard
  if (authStore.isMainEC || authStore.isElectionManager || authStore.isSubEC) return AdminDashboard
  return null
})

onMounted(async () => {
  if (!authStore.initialized) {
    await authStore.initialize()
  }
  if (!authStore.isAuthenticated) {
    router.replace('/login')
    return
  }
  if (authStore.isStudent) {
    router.replace(authStore.homeRoute)
  }
})
</script>
