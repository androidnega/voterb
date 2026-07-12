<template>
  <div class="admin-page">
    <PageHeader
      title="Academic structure"
      subtitle="Manage faculties, departments, and study levels for student onboarding and election scoping."
      icon="fas fa-university"
      icon-tone="tone-indigo"
      :loading="loading"
      :show-refresh="true"
      @refresh="fetchAll"
    >
      <template #actions>
        <button type="button" class="btn btn-primary" @click="openCreate">
          <i class="fas fa-plus"></i>
          {{ createLabel }}
        </button>
      </template>
    </PageHeader>

    <div class="stat-grid page-section">
      <StatCard label="Faculties" :value="stats.faculties" icon="fas fa-university" tone="tone-indigo" value-tone="text-indigo-700" />
      <StatCard label="Departments" :value="stats.departments" icon="fas fa-book" tone="tone-blue" value-tone="text-blue-700" />
      <StatCard label="Levels" :value="stats.levels" icon="fas fa-layer-group" tone="tone-teal" value-tone="text-teal-700" />
      <StatCard label="Active" :value="stats.active" hint="Faculties & departments" icon="fas fa-check-circle" tone="tone-slate" />
    </div>

    <TabNav v-model="activeTab" :tabs="tabs" class="page-section" />

    <div class="filter-bar page-section">
      <div class="filter-input-wrap">
        <i class="fas fa-search"></i>
        <input v-model="searchQuery" type="text" :placeholder="searchPlaceholder" />
      </div>
      <label v-if="activeTab !== 'levels'" class="filter-check">
        <input v-model="activeOnly" type="checkbox" @change="fetchAll" />
        <span>Active only</span>
      </label>
      <button v-if="searchQuery" type="button" class="btn btn-ghost" @click="searchQuery = ''">Clear</button>
    </div>

    <DataPanel :title="panelTitle" :subtitle="panelSubtitle" no-padding>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr v-if="activeTab === 'faculties'">
              <th>Faculty</th>
              <th>Code</th>
              <th>Departments</th>
              <th>Status</th>
              <th class="text-center">Actions</th>
            </tr>
            <tr v-else-if="activeTab === 'departments'">
              <th>Department</th>
              <th>Code</th>
              <th>Faculty</th>
              <th>Status</th>
              <th class="text-center">Actions</th>
            </tr>
            <tr v-else>
              <th>Level</th>
              <th>Order</th>
              <th class="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="activeTab === 'faculties'">
              <tr v-for="row in filteredFaculties" :key="row.uuid">
                <td><span class="cell-title">{{ row.name }}</span></td>
                <td class="mono">{{ row.code }}</td>
                <td class="mono">{{ row.department_count ?? 0 }}</td>
                <td><span class="admin-badge" :class="row.is_active ? 'success' : 'neutral'">{{ row.is_active ? 'Active' : 'Inactive' }}</span></td>
                <td>
                  <div class="row-actions">
                    <button type="button" class="admin-icon-btn" title="Edit" @click="editFaculty(row)"><i class="fas fa-pen"></i></button>
                    <button type="button" class="admin-icon-btn" :title="row.is_active ? 'Deactivate' : 'Activate'" @click="toggleFaculty(row)">
                      <i :class="row.is_active ? 'fas fa-ban' : 'fas fa-check'"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </template>

            <template v-else-if="activeTab === 'departments'">
              <tr v-for="row in filteredDepartments" :key="row.uuid">
                <td><span class="cell-title">{{ row.name }}</span></td>
                <td class="mono">{{ row.code }}</td>
                <td class="text-muted">{{ row.faculty_name || row.faculty?.name }}</td>
                <td><span class="admin-badge" :class="row.is_active ? 'success' : 'neutral'">{{ row.is_active ? 'Active' : 'Inactive' }}</span></td>
                <td>
                  <div class="row-actions">
                    <button type="button" class="admin-icon-btn" title="Edit" @click="editDepartment(row)"><i class="fas fa-pen"></i></button>
                    <button type="button" class="admin-icon-btn" :title="row.is_active ? 'Deactivate' : 'Activate'" @click="toggleDepartment(row)">
                      <i :class="row.is_active ? 'fas fa-ban' : 'fas fa-check'"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </template>

            <template v-else>
              <tr v-for="row in filteredLevels" :key="row.uuid">
                <td><span class="cell-title">{{ row.name }}</span></td>
                <td class="mono">{{ row.display_order }}</td>
                <td>
                  <div class="row-actions">
                    <button type="button" class="admin-icon-btn" title="Edit" @click="editLevel(row)"><i class="fas fa-pen"></i></button>
                    <button type="button" class="admin-icon-btn danger" title="Delete" @click="confirmDeleteLevel(row)"><i class="fas fa-trash"></i></button>
                  </div>
                </td>
              </tr>
            </template>

            <tr v-if="!loading && currentRows.length === 0">
              <td :colspan="activeTab === 'levels' ? 3 : 5">
                <EmptyState icon="fas fa-university" title="Nothing found" message="Adjust your search or add a new entry." />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </DataPanel>

    <Dialog v-model:visible="showDialog" :header="dialogTitle" :modal="true" class="w-full max-w-lg">
      <form class="dialog-form" @submit.prevent="submitForm">
        <template v-if="dialogType === 'faculty'">
          <div><label>Name</label><InputText v-model="form.name" class="w-full" required /></div>
          <div><label>Code</label><InputText v-model="form.code" class="w-full mono" required maxlength="20" /></div>
          <div><label>Description</label><Textarea v-model="form.description" rows="2" class="w-full" /></div>
          <label class="check-row"><input v-model="form.is_active" type="checkbox" /><span>Active</span></label>
        </template>

        <template v-else-if="dialogType === 'department'">
          <div><label>Faculty</label>
            <Dropdown v-model="form.faculty_uuid" :options="faculties" optionLabel="name" optionValue="uuid" placeholder="Select faculty" class="w-full" required />
          </div>
          <div><label>Name</label><InputText v-model="form.name" class="w-full" required /></div>
          <div><label>Code</label><InputText v-model="form.code" class="w-full mono" required maxlength="20" /></div>
          <div><label>Description</label><Textarea v-model="form.description" rows="2" class="w-full" /></div>
          <label class="check-row"><input v-model="form.is_active" type="checkbox" /><span>Active</span></label>
        </template>

        <template v-else>
          <div><label>Name</label><InputText v-model="form.name" class="w-full" required placeholder="Level 100" /></div>
          <div><label>Display order</label><InputNumber v-model="form.display_order" class="w-full" :min="0" /></div>
        </template>

        <p v-if="formError" class="form-error">{{ formError }}</p>
        <div class="dialog-actions">
          <Button label="Cancel" severity="secondary" @click="closeDialog" />
          <Button :label="editingId ? 'Save' : 'Add'" type="submit" :loading="submitting" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { academicApi } from '@/api/academic'
