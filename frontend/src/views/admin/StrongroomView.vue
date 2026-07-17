<template>
  <div class="strongroom-page">
    <!-- Always visible: nominate + peer approval requests -->
    <DataPanel
      v-if="!overviewLoading"
      class="page-section"
      title="Custody committee"
      subtitle="Nominate you + peer EC + candidate nominee. The peer EC must approve before the nominee receives a timed custody key."
    >
      <div v-if="pendingForMe.length" class="pending-banner">
        <div>
          <strong>{{ pendingForMe.length }} committee request{{ pendingForMe.length === 1 ? '' : 's' }} waiting for you</strong>
          <p>Another EC nominated you as peer. Approve to activate the custody committee and send the nominee key.</p>
        </div>
      </div>

      <div v-if="setupElections.length === 0" class="committee-empty">
        <EmptyState
          icon="fas fa-users-cog"
          title="No elections yet"
          message="Create an election first, then nominate a custody committee here."
        />
      </div>

      <div v-else class="committee-list">
        <div
          v-for="election in setupElections"
          :key="election.uuid"
          class="committee-row"
          :class="{ 'is-pending-me': canApprove(election) }"
        >
          <div class="committee-row-main">
            <p class="committee-election">{{ election.title }}</p>
            <span class="admin-badge" :class="committeeBadge(election.committee_status)">
              {{ committeeLabel(election.committee_status) }}
            </span>
          </div>
          <p class="committee-hint">{{ committeeHint(election) }}</p>
          <ul v-if="election.committee" class="committee-meta">
            <li v-if="election.committee.nominated_by">
              Nominated by {{ personName(election.committee.nominated_by) }}
            </li>
            <li v-if="election.committee.peer_ec">
              Peer EC {{ personName(election.committee.peer_ec) }}
            </li>
            <li v-if="election.committee.nominee_full_name">
              Nominee {{ election.committee.nominee_full_name }}
              <span v-if="election.committee.nominee_phone_masked">
                · {{ election.committee.nominee_phone_masked }}
              </span>
            </li>
          </ul>
          <div class="committee-actions">
            <button
              v-if="canNominate(election)"
              type="button"
              class="committee-btn committee-btn--primary"
              :disabled="actionBusy === election.uuid"
              @click="openNominate(election)"
            >
              <i :class="actionBusy === election.uuid ? 'fas fa-spinner fa-spin' : 'fas fa-user-plus'"></i>
              Request peer approval
            </button>
            <button
              v-if="canApprove(election)"
              type="button"
              class="committee-btn committee-btn--approve"
              :disabled="actionBusy === election.uuid"
              @click="approve(election)"
            >
              <i :class="actionBusy === election.uuid ? 'fas fa-spinner fa-spin' : 'fas fa-check'"></i>
              Approve committee request
            </button>
            <span v-if="waitingOnPeer(election)" class="committee-wait">
              Waiting for {{ personName(election.committee?.peer_ec) || 'peer EC' }} to approve
            </span>
            <span v-if="isAuditorOnly" class="committee-wait">View only — EC members set up the committee</span>
          </div>
          <p v-if="actionError && actionTarget === election.uuid" class="committee-error">{{ actionError }}</p>
          <p v-if="actionSuccess && actionTarget === election.uuid" class="committee-success">{{ actionSuccess }}</p>
        </div>
      </div>
    </DataPanel>

    <div v-else-if="overviewLoading" class="committee-loading">
      <i class="fas fa-spinner fa-spin"></i>
      Checking custody committee…
    </div>

    <!-- Vault unlock only after at least one committee is approved -->
    <StrongroomVaultGate
      v-if="!overviewLoading && hasApprovedCommittee && !isUnlocked"
      :authenticating="authenticating"
      :session-error="sessionError"
      :challenge="unlockChallenge"
      @authenticate="handleAuthenticate"
      @peer-confirm="handlePeerConfirm"
      @nominee-key="handleNomineeKey"
      @refresh="refreshUnlockStatus"
    />

    <div
      v-else-if="!overviewLoading && !hasApprovedCommittee"
      class="vault-blocked page-section"
    >
      <i class="fas fa-lock" aria-hidden="true"></i>
      <div>
        <strong>Strongroom vault locked</strong>
        <p>Nominate a committee and get peer EC approval first. Then unlock with EC password → peer confirm → nominee key.</p>
      </div>
    </div>

    <template v-if="isUnlocked">
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
        :loading="loading"
        @refresh="fetchData"
      />

      <div class="kpi-strip">
        <div class="kpi-item">
          <p class="kpi-label">Elections</p>
          <p class="kpi-value">{{ elections.length }}</p>
        </div>
        <div class="kpi-item">
          <p class="kpi-label">Sealed</p>
          <p class="kpi-value is-ok">{{ sealedCount }}</p>
          <p class="kpi-hint">Election seals present</p>
        </div>
        <div class="kpi-item">
          <p class="kpi-label">Ballot seals</p>
          <p class="kpi-value is-info">{{ totalBallotSeals }}</p>
        </div>
        <div class="kpi-item">
          <p class="kpi-label">Committee ready</p>
          <p class="kpi-value is-ok">{{ approvedInVaultCount }}</p>
          <p class="kpi-hint">Approved for custody access</p>
        </div>
      </div>

      <DataPanel
        class="page-section"
        title="Verify seal hash"
        subtitle="Paste an election or ballot seal hash from this vault to confirm authenticity. This is not a voter receipt code."
      >
        <div class="verify-row">
          <input
            v-model="sealHashInput"
            type="text"
            class="verify-input"
            placeholder="Paste full seal hash…"
            spellcheck="false"
            autocomplete="off"
            @keydown.enter="verifySealHash"
          />
          <button
            type="button"
            class="verify-btn"
            :disabled="!sealHashInput.trim() || verifying"
            @click="verifySealHash"
          >
            <i :class="verifying ? 'fas fa-spinner fa-spin' : 'fas fa-check-double'"></i>
            {{ verifying ? 'Checking…' : 'Verify' }}
          </button>
        </div>

        <div
          v-if="verifyResult"
          class="verify-result"
          :class="verifyResult.valid ? 'is-valid' : 'is-invalid'"
        >
          <div class="verify-result__head">
            <i :class="verifyResult.valid ? 'fas fa-check-circle' : 'fas fa-times-circle'"></i>
            <strong>{{ verifyResult.valid ? 'Valid seal' : 'No matching seal' }}</strong>
          </div>
          <template v-if="verifyResult.valid">
            <p><span>Type</span> {{ formatSealType(verifyResult.type) }}</p>
            <p><span>Election</span> {{ verifyResult.election }}</p>
            <p><span>Status</span> {{ verifyResult.status }}</p>
            <p><span>Created</span> {{ formatVerifyDate(verifyResult.created_at) }}</p>
          </template>
          <p v-else class="verify-result__msg">
            {{ verifyResult.message || 'That hash is not in the Strongroom registry.' }}
          </p>
        </div>
      </DataPanel>

      <DataPanel title="Custody registry" subtitle="Request vault access only for elections with an approved custody committee" no-padding>
        <div class="custody-grid">
          <div
            v-for="election in paginated"
            :key="election.uuid"
            class="custody-card"
            :class="{
              'is-sealed': election.election_seal,
              'is-blocked': !isCommitteeApproved(election),
            }"
          >
            <div class="custody-card-header">
              <div class="custody-shield">
                <i class="fas fa-shield-alt"></i>
              </div>
              <div>
                <p class="custody-title">{{ election.title }}</p>
                <div class="custody-badges">
                  <span class="admin-badge" :class="statusBadge(election.status)">{{ election.status }}</span>
                  <span class="admin-badge" :class="committeeBadge(election.committee_status)">
                    {{ committeeLabel(election.committee_status) }}
                  </span>
                </div>
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

            <template v-if="isCommitteeApproved(election)">
              <button type="button" class="custody-access-btn" @click="openAccessModal(election)">
                <i class="fas fa-key"></i>
                Request Vault Access
              </button>
            </template>
            <template v-else>
              <p class="custody-blocked">{{ committeeHint(election.committee_status) }}</p>
              <div class="custody-card-actions">
                <button
                  v-if="canNominate(election)"
                  type="button"
                  class="committee-btn committee-btn--primary"
                  :disabled="actionBusy === election.uuid"
                  @click="openNominate(election)"
                >
                  <i :class="actionBusy === election.uuid ? 'fas fa-spinner fa-spin' : 'fas fa-user-plus'"></i>
                  Request peer approval
                </button>
                <button
                  v-if="canApprove(election)"
                  type="button"
                  class="committee-btn committee-btn--approve"
                  :disabled="actionBusy === election.uuid"
                  @click="approve(election)"
                >
                  <i :class="actionBusy === election.uuid ? 'fas fa-spinner fa-spin' : 'fas fa-check'"></i>
                  Approve request
                </button>
              </div>
            </template>
          </div>

          <div v-if="!loading && elections.length === 0" class="custody-empty">
            <EmptyState
              icon="fas fa-shield-alt"
              title="No strongroom records"
              message="Election custody data will appear here once elections exist."
            />
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

    <!-- Nominate custody committee -->
    <Transition name="app-modal">
      <div v-if="nominateModal" class="vault-modal-overlay" @click.self="nominateModal = null">
        <div class="vault-modal app-modal-panel">
          <div class="vault-modal-header">
            <i class="fas fa-users"></i>
            <h3>Nominate custody committee</h3>
          </div>
          <p class="vault-modal-election">{{ nominateModal.title }}</p>
          <p class="vault-modal-desc">
            Committee of 3: you, a peer EC, and one candidate-nominated person. Peer approval sends a timed key to the nominee.
          </p>
          <label class="vault-modal-label">Peer EC</label>
          <select v-model="nominateForm.peer_ec_uuid" class="vault-modal-input">
            <option value="" disabled>Select peer EC</option>
            <option v-for="peer in peerEcOptions" :key="peer.uuid" :value="peer.uuid">
              {{ peer.name }} · {{ peer.email }}
            </option>
          </select>
          <label class="vault-modal-label">Nominee full name</label>
          <input v-model="nominateForm.nominee_full_name" class="vault-modal-input" placeholder="Person voted onto the committee" />
          <label class="vault-modal-label">Nominee phone</label>
          <input v-model="nominateForm.nominee_phone" class="vault-modal-input" placeholder="e.g. 024xxxxxxx" />
          <label class="vault-modal-label">Nominee email (optional)</label>
          <input v-model="nominateForm.nominee_email" type="email" class="vault-modal-input" placeholder="optional@email.com" />
          <p v-if="nominateError" class="vault-modal-error">{{ nominateError }}</p>
          <div class="vault-modal-actions">
            <button type="button" class="vault-modal-cancel" @click="nominateModal = null">Cancel</button>
            <button type="button" class="vault-modal-confirm" :disabled="nominateSubmitting" @click="submitNominate">
              <i :class="nominateSubmitting ? 'fas fa-spinner fa-spin' : 'fas fa-paper-plane'"></i>
              Submit for peer approval
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
import { useAuthStore } from '@/stores/auth'
import { useStrongroomVault } from '@/composables/useStrongroomVault'
import { usePagination } from '@/composables/usePagination'
import StrongroomVaultGate from '@/components/strongroom/StrongroomVaultGate.vue'
import PageHeader from '@/components/admin/PageHeader.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import EmptyState from '@/components/admin/EmptyState.vue'
import TablePagination from '@/components/admin/TablePagination.vue'

