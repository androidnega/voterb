<template>
  <div v-if="election" class="admin-page strongroom-detail">
    <div class="vault-secure-bar">
      <div class="vault-secure-left">
        <span class="vault-secure-badge"><i class="fas fa-lock-open"></i> Vault Session Active</span>
        <span class="vault-session-timer">
          <i class="fas fa-hourglass-half"></i>
          {{ remainingLabel }} remaining
        </span>
      </div>
      <button type="button" class="btn-back" @click="router.push('/strongroom')">
        <i class="fas fa-arrow-left"></i>
        <span>Back to registry</span>
      </button>
    </div>

    <PageHeader
      :title="election.title"
      subtitle="Secured custody vault — seals are masked until explicitly revealed."
      icon="fas fa-shield-alt"
      icon-tone="tone-teal"
      :show-refresh="false"
    />

    <div class="security-notice">
      <i class="fas fa-exclamation-triangle"></i>
      <span>All seal reveals are logged as vault evidence. Handle cryptographic hashes with care.</span>
    </div>

    <div class="stat-grid stat-grid-3 page-section">
      <StatCard label="Status" :value="election.status" icon="fas fa-flag" tone="tone-slate" />
      <StatCard
        label="Election Seal"
        :value="election.election_seal ? 'Present' : 'Missing'"
        icon="fas fa-stamp"
        tone="tone-teal"
        value-tone="text-teal-700"
      />
      <StatCard
        label="Ballot Seals"
        :value="election.ballot_seals?.length || 0"
        icon="fas fa-layer-group"
        tone="tone-blue"
        value-tone="text-blue-700"
      />
    </div>

    <DataPanel class="page-section" title="Election seal" subtitle="Cryptographic hash — reveal to view full value">
      <div v-if="election.election_seal" class="seal-block">
        <div class="seal-masked">
          <i class="fas fa-fingerprint"></i>
          <code>{{ revealedElectionSeal || maskHash(election.election_seal.seal_hash) }}</code>
        </div>
        <div class="seal-actions">
          <span class="admin-badge" :class="sealBadge(election.election_seal.status)">
            {{ election.election_seal.status }}
          </span>
          <button
            v-if="!revealedElectionSeal"
            type="button"
            class="reveal-btn"
            :disabled="revealing"
            @click="revealSeal('election', election.election_seal.uuid)"
          >
            <i :class="revealing ? 'fas fa-spinner fa-spin' : 'fas fa-eye'"></i>
            Reveal Seal
          </button>
          <button v-else type="button" class="reveal-btn revealed" @click="copyHash(revealedElectionSeal)">
            <i class="fas fa-copy"></i>
            Copy Hash
          </button>
        </div>
      </div>
      <EmptyState v-else icon="fas fa-stamp" title="No election seal" message="The election seal has not been generated yet." />
    </DataPanel>

    <DataPanel class="page-section" title="Ballot seals" subtitle="Individual ballot integrity records">
      <div v-if="election.ballot_seals?.length" class="seal-list">
        <div v-for="seal in election.ballot_seals" :key="seal.uuid" class="seal-block seal-item">
          <div class="seal-masked">
            <i class="fas fa-layer-group"></i>
            <code>{{ revealedBallots[seal.uuid] || maskHash(seal.seal_hash) }}</code>
          </div>
          <div class="seal-actions">
            <span class="admin-badge" :class="sealBadge(seal.status)">{{ seal.status }}</span>
            <button
              v-if="!revealedBallots[seal.uuid]"
              type="button"
              class="reveal-btn"
              :disabled="revealingId === seal.uuid"
              @click="revealSeal('ballot', seal.uuid)"
            >
              <i :class="revealingId === seal.uuid ? 'fas fa-spinner fa-spin' : 'fas fa-eye'"></i>
              Reveal
            </button>
            <button
              v-else
              type="button"
              class="reveal-btn revealed"
              @click="copyHash(revealedBallots[seal.uuid])"
            >
              <i class="fas fa-copy"></i>
              Copy
            </button>
          </div>
        </div>
      </div>
      <EmptyState v-else icon="fas fa-layer-group" title="No ballot seals" message="Ballot seals will appear once ballots are sealed." />
    </DataPanel>

    <DataPanel class="page-section" title="Custody timeline" subtitle="Chain of custody events for this election">
      <div v-if="election.custody_records?.length" class="timeline">
        <div v-for="record in election.custody_records" :key="record.uuid" class="timeline-item">
          <span class="timeline-dot" :class="actionClass(record.action)"></span>
          <div>
            <p class="timeline-action">{{ formatAction(record.action) }}</p>
            <p class="timeline-meta">
              {{ record.actor_email || 'System' }} · {{ formatDate(record.timestamp) }}
            </p>
          </div>
        </div>
      </div>
      <EmptyState v-else icon="fas fa-history" title="No custody records" message="Custody events will be logged here." />
    </DataPanel>
  </div>

  <div v-else class="loading-state">
    <i class="fas fa-spinner fa-spin"></i>
    <p>Verifying vault access…</p>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { strongroomApi } from '@/api/strongroom'
