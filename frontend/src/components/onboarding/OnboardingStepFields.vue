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
      <label :for="`${idPrefix}-phone`">Phone</label>
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

  <div v-else-if="stepId === 'academic'" class="fields">
    <FacultyDepartmentSelect
      v-model:faculty-uuid="form.faculty_uuid"
      v-model:department-uuid="form.department_uuid"
      :faculties-data="facultiesData"
      :departments-data="departmentsData"
    />
    <div class="field">
      <label :for="`${idPrefix}-level`">Level</label>
      <Select
        :input-id="`${idPrefix}-level`"
        v-model="form.level_uuid"
        :options="levels"
        optionLabel="name"
        optionValue="uuid"
        placeholder="Choose level"
        class="level-select"
      />
    </div>
  </div>

  <div v-else class="confirm-step">
    <p class="confirm-lead">Review your details before finishing setup.</p>

    <section class="confirm-block">
      <h3 class="confirm-block-title">Personal</h3>
      <dl class="confirm-grid">
        <div class="confirm-item">
          <dt>Index</dt>
          <dd>{{ indexNumber }}</dd>
        </div>
        <div class="confirm-item">
          <dt>Full name</dt>
          <dd>{{ form.full_name }}</dd>
        </div>
        <div class="confirm-item">
          <dt>Phone</dt>
          <dd>{{ form.phone_number }}</dd>
        </div>
      </dl>
    </section>

    <section class="confirm-block">
      <h3 class="confirm-block-title">Campus</h3>
      <dl class="confirm-grid">
        <div class="confirm-item">
          <dt>Faculty</dt>
          <dd>{{ facultyName }}</dd>
        </div>
        <div class="confirm-item">
          <dt>Department</dt>
          <dd>{{ departmentName }}</dd>
        </div>
        <div class="confirm-item">
          <dt>Level</dt>
          <dd>{{ levelName }}</dd>
        </div>
      </dl>
    </section>
  </div>
</template>

<script setup>
import Select from 'primevue/select'
import FacultyDepartmentSelect from '@/components/academic/FacultyDepartmentSelect.vue'

const form = defineModel('form', { type: Object, required: true })

defineProps({
  stepId: { type: String, required: true },
  indexNumber: { type: String, default: '—' },
  levels: { type: Array, default: () => [] },
  facultiesData: { type: Array, default: () => [] },
  departmentsData: { type: Array, default: () => [] },
  facultyName: { type: String, default: '—' },
  departmentName: { type: String, default: '—' },
  levelName: { type: String, default: '—' },
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

.level-select {
  width: 100%;
}

:deep(.level-select.p-select) {
  width: 100%;
  border: 1px solid var(--ob-border, #e8e6e1);
  border-radius: 0.5rem;
  background: var(--ob-input, #fff);
}

:deep(.level-select .p-select-label) {
  padding: 0.52rem 0.65rem;
  font-size: 0.75rem;
}

:deep(.fd-fields) {
  gap: 0.7rem;
}

:deep(.fd-field label) {
  margin-bottom: 0.25rem;
  font-size: 0.62rem;
}

:deep(.fd-hint) {
  margin: 0.25rem 0 0;
  font-size: 0.68rem;
}

:deep(.fd-select.p-select),
:deep(.level-select.p-select) {
  border-radius: 0.5rem;
}

:deep(.fd-select .p-select-label) {
  padding: 0.52rem 0.65rem;
  font-size: 0.75rem;
}

:deep(.fd-select .p-select-dropdown) {
  width: 1.85rem;
}

.confirm-step {
  display: grid;
  gap: 0.85rem;
}

.confirm-lead {
  margin: 0;
  font-size: 0.72rem;
  color: var(--ob-muted, #78716c);
  line-height: 1.45;
}

.confirm-block {
  border: 1px solid var(--ob-border, #e8e6e1);
  border-radius: 0.55rem;
  background: var(--ob-input, #fff);
  overflow: hidden;
}

.confirm-block-title {
  margin: 0;
  padding: 0.5rem 0.7rem;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ob-muted, #78716c);
  background: #f7f6f3;
  border-bottom: 1px solid var(--ob-border, #e8e6e1);
}

.confirm-grid {
  margin: 0;
  display: grid;
}

.confirm-item {
  display: grid;
  grid-template-columns: 5.5rem 1fr;
  gap: 0.65rem;
  padding: 0.55rem 0.7rem;
  border-bottom: 1px solid var(--ob-border, #e8e6e1);
}

.confirm-item:last-child {
  border-bottom: none;
}

.confirm-item dt {
  margin: 0;
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--ob-muted, #78716c);
}

.confirm-item dd {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--ob-text, #1c1917);
  text-align: right;
  word-break: break-word;
}
</style>