const router = useRouter()
const authStore = useAuthStore()
const elections = ref([])
const setupElections = ref([])
const hasApprovedCommittee = ref(false)
const overviewLoading = ref(true)
const loading = ref(false)
const accessModal = ref(null)
const accessReason = ref('')
const accessError = ref('')
const accessSubmitting = ref(false)
const sealHashInput = ref('')
const verifying = ref(false)
const verifyResult = ref(null)
const actionBusy = ref(null)
const actionError = ref('')
const actionSuccess = ref('')
const actionTarget = ref(null)

const {
  isUnlocked,
  remainingLabel,
  sessionError,
  authenticating,
  unlockChallenge,
  checkSession,
  refreshUnlockStatus,
  authenticate,
  peerConfirm,
  submitNomineeKey,
  lockVault,
} = useStrongroomVault()

const { page, size, total, totalPages, paginated, from, to, setPage, setPageSize } = usePagination(elections, 9)

const isAuditorOnly = computed(() => authStore.roleName === 'auditor' && !authStore.isSuperAdmin && !authStore.isElectionManager)
const peerEcOptions = ref([])
const nominateModal = ref(null)
const nominateForm = ref({
  peer_ec_uuid: '',
  nominee_full_name: '',
  nominee_phone: '',
  nominee_email: '',
})
const nominateError = ref('')
const nominateSubmitting = ref(false)
const sealedCount = computed(() => elections.value.filter((e) => e.election_seal).length)
const totalBallotSeals = computed(() => elections.value.reduce((sum, e) => sum + (e.ballot_seals?.length || 0), 0))
const approvedInVaultCount = computed(() => elections.value.filter((e) => isCommitteeApproved(e)).length)

