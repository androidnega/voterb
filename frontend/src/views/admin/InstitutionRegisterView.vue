<template>
  <div class="admin-page register-page">
    <PageHeader :loading="loading" :show-refresh="true" @refresh="load">
      <template #actions>
        <button
          v-if="!selected"
          type="button"
          class="btn btn-ghost"
          @click="downloadVoterTemplate"
        >
          <i class="fas fa-download"></i>
          Download template
        </button>
        <button
          v-if="!selected"
          type="button"
          class="btn btn-primary"
          :disabled="creating"
          @click="openCreate"
        >
          <i class="fas fa-plus"></i>
          Create register
        </button>
        <button
          v-else
          type="button"
          class="btn btn-ghost"
          @click="clearSelection"
        >
          <i class="fas fa-arrow-left"></i>
          All registers
        </button>
      </template>
    </PageHeader>

    <div v-if="loading && !registers.length" class="loading-state page-section">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Loading registers…</p>
    </div>

    <!-- Card grid -->
    <div v-else-if="!selected" class="page-section">
      <div v-if="banner" class="register-banner">
        <span class="register-banner__icon" aria-hidden="true">
          <i class="fas fa-check"></i>
        </span>
        <span class="register-banner__body">
          <strong>{{ bannerTitle }}</strong>
          <span>{{ banner }}</span>
        </span>
        <button type="button" class="register-banner__close" @click="banner = ''">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div v-if="registers.length" class="register-grid">
        <button
          v-for="reg in registers"
          :key="reg.uuid"
          type="button"
          class="register-card"
          @click="selectRegister(reg)"
        >
          <div class="register-card__top">
            <span class="scope-pill" :class="scopeClass(reg)">
              {{ categoryLabel(reg) }}
            </span>
            <span class="approval-badge" :class="approvalMeta(reg).cls">
              {{ approvalMeta(reg).label }}
            </span>
          </div>
          <strong class="register-card__name">{{ reg.name }}</strong>
          <span class="register-card__meta">
            {{ categoryName(reg) }}
          </span>
          <span class="register-card__count">
            <i class="fas fa-users"></i>
            {{ reg.entry_count || 0 }} voters
          </span>
        </button>
      </div>

      <EmptyState
        v-else
        icon="fas fa-book"
        title="No registers yet"
        message="Create categories under Categories, then use Create register to assign them."
      />
    </div>

    <!-- Voter list for selected card -->
    <section v-else class="register-detail page-section">
      <header class="detail-hero">
        <div>
          <span class="detail-kicker">{{ primaryCategory?.scope_label || 'Register' }}</span>
          <h2>{{ selected.name }}</h2>
          <p>
            {{ categoryName(selected) }}
            · {{ selected.entry_count || 0 }} voters
            <span class="approval-badge" :class="approvalMeta(selected).cls">
              {{ approvalMeta(selected).label }}
            </span>
          </p>
          <p class="detail-scope-note">
            Voters on this register are assigned to the selected faculty/department containers.
          </p>
          <p v-if="selected.approval_status === 'pending'" class="detail-approval-note">
            Awaiting approval from the other Main EC member before this register can be
            used in elections.
          </p>
        </div>
        <div class="detail-hero__actions">
          <button
            v-if="selected.approval_status === 'approved' && !selected.pending_replace"
            type="button"
            class="btn btn-primary"
            :disabled="replacing"
            @click="openReplace"
          >
            <i class="fas fa-upload"></i>
            Re-upload voters
          </button>
          <button type="button" class="btn btn-ghost" @click="confirmDelete">
            <i class="fas fa-trash"></i>
            Delete
          </button>
        </div>
      </header>

      <p v-if="selected.pending_replace" class="detail-approval-note">
        A voter re-upload is awaiting the other Main EC member’s approval.
        Once approved, linked Main EC and Sub EC elections update automatically.
      </p>
      <p v-else-if="selected.linked_election_count" class="detail-scope-note">
        Linked to {{ selected.linked_election_count }} election(s). Approved re-uploads
        update eligibility for all of them.
      </p>
      <DataPanel title="Voters" :no-padding="true">
        <div class="voters-toolbar">
          <div class="filter-input-wrap">
            <i class="fas fa-search"></i>
            <input
              v-model="entrySearch"
              type="search"
              placeholder="Search index or name…"
              @keyup.enter="loadEntries"
            />
          </div>
          <button type="button" class="btn btn-ghost" @click="loadEntries">Search</button>
        </div>

        <div class="admin-table-wrap voters-table-wrap">
          <table class="admin-table">
            <thead>
              <tr>
                <th>Index number</th>
                <th>Full name</th>
                <th>Phone</th>
                <th class="col-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in entries"
                :key="row.uuid"
                :class="{ 'is-pending-edit': !!pendingEditFor(row) }"
              >
                <td class="mono">
                  {{ row.voter_id }}
                  <span v-if="pendingEditFor(row)" class="pending-pill">Pending approval</span>
                </td>
                <td>
                  <span class="cell-title">{{ row.full_name }}</span>
                  <p v-if="pendingEditFor(row)" class="pending-hint">
                    Proposed:
                    {{ pendingEditFor(row).proposed.voter_id }}
                    · {{ pendingEditFor(row).proposed.full_name }}
                    · {{ pendingEditFor(row).proposed.phone_number || '—' }}
                  </p>
                </td>
                <td class="mono">{{ row.phone_number || '—' }}</td>
                <td>
                  <button
                    v-if="selected.approval_status === 'approved' && !pendingEditFor(row)"
                    type="button"
                    class="btn btn-ghost btn-sm"
                    @click="openEditEntry(row)"
                  >
                    Edit
                  </button>
                  <span v-else-if="pendingEditFor(row)" class="pending-wait">Awaiting co-approval</span>
                </td>
              </tr>
              <tr v-if="!entriesLoading && !entries.length">
                <td colspan="4">
                  <EmptyState
                    icon="fas fa-users"
                    title="No voters yet"
                    message="This register has no imported voters."
                  />
                </td>
              </tr>
              <tr v-if="entriesLoading">
                <td colspan="4" class="loading-row">
                  <i class="fas fa-spinner fa-spin"></i> Loading…
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </DataPanel>
    </section>

    <Dialog
      v-model:visible="showCreate"
      header="Create register"
      :modal="true"
      :closable="!creating"
      :close-on-escape="!creating"
      class="w-full max-w-lg create-register-dialog"
    >
      <form class="create-form" @submit.prevent="submitCreate">
        <div class="field">
          <label>Register name</label>
          <InputText
            v-model="form.name"
            class="w-full"
            required
            :disabled="creating"
            placeholder="e.g. Institutional Register"
          />
        </div>

        <p class="form-callout">
          Choose categories from Categories. Institution categories create a Main EC register;
          faculty/department create a Sub EC register. Do not mix both types.
        </p>

        <div class="field">
          <label>Categories</label>
          <MultiSelect
            v-model="form.categoryKeys"
            :options="categoryOptions"
            optionLabel="label"
            optionValue="key"
            placeholder="Search and select categories…"
            display="chip"
            filter
            filterPlaceholder="Search categories…"
            class="w-full"
            :disabled="creating"
            :showClear="true"
          />
        </div>

        <div
          v-if="selectedImportTargets.length > 1"
          class="field"
        >
          <label>Import this CSV into</label>
          <Select
            v-model="form.importTargetKey"
            :options="selectedImportTargets"
            optionLabel="label"
            optionValue="key"
            placeholder="Choose container for this upload…"
            filter
            filterPlaceholder="Search…"
            class="w-full"
            :disabled="creating"
          />
          <p class="field-hint">
            Other selected categories are created as empty containers — open the
            register later to upload a CSV into each one.
          </p>
        </div>

        <div class="field">
          <div class="field-head">
            <label>Voter CSV</label>
            <button
              type="button"
              class="template-link"
              :disabled="creating"
              @click="downloadVoterTemplate"
            >
              <i class="fas fa-download" aria-hidden="true"></i>
              Download template
            </button>
          </div>
          <label class="file-drop" :class="{ 'has-file': !!form.file, 'is-disabled': creating }">
            <input
              type="file"
              accept=".csv,text/csv"
              hidden
              :disabled="creating"
              @change="onFilePick"
            />
            <i class="fas fa-file-csv"></i>
            <span v-if="form.file">{{ form.file.name }}</span>
            <span v-else>Choose CSV — index, full name, phone</span>
          </label>
          <p class="field-hint">
            Only <strong>index</strong>, <strong>full name</strong>, and <strong>phone</strong>
            are imported. Extra columns are ignored. Headers can vary
            (index number / index_number / index, full name / full_name / name,
            phone number / phone_number / phone).
          </p>
        </div>

        <div v-if="creating" class="upload-progress">
          <div class="upload-progress__meta">
            <span>{{ progressLabel }}</span>
            <strong>{{ progressPercent }}%</strong>
          </div>
          <div
            class="upload-progress__track"
            role="progressbar"
            :aria-valuenow="progressPercent"
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <div class="upload-progress__fill" :style="{ width: `${progressPercent}%` }"></div>
          </div>
          <p v-if="progressHint" class="upload-progress__hint">{{ progressHint }}</p>
        </div>

        <p v-if="!categoryOptions.length" class="inline-hint">
          No categories yet.
          <router-link to="/categories">Create them in Categories</router-link>
          first.
        </p>

        <p v-if="formError" class="form-error">{{ formError }}</p>

        <div class="dialog-actions">
          <button
            type="button"
            class="btn btn-ghost"
            :disabled="creating"
            @click="showCreate = false"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="creating || !canSubmit"
          >
            {{ creating ? `Uploading ${progressPercent}%` : 'Create & upload' }}
          </button>
        </div>
      </form>
    </Dialog>

    <Dialog
      v-model:visible="showReplace"
      header="Re-upload voters"
      :modal="true"
      :closable="!replacing"
      :close-on-escape="!replacing"
      class="w-full max-w-lg create-register-dialog"
    >
      <form class="create-form" @submit.prevent="submitReplace">
        <p class="field-hint" style="margin-top: 0">
          Upload a new CSV for one category container. The other Main EC member must approve
          before voters are replaced. Linked Main EC and Sub EC elections then update
          automatically.
        </p>

        <div class="field" v-if="(selected?.categories || []).length > 1">
          <label>Replace voters in</label>
          <Select
            v-model="replaceForm.categoryUuid"
            :options="selected?.categories || []"
            optionLabel="name"
            optionValue="uuid"
            placeholder="Choose category…"
            class="w-full"
            :disabled="replacing"
          />
        </div>

        <div class="field">
          <div class="field-head">
            <label>Voter CSV</label>
            <button
              type="button"
              class="template-link"
              :disabled="replacing"
              @click="downloadVoterTemplate"
            >
              <i class="fas fa-download" aria-hidden="true"></i>
              Download template
            </button>
          </div>
          <label class="file-drop" :class="{ 'has-file': !!replaceForm.file, 'is-disabled': replacing }">
            <input
              type="file"
              accept=".csv,text/csv"
              hidden
              :disabled="replacing"
              @change="onReplaceFilePick"
            />
            <i class="fas fa-file-csv"></i>
            <span v-if="replaceForm.file">{{ replaceForm.file.name }}</span>
            <span v-else>Choose CSV — index, full name, phone</span>
          </label>
        </div>

        <div v-if="replacing" class="upload-progress">
          <div class="upload-progress__meta">
            <span>{{ progressLabel }}</span>
            <strong>{{ progressPercent }}%</strong>
          </div>
          <div class="upload-progress__track" role="progressbar" :aria-valuenow="progressPercent" aria-valuemin="0" aria-valuemax="100">
            <div class="upload-progress__fill" :style="{ width: `${progressPercent}%` }"></div>
          </div>
          <p v-if="progressHint" class="upload-progress__hint">{{ progressHint }}</p>
        </div>

        <p v-if="formError" class="form-error">{{ formError }}</p>

        <div class="dialog-actions">
          <button type="button" class="btn btn-ghost" :disabled="replacing" @click="showReplace = false">
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="replacing || !canReplaceSubmit"
          >
            {{ replacing ? `Uploading ${progressPercent}%` : 'Submit for approval' }}
          </button>
        </div>
      </form>
    </Dialog>

    <Dialog
      v-model:visible="showEditEntry"
      header="Edit voter"
      :modal="true"
      :closable="!editingEntry"
      :close-on-escape="!editingEntry"
      class="w-full max-w-md"
    >
      <form class="create-form" @submit.prevent="submitEditEntry">
        <p class="form-callout">
          Changes go to dual Main EC approval. The other institutional EC member must confirm
          before the voter record updates.
        </p>
        <div class="field">
          <label>Index number</label>
          <InputText v-model="editForm.voter_id" class="w-full" required :disabled="editingEntry" />
        </div>
        <div class="field">
          <label>Full name</label>
          <InputText v-model="editForm.full_name" class="w-full" required :disabled="editingEntry" />
        </div>
        <div class="field">
          <label>Phone number</label>
          <InputText v-model="editForm.phone_number" class="w-full" :disabled="editingEntry" />
        </div>
        <p v-if="formError" class="form-error">{{ formError }}</p>
        <div class="dialog-actions">
          <button type="button" class="btn btn-ghost" :disabled="editingEntry" @click="showEditEntry = false">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary" :disabled="editingEntry">
            {{ editingEntry ? 'Submitting…' : 'Submit for approval' }}
          </button>
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import MultiSelect from 'primevue/multiselect'
import Select from 'primevue/select'
import PageHeader from '@/components/admin/PageHeader.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import { institutionRegisterApi } from '@/api/registers'
import { academicApi } from '@/api/academic'
import { parseApiError } from '@/utils/apiError'
import { splitCsvFile } from '@/utils/csvChunks'
import { usePageHeading } from '@/composables/usePageHeading'

