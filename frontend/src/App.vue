<template>
  <div class="app-root">
    <div v-if="navigating" class="nav-progress" aria-hidden="true">
      <span class="nav-progress__bar" />
    </div>
    <router-view />
    <Toast position="top-right" :pt="toastPt" />
  </div>
</template>

<script setup>
import { onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Toast from 'primevue/toast'

const router = useRouter()
const navigating = ref(false)
let navTimer = null

const toastPt = {
  root: { class: 'vb-toast-root' },
  message: { class: 'vb-toast-message' },
  messageContent: { class: 'vb-toast-content' },
  summary: { class: 'vb-toast-summary' },
  detail: { class: 'vb-toast-detail' },
  buttonContainer: { class: 'vb-toast-close' },
}

const startNav = () => {
  navigating.value = true
  if (navTimer) clearTimeout(navTimer)
  navTimer = setTimeout(() => {
    navigating.value = false
  }, 8000)
}

const endNav = () => {
  if (navTimer) {
    clearTimeout(navTimer)
    navTimer = null
  }
  navigating.value = false
}

const removeBefore = router.beforeEach(() => {
  startNav()
  return true
})
const removeAfter = router.afterEach(() => endNav())
const removeError = router.onError(() => endNav())

onUnmounted(() => {
  removeBefore()
  removeAfter()
  removeError()
  if (navTimer) clearTimeout(navTimer)
})
</script>

<style>
.app-root {
  min-height: 100%;
}

.nav-progress {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  height: 2px;
  pointer-events: none;
  overflow: hidden;
  background: transparent;
}

.nav-progress__bar {
  display: block;
  height: 100%;
  width: 40%;
  background: linear-gradient(90deg, transparent, #3d4f44, transparent);
  animation: nav-slide 0.9s ease-in-out infinite;
}

@keyframes nav-slide {
  0% {
    transform: translateX(-120%);
  }
  100% {
    transform: translateX(320%);
  }
}

.vb-toast-root.p-toast {
  width: min(22rem, calc(100vw - 1.5rem));
}

.vb-toast-message.p-toast-message {
  border: 1px solid #eceae4 !important;
  border-radius: 0.95rem !important;
  box-shadow: 0 14px 36px rgba(26, 26, 26, 0.1) !important;
  background: #fff !important;
  margin: 0 0 0.65rem !important;
  overflow: hidden;
}

.vb-toast-message.p-toast-message-success {
  border-left: 3px solid #0f766e !important;
}

.vb-toast-message.p-toast-message-error {
  border-left: 3px solid #e11d48 !important;
}

.vb-toast-message.p-toast-message-info,
.vb-toast-message.p-toast-message-warn {
  border-left: 3px solid #2563eb !important;
}

.vb-toast-content {
  gap: 0.65rem !important;
  padding: 0.85rem 0.95rem !important;
  align-items: flex-start !important;
}

.vb-toast-summary {
  font-size: 0.84rem !important;
  font-weight: 750 !important;
  letter-spacing: -0.01em;
  color: #1a1a1a !important;
}

.vb-toast-detail {
  margin-top: 0.2rem !important;
  font-size: 0.76rem !important;
  line-height: 1.4 !important;
  color: #6b7280 !important;
}

.vb-toast-close .p-toast-icon-close {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 999px;
}
</style>