const statusBadge = (status) => {
  const map = { draft: 'neutral', scheduled: 'info', open: 'success', paused: 'warning', closed: 'danger', archived: 'neutral' }
  return map[status] || 'neutral'
}

const isCommitteeApproved = (election) => election?.committee_status === 'approved'

const committeeLabel = (status) => {
  const map = {
    none: 'No committee',
    draft: 'Draft',
    submitted: 'Awaiting approval',
    approved: 'Committee approved',
    rejected: 'Rejected',
  }
  return map[status] || status || 'No committee'
}

const committeeBadge = (status) => {
  const map = {
    none: 'neutral',
    draft: 'neutral',
    submitted: 'warning',
    approved: 'success',
    rejected: 'danger',
  }
  return map[status] || 'neutral'
}

const personName = (person) => {
  if (!person) return '—'
  const name = `${person.first_name || ''} ${person.last_name || ''}`.trim()
  return name || person.name || person.email || 'EC member'
}

const pendingForMe = computed(() => setupElections.value.filter((e) => canApprove(e)))

const waitingOnPeer = (election) => {
  if (!authStore.isElectionManager) return false
  const status = election.committee_status
  if (status !== 'submitted') return false
  const nominatedBy = election.committee?.nominated_by?.uuid
  return nominatedBy === authStore.user?.uuid
}

