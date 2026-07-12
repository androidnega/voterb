<template>
  <div class="app-shell vb-app-shell soft-shell min-h-screen">
    <Sidebar
      :is-mobile-menu-open="isMobileMenuOpen"
      @close-mobile="isMobileMenuOpen = false"
    />

    <div
      class="app-main soft-main min-h-screen flex flex-col transition-all duration-300"
      :class="isCollapsed ? 'is-rail' : 'is-wide'"
    >
      <div class="soft-main__inner">
        <Header @toggle-mobile="isMobileMenuOpen = !isMobileMenuOpen" />
        <main class="soft-main__content">
          <router-view />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const isMobileMenuOpen = ref(false)
const isCollapsed = ref(true)

provide('sidebarCollapsed', isCollapsed)
</script>

<style scoped>
.soft-shell {
  background: var(--vb-shell-bg);
}

.soft-main {
  min-width: 0;
}

.soft-main.is-rail {
  margin-left: 0;
}

.soft-main.is-wide {
  margin-left: 0;
}

@media (min-width: 1024px) {
  .soft-main.is-rail {
    margin-left: 6.75rem;
  }

  .soft-main.is-wide {
    margin-left: 17rem;
  }
}

.soft-main__inner {
  width: 100%;
  max-width: 84rem;
  margin: 0 auto;
  padding: 1rem 1rem 2rem;
}

@media (min-width: 640px) {
  .soft-main__inner {
    padding: 1.25rem 1.5rem 2.5rem;
  }
}

@media (min-width: 1024px) {
  .soft-main__inner {
    padding: 1.35rem 1.75rem 2.75rem;
  }
}

.soft-main__content {
  min-width: 0;
}
</style>