const { setPageHeading } = usePageHeading()
setPageHeading({
  title: 'Register',
  subtitle: 'Choose categories under Categories, then assign them to a register',
})

const ROWS_PER_CHUNK = 100

const loading = ref(false)
const creating = ref(false)
const entriesLoading = ref(false)
const registers = ref([])
const selected = ref(null)
const entries = ref([])
const institutionCategories = ref([])
const faculties = ref([])
const departments = ref([])
const entrySearch = ref('')
const showCreate = ref(false)
const showReplace = ref(false)
const replacing = ref(false)
const showEditEntry = ref(false)
const editingEntry = ref(false)
const editEntryUuid = ref(null)
const editForm = ref({
  voter_id: '',
  full_name: '',
  phone_number: '',
})
const formError = ref('')
const banner = ref('')
const progressPercent = ref(0)
const progressLabel = ref('')
const progressHint = ref('')

const form = ref({
  name: '',
  categoryKeys: [],
  importTargetKey: '',
  file: null,
})

const bannerTitle = computed(() => {
  const text = banner.value.toLowerCase()
  if (text.includes('voter change')) return 'Voter change submitted'
  if (text.includes('re-upload')) return 'Re-upload submitted'
  if (text.includes('created')) return 'Register created'
  return 'Submitted for approval'
})

