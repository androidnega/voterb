<template>
  <section class="qa-section page-section">
    <div class="qa-head">
      <div>
        <h2 class="qa-title">{{ title }}</h2>
        <p class="qa-subtitle">{{ subtitle }}</p>
      </div>
    </div>

    <div class="qa-grid" :style="{ '--qa-cols': String(Math.min(safeLinks.length, 6)) }">
      <router-link
        v-for="link in safeLinks"
        :key="link.path"
        :to="link.path"
        class="qa-card"
      >
        <span class="qa-icon" aria-hidden="true">
          <i :class="link.icon"></i>
        </span>
        <span class="qa-copy">
          <span class="qa-card-title">{{ link.title }}</span>
          <span class="qa-card-desc">{{ link.description }}</span>
        </span>
        <span class="qa-chevron" aria-hidden="true">
          <i class="fas fa-arrow-right"></i>
        </span>
      </router-link>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: 'Quick access' },
  subtitle: { type: String, default: '' },
  links: { type: Array, default: () => [] },
})

const safeLinks = computed(() =>
  (props.links || [])
    .map((link) => ({
      ...link,
      path: link.path || link.to,
      title: link.title || link.label,
    }))
    .filter((link) => typeof link.path === 'string' && link.path.length > 0),
)
</script>

<style scoped>
.qa-section {
  margin-top: 0.25rem;
}

.qa-head {
  margin-bottom: 0.9rem;
}

.qa-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--vb-ink);
}

.qa-subtitle {
  margin: 0.2rem 0 0;
  font-size: 0.8rem;
  color: var(--vb-muted);
}

.qa-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.65rem;
}

@media (min-width: 640px) {
  .qa-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 960px) {
  .qa-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (min-width: 1200px) {
  .qa-grid {
    grid-template-columns: repeat(var(--qa-cols, 3), minmax(0, 1fr));
  }
}

.qa-card {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  min-height: 4.5rem;
  padding: 0.9rem 1rem;
  border-radius: 1.15rem;
  background: var(--vb-surface, #fff);
  border: 1px solid color-mix(in srgb, var(--vb-line, #ebeae4) 88%, transparent);
  box-shadow: none;
  text-decoration: none;
  color: inherit;
  transition:
    border-color 0.2s ease,
    background-color 0.2s ease,
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.qa-card:hover {
  border-color: color-mix(in srgb, var(--vb-accent) 35%, var(--vb-line));
  background: color-mix(in srgb, var(--vb-accent-soft) 55%, #fff);
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(28, 28, 28, 0.04);
}

.qa-icon {
  width: 2.4rem;
  height: 2.4rem;
  flex-shrink: 0;
  border-radius: 0.85rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--vb-panel, #f7f6f2);
  color: var(--vb-ink);
  font-size: 0.82rem;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.qa-card:hover .qa-icon {
  background: var(--vb-accent);
  color: #fff;
}

.qa-copy {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.12rem;
}

.qa-card-title {
  font-size: 0.88rem;
  font-weight: 750;
  letter-spacing: -0.01em;
  color: var(--vb-ink);
  line-height: 1.25;
}

.qa-card-desc {
  font-size: 0.72rem;
  line-height: 1.4;
  color: var(--vb-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.qa-chevron {
  flex-shrink: 0;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #c5c2b6;
  font-size: 0.65rem;
  opacity: 0.7;
  transition: transform 0.2s ease, color 0.2s ease, opacity 0.2s ease, background-color 0.2s ease;
}

.qa-card:hover .qa-chevron {
  opacity: 1;
  color: var(--vb-accent);
  background: color-mix(in srgb, var(--vb-accent-soft) 80%, #fff);
  transform: translateX(2px);
}

/* Lumen: warmer, softer, more editorial */
:global([data-dashboard='lumen']) .qa-card {
  border-radius: 1.35rem;
  padding: 1rem 1.1rem;
  background: color-mix(in srgb, var(--vb-surface) 92%, var(--vb-panel));
  border-color: transparent;
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--vb-line) 70%, transparent);
}

:global([data-dashboard='lumen']) .qa-card:hover {
  background: #fff;
  box-shadow:
    inset 0 0 0 1px color-mix(in srgb, var(--vb-accent) 22%, transparent),
    0 10px 24px rgba(45, 45, 45, 0.05);
}

:global([data-dashboard='lumen']) .qa-icon {
  border-radius: 1rem;
  background: #fff;
  box-shadow: 0 1px 2px rgba(45, 45, 45, 0.04);
}

:global([data-dashboard='lumen']) .qa-title {
  font-weight: 800;
  letter-spacing: -0.03em;
}
</style>
