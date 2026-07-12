<template>
  <header class="page-header">
    <div class="page-header-main">
      <div class="page-header-icon" :class="iconTone">
        <i :class="icon"></i>
      </div>
      <div>
        <h1 class="page-title">{{ title }}</h1>
        <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
      </div>
    </div>
    <div class="page-header-actions">
      <slot name="actions">
        <button
          v-if="showRefresh"
          type="button"
          class="btn btn-ghost"
          :disabled="loading"
          @click="$emit('refresh')"
        >
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          <span>Refresh</span>
        </button>
      </slot>
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  icon: { type: String, default: 'fas fa-layer-group' },
  iconTone: { type: String, default: 'tone-teal' },
  showRefresh: { type: Boolean, default: true },
  loading: { type: Boolean, default: false },
})

defineEmits(['refresh'])
</script>

<style scoped>
.page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 2rem;
}

.page-header-main {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.page-header-icon {
  width: 3rem;
  height: 3rem;
  border-radius: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  border: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.page-title {
  font-size: clamp(1.5rem, 2.5vw, 1.875rem);
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.page-subtitle {
  margin-top: 0.35rem;
  font-size: 0.875rem;
  color: #64748b;
  max-width: 36rem;
  line-height: 1.5;
}

.page-header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
</style>