import PageHeader from '@/components/admin/PageHeader.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import TabNav from '@/components/admin/TabNav.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'

const loading = ref(false)
const submitting = ref(false)
const activeTab = ref('faculties')
const searchQuery = ref('')
const activeOnly = ref(false)
const showDialog = ref(false)
const dialogType = ref('faculty')
const editingId = ref(null)
const formError = ref('')

const faculties = ref([])
const departments = ref([])
const levels = ref([])

const form = ref({
  name: '',
  code: '',
  description: '',
  is_active: true,
  faculty_uuid: null,
  display_order: 0,
})

const tabs = computed(() => [
  { key: 'faculties', label: 'Faculties', icon: 'fas fa-university', count: faculties.value.length, tone: 'indigo' },
  { key: 'departments', label: 'Departments', icon: 'fas fa-book', count: departments.value.length, tone: 'blue' },
  { key: 'levels', label: 'Levels', icon: 'fas fa-layer-group', count: levels.value.length, tone: 'teal' },
])

const stats = computed(() => ({
  faculties: faculties.value.length,
  departments: departments.value.length,
  levels: levels.value.length,
  active: faculties.value.filter((f) => f.is_active).length + departments.value.filter((d) => d.is_active).length,
}))

const panelTitle = computed(() => ({
  faculties: 'Faculties',
  departments: 'Departments',
  levels: 'Study levels',
}[activeTab.value]))

const panelSubtitle = computed(() => ({
  faculties: 'School-wide academic divisions',
  departments: 'Programs under each faculty',
  levels: 'Year of study options for onboarding',
}[activeTab.value]))

const searchPlaceholder = computed(() => ({
  faculties: 'Search faculties…',
  departments: 'Search departments…',
  levels: 'Search levels…',
}[activeTab.value]))

const createLabel = computed(() => ({
  faculties: 'Add faculty',
  departments: 'Add department',
  levels: 'Add level',
}[activeTab.value]))

const dialogTitle = computed(() => {
  const action = editingId.value ? 'Edit' : 'Add'
  return `${action} ${dialogType.value}`
})

const filterRows = (rows, fields) => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return rows
  return rows.filter((row) => fields.some((field) => String(row[field] || '').toLowerCase().includes(q)))
}

