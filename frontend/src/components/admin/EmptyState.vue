<template>
  <div class="empty-state">
    <div class="empty-icon">
      <i :class="icon"></i>
    </div>
    <p class="empty-title">{{ title }}</p>
    <p v-if="message" class="empty-message">{{ message }}</p>
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, default: 'fas fa-inbox' },
  title: { type: String, default: 'No data found' },
  message: { type: String, default: '' },
})
</script>

<style scoped>
.empty-state {
  padding: 3rem 1.5rem;
  text-align: center;
}

.empty-icon {
  width: 3.5rem;
  height: 3.5rem;
  margin: 0 auto 1rem;
  border-radius: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 1.25rem;
}

.empty-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #475569;
}

.empty-message {
  margin-top: 0.35rem;
  font-size: 0.8125rem;
  color: #94a3b8;
}
</style>
