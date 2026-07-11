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
        class="control"
        :value="form.full_name"
        type="text"
        required
        placeholder="Ama Serwaa Mensah"
        autocomplete="name"
        @input="updateField('full_name', $event.target.value)"
      />
    </div>
    <div class="field">
      <label :for="`${idPrefix}-phone`">Phone</label>
      <input
        :id="`${idPrefix}-phone`"
        class="control"
        :value="form.phone_number"
        type="tel"
        required
        placeholder="+233 50 123 4567"
        autocomplete="tel"
        @input="updateField('phone_number', $event.target.value)"
      />
    </div>
  </div>

  <div v-else-if="stepId === 'academic'" class="fields">
    <FacultyDepartmentSelect
      v-model:faculty-uuid="facultyUuid"
      v-model:department-uuid="departmentUuid"
      :faculties-data="facultiesData"
      :departments-data="departmentsData"
    />
    <div class="field">
      <label :for="`${idPrefix}-level`">Level</label>
      <Select
        :input-id="`${idPrefix}-level`"
        v-model="levelUuid"
        :options="levels"
        optionLabel="name"
        optionValue="uuid"
        placeholder="Choose level"
        class="level-select"
      />
    </div>
  </div>

  <div v-else class="fields">
    <ul class="summary">
      <li><span>Index</span><strong>{{ indexNumber }}</strong></li>
      <li><span>Name</span><strong>{{ form.full_name }}</strong></li>
      <li><span>Phone</span><strong>{{ form.phone_number }}</strong></li>
      <li><span>Faculty</span><strong>{{ facultyName }}</strong></li>
      <li><span>Department</span><strong>{{ departmentName }}</strong></li>
      <li><span>Level</span><strong>{{ levelName }}</strong></li>
    </ul>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Select from 'primevue/select'
import FacultyDepartmentSelect from '@/components/academic/FacultyDepartmentSelect.vue'

const props = defineProps({
  stepId: { type: String, required: true },
  form: { type: Object, required: true },
  indexNumber: { type: String, default: '—' },
  levels: { type: Array, default: () => [] },
  facultiesData: { type: Array, default: () => [] },
  departmentsData: { type: Array, default: () => [] },
  facultyName: { type: String, default: '—' },
  departmentName: { type: String, default: '—' },
  levelName: { type: String, default: '—' },
  idPrefix: { type: String, default: 'onboard' },
})

const emit = defineEmits(['update:form'])

const facultyUuid = computed({
  get: () => props.form.faculty_uuid || null,
  set: (value) => updateField('faculty_uuid', value),
})

const departmentUuid = computed({
  get: () => props.form.department_uuid || null,
  set: (value) => updateField('department_uuid', value),
})

const levelUuid = computed({
  get: () => props.form.level_uuid || null,
  set: (value) => updateField('level_uuid', value ? String(value) : ''),
})

const updateField = (key, value) => {
  emit('update:form', { ...props.form, [key]: value ?? '' })
}
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

.summary {
  margin: 0;
  padding: 0;
  list-style: none;
  border: 1px solid var(--ob-border, #e8e6e1);
  border-radius: 0.55rem;
  overflow: hidden;
  background: var(--ob-input, #fff);
}

.summary li {
  display: flex;
  justify-content: space-between;
  gap: 0.7rem;
  padding: 0.55rem 0.7rem;
  font-size: 0.72rem;
  border-bottom: 1px solid var(--ob-border, #e8e6e1);
}

.summary li:last-child {
  border-bottom: none;
}

.summary span {
  color: var(--ob-muted, #78716c);
}

.summary strong {
  color: var(--ob-text, #1c1917);
  font-weight: 600;
  text-align: right;
}
</style>
