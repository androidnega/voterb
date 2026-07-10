<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">User Management</h1>
        <p class="text-gray-500 text-sm mt-1">Manage all users and their roles.</p>
      </div>
      <Button label="Add User" icon="pi pi-plus" @click="showCreateDialog = true" />
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Total Users</p>
        <p class="text-xl font-bold text-gray-900">{{ stats.total }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Active</p>
        <p class="text-xl font-bold text-emerald-600">{{ stats.active }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Students</p>
        <p class="text-xl font-bold text-blue-600">{{ stats.students }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <p class="text-xs font-medium text-gray-400 uppercase">Admins</p>
        <p class="text-xl font-bold text-purple-600">{{ stats.admins }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-4">
      <div class="relative flex-1 min-w-[150px]">
        <i class="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
        <InputText v-model="filters.search" placeholder="Search users..." class="w-full pl-9" @input="applyFilters" />
      </div>
      <Dropdown v-model="filters.role" :options="roles" optionLabel="name" optionValue="name" placeholder="All Roles" class="w-40" @change="applyFilters" />
      <Dropdown v-model="filters.is_active" :options="statusOptions" optionLabel="label" optionValue="value" placeholder="Status" class="w-40" @change="applyFilters" />
      <Button label="Clear" severity="secondary" @click="clearFilters" />
    </div>

    <!-- User Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">User</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Email</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Role</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Status</th>
              <th class="text-left py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Created</th>
              <th class="text-center py-3 px-4 font-semibold text-gray-600 text-xs uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.uuid" class="border-b border-gray-50 hover:bg-gray-50/30 transition-colors">
              <td class="py-3 px-4">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
                    <span class="text-emerald-700 font-semibold text-sm">{{ getInitials(user) }}</span>
                  </div>
                  <div>
                    <p class="font-medium text-gray-800">{{ user.first_name }} {{ user.last_name }}</p>
                    <p class="text-xs text-gray-400">{{ user.index_number || '—' }}</p>
                  </div>
                </div>
              </td>
              <td class="py-3 px-4 text-gray-600">{{ user.email }}</td>
              <td class="py-3 px-4">
                <Badge :value="user.role_name || 'none'" :severity="getRoleSeverity(user.role_name)" />
              </td>
              <td class="py-3 px-4">
                <Badge :value="user.is_active ? 'Active' : 'Inactive'" :severity="user.is_active ? 'success' : 'danger'" />
              </td>
              <td class="py-3 px-4 text-gray-600">{{ formatDate(user.created_at) }}</td>
              <td class="py-3 px-4 text-center">
                <div class="flex items-center justify-center gap-1">
                  <Button icon="pi pi-pencil" size="small" severity="secondary" text rounded @click="editUser(user)" tooltip="Edit" />
                  <Button v-if="user.is_active" icon="pi pi-ban" size="small" severity="warning" text rounded @click="toggleStatus(user)" tooltip="Deactivate" />
                  <Button v-else icon="pi pi-check" size="small" severity="success" text rounded @click="toggleStatus(user)" tooltip="Activate" />
                  <Button icon="pi pi-trash" size="small" severity="danger" text rounded @click="confirmDelete(user)" tooltip="Delete" />
                </div>
              </td>
            </tr>
            <tr v-if="users.length === 0 && !loading">
              <td colspan="6" class="py-12 text-center text-gray-400">
                <i class="fas fa-users text-4xl block mb-3 text-gray-200"></i>
                <p class="text-sm">No users found.</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <Dialog v-model:visible="showDialog" :header="isEditing ? 'Edit User' : 'Add User'" :modal="true" class="w-full max-w-lg">
      <form @submit.prevent="submitUser" class="p-1">
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">First Name</label>
              <InputText v-model="form.first_name" class="w-full" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
              <InputText v-model="form.last_name" class="w-full" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <InputText v-model="form.email" type="email" class="w-full" required />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Index Number</label>
              <InputText v-model="form.index_number" class="w-full" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
              <InputText v-model="form.phone_number" class="w-full" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Role</label>
            <Dropdown v-model="form.role_uuid" :options="roles" optionLabel="name" optionValue="uuid" placeholder="Select role" class="w-full" required />
          </div>
          <div v-if="!isEditing">
            <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <InputText v-model="form.password" type="password" class="w-full" required />
          </div>
          <div v-if="isEditing">
            <label class="block text-sm font-medium text-gray-700 mb-1">Reset Password</label>
            <div class="flex gap-2">
              <InputText v-model="form.new_password" type="password" class="flex-1" placeholder="Enter new password..." />
              <Button label="Reset" severity="warning" @click="resetPassword" />
            </div>
          </div>
          <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button label="Cancel" severity="secondary" @click="closeDialog" />
            <Button label="Save" type="submit" :loading="submitting" />
          </div>
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usersApi } from '@/api/users'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'

const authStore = useAuthStore()
const users = ref([])
const roles = ref([])
const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const isEditing = ref(false)
const editingUser = ref(null)

const filters = ref({
  search: '',
  role: '',
  is_active: ''
})

const statusOptions = [
  { label: 'All', value: '' },
  { label: 'Active', value: 'true' },
  { label: 'Inactive', value: 'false' }
]

const form = ref({
  email: '',
  first_name: '',
  last_name: '',
  index_number: '',
  phone_number: '',
  role_uuid: null,
  password: '',
  new_password: ''
})

const stats = computed(() => {
  const total = users.value.length
  const active = users.value.filter(u => u.is_active).length
  const students = users.value.filter(u => u.role_name === 'student').length
  const admins = users.value.filter(u => u.role_name === 'admin' || u.role_name === 'super_admin').length
  return { total, active, students, admins }
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.search) params.search = filters.value.search
    if (filters.value.role) params.role = filters.value.role
    if (filters.value.is_active) params.is_active = filters.value.is_active
    const response = await usersApi.list(params)
    users.value = response.data
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

const applyFilters = () => {
  fetchUsers()
}

const clearFilters = () => {
  filters.value = { search: '', role: '', is_active: '' }
  fetchUsers()
}

const getInitials = (user) => {
  const first = user.first_name?.charAt(0) || ''
  const last = user.last_name?.charAt(0) || ''
  return (first + last).toUpperCase() || 'U'
}

const getRoleSeverity = (role) => {
  const map = {
    student: 'info',
    candidate: 'info',
    admin: 'warning',
    super_admin: 'danger'
  }
  return map[role] || 'secondary'
}

const formatDate = (date) => {
  if (!date) return '—'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const editUser = (user) => {
  isEditing.value = true
  editingUser.value = user
  form.value = {
    email: user.email,
    first_name: user.first_name || '',
    last_name: user.last_name || '',
    index_number: user.index_number || '',
    phone_number: user.phone_number || '',
    role_uuid: user.role?.uuid || null,
    password: '',
    new_password: ''
  }
  showDialog.value = true
}

const closeDialog = () => {
  showDialog.value = false
  isEditing.value = false
  editingUser.value = null
  form.value = {
    email: '',
    first_name: '',
    last_name: '',
    index_number: '',
    phone_number: '',
    role_uuid: null,
    password: '',
    new_password: ''
  }
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
      role_uuid: form.value.role_uuid
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
  if (form.value.new_password.length < 6) {
    alert('Password must be at least 6 characters.')
    return
  }
  if (confirm(`Reset password for ${editingUser.value.email}?`)) {
    try {
      await usersApi.resetPassword(editingUser.value.uuid, form.value.new_password)
      alert('Password reset successfully.')
      form.value.new_password = ''
    } catch (error) {
      console.error('Failed to reset password:', error)
      alert('Failed to reset password.')
    }
  }
}

const toggleStatus = async (user) => {
  const action = user.is_active ? 'deactivate' : 'activate'
  if (confirm(`${action} ${user.email}?`)) {
    try {
      if (user.is_active) {
        await usersApi.deactivate(user.uuid)
      } else {
        await usersApi.activate(user.uuid)
      }
      await fetchUsers()
    } catch (error) {
      console.error('Failed to toggle status:', error)
      alert('Failed to update user status.')
    }
  }
}

const confirmDelete = (user) => {
  if (confirm(`Delete ${user.email} permanently? This cannot be undone.`)) {
    deleteUser(user.uuid)
  }
}

const deleteUser = async (uuid) => {
  try {
    await usersApi.delete(uuid)
    await fetchUsers()
  } catch (error) {
    console.error('Failed to delete user:', error)
    alert('Failed to delete user.')
  }
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
})
</script>
