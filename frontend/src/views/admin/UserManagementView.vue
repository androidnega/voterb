<template>
  <div class="admin-page">
    <PageHeader
      :loading="loading"
      :show-refresh="true"
      @refresh="fetchUsers"
    >
      <template #actions>
        <button type="button" class="btn btn-primary" @click="openCreateDialog">
          <i class="fas fa-plus"></i> Add User
        </button>
      </template>
    </PageHeader>

    <div class="kpi-strip">
      <div class="kpi-item">
        <p class="kpi-label">Total users</p>
        <p class="kpi-value">{{ stats.total }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Active</p>
        <p class="kpi-value is-ok">{{ stats.active }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Students</p>
        <p class="kpi-value is-info">{{ stats.students }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Staff</p>
        <p class="kpi-value">{{ stats.admins }}</p>
      </div>
    </div>

    <div class="filter-bar page-section">
      <div class="filter-input-wrap">
        <i class="fas fa-search"></i>
        <input v-model="filters.search" type="text" placeholder="Search users…" @input="applyFilters" />
      </div>
      <select v-model="filters.role" class="filter-select" @change="applyFilters">
        <option value="">All roles</option>
        <option v-for="role in roles" :key="role.uuid" :value="role.name">{{ roleLabel(role.name) }}</option>
      </select>
      <select v-model="filters.is_active" class="filter-select" @change="applyFilters">
        <option v-for="opt in statusOptions" :key="opt.label" :value="opt.value">{{ opt.label }}</option>
      </select>
      <button type="button" class="btn btn-ghost" @click="clearFilters">Clear</button>
    </div>

    <section class="table-surface">
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Role</th>
              <th>Institution</th>
              <th>Status</th>
              <th>Created</th>
              <th class="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in paginated" :key="user.uuid">
              <td>
                <div class="user-cell">
                  <div class="avatar">{{ getInitials(user) }}</div>
                  <div>
                    <p class="cell-title">{{ user.first_name }} {{ user.last_name }}</p>
                    <p class="cell-sub">{{ formatIndexDisplay(user.index_number) }}</p>
                  </div>
                </div>
              </td>
              <td>{{ user.email }}</td>
              <td><span class="admin-badge" :class="roleBadge(user.role_name)">{{ roleLabel(user.role_name) }}</span></td>
              <td class="text-muted">{{ user.institution_name || '—' }}</td>
              <td><span class="admin-badge" :class="user.is_active ? 'success' : 'danger'">{{ user.is_active ? 'Active' : 'Inactive' }}</span></td>
              <td class="text-muted">{{ formatDate(user.created_at) }}</td>
              <td>
                <div class="row-actions">
                  <button type="button" class="admin-icon-btn" title="Edit" @click="editUser(user)"><i class="fas fa-pen"></i></button>
                  <button type="button" class="admin-icon-btn" :title="user.is_active ? 'Deactivate' : 'Activate'" @click="toggleStatus(user)">
                    <i :class="user.is_active ? 'fas fa-ban' : 'fas fa-check'"></i>
                  </button>
                  <button type="button" class="admin-icon-btn danger" title="Delete" @click="confirmDelete(user)"><i class="fas fa-trash"></i></button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && users.length === 0">
              <td colspan="7"><EmptyState icon="fas fa-users" title="No users found" message="Try adjusting your search or add a new user." /></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="table-surface__foot">
        <TablePagination
          :page="page"
          :page-size="size"
          :total="total"
          :total-pages="totalPages"
          :from="from"
          :to="to"
          @update:page="setPage"
          @update:page-size="setPageSize"
        />
      </div>
    </section>

    <Dialog
      v-model:visible="showDialog"
      :header="isEditing ? 'Edit User' : 'Add User'"
      :modal="true"
      class="user-dialog"
      :style="{ width: 'min(640px, 96vw)' }"
    >
      <form @submit.prevent="submitUser" class="dialog-form">
        <div class="form-grid">
          <div>
            <label>First name</label>
            <InputText v-model="form.first_name" class="w-full" required />
          </div>
          <div>
            <label>Last name</label>
            <InputText v-model="form.last_name" class="w-full" required />
          </div>
        </div>

        <div>
          <label>Email</label>
          <InputText v-model="form.email" type="email" class="w-full" required />
        </div>

        <div class="form-grid">
          <div>
            <label>Phone number</label>
            <InputText v-model="form.phone_number" class="w-full" placeholder="024…" />
          </div>
          <div>
            <label>Index number</label>
            <InputText v-model="form.index_number" class="w-full" placeholder="Optional for staff" />
          </div>
        </div>

        <div class="form-grid">
          <div>
            <label>Role</label>
            <Dropdown
              v-model="form.role_uuid"
              :options="roleOptions"
              optionLabel="label"
              optionValue="uuid"
              placeholder="Select role"
              class="w-full"
            ></Dropdown>
          </div>
          <div>
            <label>Institution</label>
            <Dropdown
              v-model="form.institution_uuid"
              :options="institutions"
              optionLabel="label"
              optionValue="uuid"
              placeholder="Select institution"
              class="w-full"
              showClear
            ></Dropdown>
          </div>
        </div>

        <p v-if="isAdminRole" class="field-hint">
          Role <strong>admin</strong> is Main EC. Choosing an institution attaches this user to that institution’s Main EC unit.
        </p>
        <p v-else-if="isSuperAdminRole" class="field-hint">
          Super Admin is platform-wide. Institution is optional.
        </p>

        <template v-if="isStudentRole">
          <FacultyDepartmentSelect
            v-model:faculty-uuid="form.faculty_uuid"
            v-model:department-uuid="form.department_uuid"
            grid
          />
        </template>

        <div v-if="!isEditing">
          <label>Password</label>
          <InputText v-model="form.password" type="password" class="w-full" required minlength="8" />
          <p class="field-hint">Minimum 8 characters.</p>
        </div>

        <div v-if="isEditing">
          <label>Reset password</label>
          <div class="reset-row">
            <InputText v-model="form.new_password" type="password" class="flex-1" placeholder="New password…" />
            <Button label="Reset" severity="warning" type="button" @click="resetPassword" />
          </div>
        </div>

        <div class="dialog-actions">
          <Button label="Cancel" severity="secondary" type="button" @click="closeDialog" />
          <Button :label="isEditing ? 'Save changes' : 'Create user'" type="submit" :loading="submitting" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { usersApi } from '@/api/users'
import { institutionApi } from '@/api/institutions'
import { formatIndexDisplay } from '@/utils/index'
import { usePagination } from '@/composables/usePagination'
import PageHeader from '@/components/admin/PageHeader.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import TablePagination from '@/components/admin/TablePagination.vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import FacultyDepartmentSelect from '@/components/academic/FacultyDepartmentSelect.vue'

const ROLE_LABELS = {
  student: 'Student',
  candidate: 'Candidate',
  admin: 'Main EC (admin)',
  sub_ec: 'Sub EC',
  auditor: 'Auditor',
  super_admin: 'Super Admin',
}

const users = ref([])
const roles = ref([])
const institutions = ref([])
const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const isEditing = ref(false)
const editingUser = ref(null)

const filters = ref({ search: '', role: '', is_active: '' })

const { page, size, total, totalPages, paginated, from, to, setPage, setPageSize, reset } = usePagination(users, 10)

const statusOptions = [
  { label: 'All statuses', value: '' },
  { label: 'Active', value: 'true' },
  { label: 'Inactive', value: 'false' },
]

const emptyForm = () => ({
  email: '',
  first_name: '',
  last_name: '',
  index_number: '',
  phone_number: '',
  role_uuid: null,
  institution_uuid: null,
  password: '',
  new_password: '',
  faculty_uuid: null,
  department_uuid: null,
})

const form = ref(emptyForm())

const selectedRole = computed(() => roles.value.find((r) => r.uuid === form.value.role_uuid) || null)
const isStudentRole = computed(() => selectedRole.value?.name === 'student')
const isAdminRole = computed(() => selectedRole.value?.name === 'admin')
const isSuperAdminRole = computed(() => selectedRole.value?.name === 'super_admin')
const needsInstitution = computed(() => ['admin', 'sub_ec', 'auditor'].includes(selectedRole.value?.name))

const roleOptions = computed(() =>
  roles.value.map((role) => ({
    uuid: role.uuid,
    name: role.name,
    label: ROLE_LABELS[role.name] || role.name,
  })),
)

const stats = computed(() => {
  const totalCount = users.value.length
  const active = users.value.filter((u) => u.is_active).length
  const students = users.value.filter((u) => u.role_name === 'student').length
  const admins = users.value.filter((u) => ['admin', 'super_admin', 'auditor', 'sub_ec'].includes(u.role_name)).length
  return { total: totalCount, active, students, admins }
})

const roleLabel = (role) => ROLE_LABELS[role] || role || 'none'
const roleBadge = (role) => ({
  student: 'info',
  candidate: 'info',
  admin: 'warning',
  sub_ec: 'warning',
  super_admin: 'danger',
  auditor: 'neutral',
}[role] || 'neutral')

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.search) params.search = filters.value.search
    if (filters.value.role) params.role = filters.value.role
    if (filters.value.is_active) params.is_active = filters.value.is_active
    const response = await usersApi.list(params)
    users.value = response.data
    reset()
  } catch (error) {
    console.error('Failed to fetch users:', error)
  } finally {
    loading.value = false
  }
}