const replaceForm = ref({
  categoryUuid: '',
  file: null,
})

const categoryOptions = computed(() => {
  const options = []
  for (const row of institutionCategories.value) {
    options.push({
      key: `institution:${row.uuid}`,
      label: `Institution · ${row.name}`,
      type: 'institution',
      uuid: row.uuid,
    })
  }
  for (const row of faculties.value) {
    options.push({
      key: `faculty:${row.uuid}`,
      label: `Faculty · ${row.name}`,
      type: 'faculty',
      uuid: row.uuid,
    })
  }
  for (const row of departments.value) {
    options.push({
      key: `department:${row.uuid}`,
      label: `Department · ${row.name}`,
      type: 'department',
      uuid: row.uuid,
    })
  }
  return options
})

const splitCategoryKeys = (keys = []) => {
  const institution_category_uuids = []
  const faculty_uuids = []
  const department_uuids = []
  for (const key of keys) {
    if (key.startsWith('institution:')) institution_category_uuids.push(key.slice('institution:'.length))
    else if (key.startsWith('faculty:')) faculty_uuids.push(key.slice('faculty:'.length))
    else if (key.startsWith('department:')) department_uuids.push(key.slice('department:'.length))
  }
  return { institution_category_uuids, faculty_uuids, department_uuids }
}