const committeeHint = (electionOrStatus) => {
  const election = typeof electionOrStatus === 'string' ? { committee_status: electionOrStatus } : (electionOrStatus || {})
  const status = election.committee_status || 'none'
  if (status === 'approved') return 'Committee approved. Unlock the Strongroom vault with the three-party flow.'
  if (canApprove(election)) {
    return `${personName(election.committee?.nominated_by)} requested your approval as peer EC.`
  }
  if (status === 'submitted') {
    return `Waiting for ${personName(election.committee?.peer_ec)} to approve. Nominee key is sent only after approval.`
  }
  if (status === 'rejected') return 'Previous nomination was rejected. Submit a new committee request.'
  return 'Submit a request: you + peer EC + nominee. Peer must approve before the nominee key is sent.'
}

const canNominate = (election) => {
  if (!authStore.isElectionManager) return false
  const status = election.committee_status || 'none'
  return status === 'none' || status === 'draft' || status === 'rejected'
}

const canApprove = (election) => {
  if (!authStore.isElectionManager) return false
  const status = election.committee_status
  if (status !== 'submitted' && status !== 'draft') return false
  const peerUuid = election.committee?.peer_ec?.uuid
  return !!peerUuid && peerUuid === authStore.user?.uuid
}

const fetchOverview = async () => {
  overviewLoading.value = true
  try {
    const { data } = await strongroomApi.committeeOverview()
    hasApprovedCommittee.value = !!data.has_approved_committee
    setupElections.value = data.elections || []
    peerEcOptions.value = data.peer_ec_options || []
  } catch (error) {
    console.error('Failed to load committee overview:', error)
    hasApprovedCommittee.value = false
    setupElections.value = []
    peerEcOptions.value = []
  } finally {
    overviewLoading.value = false
  }
}

