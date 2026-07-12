<template>
  <div class="friendly-state" :class="`friendly-state--${tone}`" role="status">
    <div class="friendly-state__icon" aria-hidden="true">
      <i :class="iconClass"></i>
    </div>
    <p class="friendly-state__title">{{ title }}</p>
    <p v-if="message" class="friendly-state__copy">{{ message }}</p>
    <button
      v-if="actionLabel"
      type="button"
      class="friendly-state__action"
      @click="$emit('action')"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tone: { type: String, default: 'muted' }, // muted | error | empty
  title: { type: String, required: true },
  message: { type: String, default: '' },
  actionLabel: { type: String, default: '' },
  icon: { type: String, default: '' },
})

defineEmits(['action'])

const iconClass = computed(() => {
  if (props.icon) return props.icon
  if (props.tone === 'error') return 'fas fa-wifi'
  if (props.tone === 'empty') return 'far fa-inbox'
  return 'fas fa-circle-notch fa-spin'
})
</script>

<style scoped>
.friendly-state {
  display: grid;
  justify-items: center;
  gap: 0.45rem;
  padding: 2.25rem 1rem;
  text-align: center;
}

.friendly-state__icon {
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  margin-bottom: 0.15rem;
  background: #fff;
  border: 1px solid #ebe8e2;
  color: #a8a29e;
  font-size: 0.85rem;
}

.friendly-state--error .friendly-state__icon {
  color: #b45309;
  border-color: #f5e6d3;
  background: #fffbeb;
}

.friendly-state--empty .friendly-state__icon {
  color: var(--vb-accent, #0f766e);
  background: #f0fdf9;
  border-color: #d1fae5;
}

.friendly-state__title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 650;
  color: #1c1917;
  letter-spacing: -0.01em;
}

.friendly-state__copy {
  margin: 0;
  max-width: 18rem;
  font-size: 0.78rem;
  line-height: 1.5;
  color: #78716c;
}

.friendly-state__action {
  margin-top: 0.45rem;
  border: 1px solid #e5e2db;
  background: #fff;
  color: #1c1917;
  font-size: 0.74rem;
  font-weight: 600;
  padding: 0.5rem 0.95rem;
  border-radius: 999px;
  cursor: pointer;
}

.friendly-state__action:hover {
  border-color: #d6d3d1;
}
</style>
