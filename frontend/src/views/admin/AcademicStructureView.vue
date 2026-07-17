<template>
  <div class="admin-page">
    <PageHeader
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

    <TabNav v-model="activeTab" :tabs="tabs" class="page-section" />

    <div class="filter-bar page-section">
      <div class="filter-input-wrap">
        <i class="fas fa-search"></i>
        <input v-model="searchQuery" type="text" :placeholder="searchPlaceholder" />
      </div>
      <label class="filter-check">
        <input v-model="activeOnly" type="checkbox" @change="fetchAll" />
        <span>Active only</span>
      </label>
      <button v-if="searchQuery" type="button" class="btn btn-ghost" @click="searchQuery = ''">Clear</button>
    </div>

    <DataPanel :title="panelTitle" :subtitle="panelSubtitle" no-padding>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr v-if="activeTab === 'institution'">
              <th>Category</th>
              <th>Code</th>
              <th>Status</th>
              <th class="text-center">Actions</th>
            </tr>
            <tr v-else-if="activeTab === 'faculties'">
              <th>Faculty</th>
              <th>Code</th>
              <th>Departments</th>
              <th>Status</th>
              <th class="text-center">Actions</th>
            </tr>
            <tr v-else>
              <th>Department</th>
              <th>Code</th>
              <th>Faculty</th>
              <th>Status</th>
              <th class="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="activeTab === 'institution'">
              <tr v-for="row in filteredInstitutionCategories" :key="row.uuid">
                <td><span class="cell-title">{{ row.name }}</span></td>
                <td class="mono">{{ row.code || '—' }}</td>
                <td>
                  <span class="admin-badge" :class="row.is_active ? 'success' : 'neutral'">
                    {{ row.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>
                  <div class="row-actions">
                    <button type="button" class="admin-icon-btn" title="Edit" @click="editInstitutionCategory(row)">
                      <i class="fas fa-pen"></i>
                    </button>
                    <button
                      type="button"
                      class="admin-icon-btn"
                      :title="row.is_active ? 'Deactivate' : 'Activate'"
                      @click="toggleInstitutionCategory(row)"
                    >
                      <i :class="row.is_active ? 'fas fa-ban' : 'fas fa-check'"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </template>

            <template v-else-if="activeTab === 'faculties'">
              <tr v-for="row in filteredFaculties" :key="row.uuid">
                <td><span class="cell-title">{{ row.name }}</span></td>
                <td class="mono">{{ row.code }}</td>
                <td>
                  <button
                    type="button"
                    class="dept-count-btn"
                    :disabled="!(row.department_count > 0)"
                    :title="row.department_count > 0 ? 'View departments' : 'No departments linked'"
                    @click="openFacultyDepartments(row)"
                  >
                    {{ row.department_count ?? 0 }}
                  </button>
                </td>
                <td>
                  <span class="admin-badge" :class="row.is_active ? 'success' : 'neutral'">
                    {{ row.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>
                  <div class="row-actions">
                    <button type="button" class="admin-icon-btn" title="Edit" @click="editFaculty(row)">
                      <i class="fas fa-pen"></i>
                    </button>
                    <button
                      type="button"
                      class="admin-icon-btn"
                      :title="row.is_active ? 'Deactivate' : 'Activate'"
                      @click="toggleFaculty(row)"
                    >
                      <i :class="row.is_active ? 'fas fa-ban' : 'fas fa-check'"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </template>

            <template v-else>
              <tr v-for="row in filteredDepartments" :key="row.uuid">
                <td><span class="cell-title">{{ row.name }}</span></td>
                <td class="mono">{{ row.code }}</td>
                <td>
                  <span class="faculty-link">{{ row.faculty_name || row.faculty?.name || '—' }}</span>
                </td>
                <td>
                  <span class="admin-badge" :class="row.is_active ? 'success' : 'neutral'">
                    {{ row.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>
                  <div class="row-actions">
                    <button type="button" class="admin-icon-btn" title="Edit" @click="editDepartment(row)">
                      <i class="fas fa-pen"></i>
                    </button>
                    <button
                      type="button"
                      class="admin-icon-btn"
                      :title="row.is_active ? 'Deactivate' : 'Activate'"
                      @click="toggleDepartment(row)"
                    >
                      <i :class="row.is_active ? 'fas fa-ban' : 'fas fa-check'"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </template>

            <tr v-if="!loading && currentRows.length === 0">
              <td :colspan="activeTab === 'institution' ? 4 : 5">
                <EmptyState
                  icon="fas fa-university"
                  title="Nothing found"
                  message="Adjust your search or add a new entry."
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </DataPanel>

    <Dialog v-model:visible="showDialog" :header="dialogTitle" :modal="true" class="w-full max-w-lg">
      <form class="dialog-form" @submit.prevent="submitForm">
        <template v-if="dialogType === 'institution'">
          <div>
            <label>Name</label>
            <InputText v-model="form.name" class="w-full" required placeholder="e.g. Institution" />
          </div>
          <div>
            <label>Code</label>
            <InputText v-model="form.code" class="w-full mono" maxlength="20" placeholder="Optional code" />
          </div>
          <div>
            <label>Description</label>
            <Textarea v-model="form.description" rows="2" class="w-full" placeholder="Optional description" />
          </div>
          <label class="check-row">
            <input v-model="form.is_active" type="checkbox" />
            <span>Active</span>
          </label>
        </template>

        <template v-else-if="dialogType === 'faculty'">
          <div>
            <label>Name</label>
            <InputText v-model="form.name" class="w-full" required placeholder="e.g. Faculty of Engineering" />
          </div>
          <div>
            <label>Code</label>
            <InputText v-model="form.code" class="w-full mono" required maxlength="20" placeholder="e.g. FOE" />
          </div>
          <div>
            <label>Description</label>
            <Textarea v-model="form.description" rows="2" class="w-full" placeholder="Optional description" />
          </div>
          <label class="check-row">
            <input v-model="form.is_active" type="checkbox" />
            <span>Active</span>
          </label>
        </template>

        <template v-else>
          <div>
            <label>Faculty</label>
            <Dropdown
              v-model="form.faculty_uuid"
              :options="faculties"
              optionLabel="name"
              optionValue="uuid"
              placeholder="Select faculty"
              class="w-full"
              required
            />
          </div>
          <div>
            <label>Name</label>
            <InputText
              v-model="form.name"
              class="w-full"
              required
              placeholder="e.g. Computer Science Department"
            />
          </div>
          <div>
            <label>Code</label>
            <InputText v-model="form.code" class="w-full mono" required maxlength="20" placeholder="e.g. CS" />
          </div>
          <div>
            <label>Description</label>
            <Textarea v-model="form.description" rows="2" class="w-full" placeholder="Optional description" />
          </div>
          <label class="check-row">
            <input v-model="form.is_active" type="checkbox" />
            <span>Active</span>
          </label>
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
import DataPanel from '@/components/admin/DataPanel.vue'
import TabNav from '@/components/admin/TabNav.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import { usePageHeading } from '@/composables/usePageHeading'

const { setPageHeading } = usePageHeading()
setPageHeading({
  title: 'Categories',
  subtitle: 'Institution categories for Main EC, and faculties/departments for Sub EC registers',
})

const loading = ref(false)
const submitting = ref(false)
const activeTab = ref('institution')
const searchQuery = ref('')
const activeOnly = ref(true)
const showDialog = ref(false)
const dialogType = ref('institution')
const editingId = ref(null)
const formError = ref('')

const institutionCategories = ref([])
const faculties = ref([])
const departments = ref([])

const form = ref({
  name: '',
  code: '',
  description: '',
  is_active: true,
  faculty_uuid: null,
})

const tabs = computed(() => [
  { key: 'institution', label: 'Institution', icon: 'fas fa-building', count: institutionCategories.value.length, tone: 'teal' },
  { key: 'faculties', label: 'Faculties', icon: 'fas fa-university', count: faculties.value.length, tone: 'indigo' },
  { key: 'departments', label: 'Departments', icon: 'fas fa-book', count: departments.value.length, tone: 'blue' },
])

const panelTitle = computed(() => ({
  institution: 'Institution',
  faculties: 'Faculties',
  departments: 'Departments',
}[activeTab.value]))

const panelSubtitle = computed(() => ({
  institution: 'Main EC institution-wide categories (e.g. Institution, General, SRC)',
  faculties: 'Faculty categories (e.g. FAS, FAAT) used for Sub EC assignment',
  departments: 'Department categories under each faculty (e.g. Hospitality, Comp. Sci.)',
}[activeTab.value]))

const searchPlaceholder = computed(() => ({
  institution: 'Search institution categories…',
  faculties: 'Search faculties…',
  departments: 'Search departments…',
}[activeTab.value]))

const createLabel = computed(() => ({
  institution: 'Add institution category',
  faculties: 'Add faculty',
  departments: 'Add department',
}[activeTab.value]))

const dialogTitle = computed(() => {
  const action = editingId.value ? 'Edit' : 'Add'
  const labels = {
    institution: 'institution category',
    faculty: 'faculty',
    department: 'department',
  }
  return `${action} ${labels[dialogType.value] || dialogType.value}`
})

const filterRows = (rows, fields) => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return rows
  return rows.filter((row) => fields.some((field) => String(row[field] || '').toLowerCase().includes(q)))
}

const filteredInstitutionCategories = computed(() => filterRows(institutionCategories.value, ['name', 'code']))
const filteredFaculties = computed(() => filterRows(faculties.value, ['name', 'code']))
const filteredDepartments = computed(() => filterRows(departments.value, ['name', 'code', 'faculty_name']))

const currentRows = computed(() => {
  if (activeTab.value === 'institution') return filteredInstitutionCategories.value
  if (activeTab.value === 'faculties') return filteredFaculties.value
  return filteredDepartments.value
})

const listParams = computed(() => (
  activeOnly.value ? {} : { include_inactive: 'true' }
))

const fetchAll = async () => {
  loading.value = true
  try {
    const [iRes, fRes, dRes] = await Promise.all([
      academicApi.institutionCategories(listParams.value),
      academicApi.faculties(listParams.value),
      academicApi.departments(listParams.value),
    ])
    institutionCategories.value = Array.isArray(iRes.data) ? iRes.data : []
    const facultyRows = Array.isArray(fRes.data) ? fRes.data : []
    const departmentRows = Array.isArray(dRes.data) ? dRes.data : []
    faculties.value = facultyRows.map((f) => ({
      ...f,
      department_count: Number(f.department_count ?? 0),
    }))
    departments.value = departmentRows.map((d) => ({
      ...d,
      faculty_name: d.faculty_name || d.faculty?.name || '—',
      faculty_uuid: d.faculty?.uuid || d.faculty_uuid,
    }))
  } catch (error) {
    console.error('Failed to load academic structure:', error)
  } finally {
    loading.value = false
  }
}

const openFacultyDepartments = (faculty) => {
  activeTab.value = 'departments'
  searchQuery.value = faculty.name || ''
}

const resetForm = () => {
  form.value = {
    name: '',
    code: '',
    description: '',
    is_active: true,
    faculty_uuid: null,
  }
  formError.value = ''
  editingId.value = null
}

const openCreate = () => {
  dialogType.value = {
    institution: 'institution',
    faculties: 'faculty',
    departments: 'department',
  }[activeTab.value] || 'institution'
  resetForm()
  showDialog.value = true
}

const closeDialog = () => {
  showDialog.value = false
  resetForm()
}

const editInstitutionCategory = (row) => {
  dialogType.value = 'institution'
  editingId.value = row.uuid
  form.value = {
    name: row.name,
    code: row.code || '',
    description: row.description || '',
    is_active: row.is_active,
  }
  showDialog.value = true
}

const editFaculty = (row) => {
  dialogType.value = 'faculty'
  editingId.value = row.uuid
  form.value = {
    name: row.name,
    code: row.code,
    description: row.description || '',
    is_active: row.is_active,
  }
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

const submitForm = async () => {
  submitting.value = true
  formError.value = ''
  try {
    if (dialogType.value === 'institution') {
      const payload = {
        name: form.value.name.trim(),
        code: (form.value.code || '').trim().toUpperCase(),
        description: form.value.description,
        is_active: form.value.is_active,
      }
      if (editingId.value) await academicApi.updateInstitutionCategory(editingId.value, payload)
      else await academicApi.createInstitutionCategory(payload)
    } else if (dialogType.value === 'faculty') {
      const payload = {
        name: form.value.name.trim(),
        code: form.value.code.trim().toUpperCase(),
        description: form.value.description,
        is_active: form.value.is_active,
      }
      if (editingId.value) await academicApi.updateFaculty(editingId.value, payload)
      else await academicApi.createFaculty(payload)
    } else {
      const payload = {
        name: form.value.name.trim(),
        code: form.value.code.trim().toUpperCase(),
        description: form.value.description,
        is_active: form.value.is_active,
        faculty_uuid: form.value.faculty_uuid,
      }
      if (editingId.value) await academicApi.updateDepartment(editingId.value, payload)
      else await academicApi.createDepartment(payload)
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

const toggleInstitutionCategory = async (row) => {
  await academicApi.updateInstitutionCategory(row.uuid, { is_active: !row.is_active })
  await fetchAll()
}

const toggleFaculty = async (row) => {
  await academicApi.updateFaculty(row.uuid, { is_active: !row.is_active })
  await fetchAll()
}

const toggleDepartment = async (row) => {
  await academicApi.updateDepartment(row.uuid, { is_active: !row.is_active })
  await fetchAll()
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

.dept-count-btn {
  min-width: 2rem;
  padding: 0.2rem 0.5rem;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 0.45rem;
  background: #fff;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.8125rem;
  font-weight: 650;
  color: var(--vb-ink, #1f2937);
  cursor: pointer;
}
.dept-count-btn:hover:not(:disabled) {
  border-color: var(--vb-accent, #3d4f44);
  color: var(--vb-accent, #3d4f44);
}
.dept-count-btn:disabled {
  opacity: 0.55;
  cursor: default;
}

.faculty-link {
  color: var(--vb-ink, #1f2937);
  font-weight: 550;
}
</style>
