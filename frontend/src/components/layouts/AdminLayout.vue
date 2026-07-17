<template>
  <div class="app-shell vb-app-shell soft-shell min-h-screen">
    <Sidebar
      :is-mobile-menu-open="isMobileMenuOpen"
      @close-mobile="isMobileMenuOpen = false"
    />

    <div
      class="app-main soft-main min-h-screen flex flex-col"
      :class="isCollapsed ? 'is-rail' : 'is-wide'"
    >
      <div class="soft-main__inner">
        <Header
          :sidebar-collapsed="isCollapsed"
          @toggle-sidebar="toggleSidebar"
        />
        <main class="soft-main__content">
          <router-view />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, provide, onMounted, onUnmounted } from 'vue'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const isMobileMenuOpen = ref(false)
const isCollapsed = ref(false)
const isDesktop = ref(typeof window !== 'undefined' ? window.innerWidth >= 1024 : true)

provide('sidebarCollapsed', isCollapsed)

const syncViewport = () => {
  isDesktop.value = window.innerWidth >= 1024
  if (isDesktop.value) {
    isMobileMenuOpen.value = false
  }
}

const toggleSidebar = () => {
  if (window.innerWidth < 1024) {
    isMobileMenuOpen.value = !isMobileMenuOpen.value
    return
  }
  isCollapsed.value = !isCollapsed.value
}

onMounted(() => {
  syncViewport()
  window.addEventListener('resize', syncViewport)
})

onUnmounted(() => {
  window.removeEventListener('resize', syncViewport)
})
</script>

<style scoped>
.soft-shell {
  background: var(--vb-shell-bg);
}

.soft-main {
  min-width: 0;
  transition: margin-left 0.3s ease;
}

.soft-main.is-rail,
.soft-main.is-wide {
  margin-left: 0;
}

@media (min-width: 1024px) {
  /* collapsed rail: 5.25rem sidebar + 0.85rem left offset + 0.35rem gap */
  .soft-main.is-rail {
    margin-left: 6.45rem;
  }

  /* expanded: 15rem sidebar + 0.85rem left offset + 0.35rem gap */
  .soft-main.is-wide {
    margin-left: 16.2rem;
  }
}

.soft-main__inner {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 0.75rem 0.85rem 1.75rem;
  transition: padding 0.3s ease;
}

@media (min-width: 640px) {
  .soft-main__inner {
    padding: 1.1rem 1.15rem 2.25rem 0.9rem;
  }
}

@media (min-width: 1024px) {
  .soft-main__inner {
    /* Tighter left padding so content meets the sidebar */
    padding: 1.15rem 1.25rem 2.5rem 0.65rem;
  }
}

.soft-main__content {
  min-width: 0;
  width: 100%;
}
</style>