const selectedImportTargets = computed(() => {
  const targets = []
  for (const key of form.value.categoryKeys || []) {
    const opt = categoryOptions.value.find((x) => x.key === key)
    if (opt) targets.push({ key: opt.key, label: opt.label, uuid: opt.uuid, type: opt.type })
  }
  return targets
})

const primaryCategory = computed(() => selected.value?.categories?.[0] || null)

const canSubmit = computed(() => (
  !!form.value.name.trim()
  && !!form.value.file
  && (form.value.categoryKeys?.length || 0) > 0
))

const canReplaceSubmit = computed(() => {
  const cats = selected.value?.categories || []
  const categoryUuid = replaceForm.value.categoryUuid || cats[0]?.uuid
  return !!replaceForm.value.file && !!categoryUuid
})

const categoryLabel = (reg) => {
  if (reg?.audience === 'main') return 'Main EC'
  const cats = reg.categories || []
  if (!cats.length) return 'Register'
  if (cats.length > 1) return `${cats.length} containers`
  return cats[0].scope_label || cats[0].category_type || 'Register'
}

const categoryName = (reg) => {
  const cats = reg.categories || []
  if (!cats.length) return 'No category'
  if (cats.length === 1) return cats[0].name
  return cats.map((c) => c.name).slice(0, 3).join(', ') + (cats.length > 3 ? '…' : '')
}

const scopeClass = (reg) => {
  if (reg?.audience === 'main') return 'is-main'
  const cats = reg.categories || []
  if (cats.length > 1) return 'is-multi'
  const type = cats[0]?.category_type || 'custom'
  return `is-${type}`
}

const approvalMeta = (reg) => {
  switch (reg?.approval_status) {
    case 'approved':
      return { label: 'Approved', cls: 'is-approved' }
    case 'rejected':
      return { label: 'Rejected', cls: 'is-rejected' }
    default:
      return { label: 'Pending approval', cls: 'is-pending' }
  }
}

const maybeAutofillName = () => {
  if (form.value.name.trim()) return
  const targets = selectedImportTargets.value
  if (targets.length === 1) {
    const name = targets[0].label.replace(/^(Institution|Faculty|Department) · /, '')
    form.value.name = `${name} Register`
  } else if (targets.length > 1) {
    form.value.name = 'Institutional Register'
  }
}

watch(
  () => form.value.categoryKeys,
  () => {
    maybeAutofillName()
    const targets = selectedImportTargets.value
    if (!targets.length) {
      form.value.importTargetKey = ''
      return
    }
    if (!targets.some((t) => t.key === form.value.importTargetKey)) {
      form.value.importTargetKey = targets[0].key
    }
  },
  { deep: true },
)

