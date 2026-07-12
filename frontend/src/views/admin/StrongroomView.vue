<template>
  <div class="strongroom-page">
    <StrongroomVaultGate
      v-if="!isUnlocked"
      :authenticating="authenticating"
      :session-error="sessionError"
      @authenticate="handleAuthenticate"
    />

    <template v-else>
      <div class="vault-secure-bar">
        <div class="vault-secure-left">
          <span class="vault-secure-badge"><i class="fas fa-lock-open"></i> Vault Unlocked</span>
          <span class="vault-session-timer">
            <i class="fas fa-hourglass-half"></i>
            Session expires in {{ remainingLabel }}
          </span>
        </div>
        <button type="button" class="vault-lock-btn" @click="handleLock">
          <i class="fas fa-lock"></i>
          Lock Vault
        </button>
      </div>

      <PageHeader
        title="Strongroom"
        subtitle="Secured custody registry — election seals, ballot integrity, and vault evidence."
        icon="fas fa-shield-alt"
        icon-tone="tone-teal"
        :loading="loading"
        @refresh="fetchData"
      />

      <div class="stat-grid page-section">
        <StatCard label="Elections" :value="elections.length" icon="fas fa-box-archive" tone="tone-slate" />
        <StatCard label="Sealed" :value="sealedCount" hint="Election seals present" icon="fas fa-stamp" tone="tone-teal" value-tone="text-teal-700" />
        <StatCard label="Ballot Seals" :value="totalBallotSeals" icon="fas fa-layer-group" tone="tone-blue" value-tone="text-blue-700" />
        <StatCard label="Locked" :value="lockedCount" hint="Custody locked" icon="fas fa-lock" tone="tone-amber" value-tone="text-amber-700" />
      </div>

      <DataPanel title="Custody registry" subtitle="Select an election to request vault access and inspect seals" no-padding>
        <div class="custody-grid">
          <div
            v-for="election in paginated"
            :key="election.uuid"
            class="custody-card"
            :class="{ 'is-sealed': election.election_seal }"
          >
            <div class="custody-card-header">
              <div class="custody-shield">
                <i class="fas fa-shield-alt"></i>
              </div>
              <div>
                <p class="custody-title">{{ election.title }}</p>
                <span class="admin-badge" :class="statusBadge(election.status)">{{ election.status }}</span>
              </div>
            </div>

            <div class="custody-meta">
              <div class="custody-meta-row">
                <span>Election Seal</span>
                <span v-if="election.election_seal" class="seal-ok">
                  <i class="fas fa-check-circle"></i> Present
                </span>
                <span v-else class="seal-missing">Not generated</span>
              </div>
              <div class="custody-meta-row">
                <span>Ballot Seals</span>
                <span>{{ election.ballot_seals?.length || 0 }}</span>
              </div>
              <div v-if="election.election_seal" class="custody-hash">
                {{ election.election_seal.seal_hash.slice(0, 20) }}••••••••
              </div>
            </div>

            <button type="button" class="custody-access-btn" @click="openAccessModal(election)">
              <i class="fas fa-key"></i>
              Request Vault Access
            </button>
          </div>

          <div v-if="!loading && elections.length === 0" class="custody-empty">
            <EmptyState icon="fas fa-shield-alt" title="No strongroom records" message="Election custody data will appear here." />
          </div>
        </div>

        <template #footer>
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
        </template>
      </DataPanel>
    </template>

    <!-- Access request modal -->
    <Transition name="app-modal">
      <div v-if="accessModal" class="vault-modal-overlay" @click.self="accessModal = null">
        <div class="vault-modal app-modal-panel">
        <div class="vault-modal-header">
          <i class="fas fa-fingerprint"></i>
          <h3>Vault Access Request</h3>
        </div>
        <p class="vault-modal-election">{{ accessModal.title }}</p>
        <p class="vault-modal-desc">
          State your reason for accessing this election's custody vault. This request is logged.
        </p>
        <textarea
          v-model="accessReason"
          class="vault-modal-textarea"
          rows="3"
          placeholder="e.g. Post-election integrity audit per EC directive…"
        ></textarea>
        <p v-if="accessError" class="vault-modal-error">{{ accessError }}</p>
        <div class="vault-modal-actions">
          <button type="button" class="vault-modal-cancel" @click="accessModal = null">Cancel</button>
          <button
            type="button"
            class="vault-modal-confirm"
            :disabled="accessSubmitting || accessReason.trim().length < 10"
            @click="submitAccess"
          >
            <i :class="accessSubmitting ? 'fas fa-spinner fa-spin' : 'fas fa-unlock'"></i>
            Grant Access & Enter
          </button>
        </div>
      </div>
    </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { strongroomApi } from '@/api/strongroom'
import { useStrongroomVault } from '@/composables/useStrongroomVault'
import { usePagination } from '@/composables/usePagination'
import StrongroomVaultGate from '@/components/strongroom/StrongroomVaultGate.vue'
import PageHeader from '@/components/admin/PageHeader.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import TablePagination from '@/components/admin/TablePagination.vue'

const router = useRouter()
const elections = ref([])
const loading = ref(false)
const accessModal = ref(null)
const accessReason = ref('')
const accessError = ref('')
const accessSubmitting = ref(false)

const {
  isUnlocked,
  remainingLabel,
  sessionError,
  authenticating,
  checkSession,
  authenticate,
  lockVault,
} = useStrongroomVault()

const { page, size, total, totalPages, paginated, from, to, setPage, setPageSize } = usePagination(elections, 9)