const openNominate = (election) => {
  nominateModal.value = election
  nominateError.value = ''
  nominateForm.value = {
    peer_ec_uuid: peerEcOptions.value[0]?.uuid || '',
    nominee_full_name: '',
    nominee_phone: '',
    nominee_email: '',
  }
}

const submitNominate = async () => {
  if (!nominateModal.value) return
  if (!nominateForm.value.peer_ec_uuid || !nominateForm.value.nominee_full_name.trim() || !nominateForm.value.nominee_phone.trim()) {
    nominateError.value = 'Peer EC, nominee name, and phone are required.'
    return
  }
  nominateSubmitting.value = true
  nominateError.value = ''
  try {
    await strongroomApi.nominateCommittee(nominateModal.value.uuid, {
      peer_ec_uuid: nominateForm.value.peer_ec_uuid,
      nominee_full_name: nominateForm.value.nominee_full_name.trim(),
      nominee_phone: nominateForm.value.nominee_phone.trim(),
      nominee_email: nominateForm.value.nominee_email.trim(),
    })
    const targetUuid = nominateModal.value.uuid
    nominateModal.value = null
    actionTarget.value = targetUuid
    actionSuccess.value = 'Committee request sent. Waiting for peer EC approval.'
    actionError.value = ''
    await fetchOverview()
    if (isUnlocked.value) await fetchData()
  } catch (error) {
    nominateError.value = error.response?.data?.error || 'Nomination failed'
  } finally {
    nominateSubmitting.value = false
  }
}

const approve = async (election) => {
  actionBusy.value = election.uuid
  actionError.value = ''
  actionSuccess.value = ''
  actionTarget.value = election.uuid
  try {
    await strongroomApi.approveCommittee(election.uuid)
    actionSuccess.value = 'Committee approved. Nominee custody key has been sent.'
    await fetchOverview()
    if (isUnlocked.value) await fetchData()
  } catch (error) {
    actionError.value = error.response?.data?.error || 'Approval failed'
  } finally {
    actionBusy.value = null
  }
}

const handleAuthenticate = async (password) => {
  const result = await authenticate(password)
  if (result === true) await fetchData()
}

const handlePeerConfirm = async () => {
  const uuid = unlockChallenge.value?.uuid
  if (!uuid) return
  await peerConfirm(uuid)
}

const handleNomineeKey = async (key) => {
  const uuid = unlockChallenge.value?.uuid
  if (!uuid) return
  const ok = await submitNomineeKey(uuid, key)
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
  if (!isCommitteeApproved(election)) return
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

const formatSealType = (type) => {
  if (type === 'election_seal') return 'Election seal'
  if (type === 'ballot_seal') return 'Ballot seal'
  return type || '—'
}

const formatVerifyDate = (date) => {
  if (!date) return '—'
  return new Date(date).toLocaleString()
}

const verifySealHash = async () => {
  const hash = sealHashInput.value.trim()
  if (!hash || verifying.value) return
  verifying.value = true
  verifyResult.value = null
  try {
    const { data } = await strongroomApi.verifySeal(hash)
    verifyResult.value = data
  } catch (error) {
    verifyResult.value = {
      valid: false,
      message: error.response?.data?.error || 'Verification failed. Try again.',
    }
  } finally {
    verifying.value = false
  }
}

onMounted(async () => {
  await fetchOverview()
  if (!hasApprovedCommittee.value) {
    await lockVault()
    return
  }
  const active = await checkSession()
  if (active) await fetchData()
  else await refreshUnlockStatus()
})
</script>

<style scoped>
.strongroom-page {
  min-height: 100%;
}

.committee-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  padding: 3rem 1rem;
  color: #64748b;
  font-size: 0.9rem;
}

.pending-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding: 0.9rem 1rem;
  border-radius: 0.85rem;
  border: 1px solid #fde68a;
  background: #fffbeb;
  color: #92400e;
}

.pending-banner strong {
  display: block;
  font-size: 0.92rem;
}

.pending-banner p {
  margin: 0.25rem 0 0;
  font-size: 0.82rem;
  line-height: 1.4;
  color: #a16207;
}

.committee-row.is-pending-me {
  border-color: #f59e0b;
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.2);
}

