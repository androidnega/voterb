<template>
  <div class="fd-fields" :class="{ 'fd-fields--split': grid }">
    <div class="fd-field">
      <label for="fd-faculty">Faculty</label>
      <Select
        input-id="fd-faculty"
        v-model="facultyModel"
        :options="faculties"
        optionLabel="name"
        optionValue="uuid"
        placeholder="Choose faculty"
        class="fd-select"
        :disabled="loading || disabled"
      />
    </div>

    <div class="fd-field">
      <label for="fd-department">Department</label>
      <Select
        :key="`dept-${facultyKey}`"
        input-id="fd-department"
        v-model="departmentModel"
        :options="filteredDepartments"
        optionLabel="name"
        optionValue="uuid"
        :placeholder="departmentPlaceholder"
        class="fd-select"
        :disabled="loading || disabled || !hasFaculty"
      />
      <p v-if="hasFaculty && !filteredDepartments.length" class="fd-hint fd-hint--warn">
        No departments for this faculty yet.
      </p>
      <p v-else-if="!hasFaculty && showHint" class="fd-hint">Pick a faculty first.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { academicApi } from '@/api/academic'
import Select from 'primevue/select'

const props = defineProps({
  facultyUuid: { type: [String, null], default: null },
  departmentUuid: { type: [String, null], default: null },
  disabled: { type: Boolean, default: false },
  grid: { type: Boolean, default: false },
  showHint: { type: Boolean, default: true },
  activeOnly: { type: Boolean, default: true },
  facultiesData: { type: Array, default: null },
  departmentsData: { type: Array, default: null },
})

const emit = defineEmits(['update:facultyUuid', 'update:departmentUuid'])

const loading = ref(false)
const faculties = ref([])
const departments = ref([])
const selectedFacultyUuid = ref('')
const selectedDepartmentUuid = ref('')

const normalizeUuid = (value) => {
  if (value == null || value === '') return ''
  if (typeof value === 'object') {
    return String(value.uuid ?? value.value ?? '').trim()
  }
  return String(value).trim()
}

watch(
  () => props.facultyUuid,
  (value) => {
    selectedFacultyUuid.value = normalizeUuid(value)
  },
  { immediate: true }
)

watch(
  () => props.departmentUuid,
  (value) => {
    selectedDepartmentUuid.value = normalizeUuid(value)
  },
  { immediate: true }
)

const facultyModel = computed({
  get: () => selectedFacultyUuid.value || null,
  set: (value) => onFacultyChange(value),
})

const departmentModel = computed({
  get: () => selectedDepartmentUuid.value || null,
  set: (value) => onDepartmentChange(value),
})

const facultyKey = computed(() => selectedFacultyUuid.value)
const hasFaculty = computed(() => Boolean(selectedFacultyUuid.value))

const departmentPlaceholder = computed(() => {
  if (!hasFaculty.value) return 'Select faculty first'
  if (!filteredDepartments.value.length) return 'No departments found'
  return 'Choose department'
})

const resolveFacultyUuid = (dept) => {
  if (!dept) return ''
  return normalizeUuid(dept.faculty?.uuid ?? dept.faculty_uuid ?? dept.faculty)
}

const filteredDepartments = computed(() => {
  if (!hasFaculty.value) return []
  return departments.value.filter((dept) => resolveFacultyUuid(dept) === facultyKey.value)
})

const applyPreloaded = () => {
  if (!props.facultiesData?.length) return false
  faculties.value = props.facultiesData
  departments.value = props.departmentsData || []
  return true
}

const onFacultyChange = (value) => {
  const next = normalizeUuid(value)
  selectedFacultyUuid.value = next
  selectedDepartmentUuid.value = ''
  emit('update:facultyUuid', next || null)
  emit('update:departmentUuid', null)
}

const onDepartmentChange = (value) => {
  const next = normalizeUuid(value)
  selectedDepartmentUuid.value = next
  emit('update:departmentUuid', next || null)
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = props.activeOnly ? { active_only: 'true' } : {}
    const [fRes, dRes] = await Promise.all([
      academicApi.faculties(params),
      academicApi.departments(params),
    ])
    faculties.value = fRes.data
    departments.value = dRes.data
  } catch (error) {
    console.error('Failed to load faculties/departments:', error)
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.facultiesData, props.departmentsData],
  () => {
    applyPreloaded()
  },
  { deep: true, immediate: true }
)

onMounted(() => {
  if (!faculties.value.length) fetchData()
})

defineExpose({ refresh: fetchData, faculties, departments })
</script>

<style scoped>
.fd-fields {
  display: grid;
  gap: 1rem;
}

.fd-fields--split {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.fd-field label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ob-muted, #78716c);
}

.fd-hint {
  margin: 0.35rem 0 0;
  font-size: 0.75rem;
  color: var(--ob-muted, #78716c);
}

.fd-hint--warn {
  color: #b45309;
}

.fd-select {
  width: 100%;
}

:deep(.p-select) {
  width: 100%;
  border: 1px solid var(--ob-border, #e8e6e1);
  border-radius: 0.65rem;
  background: var(--ob-input, #fff);
  box-shadow: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

:deep(.p-select:not(.p-disabled):hover) {
  border-color: #d6d3cd;
}

:deep(.p-select.p-focus) {
  border-color: var(--vb-accent, #0f766e);
  box-shadow: 0 0 0 3px var(--vb-focus-ring, rgba(15, 118, 110, 0.12));
}

:deep(.p-select .p-select-label) {
  padding: 0.72rem 0.85rem;
  font-size: 0.875rem;
  color: var(--ob-text, #1c1917);
}

:deep(.p-select .p-select-label.p-placeholder) {
  color: #a8a29e;
}

:deep(.p-select .p-select-dropdown) {
  width: 2.25rem;
  color: #a8a29e;
}

.fd-reveal-enter-active,
.fd-reveal-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fd-reveal-enter-from,
.fd-reveal-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 640px) {
  .fd-fields--split {
    grid-template-columns: 1fr;
  }
}
</style>
