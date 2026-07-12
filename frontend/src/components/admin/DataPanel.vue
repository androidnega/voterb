<template>
  <section class="data-panel">
    <div v-if="title || $slots.header" class="data-panel-head">
      <div>
        <h2 v-if="title" class="data-panel-title">{{ title }}</h2>
        <p v-if="subtitle" class="data-panel-subtitle">{{ subtitle }}</p>
      </div>
      <slot name="header" />
    </div>
    <div class="data-panel-body" :class="{ 'no-padding': noPadding }">
      <slot />
    </div>
    <div v-if="$slots.footer" class="data-panel-foot">
      <slot name="footer" />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  noPadding: { type: Boolean, default: false },
})
</script>

<style scoped>
.data-panel {
  background: #fff;
  border: none;
  border-radius: var(--vb-card-radius, 1.5rem);
  overflow: hidden;
  box-shadow: var(--vb-card-shadow, 0 8px 28px rgba(28, 28, 28, 0.05));
}

.data-panel-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 1.15rem 1.35rem;
  border-bottom: 1px solid var(--vb-line, #ebeae4);
  background: transparent;
}

.data-panel-title {
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--vb-ink, #1c1c1c);
}

.data-panel-subtitle {
  margin-top: 0.2rem;
  font-size: 0.82rem;
  color: var(--vb-muted, #8a8a8a);
}

.data-panel-body {
  padding: 1.25rem;
}

.data-panel-body.no-padding {
  padding: 0;
}

.data-panel-foot {
  border-top: 1px solid var(--vb-line, #ebeae4);
}
</style>
