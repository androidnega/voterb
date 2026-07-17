<template>
  <div v-if="institution" class="admin-page">
    <button type="button" class="btn-back page-section" @click="router.push('/institutions')">
      <i class="fas fa-arrow-left"></i>
      Back to institutions
    </button>

    <PageHeader :show-refresh="true" :loading="loading" @refresh="fetchDetail">
      <template #actions>
        <button type="button" class="btn btn-primary" @click="showMainEC = true">
          <i class="fas fa-user-plus"></i>
          Add Main EC
        </button>
      </template>
    </PageHeader>

    <section class="arch-strip page-section">
      <div class="arch-node">
        <span class="arch-node__label">Institution</span>
        <strong>{{ institution.short_name || institution.name }}</strong>
      </div>
      <i class="fas fa-chevron-right arch-arrow" aria-hidden="true"></i>
      <div class="arch-node is-accent">
        <span class="arch-node__label">Main EC</span>
        <strong>{{ mainEcCount }} / {{ requiredMainEc }}</strong>
      </div>
      <i class="fas fa-chevron-right arch-arrow" aria-hidden="true"></i>
      <div class="arch-node">
        <span class="arch-node__label">Categories</span>
        <strong>Faculties · Depts</strong>
      </div>
      <i class="fas fa-chevron-right arch-arrow" aria-hidden="true"></i>
      <div class="arch-node is-accent">
        <span class="arch-node__label">Register</span>
        <strong>Voters</strong>
      </div>
      <i class="fas fa-chevron-right arch-arrow" aria-hidden="true"></i>
      <div class="arch-node">
        <span class="arch-node__label">Sub EC</span>
        <strong>{{ (institution.sub_ec_units || []).length }} units</strong>
      </div>
    </section>

    <section
      class="gov-readiness page-section"
      :class="institutionReady ? 'is-ready' : 'is-blocked'"
    >
      <div>
        <strong>{{ institutionReady ? 'Ready for operations' : 'Not ready for operations' }}</strong>
        <p>
          {{
            institution.governance?.message
              || `An institution needs at least ${requiredMainEc} Main EC members. All Main EC decisions require approval before enrollment.`
          }}
        </p>
      </div>
      <button
        v-if="!institutionReady"
        type="button"
        class="btn btn-primary"
        @click="showMainEC = true"
      >
        Add Main EC ({{ mainEcCount }}/{{ requiredMainEc }})
      </button>
    </section>

    <DataPanel
      title="Main Electoral Commission"
      subtitle="Requires at least two institutional EC accounts. Decisions need both approvals before enrollment."
      class="page-section"
    >
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="member in institution.main_ec_members || []" :key="member.uuid">
              <td>
                <span class="cell-title">
                  {{ [member.first_name, member.last_name].filter(Boolean).join(' ') || '—' }}
                </span>
              </td>
              <td class="mono">{{ member.email }}</td>
              <td>
                <span class="admin-badge" :class="member.is_active ? 'success' : 'neutral'">
                  {{ member.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
            </tr>
            <tr v-if="!(institution.main_ec_members || []).length">
              <td colspan="3">
                <EmptyState
                  icon="fas fa-user-tie"
                  title="No Main EC yet"
                  message="Create two Main EC accounts for this institution (as in your architecture)."
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </DataPanel>

    <DataPanel
      title="Sub EC units"
      subtitle="Faculty / department Sub ECs — proposed by Main EC, approved, then assigned to categories"
      class="page-section"
    >
      <div v-if="!(institution.sub_ec_units || []).length" class="empty-hint">
        No Sub ECs yet. Main EC proposes them under Sub ECs and assigns faculties/departments from Categories.
      </div>
      <ul v-else class="sub-list">
        <li v-for="unit in institution.sub_ec_units" :key="unit.uuid">
          <strong>{{ unit.name }}</strong>
          <span>{{ unit.member_count }} members</span>
        </li>
      </ul>
    </DataPanel>

    <Dialog v-model:visible="showMainEC" header="Add Main EC" :modal="true" class="w-full max-w-md">
      <form class="dialog-form" @submit.prevent="createMainEC">
        <div class="field">
          <label>First name</label>
          <InputText v-model="ecForm.first_name" class="w-full" placeholder="e.g. Ama" />
        </div>
        <div class="field">
          <label>Last name</label>
          <InputText v-model="ecForm.last_name" class="w-full" placeholder="e.g. Mensah" />
        </div>
        <div class="field">
          <label>Email</label>
          <InputText v-model="ecForm.email" type="email" class="w-full" required placeholder="name@institution.edu" />
        </div>
        <div class="field">
          <label>Phone</label>
          <InputText v-model="ecForm.phone_number" class="w-full" placeholder="e.g. 0201234567" />
        </div>
        <div class="field">
          <label>Password</label>
          <InputText v-model="ecForm.password" type="password" class="w-full" required placeholder="At least 8 characters" />
        </div>
        <p v-if="formError" class="form-error">{{ formError }}</p>
        <div class="dialog-actions">
          <button type="button" class="btn btn-ghost" @click="showMainEC = false">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Creating…' : 'Create Main EC' }}
          </button>
        </div>
      </form>
    </Dialog>
  </div>

  <div v-else class="admin-page">
    <div class="loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Loading institution…</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import PageHeader from '@/components/admin/PageHeader.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import { institutionApi } from '@/api/institutions'
import { usePageHeading } from '@/composables/usePageHeading'
import { parseApiError } from '@/utils/apiError'

const route = useRoute()
const router = useRouter()
const { setPageHeading } = usePageHeading()

const institution = ref(null)
const loading = ref(false)
const showMainEC = ref(false)
const saving = ref(false)
const formError = ref('')
const ecForm = ref({
  first_name: '',
  last_name: '',
  email: '',
  phone_number: '',
  password: '',
})

const mainEcCount = computed(
  () => (institution.value?.main_ec_members || []).length
    || institution.value?.governance?.main_ec_count
    || 0,
)
const requiredMainEc = computed(
  () => institution.value?.required_main_ec_count
    || institution.value?.governance?.required_main_ec_count
    || 2,
)
const institutionReady = computed(
  () => institution.value?.governance?.ready === true || mainEcCount.value >= requiredMainEc.value,
)

watch(
  institution,
  (value) => {
    if (!value) return
    setPageHeading({
      title: value.name,
      subtitle: `${value.code || value.short_name} · Institution hierarchy`,
    })
  },
  { immediate: true },
)

const fetchDetail = async () => {
  loading.value = true
  try {
    const { data } = await institutionApi.get(route.params.uuid)
    institution.value = data
  } catch (error) {
    console.error(error)
    router.push('/institutions')
  } finally {
    loading.value = false
  }
}

const createMainEC = async () => {
  formError.value = ''
  saving.value = true
  try {
    await institutionApi.createMainEC(route.params.uuid, { ...ecForm.value })
    showMainEC.value = false
    ecForm.value = {
      first_name: '',
      last_name: '',
      email: '',
      phone_number: '',
      password: '',
    }
    await fetchDetail()
  } catch (error) {
    formError.value = parseApiError(error) || 'Could not create Main EC.'
  } finally {
    saving.value = false
  }
}

onMounted(fetchDetail)
</script>

<style scoped>
.btn-back {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.5rem;
  border: none;
  background: transparent;
  color: var(--vb-muted, #8a8a8a);
  font-weight: 650;
  cursor: pointer;
}

.arch-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem;
  padding: 1rem 1.1rem;
  border-radius: 1rem;
  background: var(--vb-panel, #f7f6f2);
  border: 1px solid var(--vb-line, #ebeae4);
}

.arch-node {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.65rem 0.85rem;
  border-radius: 0.75rem;
  background: #fff;
  border: 1px solid var(--vb-line, #ebeae4);
  min-width: 7.5rem;
}

.arch-node.is-accent {
  border-color: var(--vb-accent-border, #c5d4bc);
  box-shadow: inset 0 0 0 1px var(--vb-accent-border, #c5d4bc);
}

.arch-node.is-muted {
  opacity: 0.7;
}

.arch-node__label {
  font-size: 0.65rem;
  font-weight: 750;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--vb-muted, #8a8a8a);
}

.arch-arrow {
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.75rem;
}

.gov-readiness {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.85rem;
  padding: 1rem 1.15rem;
  border-radius: 1rem;
  border: 1px solid var(--vb-line, #ebeae4);
}

.gov-readiness.is-ready {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.gov-readiness.is-blocked {
  background: #fff7ed;
  border-color: #fed7aa;
}

.gov-readiness p {
  margin: 0.35rem 0 0;
  font-size: 0.85rem;
  color: var(--vb-muted, #8a8a8a);
  max-width: 36rem;
}

.empty-hint {
  padding: 0.75rem 0;
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.88rem;
}

.sub-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.sub-list li {
  display: flex;
  justify-content: space-between;
  padding: 0.7rem 0.85rem;
  border-radius: 0.75rem;
  background: var(--vb-panel, #f7f6f2);
}

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.dialog-form .field label {
  display: block;
  margin-bottom: 0.3rem;
  font-size: 0.8rem;
  font-weight: 650;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.form-error {
  margin: 0;
  color: #be123c;
  font-size: 0.8rem;
}

.w-full { width: 100%; }
</style>
