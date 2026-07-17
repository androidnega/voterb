<template>
  <div class="admin-page">
    <PageHeader :loading="loading" :show-refresh="true" @refresh="fetchInstitutions">
      <template #actions>
        <button type="button" class="btn btn-primary" @click="showCreate = true">
          <i class="fas fa-plus"></i>
          New institution
        </button>
      </template>
    </PageHeader>

    <p class="page-lead page-section">
      Super Admin creates institutions, then attaches Main Electoral Commission accounts under each one.
    </p>

    <div v-if="loading" class="loading-state page-section">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Loading institutions…</p>
    </div>

    <div v-else-if="!institutions.length" class="page-section">
      <EmptyState
        icon="fas fa-university"
        title="No institutions yet"
        message="Create TTU (or another institution) to start the Main EC hierarchy."
      />
      <button type="button" class="btn btn-primary" @click="showCreate = true">
        Create institution
      </button>
    </div>

    <div v-else class="inst-grid page-section">
      <button
        v-for="inst in institutions"
        :key="inst.uuid"
        type="button"
        class="inst-card"
        @click="router.push(`/institutions/${inst.uuid}`)"
      >
        <span class="inst-card__code">{{ inst.code || inst.short_name }}</span>
        <strong class="inst-card__name">{{ inst.name }}</strong>
        <span class="inst-card__meta">
          {{ inst.main_ec_count || 0 }} / {{ inst.governance?.required_main_ec_count || 2 }} Main EC
          ·
          {{ inst.sub_ec_count || 0 }} Sub EC
        </span>
        <span
          class="inst-card__status"
          :class="inst.governance?.ready ? 'is-on' : (inst.is_active ? 'is-warn' : 'is-off')"
        >
          {{
            !inst.is_active
              ? 'Inactive'
              : inst.governance?.ready
                ? 'Operational'
                : 'Needs 2 Main ECs'
          }}
        </span>
      </button>
    </div>

    <Dialog v-model:visible="showCreate" header="Create institution" :modal="true" class="w-full max-w-md">
      <form class="dialog-form" @submit.prevent="createInstitution">
        <div class="field">
          <label>Name</label>
          <InputText v-model="form.name" class="w-full" required placeholder="Takoradi Technical University" />
        </div>
        <div class="field">
          <label>Short name</label>
          <InputText v-model="form.short_name" class="w-full" required placeholder="TTU" />
        </div>
        <div class="field">
          <label>Code</label>
          <InputText v-model="form.code" class="w-full" placeholder="TTU" />
        </div>
        <p v-if="formError" class="form-error">{{ formError }}</p>
        <div class="dialog-actions">
          <button type="button" class="btn btn-ghost" @click="showCreate = false">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Creating…' : 'Create' }}
          </button>
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import PageHeader from '@/components/admin/PageHeader.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import { institutionApi } from '@/api/institutions'
import { usePageHeading } from '@/composables/usePageHeading'
import { parseApiError } from '@/utils/apiError'

const router = useRouter()
const { setPageHeading } = usePageHeading()
setPageHeading({
  title: 'Institutions',
  subtitle: 'Super Admin → Institution → Main EC → Categories → Sub EC → Registers',
})

const institutions = ref([])
const loading = ref(false)
const showCreate = ref(false)
const saving = ref(false)
const formError = ref('')
const form = ref({ name: '', short_name: '', code: '' })

const fetchInstitutions = async () => {
  loading.value = true
  try {
    const { data } = await institutionApi.list()
    institutions.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error(error)
    institutions.value = []
  } finally {
    loading.value = false
  }
}

const createInstitution = async () => {
  formError.value = ''
  saving.value = true
  try {
    const { data } = await institutionApi.create({
      name: form.value.name.trim(),
      short_name: form.value.short_name.trim(),
      code: (form.value.code || form.value.short_name).trim().toUpperCase(),
      is_active: true,
    })
    showCreate.value = false
    form.value = { name: '', short_name: '', code: '' }
    await fetchInstitutions()
    if (data?.uuid) router.push(`/institutions/${data.uuid}`)
  } catch (error) {
    formError.value = parseApiError(error) || 'Could not create institution.'
  } finally {
    saving.value = false
  }
}

onMounted(fetchInstitutions)
</script>

<style scoped>
.page-lead {
  margin: 0 0 1rem;
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.9rem;
  max-width: 40rem;
}

.inst-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr));
  gap: 0.85rem;
}

.inst-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.35rem;
  text-align: left;
  padding: 1.1rem 1.15rem;
  border-radius: 1rem;
  border: 1px solid var(--vb-line, #ebeae4);
  background: #fff;
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

.inst-card:hover {
  border-color: var(--vb-accent-border, #c5d4bc);
  box-shadow: 0 8px 22px rgba(61, 79, 68, 0.1);
  transform: translateY(-1px);
}

.inst-card__code {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--vb-accent, #3d4f44);
}

.inst-card__name {
  font-size: 1rem;
  letter-spacing: -0.02em;
}

.inst-card__meta {
  font-size: 0.78rem;
  color: var(--vb-muted, #8a8a8a);
}

.inst-card__status {
  margin-top: 0.35rem;
  font-size: 0.7rem;
  font-weight: 700;
}

.inst-card__status.is-on { color: #15803d; }
.inst-card__status.is-off { color: #b45309; }
.inst-card__status.is-warn { color: #c2410c; }

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.dialog-form .field label {
  display: block;
  margin-bottom: 0.35rem;
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
</style>