const filteredFaculties = computed(() => filterRows(faculties.value, ['name', 'code']))
const filteredDepartments = computed(() => filterRows(departments.value, ['name', 'code', 'faculty_name']))
const filteredLevels = computed(() => filterRows(levels.value, ['name']))

const currentRows = computed(() => {
  if (activeTab.value === 'faculties') return filteredFaculties.value
  if (activeTab.value === 'departments') return filteredDepartments.value
  return filteredLevels.value
})

const listParams = computed(() => (activeOnly.value ? { active_only: 'true' } : {}))

const fetchAll = async () => {
  loading.value = true
  try {
    const [fRes, dRes, lRes] = await Promise.all([
      academicApi.faculties(listParams.value),
      academicApi.departments(listParams.value),
      academicApi.levels(),
    ])
    faculties.value = fRes.data
    departments.value = dRes.data.map((d) => ({
      ...d,
      faculty_name: d.faculty_name || d.faculty?.name,
    }))
    levels.value = lRes.data
  } catch (error) {
    console.error('Failed to load academic structure:', error)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    name: '',
    code: '',
    description: '',
    is_active: true,
    faculty_uuid: null,
    display_order: levels.value.length + 1,
  }
  formError.value = ''
  editingId.value = null
}

const openCreate = () => {
  if (activeTab.value === 'faculties') dialogType.value = 'faculty'
  else if (activeTab.value === 'departments') dialogType.value = 'department'
  else dialogType.value = 'level'
  resetForm()
  showDialog.value = true
}

const closeDialog = () => {
  showDialog.value = false
  resetForm()
}

const editFaculty = (row) => {
  dialogType.value = 'faculty'
  editingId.value = row.uuid
  form.value = { name: row.name, code: row.code, description: row.description || '', is_active: row.is_active }
  showDialog.value = true
}

const editDepartment = (row) => {
  dialogType.value = 'department'
  editingId.value = row.uuid
  form.value = {
    name: row.name,
    code: row.code,
    description: row.description || '',
    is_active: row.is_active,
    faculty_uuid: row.faculty?.uuid || row.faculty_uuid,
  }
  showDialog.value = true
}

const editLevel = (row) => {
  dialogType.value = 'level'
  editingId.value = row.uuid
  form.value = { name: row.name, display_order: row.display_order }
  showDialog.value = true
}

const submitForm = async () => {
  submitting.value = true
  formError.value = ''
  try {
    if (dialogType.value === 'faculty') {
      const payload = {
        name: form.value.name.trim(),
        code: form.value.code.trim().toUpperCase(),
        description: form.value.description,
        is_active: form.value.is_active,
      }
      if (editingId.value) await academicApi.updateFaculty(editingId.value, payload)
      else await academicApi.createFaculty(payload)
    } else if (dialogType.value === 'department') {
      const payload = {
        name: form.value.name.trim(),
        code: form.value.code.trim().toUpperCase(),
        description: form.value.description,
        is_active: form.value.is_active,
        faculty_uuid: form.value.faculty_uuid,
      }
      if (editingId.value) await academicApi.updateDepartment(editingId.value, payload)
      else await academicApi.createDepartment(payload)
    } else {
      const payload = { name: form.value.name.trim(), display_order: form.value.display_order }
      if (editingId.value) await academicApi.updateLevel(editingId.value, payload)
      else await academicApi.createLevel(payload)
    }
    closeDialog()
    await fetchAll()
  } catch (error) {
    formError.value = error.response?.data?.error
      || Object.values(error.response?.data || {}).flat().join(' ')
      || 'Save failed. Please try again.'
  } finally {
    submitting.value = false
  }
}

const toggleFaculty = async (row) => {
  await academicApi.updateFaculty(row.uuid, { is_active: !row.is_active })
  await fetchAll()
}

const toggleDepartment = async (row) => {
  await academicApi.updateDepartment(row.uuid, { is_active: !row.is_active })
  await fetchAll()
}

const confirmDeleteLevel = async (row) => {
  if (!confirm(`Delete "${row.name}"?`)) return
  try {
    await academicApi.deleteLevel(row.uuid)
    await fetchAll()
  } catch (error) {
    alert(error.response?.data?.error || 'Could not delete level.')
  }
}

onMounted(fetchAll)
</script>

<style scoped>
.filter-check {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8125rem;
  color: #64748b;
  cursor: pointer;
  user-select: none;
}

.check-row {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.8125rem;
  color: #475569;
}

.form-error {
  margin: 0;
  font-size: 0.8125rem;
  color: #dc2626;
}
</style>
