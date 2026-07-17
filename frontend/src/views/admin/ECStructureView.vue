<template>
  <div class="admin-page">
    <PageHeader :loading="loading" :show-refresh="true" @refresh="load">
      <template #actions>
        <button
          v-if="!showForm"
          type="button"
          class="btn btn-primary"
          :disabled="!structure?.governance?.ready"
          @click="openCreateForm"
        >
          <i class="fas fa-user-plus"></i>
          Propose Sub EC
        </button>
        <button
          v-else
          type="button"
          class="btn btn-ghost"
          @click="closeForm"
        >
          Cancel
        </button>
      </template>
    </PageHeader>

    <section
      v-if="structure"
      class="governance-note page-section"
      :class="{ 'is-blocked': !structure.governance?.ready }"
    >
      <i class="fas fa-check-double"></i>
      <div>
        <strong>Main EC controlled</strong>
        <p>
          Propose or edit a Sub EC and assign it to faculties or departments from
          <router-link to="/categories">Categories</router-link>.
          Creates and edits both require the other Main EC to approve before they take effect.
        </p>
        <small v-if="!structure.governance?.ready">{{ structure.governance?.message }}</small>
      </div>
    </section>

    <DataPanel
      v-if="showForm"
      :title="editingUnit ? 'Edit Sub EC' : 'Propose Sub EC'"
      :subtitle="editingUnit
        ? 'Changes are submitted for dual Main EC approval before they apply'
        : 'Account details and category assignment (faculty / department)'"
      class="page-section"
    >
      <form class="propose-form" @submit.prevent="submitProposal">
        <div class="field">
          <label>Sub EC unit name</label>
          <InputText
            v-model="form.unit_name"
            class="w-full"
            required
            placeholder="e.g. Faculty of Applied Arts EC"
          />
        </div>

        <div class="form-grid">
          <div class="field">
            <label>First name</label>
            <InputText v-model="form.first_name" class="w-full" required placeholder="e.g. Kwame" />
          </div>
          <div class="field">
            <label>Last name</label>
            <InputText v-model="form.last_name" class="w-full" required placeholder="e.g. Boateng" />
          </div>
        </div>

        <div class="field">
          <label>Email</label>
          <InputText
            v-model="form.email"
            type="email"
            class="w-full"
            required
            placeholder="subec@institution.edu"
          />
        </div>

        <div class="form-grid">
          <div class="field">
            <label>Phone</label>
            <InputText
              v-model="form.phone_number"
              class="w-full"
              placeholder="e.g. 0241234567"
            />
          </div>
          <div class="field">
            <label>{{ editingUnit ? 'New password (optional)' : 'Temporary password' }}</label>
            <InputText
              v-model="form.password"
              type="password"
              class="w-full"
              :required="!editingUnit"
              placeholder="At least 8 characters"
            />
          </div>
        </div>

        <label v-if="editingUnit" class="active-toggle">
          <input v-model="form.is_active" type="checkbox" />
          Sub EC unit is active
        </label>

        <div class="assign-block">
          <strong>Assign to</strong>
          <p>
            Choose from faculties and departments managed under
            <router-link to="/categories">Categories</router-link>.
          </p>

          <div v-if="!faculties.length && !departments.length" class="empty-hint">
            <p>No faculties or departments yet.</p>
            <router-link to="/categories" class="btn btn-ghost">Go to Categories</router-link>
          </div>

          <template v-else>
            <div class="assign-row">
              <div class="field grow">
                <label>Faculty</label>
                <select v-model="pickFaculty" class="filter-select w-full">
                  <option value="">Select faculty…</option>
                  <option
                    v-for="f in availableFaculties"
                    :key="f.uuid"
                    :value="f.uuid"
                  >
                    {{ f.name }}
                  </option>
                </select>
              </div>
              <button
                type="button"
                class="btn btn-ghost assign-btn"
                :disabled="!pickFaculty"
                @click="addFacultyScope"
              >
                Add
              </button>
            </div>

            <div class="assign-row">
              <div class="field grow">
                <label>Department</label>
                <select v-model="pickDepartment" class="filter-select w-full">
                  <option value="">Select department…</option>
                  <option
                    v-for="d in availableDepartments"
                    :key="d.uuid"
                    :value="d.uuid"
                  >
                    {{ d.name }}{{ d.faculty_name ? ` (${d.faculty_name})` : '' }}
                  </option>
                </select>
              </div>
              <button
                type="button"
                class="btn btn-ghost assign-btn"
                :disabled="!pickDepartment"
                @click="addDepartmentScope"
              >
                Add
              </button>
            </div>

            <div v-if="selectedScopes.length" class="chip-row">
              <button
                v-for="item in selectedScopes"
                :key="item.key"
                type="button"
                class="scope-chip is-removable"
                @click="removeScope(item)"
              >
                {{ item.label }}
                <i class="fas fa-times"></i>
              </button>
            </div>
            <p v-else class="hint-muted">No faculty or department selected yet.</p>
          </template>
        </div>

        <p class="approval-copy">
          <i class="fas fa-lock"></i>
          {{ editingUnit
            ? 'Nothing changes yet. This edit goes to the other Main EC for approval.'
            : 'Nothing is created now. This proposal goes to the other Main EC for approval.' }}
        </p>
        <p v-if="formError" class="form-error">{{ formError }}</p>
        <div class="form-actions">
          <button type="button" class="btn btn-ghost" @click="closeForm">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Submitting…' : 'Submit for approval' }}
          </button>
        </div>
      </form>
    </DataPanel>

    <div v-if="loading" class="loading-state page-section">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Loading EC structure…</p>
    </div>

    <div v-else-if="!units.length" class="empty-card page-section">
      <i class="fas fa-sitemap"></i>
      <strong>No Sub EC units</strong>
      <p>
        Manage faculties and departments in
        <router-link to="/categories">Categories</router-link>, then propose a Sub EC.
      </p>
    </div>

    <div v-else class="unit-grid page-section">
      <article
        v-for="unit in units"
        :key="unit.uuid"
        class="unit-card"
        :class="{ 'has-pending': !!unit.pending_approval }"
      >
        <header>
          <div>
            <span class="unit-type">Sub EC</span>
            <h3>{{ unit.name }}</h3>
          </div>
          <div class="unit-badges">
            <span
              v-if="unit.pending_approval"
              class="admin-badge warning"
              title="A change is waiting for the other Main EC to approve"
            >
              Pending approval
              <template v-if="unit.pending_approval.approvals_received != null">
                · {{ unit.pending_approval.approvals_received }}/{{ unit.pending_approval.approvals_required }}
              </template>
            </span>
            <span class="admin-badge" :class="unit.is_active ? 'success' : 'neutral'">
              {{ unit.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
        </header>
        <p v-if="unit.pending_approval" class="pending-note">
          <i class="fas fa-clock"></i>
          Changes submitted — awaiting co-approval from the other Main EC.
          <router-link to="/approvals">Review on Dual Approvals</router-link>
        </p>
        <div class="unit-members">
          <span v-for="member in unit.members" :key="member.uuid">
            <i class="fas fa-user"></i>
            {{ member.name || member.email }}
          </span>
        </div>
        <div class="scope-group">
          <span v-for="faculty in unit.faculties" :key="faculty.uuid" class="scope-chip">
            Faculty · {{ faculty.name }}
          </span>
          <span v-for="department in unit.departments" :key="department.uuid" class="scope-chip">
            Department · {{ department.name }}
          </span>
          <span v-if="!unit.faculties.length && !unit.departments.length" class="scope-empty">
            No faculty/department assigned
          </span>
        </div>
        <footer class="unit-card__actions">
          <button
            type="button"
            class="btn btn-ghost"
            :disabled="!structure?.governance?.ready || showForm || !!unit.pending_approval"
            :title="unit.pending_approval ? 'Wait for the pending change to be approved or rejected' : 'Edit Sub EC'"
            @click="openEditForm(unit)"
          >
            <i class="fas fa-pen"></i>
            {{ unit.pending_approval ? 'Edit locked' : 'Edit' }}
          </button>
        </footer>
      </article>
    </div>
  </div>

  <GovernanceSubmittedModal
    v-model:visible="showGovernanceModal"
    :message="governanceMessage"
  />
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import InputText from 'primevue/inputtext'
import PageHeader from '@/components/admin/PageHeader.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import GovernanceSubmittedModal from '@/components/admin/GovernanceSubmittedModal.vue'
import { governanceApi } from '@/api/governance'
import { academicApi } from '@/api/academic'
import { parseApiError } from '@/utils/apiError'
import { usePageHeading } from '@/composables/usePageHeading'

const { setPageHeading } = usePageHeading()
setPageHeading({
  title: 'Sub ECs',
  subtitle: 'Faculty and department Sub Electoral Commissions — dual-approved by Main EC',
})

const structure = ref(null)
const faculties = ref([])
const departments = ref([])
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const formError = ref('')
const pickFaculty = ref('')
const pickDepartment = ref('')
const showGovernanceModal = ref(false)
const governanceMessage = ref('')

const emptyForm = () => ({
  unit_name: '',
  first_name: '',
  last_name: '',
  email: '',
  phone_number: '',
  password: '',
  is_active: true,
  faculty_uuids: [],
  department_uuids: [],
})
const form = ref(emptyForm())
const editingUnit = ref(null)
const units = computed(() => structure.value?.sub_ec_units || [])

const availableFaculties = computed(() =>
  faculties.value.filter((f) => !form.value.faculty_uuids.includes(f.uuid)),
)
const availableDepartments = computed(() =>
  departments.value.filter((d) => !form.value.department_uuids.includes(d.uuid)),
)

const selectedScopes = computed(() => {
  const items = []
  for (const uuid of form.value.faculty_uuids) {
    const f = faculties.value.find((row) => row.uuid === uuid)
    if (f) items.push({ key: `f-${uuid}`, type: 'faculty', uuid, label: `Faculty · ${f.name}` })
  }
  for (const uuid of form.value.department_uuids) {
    const d = departments.value.find((row) => row.uuid === uuid)
    if (d) items.push({ key: `d-${uuid}`, type: 'department', uuid, label: `Department · ${d.name}` })
  }
  return items
})

const load = async () => {
  loading.value = true
  try {
    const [structureRes, facultiesRes, departmentsRes] = await Promise.all([
      governanceApi.getECStructure(),
      academicApi.faculties(),
      academicApi.departments(),
    ])
    structure.value = structureRes.data
    faculties.value = Array.isArray(facultiesRes.data) ? facultiesRes.data : []
    departments.value = Array.isArray(departmentsRes.data)
      ? departmentsRes.data.map((d) => ({
          ...d,
          faculty_name: d.faculty_name || d.faculty?.name,
        }))
      : []
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const openCreateForm = () => {
  editingUnit.value = null
  form.value = emptyForm()
  formError.value = ''
  pickFaculty.value = ''
  pickDepartment.value = ''
  showForm.value = true
}

const openEditForm = (unit) => {
  const member = unit.members?.[0] || {}
  editingUnit.value = unit
  form.value = {
    unit_name: unit.name || '',
    first_name: member.first_name || '',
    last_name: member.last_name || '',
    email: member.email || '',
    phone_number: member.phone_number || '',
    password: '',
    is_active: !!unit.is_active,
    faculty_uuids: (unit.faculties || []).map((f) => f.uuid),
    department_uuids: (unit.departments || []).map((d) => d.uuid),
  }
  formError.value = ''
  pickFaculty.value = ''
  pickDepartment.value = ''
  showForm.value = true
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const closeForm = () => {
  showForm.value = false
  editingUnit.value = null
  form.value = emptyForm()
  formError.value = ''
}

const addFacultyScope = () => {
  if (!pickFaculty.value) return
  if (!form.value.faculty_uuids.includes(pickFaculty.value)) {
    form.value.faculty_uuids.push(pickFaculty.value)
  }
  pickFaculty.value = ''
}

const addDepartmentScope = () => {
  if (!pickDepartment.value) return
  if (!form.value.department_uuids.includes(pickDepartment.value)) {
    form.value.department_uuids.push(pickDepartment.value)
  }
  pickDepartment.value = ''
}

const removeScope = (item) => {
  if (item.type === 'faculty') {
    form.value.faculty_uuids = form.value.faculty_uuids.filter((id) => id !== item.uuid)
  } else {
    form.value.department_uuids = form.value.department_uuids.filter((id) => id !== item.uuid)
  }
}

const submitProposal = async () => {
  formError.value = ''
  if (!form.value.faculty_uuids.length && !form.value.department_uuids.length) {
    formError.value = 'Select at least one faculty or department.'
    return
  }
  if (!editingUnit.value && (!form.value.password || form.value.password.length < 8)) {
    formError.value = 'Password must be at least 8 characters.'
    return
  }
  if (editingUnit.value && form.value.password && form.value.password.length < 8) {
    formError.value = 'New password must be at least 8 characters.'
    return
  }

  saving.value = true
  try {
    const payload = {
      unit_name: form.value.unit_name,
      first_name: form.value.first_name,
      last_name: form.value.last_name,
      email: form.value.email,
      phone_number: form.value.phone_number,
      faculty_uuids: form.value.faculty_uuids,
      department_uuids: form.value.department_uuids,
    }
    if (form.value.password) payload.password = form.value.password

    let data
    if (editingUnit.value) {
      payload.is_active = form.value.is_active
      ;({ data } = await governanceApi.proposeSubECUpdate(editingUnit.value.uuid, payload))
    } else {
      ;({ data } = await governanceApi.proposeSubEC(payload))
    }
    closeForm()
    governanceMessage.value = data.message || 'Submitted for dual Main EC approval. Your approval is recorded; the other institutional EC member must also approve before enrollment.'
    showGovernanceModal.value = true
  } catch (error) {
    formError.value = parseApiError(error) || 'Could not submit for approval.'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.governance-note {
  display: flex;
  gap: 0.8rem;
  padding: 1rem 1.1rem;
  border: 1px solid #bbf7d0;
  border-radius: 1rem;
  background: #f0fdf4;
  color: #166534;
}
.governance-note.is-blocked { border-color: #fed7aa; background: #fff7ed; color: #9a3412; }
.governance-note p { margin: 0.25rem 0; font-size: 0.84rem; color: var(--vb-muted, #8a8a8a); }
.governance-note a { color: inherit; font-weight: 700; text-decoration: underline; }

.propose-form {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  width: 100%;
  max-width: none;
}
.field label { display: block; margin-bottom: 0.3rem; font-size: 0.8rem; font-weight: 650; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem; }
.field.grow { flex: 1; min-width: 0; }

.assign-block {
  padding: 0.9rem 1rem;
  border-radius: 0.85rem;
  background: var(--vb-panel, #f7f6f2);
  width: 100%;
}
.assign-block > p { margin: 0.25rem 0 0.75rem; color: var(--vb-muted, #8a8a8a); font-size: 0.75rem; }
.assign-block a { font-weight: 650; text-decoration: underline; }
.assign-row { display: flex; gap: 0.5rem; align-items: flex-end; margin-bottom: 0.55rem; width: 100%; }
.assign-btn { flex-shrink: 0; margin-bottom: 0.05rem; }
.filter-select {
  width: 100%;
  padding: 0.5rem 0.65rem;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 0.5rem;
  font-size: 0.85rem;
  background: #fff;
}
.empty-hint {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-start;
}
.empty-hint p { margin: 0; font-size: 0.8rem; color: var(--vb-muted, #8a8a8a); }
.hint-muted { margin: 0; color: var(--vb-muted, #8a8a8a); font-size: 0.75rem; }

.chip-row { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.35rem; }
.scope-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.3rem 0.55rem;
  border-radius: 999px;
  background: #fff;
  border: 1px solid var(--vb-line, #ebeae4);
  font-size: 0.72rem;
}
.scope-chip.is-removable { cursor: pointer; }
.scope-chip.is-removable:hover { border-color: #be123c; color: #be123c; }

.approval-copy {
  margin: 0;
  padding: 0.65rem 0.75rem;
  border-radius: 0.7rem;
  background: #eff6ff;
  color: #1e40af;
  font-size: 0.76rem;
}
.form-actions { display: flex; justify-content: flex-end; gap: 0.5rem; }
.form-error { margin: 0; color: #be123c; font-size: 0.8rem; }

.unit-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr)); gap: 0.85rem; }
.unit-card { padding: 1rem; border: 1px solid var(--vb-line, #ebeae4); border-radius: 1rem; background: #fff; }
.unit-card.has-pending {
  border-color: #f5e2b8;
  background: #fffdf8;
}
.unit-card header { display: flex; justify-content: space-between; gap: 0.6rem; }
.unit-card h3 { margin: 0.2rem 0 0; font-size: 1rem; }
.unit-type { color: var(--vb-accent, #3d4f44); font-size: 0.68rem; font-weight: 800; text-transform: uppercase; }
.unit-badges { display: flex; flex-wrap: wrap; gap: 0.35rem; justify-content: flex-end; align-items: flex-start; }
.pending-note {
  margin: 0.65rem 0 0;
  padding: 0.55rem 0.7rem;
  border-radius: 0.65rem;
  background: #fff8ec;
  border: 1px solid #f5e2b8;
  color: #92610a;
  font-size: 0.76rem;
  line-height: 1.4;
}
.pending-note a { font-weight: 700; text-decoration: underline; color: inherit; }
.unit-members { margin-top: 0.7rem; font-size: 0.8rem; color: var(--vb-muted, #8a8a8a); }
.scope-group { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.75rem; }
.scope-empty { color: var(--vb-muted, #8a8a8a); font-size: 0.75rem; }
.unit-card__actions {
  margin-top: 0.9rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--vb-line, #ebeae4);
  display: flex;
  justify-content: flex-end;
}
.active-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.84rem;
  font-weight: 650;
}
.empty-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  padding: 2rem;
  text-align: center;
  border: 1px dashed var(--vb-line, #ebeae4);
  border-radius: 1rem;
}
.empty-card p { margin: 0; color: var(--vb-muted, #8a8a8a); }
.empty-card a { font-weight: 650; text-decoration: underline; }

@media (max-width: 720px) {
  .form-grid { grid-template-columns: 1fr; }
  .assign-row { flex-direction: column; align-items: stretch; }
  .assign-btn { align-self: flex-end; }
}
</style>