.committee-meta {
  list-style: none;
  margin: 0.45rem 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.85rem;
  font-size: 0.78rem;
  color: #78716c;
}

.committee-success {
  margin: 0.55rem 0 0;
  font-size: 0.8rem;
  color: #166534;
}

.vault-blocked {
  display: flex;
  gap: 0.85rem;
  align-items: flex-start;
  padding: 1rem 1.1rem;
  border-radius: 1rem;
  border: 1px dashed #d6d3d1;
  background: #fafaf9;
  color: #57534e;
}

.vault-blocked i {
  margin-top: 0.15rem;
  color: #a8a29e;
}

.vault-blocked strong {
  display: block;
  font-size: 0.95rem;
  color: #1c1917;
}

.vault-blocked p {
  margin: 0.25rem 0 0;
  font-size: 0.84rem;
  line-height: 1.45;
  color: #78716c;
}

.committee-empty {
  padding: 0.5rem 0;
}

.committee-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.committee-row {
  border: 1px solid #e7e5e4;
  border-radius: 0.85rem;
  padding: 1rem 1.1rem;
  background: #fafaf9;
}

.committee-row-main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 0.35rem;
}

.committee-election {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
}

.committee-hint {
  margin: 0 0 0.75rem;
  font-size: 0.8rem;
  color: #78716c;
}

.committee-actions,
.custody-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.committee-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border: none;
  border-radius: 0.55rem;
  padding: 0.5rem 0.85rem;
  font-size: 0.78rem;
  font-weight: 650;
  cursor: pointer;
}

.committee-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.committee-btn--primary {
  background: #0f172a;
  color: #fff;
}

.committee-btn--approve {
  background: #0f766e;
  color: #fff;
}

.committee-wait {
  font-size: 0.78rem;
  color: #a8a29e;
}

.committee-error {
  margin: 0.55rem 0 0;
  font-size: 0.78rem;
  color: #dc2626;
}

.custody-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.custody-blocked {
  margin: 0;
  font-size: 0.75rem;
  color: #a8a29e;
  line-height: 1.4;
}

.custody-card.is-blocked {
  border-color: #e7e5e4;
  background: #fafaf9;
}

.custody-card.is-blocked:hover {
  border-color: #d6d3d1;
  box-shadow: none;
}

.verify-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  align-items: stretch;
}

.verify-input {
  flex: 1 1 16rem;
  min-width: 0;
  border: 1px solid #e7e5e4;
  border-radius: 0.75rem;
  padding: 0.7rem 0.85rem;
  font-size: 0.8rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: #1c1917;
  background: #fafaf9;
}

.verify-input:focus {
  outline: none;
  border-color: #99f6e4;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12);
  background: #fff;
}

.verify-btn {
  border: none;
  background: #0f766e;
  color: #fff;
  font-size: 0.8rem;
  font-weight: 650;
  padding: 0.7rem 1.05rem;
  border-radius: 0.75rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  white-space: nowrap;
}

.verify-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.verify-btn:hover:not(:disabled) {
  background: #0d6b64;
}

.verify-result {
  margin-top: 0.85rem;
  padding: 0.85rem 0.95rem;
  border-radius: 0.8rem;
  display: grid;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: #44403c;
}

.verify-result.is-valid {
  background: #f0fdf9;
  border: 1px solid #bbf7d0;
}

.verify-result.is-invalid {
  background: #fffbeb;
  border: 1px solid #f5e6d3;
}

.verify-result__head {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin-bottom: 0.15rem;
}

.verify-result.is-valid .verify-result__head {
  color: #0f766e;
}

.verify-result.is-invalid .verify-result__head {
  color: #b45309;
}

.verify-result p {
  margin: 0;
  display: flex;
  gap: 0.65rem;
}

.verify-result p span {
  min-width: 4.5rem;
  color: #a8a29e;
  font-weight: 600;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.verify-result__msg {
  color: #92400e;
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

.vault-modal-label {
  display: block;
  margin: 0.65rem 0 0.3rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #78716c;
}

.vault-modal-input {
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.55rem;
  font-size: 0.88rem;
  outline: none;
  background: #fff;
}

.vault-modal-input:focus {
  border-color: #0f766e;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12);
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
