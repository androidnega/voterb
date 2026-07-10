<template>
  <div class="min-h-screen bg-gray-50">
    <Sidebar
      :is-mobile-menu-open="isMobileMenuOpen"
      @close-mobile="isMobileMenuOpen = false"
    />

    <div
      class="transition-all duration-300"
      :class="[
        'lg:ml-64',
        isCollapsed ? 'lg:ml-20' : '',
      ]"
    >
      <Header @toggle-mobile="isMobileMenuOpen = !isMobileMenuOpen" />

      <main class="p-4 sm:p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const isMobileMenuOpen = ref(false)
const isCollapsed = ref(false)

provide('sidebarCollapsed', isCollapsed)
</script>
