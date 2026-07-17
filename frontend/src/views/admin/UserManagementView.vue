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
        <option v-for="role in roles" :key="role.uuid" :value="role.name">{{ role.name }}</option>
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
              <td><span class="admin-badge" :class="roleBadge(user.role_name)">{{ user.role_name || 'none' }}</span></td>
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
              <td colspan="6"><EmptyState icon="fas fa-users" title="No users found" message="Try adjusting your search or add a new user." /></td>
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

    <Dialog v-model:visible="showDialog" :header="isEditing ? 'Edit User' : 'Add User'" :modal="true" class="w-full max-w-lg">
      <form @submit.prevent="submitUser" class="dialog-form">
        <div class="form-grid">
          <div><label>First Name</label><InputText v-model="form.first_name" class="w-full" /></div>
          <div><label>Last Name</label><InputText v-model="form.last_name" class="w-full" /></div>
        </div>
        <div><label>Email</label><InputText v-model="form.email" type="email" class="w-full" required /></div>
        <div class="form-grid">
          <div><label>Index Number</label><InputText v-model="form.index_number" class="w-full" /></div>
          <div><label>Phone</label><InputText v-model="form.phone_number" class="w-full" /></div>
        </div>
        <div><label>Role</label><Dropdown v-model="form.role_uuid" :options="roles" optionLabel="name" optionValue="uuid" placeholder="Select role" class="w-full" required /></div>
        <template v-if="isStudentRole">
          <FacultyDepartmentSelect
            v-model:faculty-uuid="form.faculty_uuid"
            v-model:department-uuid="form.department_uuid"
          />
        </template>
        <div v-if="!isEditing"><label>Password</label><InputText v-model="form.password" type="password" class="w-full" required /></div>
        <div v-if="isEditing">
          <label>Reset Password</label>
          <div class="reset-row">
            <InputText v-model="form.new_password" type="password" class="flex-1" placeholder="New password…" />
            <Button label="Reset" severity="warning" @click="resetPassword" />
          </div>
        </div>
        <div class="dialog-actions">
          <Button label="Cancel" severity="secondary" @click="closeDialog" />
          <Button label="Save" type="submit" :loading="submitting" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { usersApi } from '@/api/users'
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

const users = ref([])
const roles = ref([])
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
  password: '',
  new_password: '',
  faculty_uuid: null,
  department_uuid: null,
})

const form = ref(emptyForm())

const isStudentRole = computed(() => {
  const role = roles.value.find((r) => r.uuid === form.value.role_uuid)
  return role?.name === 'student'
})

const stats = computed(() => {
  const total = users.value.length
  const active = users.value.filter((u) => u.is_active).length
  const students = users.value.filter((u) => u.role_name === 'student').length
  const admins = users.value.filter((u) => ['admin', 'super_admin', 'auditor'].includes(u.role_name)).length
  return { total, active, students, admins }
})

const roleBadge = (role) => ({ student: 'info', candidate: 'info', admin: 'warning', super_admin: 'danger', auditor: 'neutral' }[role] || 'neutral')

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

const applyFilters = () => fetchUsers()
const clearFilters = () => { filters.value = { search: '', role: '', is_active: '' }; fetchUsers() }

const getInitials = (user) => {
  const first = user.first_name?.charAt(0) || ''
  const last = user.last_name?.charAt(0) || ''
  return (first + last).toUpperCase() || 'U'
}

const formatDate = (date) => date ? new Date(date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'

const openCreateDialog = () => {
  isEditing.value = false
  editingUser.value = null
  form.value = emptyForm()
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
    role_uuid: user.role?.uuid || null,
    faculty_uuid: user.faculty?.uuid || null,
    department_uuid: user.department?.uuid || null,
  }
  showDialog.value = true
}

const closeDialog = () => {
  showDialog.value = false
  isEditing.value = false
  editingUser.value = null
}

const submitUser = async () => {
  submitting.value = true
  try {
    const data = {
      email: form.value.email,
      first_name: form.value.first_name,
      last_name: form.value.last_name,
      index_number: form.value.index_number,
      phone_number: form.value.phone_number,
      role_uuid: form.value.role_uuid,
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
    alert('Failed to save user. Please check the form.')
  } finally {
    submitting.value = false
  }
}

const resetPassword = async () => {
  if (!editingUser.value || !form.value.new_password) return
  if (form.value.new_password.length < 6) { alert('Password must be at least 6 characters.'); return }
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

onMounted(() => { fetchUsers(); fetchRoles() })
</script>