const sealedCount = computed(() => elections.value.filter((e) => e.election_seal).length)
const totalBallotSeals = computed(() => elections.value.reduce((sum, e) => sum + (e.ballot_seals?.length || 0), 0))
const lockedCount = computed(() => elections.value.filter((e) => e.custody_records?.some((r) => r.action === 'election_locked')).length)

const statusBadge = (status) => {
  const map = { draft: 'neutral', scheduled: 'info', open: 'success', paused: 'warning', closed: 'danger', archived: 'neutral' }
  return map[status] || 'neutral'
}

const handleAuthenticate = async (password) => {
  const ok = await authenticate(password)
  if (ok) await fetchData()
}

const handleLock = async () => {
  await lockVault()
  elections.value = []
}

const fetchData = async () => {
  if (!isUnlocked.value) return
  loading.value = true
  try {
    const response = await strongroomApi.list()
    elections.value = response.data
  } catch (error) {
    if (error.response?.data?.code === 'vault_session_required') {
      await lockVault()
    }
    console.error('Failed to fetch strongroom data:', error)
  } finally {
    loading.value = false
  }
}

const openAccessModal = (election) => {
  accessModal.value = election
  accessReason.value = ''
  accessError.value = ''
}

const submitAccess = async () => {
  if (!accessModal.value) return
  accessSubmitting.value = true
  accessError.value = ''
  try {
    await strongroomApi.requestAccess(accessModal.value.uuid, accessReason.value.trim())
    const uuid = accessModal.value.uuid
    accessModal.value = null
    router.push(`/strongroom/${uuid}`)
  } catch (error) {
    accessError.value = error.response?.data?.error || 'Access request failed'
  } finally {
    accessSubmitting.value = false
  }
}

onMounted(async () => {
  const active = await checkSession()
  if (active) await fetchData()
})
</script>

<style scoped>
.strongroom-page {
  min-height: 100%;
}

.vault-secure-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.65rem 1rem;
  margin-bottom: 1rem;
  border-radius: 0.75rem;
  background: linear-gradient(90deg, rgba(16, 185, 129, 0.12), rgba(16, 185, 129, 0.04));
  border: 1px solid rgba(16, 185, 129, 0.25);
}

.vault-secure-left {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
}

.vault-secure-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: #059669;
}

.vault-session-timer {
  font-size: 0.75rem;
  color: #64748b;
  font-family: ui-monospace, monospace;
}

.vault-lock-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.85rem;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #475569;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
}

.vault-lock-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.custody-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
  padding: 1rem;
}

.custody-card {
  border-radius: 0.85rem;
  border: 1px solid #e2e8f0;
  background: #fff;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.custody-card:hover {
  border-color: #99f6e4;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.08);
}

.custody-card.is-sealed {
  border-color: rgba(16, 185, 129, 0.35);
}

.custody-card-header {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}

.custody-shield {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.6rem;
  background: linear-gradient(135deg, #0f766e, #14b8a6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1rem;
  flex-shrink: 0;
}

.custody-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.3rem;
}

.custody-meta {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.78rem;
}

.custody-meta-row {
  display: flex;
  justify-content: space-between;
  color: #64748b;
}

.seal-ok {
  color: #059669;
  font-weight: 600;
}

.seal-missing {
  color: #94a3b8;
}

.custody-hash {
  font-family: ui-monospace, monospace;
  font-size: 0.68rem;
  color: #94a3b8;
  padding: 0.35rem 0.5rem;
  background: #f8fafc;
  border-radius: 0.35rem;
  margin-top: 0.25rem;
}

.custody-access-btn {
  margin-top: auto;
  width: 100%;
  padding: 0.6rem;
  border: none;
  border-radius: 0.55rem;
  background: #0f172a;
  color: #fff;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: background 0.15s ease;
}

.custody-access-btn:hover {
  background: #1e293b;
}

.custody-empty {
  grid-column: 1 / -1;
}

/* Modal */
.vault-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.vault-modal {
  width: 100%;
  max-width: 26rem;
  background: #fff;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow:
    0 25px 50px -12px rgba(15, 23, 42, 0.28),
    0 0 0 1px rgba(255, 255, 255, 0.06);
  transform-origin: center center;
  will-change: transform, opacity;
}

.vault-modal-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: #0f766e;
  margin-bottom: 0.5rem;
}

.vault-modal-header h3 {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
}

.vault-modal-election {
  font-weight: 600;
  color: #334155;
  margin-bottom: 0.5rem;
}

.vault-modal-desc {
  font-size: 0.82rem;
  color: #64748b;
  margin-bottom: 0.85rem;
}

.vault-modal-textarea {
  width: 100%;
  padding: 0.65rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.55rem;
  font-size: 0.85rem;
  resize: vertical;
  outline: none;
}

.vault-modal-textarea:focus {
  border-color: #14b8a6;
  box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.15);
}

.vault-modal-error {
  margin-top: 0.5rem;
  font-size: 0.78rem;
  color: #dc2626;
}

.vault-modal-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
  justify-content: flex-end;
}

.vault-modal-cancel {
  padding: 0.55rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #fff;
  color: #64748b;
  font-weight: 600;
  font-size: 0.82rem;
  cursor: pointer;
}

.vault-modal-confirm {
  padding: 0.55rem 1rem;
  border: none;
  border-radius: 0.5rem;
  background: #0f766e;
  color: #fff;
  font-weight: 600;
  font-size: 0.82rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.vault-modal-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
