<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
      <InputText v-model="form.title" class="w-full" required />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
      <Textarea v-model="form.description" rows="3" class="w-full" />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
      <Dropdown
        v-model="form.election_type"
        :options="types"
        optionLabel="label"
        optionValue="value"
        placeholder="Select type"
        class="w-full"
      />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Eligibility scope</label>
      <Dropdown
        v-model="form.scope_type"
        :options="scopeTypes"
        optionLabel="label"
        optionValue="value"
        placeholder="Who can vote"
        class="w-full"
        @change="onScopeTypeChange"
      />
      <p class="mt-1 text-xs text-gray-500">Students still have a faculty and department regardless of scope.</p>
    </div>

    <div v-if="form.scope_type === 'faculty'">
      <label class="block text-sm font-medium text-gray-700 mb-1">Faculty</label>
      <Dropdown
        v-model="form.scope_faculty_uuid"
        :options="faculties"
        optionLabel="name"
        optionValue="uuid"
        placeholder="Select faculty"
        class="w-full"
        required
      />
    </div>

    <FacultyDepartmentSelect
      v-if="form.scope_type === 'department'"
      v-model:faculty-uuid="scopeFacultyUuid"
      v-model:department-uuid="form.scope_department_uuid"
      :grid="false"
      required
    />

    <div v-if="form.scope_type === 'level'">
      <label class="block text-sm font-medium text-gray-700 mb-1">Level</label>
      <Dropdown
        v-model="form.scope_level_uuid"
        :options="levels"
        optionLabel="name"
        optionValue="uuid"
        placeholder="Select level"
        class="w-full"
        required
      />
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Start Date *</label>
        <Calendar v-model="form.start_date" showTime hourFormat="24" class="w-full" required />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">End Date *</label>
        <Calendar v-model="form.end_date" showTime hourFormat="24" class="w-full" required />
      </div>
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Voting Channels</label>
      <div class="flex items-center space-x-4">
        <div class="flex items-center">
          <Checkbox v-model="form.allow_web_voting" binary />
          <label class="ml-2 text-sm">Web</label>
        </div>
        <div class="flex items-center">
          <Checkbox v-model="form.allow_ussd_voting" binary />
          <label class="ml-2 text-sm">USSD</label>
        </div>
      </div>
    </div>
    <div class="flex justify-end space-x-3 pt-4">
      <Button label="Cancel" severity="secondary" @click="$emit('cancel')" />
      <Button label="Create" type="submit" :loading="loading" />
    </div>
  </form>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { electionApi } from '@/api/elections'
import { academicApi } from '@/api/academic'
import FacultyDepartmentSelect from '@/components/academic/FacultyDepartmentSelect.vue'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import Calendar from 'primevue/calendar'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'

const emit = defineEmits(['success', 'cancel'])

const types = [
  { label: 'General', value: 'general' },
  { label: 'Student Union', value: 'student_union' },
  { label: 'Faculty', value: 'faculty' },
  { label: 'Departmental', value: 'departmental' },
  { label: 'Special', value: 'special' },
]

const scopeTypes = [
  { label: 'School-wide', value: 'school' },
  { label: 'Faculty', value: 'faculty' },
  { label: 'Department', value: 'department' },
  { label: 'Level', value: 'level' },
]

const faculties = ref([])
const levels = ref([])
const scopeFacultyUuid = ref(null)

const form = ref({
  title: '',
  description: '',
  election_type: 'general',
  scope_type: 'school',
  scope_faculty_uuid: null,
  scope_department_uuid: null,
  scope_level_uuid: null,
  start_date: null,
  end_date: null,
  allow_web_voting: true,
  allow_ussd_voting: false,
})

const loading = ref(false)

const onScopeTypeChange = () => {
  form.value.scope_faculty_uuid = null
  form.value.scope_department_uuid = null
  form.value.scope_level_uuid = null
  scopeFacultyUuid.value = null
}

const loadScopeOptions = async () => {
  try {
    const [facultiesRes, levelsRes] = await Promise.all([
      academicApi.faculties({ active_only: 'true' }),
      academicApi.levels(),
    ])
    faculties.value = facultiesRes.data
    levels.value = levelsRes.data
  } catch (error) {
    console.error('Failed to load scope options:', error)
  }
}

const handleSubmit = async () => {
  if (!form.value.start_date || !form.value.end_date) {
    alert('Please set both start and end dates.')
    return
  }
  if (new Date(form.value.end_date) <= new Date(form.value.start_date)) {
    alert('End date must be after the start date.')
    return
  }
  if (form.value.scope_type === 'faculty' && !form.value.scope_faculty_uuid) {
    alert('Please select a faculty for this election scope.')
    return
  }
  if (form.value.scope_type === 'department' && !form.value.scope_department_uuid) {
    alert('Please select a faculty and department for this election scope.')
    return
  }
  if (form.value.scope_type === 'level' && !form.value.scope_level_uuid) {
    alert('Please select a level for this election scope.')
    return
  }

  loading.value = true
  try {
    const payload = {
      ...form.value,
      start_date: new Date(form.value.start_date).toISOString(),
      end_date: new Date(form.value.end_date).toISOString(),
    }
    await electionApi.create(payload)
    emit('success')
  } catch (error) {
    console.error('Failed to create election:', error)
    alert('Failed to create election. Please check the form.')
  } finally {
    loading.value = false
  }
}

onMounted(loadScopeOptions)
</script>