const fetchRoles = async () => {
  try {
    const response = await usersApi.getRoles()
    roles.value = response.data
  } catch (error) {
    console.error('Failed to fetch roles:', error)
  }
}

const fetchInstitutions = async () => {
  try {
    const response = await institutionApi.list()
    const rows = Array.isArray(response.data) ? response.data : (response.data?.results || [])
    institutions.value = rows.map((row) => ({
      uuid: row.uuid,
      name: row.name,
      label: row.short_name ? `${row.name} (${row.short_name})` : row.name,
    }))
  } catch (error) {
    console.error('Failed to fetch institutions:', error)
    institutions.value = []
  }
}

const applyFilters = () => fetchUsers()
const clearFilters = () => { filters.value = { search: '', role: '', is_active: '' }; fetchUsers() }

const getInitials = (user) => {
  const first = user.first_name?.charAt(0) || ''
  const last = user.last_name?.charAt(0) || ''
  return (first + last).toUpperCase() || 'U'
}

const formatDate = (date) => date
  ? new Date(date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  : '—'

const openCreateDialog = () => {
  isEditing.value = false
  editingUser.value = null
  form.value = emptyForm()
  // Default institution to TTU when present
  const ttu = institutions.value.find((i) => /ttu|takoradi/i.test(i.label))
  if (ttu) form.value.institution_uuid = ttu.uuid
  showDialog.value = true
}

const editUser = (user) => {
  isEditing.value = true
  editingUser.value = user
  form.value = {
    ...emptyForm(),
    email: user.email,
    first_name: user.first_name || '',
    last_name: user.last_name || '',
    index_number: user.index_number || '',
    phone_number: user.phone_number || '',
    role_uuid: user.role_uuid || user.role?.uuid || user.role || null,
    institution_uuid: user.institution_uuid || null,
    faculty_uuid: user.faculty_uuid || null,
    department_uuid: user.department_uuid || null,
  }
  showDialog.value = true
}

const closeDialog = () => {
  showDialog.value = false
  isEditing.value = false
  editingUser.value = null
}

const submitUser = async () => {
  if (!form.value.role_uuid) {
    alert('Please select a role.')
    return
  }
  if (needsInstitution.value && !form.value.institution_uuid) {
    alert('Please select an institution for this role.')
    return
  }
  if (!isEditing.value && (!form.value.password || form.value.password.length < 8)) {
    alert('Password must be at least 8 characters.')
    return
  }

  submitting.value = true
  try {
    const data = {
      email: form.value.email,
      first_name: form.value.first_name,
      last_name: form.value.last_name,
      index_number: form.value.index_number || '',
      phone_number: form.value.phone_number || '',
      role_uuid: form.value.role_uuid,
      institution_uuid: form.value.institution_uuid || null,
    }
    if (isStudentRole.value) {
      data.faculty_uuid = form.value.faculty_uuid
      data.department_uuid = form.value.department_uuid
    }
    if (!isEditing.value) {
      data.password = form.value.password
      await usersApi.create(data)
    } else {
      await usersApi.update(editingUser.value.uuid, data)
    }
    closeDialog()
    await fetchUsers()
  } catch (error) {
    console.error('Failed to save user:', error)
    const detail = error?.response?.data
    const message = typeof detail === 'string'
      ? detail
      : detail?.detail || detail?.email?.[0] || 'Failed to save user. Please check the form.'
    alert(message)
  } finally {
    submitting.value = false
  }
}

const resetPassword = async () => {
  if (!editingUser.value || !form.value.new_password) return
  if (form.value.new_password.length < 8) { alert('Password must be at least 8 characters.'); return }
  if (!confirm(`Reset password for ${editingUser.value.email}?`)) return
  try {
    await usersApi.resetPassword(editingUser.value.uuid, form.value.new_password)
    alert('Password reset successfully.')
    form.value.new_password = ''
  } catch {
    alert('Failed to reset password.')
  }
}

const toggleStatus = async (user) => {
  const action = user.is_active ? 'deactivate' : 'activate'
  if (!confirm(`${action} ${user.email}?`)) return
  try {
    if (user.is_active) await usersApi.deactivate(user.uuid)
    else await usersApi.activate(user.uuid)
    await fetchUsers()
  } catch {
    alert('Failed to update user status.')
  }
}

const confirmDelete = (user) => {
  if (confirm(`Delete ${user.email} permanently? This cannot be undone.`)) deleteUser(user.uuid)
}

const deleteUser = async (uuid) => {
  try {
    await usersApi.delete(uuid)
    await fetchUsers()
  } catch {
    alert('Failed to delete user.')
  }
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
  fetchInstitutions()
})
</script>

<style scoped>
.user-dialog :deep(.p-dialog-content) {
  padding-top: 0.25rem;
}

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.dialog-form label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted, #64748b);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem;
}

.field-hint {
  margin: -0.35rem 0 0;
  font-size: 0.78rem;
  line-height: 1.4;
  color: var(--text-muted, #64748b);
}

.reset-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 0.35rem;
  padding-top: 0.75rem;
  border-top: 1px solid color-mix(in srgb, var(--border, #e2e8f0) 80%, transparent);
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
