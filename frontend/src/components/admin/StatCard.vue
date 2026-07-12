<template>
  <article class="stat-card">
    <div class="stat-icon" :class="tone">
      <i :class="icon"></i>
    </div>
    <div>
      <p class="stat-label">{{ label }}</p>
      <p class="stat-value" :class="valueTone">{{ value }}</p>
      <p v-if="hint" class="stat-hint">{{ hint }}</p>
    </div>
  </article>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  hint: { type: String, default: '' },
  icon: { type: String, default: 'fas fa-chart-bar' },
  tone: { type: String, default: 'tone-slate' },
  valueTone: { type: String, default: 'text-slate-900' },
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.25rem 1.35rem;
  background: #fff;
  border: none;
  border-radius: var(--vb-card-radius, 1.5rem);
  box-shadow: var(--vb-card-shadow, 0 8px 28px rgba(28, 28, 28, 0.05));
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.stat-card:hover {
  box-shadow: 0 1px 3px rgba(28, 28, 28, 0.05);
  transform: none;
}

.stat-icon {
  width: 2.65rem;
  height: 2.65rem;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  flex-shrink: 0;
}

.stat-label {
  font-size: 0.82rem;
  font-weight: 500;
  letter-spacing: 0;
  text-transform: none;
  color: var(--vb-muted, #8a8a8a);
}

.stat-value {
  margin-top: 0.3rem;
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.1;
  color: var(--vb-ink, #1c1c1c);
}

.stat-hint {
  margin-top: 0.3rem;
  font-size: 0.75rem;
  color: var(--vb-muted, #8a8a8a);
}
</style>