const downloadVoterTemplate = () => {
  const csv = [
    'index_number,full_name,phone_number',
    'SC/2021/PL/001,Ama Mensah,0244123456',
    'SC/2021/PL/002,Kwame Boateng,0555123456',
    'SC/2021/PL/003,Akosua Owusu,',
  ].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'voter-register-template.csv'
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

const onFilePick = (event) => {
  form.value.file = event.target.files?.[0] || null
}

const onReplaceFilePick = (event) => {
  replaceForm.value.file = event.target.files?.[0] || null
}

const openReplace = () => {
  const cats = selected.value?.categories || []
  replaceForm.value = {
    categoryUuid: cats[0]?.uuid || '',
    file: null,
  }
  formError.value = ''
  progressPercent.value = 0
  progressLabel.value = ''
  progressHint.value = ''
  showReplace.value = true
}

const submitReplace = async () => {
  formError.value = ''
  if (!selected.value || !canReplaceSubmit.value) {
    formError.value = 'Choose a CSV file to re-upload.'
    return
  }

  const liveCategoryUuid = replaceForm.value.categoryUuid || selected.value.categories?.[0]?.uuid
  if (!liveCategoryUuid) {
    formError.value = 'This register has no category container.'
    return
  }

  replacing.value = true
  setProgress(4, 'Submitting for approval…', 'Creating staging draft for dual Main EC review')

  try {
    const { chunks, totalRows } = await splitCsvFile(replaceForm.value.file, ROWS_PER_CHUNK)
    const { data: started } = await institutionRegisterApi.startReplace(selected.value.uuid, {
      categoryUuid: liveCategoryUuid,
    })

    const stagingUuid = started.staging_register_uuid
    const stagingCategoryUuid =
      started.target_staging_category_uuid
      || started.category_map?.[liveCategoryUuid]

    if (!stagingUuid || !stagingCategoryUuid) {
      throw new Error('Could not prepare staging register for re-upload.')
    }

    setProgress(12, 'Uploading to staging…', `${totalRows} voters awaiting co-approval`)

    let created = 0
    let rowErrors = 0
    const base = 12
    const span = 86

    for (let i = 0; i < chunks.length; i += 1) {
      const chunk = chunks[i]
      const chunkStart = base + (i / chunks.length) * span
      setProgress(
        chunkStart,
        `Queue ${i + 1}/${chunks.length} · ${Math.round((i / chunks.length) * 100)}%`,
        `${chunk.rowCount} rows in this batch`,
      )
      const { data } = await institutionRegisterApi.importCsv(stagingUuid, {
        categoryUuid: stagingCategoryUuid,
        file: chunk.blob,
        fileName: chunk.fileName,
        onUploadProgress: (pct) => {
          const within = (pct / 100) * (span / chunks.length)
          setProgress(
            chunkStart + within,
            `Queue ${i + 1}/${chunks.length} · ${Math.round((i / chunks.length) * 100 + pct / chunks.length)}%`,
            `${pct}% of this batch`,
          )
        },
      })
      created += data?.rows_created || 0
      rowErrors += Array.isArray(data?.errors) ? data.errors.length : 0
    }

    setProgress(100, 'Submitted', `${created} voter(s) staged${rowErrors ? `, ${rowErrors} row error(s)` : ''}`)
    showReplace.value = false
    banner.value =
      started?.decision?.message
      || started?.message
      || 'Re-upload submitted. The other Main EC member must approve before elections update.'
    await load()
    if (selected.value?.uuid) {
      const fresh = registers.value.find((r) => r.uuid === selected.value.uuid)
      if (fresh) {
        selected.value = fresh
        await loadEntries()
      }
    }
  } catch (error) {
    formError.value = extractError(error) || 'Could not submit re-upload.'
  } finally {
    replacing.value = false
  }
}

const openCreate = () => {
  form.value = {
    name: '',
    categoryKeys: [],
    importTargetKey: '',
    file: null,
  }
  formError.value = ''
  progressPercent.value = 0
  progressLabel.value = ''
  progressHint.value = ''
  showCreate.value = true
}

const extractError = (error) => {
  const data = error?.response?.data
  if (data && typeof data === 'object') {
    if (typeof data.error === 'string') return data.error
    if (typeof data.detail === 'string') return data.detail
    const firstKey = Object.keys(data)[0]
    if (firstKey) {
      const val = data[firstKey]
      const msg = Array.isArray(val) ? val[0] : val
      if (typeof msg === 'string') {
        return firstKey === 'non_field_errors' ? msg : `${firstKey}: ${msg}`
      }
    }
  }
  return parseApiError(error)
}

const setProgress = (percent, label, hint = '') => {
  progressPercent.value = Math.max(0, Math.min(100, Math.round(percent)))
  progressLabel.value = label
  progressHint.value = hint
}

const clearSelection = () => {
  selected.value = null
  entries.value = []
  entrySearch.value = ''
}

const submitCreate = async () => {
  formError.value = ''
  if (!canSubmit.value) {
    formError.value = 'Name, at least one category, and a CSV file are required.'
    return
  }

  const {
    institution_category_uuids,
    faculty_uuids,
    department_uuids,
  } = splitCategoryKeys(form.value.categoryKeys)

  const hasInstitution = institution_category_uuids.length > 0
  const hasSub = faculty_uuids.length > 0 || department_uuids.length > 0
  if (hasInstitution && hasSub) {
    formError.value = 'Do not mix institution categories with faculty/department categories.'
    return
  }

  creating.value = true
  setProgress(2, 'Preparing…', 'Validating CSV and creating register')

  let createdRegister = null
  try {
    const { chunks, totalRows } = await splitCsvFile(form.value.file, ROWS_PER_CHUNK)
    setProgress(8, 'Creating register…', `${totalRows} voters · ${chunks.length} upload batch(es)`)

    const payload = {
      name: form.value.name.trim(),
      description: '',
      institution_category_uuids,
      faculty_uuids,
      department_uuids,
    }

    const { data: register } = await institutionRegisterApi.create(payload)
    createdRegister = register

    const cats = register.categories?.length
      ? register.categories
      : [register.primary_category].filter(Boolean)

    let categoryUuid = cats[0]?.uuid
    const targetKey = form.value.importTargetKey || selectedImportTargets.value[0]?.key
    if (targetKey?.startsWith('institution:')) {
      const instUuid = targetKey.slice('institution:'.length)
      const inst = institutionCategories.value.find((c) => c.uuid === instUuid)
      if (inst) {
        categoryUuid = cats.find((c) => c.name === inst.name)?.uuid || categoryUuid
      }
    } else if (targetKey?.startsWith('faculty:')) {
      const facUuid = targetKey.slice('faculty:'.length)
      categoryUuid = cats.find((c) => c.faculty?.uuid === facUuid || c.faculty_uuid === facUuid)?.uuid
        || categoryUuid
    } else if (targetKey?.startsWith('department:')) {
      const depUuid = targetKey.slice('department:'.length)
      categoryUuid = cats.find((c) => c.department?.uuid === depUuid || c.department_uuid === depUuid)?.uuid
        || categoryUuid
    }

    if (!categoryUuid) {
      throw new Error('Register was created without a category.')
    }

    setProgress(12, 'Queued upload…', `${chunks.length} batch(es) · one at a time to avoid timeouts`)

    let created = 0
    let rowErrors = 0
    const base = 12
    const span = 86

    for (let i = 0; i < chunks.length; i += 1) {
      const chunk = chunks[i]
      const chunkStart = base + (i / chunks.length) * span
      const overallPct = Math.round(((i) / chunks.length) * 100)

      setProgress(
        chunkStart,
        `Queue ${i + 1}/${chunks.length} · ${overallPct}%`,
        `${chunk.rowCount} rows in this batch`,
      )

      const { data } = await institutionRegisterApi.importCsv(register.uuid, {
        categoryUuid,
        file: chunk.blob,
        fileName: chunk.fileName,
        onUploadProgress: (pct) => {
          const within = (pct / 100) * (span / chunks.length)
          const doneBatches = (i / chunks.length) * 100
          const batchShare = (1 / chunks.length) * pct
          setProgress(
            chunkStart + within,
            `Queue ${i + 1}/${chunks.length} · ${Math.round(doneBatches + batchShare)}%`,
            `${pct}% of current batch`,
          )
        },
      })

      created += data?.rows_created ?? 0
      rowErrors += data?.errors?.length || 0
    }

    setProgress(100, 'Done', `${created} voter(s) imported${rowErrors ? `, ${rowErrors} row error(s)` : ''}`)
    banner.value = register.message
      || 'Register created and submitted for approval. It will be available for elections after approval.'
    showCreate.value = false
    await load()
    clearSelection()
  } catch (error) {
    formError.value = extractError(error) || error?.message || 'Could not create register.'
    if (createdRegister?.uuid) {
      progressHint.value = 'Register may have been partially created. You can delete it and retry.'
    }
  } finally {
    creating.value = false
  }
}

const load = async () => {
  loading.value = true
  try {
    const [regRes, instRes, facRes, depRes] = await Promise.all([
      institutionRegisterApi.list(),
      academicApi.institutionCategories(),
      academicApi.faculties(),
      academicApi.departments(),
    ])
    registers.value = Array.isArray(regRes.data) ? regRes.data : []
    institutionCategories.value = Array.isArray(instRes.data) ? instRes.data : []
    faculties.value = Array.isArray(facRes.data) ? facRes.data : []
    departments.value = Array.isArray(depRes.data)
      ? depRes.data.map((d) => ({
          ...d,
          faculty_name: d.faculty_name || d.faculty?.name,
        }))
      : []

    if (selected.value) {
      const fresh = registers.value.find((r) => r.uuid === selected.value.uuid)
      if (fresh) await selectRegister(fresh)
      else clearSelection()
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const selectRegister = async (reg) => {
  selected.value = reg
  entries.value = []
  entrySearch.value = ''
  try {
    const { data } = await institutionRegisterApi.get(reg.uuid)
    selected.value = data
    await loadEntries()
  } catch (error) {
    console.error(error)
  }
}

const loadEntries = async () => {
  if (!selected.value) {
    entries.value = []
    return
  }
  entriesLoading.value = true
  try {
    const { data } = await institutionRegisterApi.listEntries(selected.value.uuid, {
      search: entrySearch.value.trim() || undefined,
    })
    entries.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error(error)
    entries.value = []
  } finally {
    entriesLoading.value = false
  }
}

const openEditEntry = (row) => {
  editEntryUuid.value = row.uuid
  editForm.value = {
    voter_id: row.voter_id || '',
    full_name: row.full_name || '',
    phone_number: row.phone_number || '',
  }
  formError.value = ''
  showEditEntry.value = true
}

const submitEditEntry = async () => {
  formError.value = ''
  if (!selected.value || !editEntryUuid.value) return
  if (!editForm.value.voter_id.trim() || !editForm.value.full_name.trim()) {
    formError.value = 'Index number and full name are required.'
    return
  }
  editingEntry.value = true
  try {
    const { data } = await institutionRegisterApi.updateEntry(
      selected.value.uuid,
      editEntryUuid.value,
      {
        voter_id: editForm.value.voter_id.trim(),
        full_name: editForm.value.full_name.trim(),
        phone_number: editForm.value.phone_number.trim(),
      },
    )
    showEditEntry.value = false
    banner.value = data?.message || 'Voter change submitted for dual Main EC approval. Live list stays on current data until approved.'
    // Refresh register + entries so pending badges appear; live rows stay pre-approval.
    await selectRegister(selected.value)
  } catch (error) {
    formError.value = parseApiError(error) || 'Could not submit voter change.'
  } finally {
    editingEntry.value = false
  }
}

const pendingEditsByEntry = computed(() => {
  const map = {}
  for (const edit of selected.value?.pending_entry_edits || []) {
    if (edit?.entry_uuid) map[edit.entry_uuid] = edit
  }
  return map
})

const pendingEditFor = (row) => pendingEditsByEntry.value[row?.uuid] || null

const confirmDelete = async () => {
  if (!selected.value) return
  if (!confirm(`Delete register “${selected.value.name}”?`)) return
  try {
    await institutionRegisterApi.remove(selected.value.uuid)
    clearSelection()
    await load()
  } catch (error) {
    alert(parseApiError(error) || 'Could not delete register.')
  }
}

onMounted(load)
</script>

<style scoped>
.register-page {
  max-width: 96rem;
}

.register-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  margin-bottom: 1rem;
  border-radius: 1rem;
  background: linear-gradient(180deg, #ffffff, #fbfdfb);
  border: 1px solid rgba(61, 79, 68, 0.14);
  color: var(--vb-ink, #1c1c1c);
  box-shadow: 0 10px 28px rgba(28, 28, 28, 0.05);
}

.register-banner__icon {
  width: 2rem;
  height: 2rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.65rem;
  background: #e8efe6;
  color: var(--vb-accent, #3d4f44);
  font-size: 0.78rem;
  flex-shrink: 0;
}

.register-banner__body {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
  font-size: 0.82rem;
  line-height: 1.4;
}

.register-banner__body strong {
  font-size: 0.88rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.register-banner__body span {
  color: var(--vb-muted, #8a8a8a);
}

.register-banner__close {
  margin-left: auto;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  opacity: 0.45;
  padding: 0.2rem;
  border-radius: 0.45rem;
}

.register-banner__close:hover {
  opacity: 1;
  background: var(--vb-panel, #f7f6f2);
}

.approval-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.approval-badge.is-approved { background: #ecfdf5; color: #047857; }
.approval-badge.is-pending { background: #fff8ec; color: #b45309; }
.approval-badge.is-rejected { background: #fef2f2; color: #be123c; }

.detail-approval-note {
  margin-top: 0.4rem !important;
  font-size: 0.8rem;
  color: #b45309;
}

.register-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(16.5rem, 1fr));
  gap: 0.9rem;
}

.register-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.35rem;
  padding: 1.1rem 1.15rem;
  text-align: left;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 1.1rem;
  background: #fff;
  box-shadow: var(--vb-card-shadow, 0 8px 28px rgba(28, 28, 28, 0.04));
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

.register-card:hover {
  border-color: rgba(61, 79, 68, 0.28);
  box-shadow: 0 10px 28px rgba(28, 28, 28, 0.07);
  transform: translateY(-1px);
}

.register-card__top {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.scope-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  font-size: 0.66rem;
  font-weight: 750;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  background: var(--vb-panel, #f7f6f2);
  color: var(--vb-accent, #3d4f44);
}

.scope-pill.is-faculty { background: #eef2ff; color: #3730a3; }
.scope-pill.is-department { background: #ecfdf5; color: #047857; }
.scope-pill.is-custom { background: #fff7ed; color: #c2410c; }
.scope-pill.is-main { background: #ecfeff; color: #0e7490; }
.scope-pill.is-multi { background: #f0f7f3; color: #3d4f44; }

.audience-toggle {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.4rem;
  padding: 0.25rem;
  border-radius: 0.85rem;
  background: #f5f5f2;
  border: 1px solid var(--vb-line, #ebeae4);
}

.audience-toggle__btn {
  border: none;
  border-radius: 0.7rem;
  padding: 0.65rem 0.75rem;
  background: transparent;
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
}

.audience-toggle__btn.is-active {
  background: #fff;
  color: var(--vb-ink, #1c1c1c);
  box-shadow: 0 1px 4px rgba(28, 28, 28, 0.06);
}

.detail-scope-note {
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
  color: var(--vb-muted, #8a8a8a);
}

.form-callout {
  margin: 0;
  padding: 0.78rem 0.9rem;
  border-radius: 0.9rem;
  background: linear-gradient(180deg, #ffffff, #fbfaf7);
  border: 1px solid var(--vb-line, #ebeae4);
  font-size: 0.8rem;
  line-height: 1.45;
  color: var(--vb-ink, #1c1c1c);
}

.field-hint {
  margin: 0.35rem 0 0;
  font-size: 0.72rem;
  color: var(--vb-muted, #8a8a8a);
  line-height: 1.4;
}

.field-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.4rem;
}

.field-head label {
  margin-bottom: 0;
}

.template-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border: none;
  background: transparent;
  color: var(--vb-accent, #3d4f44);
  font-size: 0.74rem;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
}

.template-link:hover:not(:disabled) {
  text-decoration: underline;
}

.template-link:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.register-card__chevron {
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.75rem;
}

.register-card__name {
  font-size: 1.02rem;
  letter-spacing: -0.015em;
  color: var(--vb-ink, #1c1c1c);
}

.register-card__meta {
  font-size: 0.8rem;
  color: var(--vb-muted, #8a8a8a);
}

.register-card__count {
  margin-top: 0.55rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 650;
  color: var(--vb-ink, #1c1c1c);
}

.detail-hero {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1rem;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid var(--vb-line, #ebeae4);
}

.detail-hero__actions {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: flex-end;
}

.detail-kicker {
  display: block;
  font-size: 0.68rem;
  font-weight: 750;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--vb-muted, #8a8a8a);
  margin-bottom: 0.2rem;
}

.detail-hero h2 {
  margin: 0;
  font-size: 1.3rem;
  letter-spacing: -0.02em;
}

.detail-hero p {
  margin: 0.25rem 0 0;
  font-size: 0.86rem;
  color: var(--vb-muted, #8a8a8a);
}

.voters-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  align-items: center;
  padding: 0.9rem 1.15rem;
  border-bottom: 1px solid var(--vb-line, #ebeae4);
}

.filter-input-wrap {
  flex: 1 1 14rem;
  position: relative;
}

.filter-input-wrap i {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.8rem;
}

.filter-input-wrap input,
.filter-select {
  width: 100%;
  padding: 0.55rem 0.75rem 0.55rem 2rem;
  border: 1px solid var(--vb-line, #ebeae4);
  border-radius: 0.65rem;
  background: #fff;
  font-size: 0.86rem;
}

.filter-select {
  padding-left: 0.75rem;
}

.voters-table-wrap {
  max-height: min(32rem, calc(100vh - 16rem));
  overflow: auto;
}

.voters-table-wrap thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #fff;
}

.loading-row {
  text-align: center;
  color: var(--vb-muted, #8a8a8a);
  padding: 1.25rem !important;
}

.create-form {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.field label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.8rem;
  font-weight: 650;
}

.scope-toggle {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.4rem;
  padding: 0.3rem;
  border-radius: 0.75rem;
  background: var(--vb-panel, #f7f6f2);
}

.scope-toggle__btn {
  border: none;
  background: transparent;
  border-radius: 0.55rem;
  padding: 0.55rem 0.75rem;
  font-size: 0.84rem;
  font-weight: 650;
  cursor: pointer;
  color: var(--vb-muted, #8a8a8a);
}

.scope-toggle__btn.is-active {
  background: #fff;
  color: var(--vb-ink, #1c1c1c);
  box-shadow: 0 1px 3px rgba(28, 28, 28, 0.08);
}

.file-drop {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.95rem 1rem;
  border: 1px dashed var(--vb-line, #ebeae4);
  border-radius: 0.95rem;
  background: linear-gradient(180deg, #ffffff, #fbfaf7);
  cursor: pointer;
  font-size: 0.84rem;
  color: var(--vb-muted, #8a8a8a);
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
}

.file-drop:hover:not(.is-disabled) {
  border-color: rgba(61, 79, 68, 0.3);
  background: #fff;
}

.file-drop.has-file {
  border-style: solid;
  border-color: rgba(61, 79, 68, 0.24);
  color: var(--vb-ink, #1c1c1c);
  background: #fff;
}

.file-drop i {
  width: 2rem;
  height: 2rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.65rem;
  background: #f7f6f2;
  color: var(--vb-accent, #3d4f44);
  flex-shrink: 0;
}

.file-drop.is-disabled {
  opacity: 0.65;
  pointer-events: none;
}

.upload-progress {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0.85rem 0.95rem;
  border-radius: 0.95rem;
  background: #fff;
  border: 1px solid var(--vb-line, #ebeae4);
  box-shadow: 0 8px 24px rgba(28, 28, 28, 0.04);
}

.upload-progress__meta {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: var(--vb-ink, #1c1c1c);
}

.upload-progress__track {
  height: 0.45rem;
  border-radius: 999px;
  background: #f0efea;
  overflow: hidden;
}

.upload-progress__fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--vb-accent, #3d4f44), #8da081);
  transition: width 0.2s ease;
}

.upload-progress__hint {
  margin: 0;
  font-size: 0.72rem;
  color: var(--vb-muted, #8a8a8a);
}

.inline-hint {
  margin: 0;
  font-size: 0.8rem;
  color: var(--vb-muted, #8a8a8a);
}

.inline-hint a {
  font-weight: 650;
  text-decoration: underline;
}

.form-error {
  margin: 0;
  color: #be123c;
  font-size: 0.8rem;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 0.25rem;
}

tr.is-pending-edit td {
  background: #fffbeb;
}

.pending-pill {
  display: inline-block;
  margin-left: 0.45rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  background: #fef3c7;
  color: #92400e;
  vertical-align: middle;
}

.pending-hint {
  margin: 0.25rem 0 0;
  font-size: 0.72rem;
  color: #92610a;
  line-height: 1.35;
}

.pending-wait {
  font-size: 0.75rem;
  color: #92610a;
  font-weight: 600;
}
</style>
