<template>
  <div v-if="stepId === 'profile'" class="fields">
    <div class="field">
      <label :for="`${idPrefix}-index`">Index number</label>
      <div :id="`${idPrefix}-index`" class="control is-readonly">{{ indexNumber }}</div>
    </div>
    <div class="field">
      <label :for="`${idPrefix}-full-name`">Full name</label>
      <input
        :id="`${idPrefix}-full-name`"
        v-model="form.full_name"
        class="control"
        type="text"
        required
        placeholder="Ama Serwaa Mensah"
        autocomplete="name"
      />
    </div>
    <div class="field">
      <label :for="`${idPrefix}-phone`">Mobile number</label>
      <input
        :id="`${idPrefix}-phone`"
        v-model="form.phone_number"
        class="control"
        type="tel"
        required
        placeholder="+233 50 123 4567"
        autocomplete="tel"
      />
    </div>
  </div>
</template>

<script setup>
const form = defineModel('form', { type: Object, required: true })

defineProps({
  stepId: { type: String, default: 'profile' },
  indexNumber: { type: String, default: '—' },
  idPrefix: { type: String, default: 'onboard' },
})
</script>

<style scoped>
.fields {
  display: grid;
  gap: 0.7rem;
}

.field label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ob-muted, #78716c);
}

.control {
  width: 100%;
  padding: 0.52rem 0.65rem;
  border: 1px solid var(--ob-border, #e8e6e1);
  border-radius: 0.5rem;
  font-size: 0.75rem;
  color: var(--ob-text, #1c1917);
  background: var(--ob-input, #fff);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.control::placeholder {
  color: #a8a29e;
}

.control:hover {
  border-color: #d6d3cd;
}

.control:focus {
  outline: none;
  border-color: var(--vb-accent, #0f766e);
  box-shadow: 0 0 0 3px var(--vb-focus-ring, rgba(15, 118, 110, 0.12));
}

.control.is-readonly {
  color: var(--ob-muted, #78716c);
  background: #f5f4f1;
  cursor: default;
  user-select: all;
}
</style>
