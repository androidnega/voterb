<template>
  <!-- Sidebar overlay for mobile -->
  <div 
    v-if="isMobileMenuOpen" 
    class="fixed inset-0 bg-black/50 z-40 lg:hidden"
    @click="closeMobileMenu"
  ></div>

  <!-- Sidebar -->
  <aside 
    class="fixed top-0 left-0 z-50 h-screen bg-white border-r border-gray-200 transition-all duration-300 ease-in-out flex flex-col"
    :class="[
      isCollapsed ? 'w-20' : 'w-64',
      isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
    ]"
  >
    <!-- Logo -->
    <div class="flex items-center justify-between h-16 px-4 border-b border-gray-200 flex-shrink-0">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <i class="fas fa-check-circle text-white text-sm"></i>
        </div>
        <span v-if="!isCollapsed" class="text-lg font-bold text-gray-900">VoterB</span>
      </div>
      <button 
        @click="toggleCollapse" 
        class="p-1.5 hover:bg-gray-100 rounded-lg transition-colors hidden lg:block"
      >
        <i :class="isCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left'" class="text-gray-500 text-sm"></i>
      </button>
      <button 
        @click="closeMobileMenu" 
        class="p-1.5 hover:bg-gray-100 rounded-lg transition-colors lg:hidden"
      >
        <i class="fas fa-times text-gray-500"></i>
      </button>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto py-4 px-3">
      <ul class="space-y-1">
        <li v-for="item in menuItems" :key="item.path">
          <router-link 
            :to="item.path" 
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group"
            :class="[
              $route.path === item.path || $route.path.startsWith(item.path + '/') 
                ? 'bg-emerald-50 text-emerald-700' 
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            ]"
            @click="closeMobileMenu"
          >
            <i :class="item.icon" class="text-lg w-5 text-center flex-shrink-0"></i>
            <span v-if="!isCollapsed" class="text-sm font-medium">{{ item.label }}</span>
            <span v-if="isCollapsed" class="sr-only">{{ item.label }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- Bottom section -->
    <div class="border-t border-gray-200 p-3 flex-shrink-0">
      <button 
        @click="logout" 
        class="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-gray-600 hover:bg-red-50 hover:text-red-600 transition-all duration-200"
      >
        <i class="fas fa-sign-out-alt text-lg w-5 text-center flex-shrink-0"></i>
        <span v-if="!isCollapsed" class="text-sm font-medium">Sign Out</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  isMobileMenuOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close-mobile', 'toggle-collapse'])

const router = useRouter()
const authStore = useAuthStore()
const isCollapsed = ref(false)

// Role-based menu items
const menuItems = computed(() => {
  const role = authStore.roleName
  const items = []

  if (authStore.isStudent) {
    items.push({ path: '/student', label: 'Dashboard', icon: 'fas fa-th-large' })
  } else if (authStore.isAdmin) {
    items.push({ path: '/dashboard', label: 'Dashboard', icon: 'fas fa-th-large' })
    items.push({ path: '/elections', label: 'Elections', icon: 'fas fa-calendar-check' })
    items.push({ path: '/results', label: 'Results', icon: 'fas fa-chart-bar' })
    items.push({ path: '/strongroom', label: 'Strongroom', icon: 'fas fa-shield-alt' })

    if (role === 'super_admin' || authStore.user?.is_superuser) {
      items.push({ path: '/settings', label: 'Settings', icon: 'fas fa-cog' })
    }
  } else {
    items.push({ path: '/dashboard', label: 'Dashboard', icon: 'fas fa-th-large' })
  }

  return items
})

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  emit('toggle-collapse')
}

const closeMobileMenu = () => {
  emit('close-mobile')
}

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>
