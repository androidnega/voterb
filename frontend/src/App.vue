<template>
  <router-view />
  <Toast position="top-right" :pt="toastPt" />
</template>

<script setup>
import Toast from 'primevue/toast'

const toastPt = {
  root: { class: 'vb-toast-root' },
  message: { class: 'vb-toast-message' },
  messageContent: { class: 'vb-toast-content' },
  summary: { class: 'vb-toast-summary' },
  detail: { class: 'vb-toast-detail' },
  buttonContainer: { class: 'vb-toast-close' },
}
</script>

<style>
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