import { useStrongroomVault } from '@/composables/useStrongroomVault'
import PageHeader from '@/components/admin/PageHeader.vue'
import StatCard from '@/components/admin/StatCard.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import EmptyState from '@/components/admin/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const election = ref(null)
const revealedElectionSeal = ref('')
const revealedBallots = reactive({})
const revealing = ref(false)
const revealingId = ref(null)

const { remainingLabel, checkSession, lockVault } = useStrongroomVault()

const maskHash = (hash) => `${hash.slice(0, 12)}${'•'.repeat(20)}${hash.slice(-8)}`

const fetchDetail = async () => {
  const active = await checkSession()
  if (!active) {
    router.push('/strongroom')
    return
  }
  try {
    const response = await strongroomApi.detail(route.params.uuid)
    election.value = response.data
  } catch (error) {
    if (error.response?.data?.code === 'vault_session_required') {
      await lockVault()
    }
    router.push('/strongroom')
  }
}

const revealSeal = async (sealType, sealUuid) => {
  if (sealType === 'election') revealing.value = true
  else revealingId.value = sealUuid

  try {
    const { data } = await strongroomApi.revealSeal(route.params.uuid, sealType, sealUuid)
    if (sealType === 'election') {
      revealedElectionSeal.value = data.seal_hash
    } else {
      revealedBallots[sealUuid] = data.seal_hash
    }
    await fetchDetail()
  } catch (error) {
    alert(error.response?.data?.error || 'Failed to reveal seal')
  } finally {
    revealing.value = false
    revealingId.value = null
  }
}

const copyHash = async (hash) => {
  try {
    await navigator.clipboard.writeText(hash)
  } catch {
    // ignore
  }
}

const formatDate = (date) => {
  if (!date) return '—'
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatAction = (action) => action.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

const actionClass = (action) => {
  if (action.includes('lock') || action.includes('exit')) return 'dot-warn'
  if (action.includes('reveal') || action.includes('access')) return 'dot-info'
  if (action.includes('enter') || action.includes('granted')) return 'dot-ok'
  return ''
}

const sealBadge = (status) => {
  const map = { active: 'success', valid: 'success', pending: 'warning', revoked: 'danger', invalid: 'danger' }
  return map[status] || 'neutral'
}

onMounted(fetchDetail)
</script>

<style scoped>
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

.btn-back {
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

.security-notice {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.65rem 1rem;
  margin-bottom: 1rem;
  border-radius: 0.6rem;
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
  font-size: 0.8rem;
}

.seal-block {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  border-radius: 0.65rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.seal-item {
  margin-bottom: 0.5rem;
}

.seal-masked {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-width: 0;
  flex: 1;
}

.seal-masked i {
  color: #64748b;
  flex-shrink: 0;
}

.seal-masked code {
  font-family: ui-monospace, monospace;
  font-size: 0.78rem;
  color: #334155;
  word-break: break-all;
}

.seal-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.reveal-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.75rem;
  border: none;
  border-radius: 0.45rem;
  background: #0f172a;
  color: #fff;
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
}

.reveal-btn.revealed {
  background: #0f766e;
}

.reveal-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.timeline-item {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}

.timeline-dot {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 9999px;
  background: #94a3b8;
  margin-top: 0.35rem;
  flex-shrink: 0;
}

.timeline-dot.dot-ok { background: #10b981; }
.timeline-dot.dot-warn { background: #f59e0b; }
.timeline-dot.dot-info { background: #3b82f6; }

.timeline-action {
  font-size: 0.85rem;
  font-weight: 600;
  color: #0f172a;
}

.timeline-meta {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 4rem;
  color: #64748b;
}
</style>
