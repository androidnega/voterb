<template>
  <StudentDashboard v-if="isStudent" />
  <AdminDashboard v-else-if="isStaffDashboard" />
  <div v-else class="text-center py-12 text-gray-500">
    <i class="fas fa-spinner fa-spin text-3xl"></i>
    <p class="mt-2">Loading dashboard...</p>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import StudentDashboard from '@/views/student/StudentDashboardView.vue'
import AdminDashboard from '@/views/admin/AdminDashboardView.vue'

const router = useRouter()
const authStore = useAuthStore()

const isStudent = computed(() => authStore.isStudent)
const isStaffDashboard = computed(() => authStore.isAdmin)

onMounted(async () => {
  await authStore.initialize()
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  if (isStudent.value) {
    router.replace('/student')
  }
})
</script>
