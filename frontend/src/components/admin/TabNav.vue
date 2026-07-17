<template>
  <nav class="section-switch" aria-label="Sections">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      type="button"
      class="section-tile"
      :class="[
        tab.tone ? `section-tile--${tab.tone}` : '',
        { 'is-active': modelValue === tab.key },
      ]"
      :aria-current="modelValue === tab.key ? 'page' : undefined"
      @click="$emit('update:modelValue', tab.key)"
    >
      <span class="section-tile__icon" aria-hidden="true">
        <i :class="tab.icon"></i>
      </span>
      <span class="section-tile__body">
        <span class="section-tile__label">{{ tab.label }}</span>
        <span v-if="tab.count != null" class="section-tile__meta">{{ tab.count }}</span>
      </span>
      <span class="section-tile__mark" aria-hidden="true"></span>
    </button>
  </nav>
</template>

<script setup>
defineProps({
  tabs: { type: Array, required: true },
  modelValue: { type: String, required: true },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.section-switch {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9.5rem, 1fr));
  gap: 0.65rem;
  margin-bottom: 1.35rem;
}

.section-tile {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  text-align: left;
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  border: 1px solid var(--vb-line, #ebeae4);
  background: var(--vb-surface, #fff);
  color: var(--vb-muted, #8a8a8a);
  cursor: pointer;
  transition:
    border-color 0.16s ease,
    background 0.16s ease,
    box-shadow 0.16s ease,
    color 0.16s ease,
    transform 0.16s ease;
}

.section-tile:hover {
  color: var(--vb-ink, #1c1c1c);
  border-color: var(--vb-accent-border, #c5d4bc);
  transform: translateY(-1px);
}

.section-tile.is-active {
  color: var(--vb-ink, #1c1c1c);
  border-color: transparent;
  background: var(--vb-panel, #f7f6f2);
  box-shadow: inset 0 0 0 1.5px var(--section-accent, var(--vb-accent, #3d4f44));
}

.section-tile__icon {
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 0.75rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.9rem;
  background: var(--vb-panel, #f7f6f2);
  color: var(--vb-muted, #8a8a8a);
  transition: background 0.16s ease, color 0.16s ease;
}

.section-tile.is-active .section-tile__icon {
  background: var(--section-accent, var(--vb-accent, #3d4f44));
  color: #fff;
}

.section-tile__body {
  display: flex;
  flex-direction: column;
  gap: 0.12rem;
  min-width: 0;
}

.section-tile__label {
  font-size: 0.88rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  line-height: 1.15;
}

.section-tile__meta {
  font-size: 0.72rem;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
  color: var(--vb-muted, #8a8a8a);
}

.section-tile.is-active .section-tile__meta {
  color: var(--section-accent, var(--vb-accent, #3d4f44));
}

.section-tile__mark {
  position: absolute;
  left: 0;
  top: 0.85rem;
  bottom: 0.85rem;
  width: 3px;
  border-radius: 999px;
  background: transparent;
  transition: background 0.16s ease;
}

.section-tile.is-active .section-tile__mark {
  background: var(--section-accent, var(--vb-accent, #3d4f44));
}

.section-tile--indigo { --section-accent: #4338ca; }
.section-tile--amber { --section-accent: #d97706; }
.section-tile--teal { --section-accent: var(--vb-accent, #3d4f44); }
.section-tile--slate { --section-accent: #334155; }
.section-tile--blue { --section-accent: #1d4ed8; }

@media (max-width: 640px) {
  .section-switch {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
