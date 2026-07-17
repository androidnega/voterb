<template>
  <div class="admin-page">
    <PageHeader :loading="loading" :show-refresh="true" @refresh="load">
      <template #actions>
        <span class="gov-pill" :class="status?.ready ? 'is-ready' : 'is-blocked'">
          {{ status?.ready ? 'Operational' : 'Not ready' }}
        </span>
      </template>
    </PageHeader>

    <section v-if="status" class="gov-banner page-section" :class="status.ready ? 'is-ready' : 'is-blocked'">
      <div>
        <strong>{{ status.institution?.short_name || status.institution?.name || 'Institution' }}</strong>
        <p>{{ status.message }}</p>
      </div>
      <div class="gov-banner__stats">
        <span>{{ status.main_ec_count }} / {{ status.required_main_ec_count }} Main EC</span>
        <span>{{ awaitingMine.length }} need your vote</span>
      </div>
    </section>

    <DataPanel
      title="Pending decisions"
      subtitle="Both Main EC members must approve before a decision is enrolled"
      class="page-section"
    >
      <div v-if="loading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i>
        <p>Loading…</p>
      </div>
      <div v-else-if="!decisions.length" class="empty-hint">
        No pending decisions. Create or change elections to propose one.
      </div>
      <div v-else class="decision-list">
        <article
          v-for="d in decisions"
          :key="d.uuid"
          class="decision-card"
          :class="{
            'needs-you': needsMyAction(d),
            'is-signed': userHasApproved(d) && !needsMyAction(d),
          }"
        >
          <header class="decision-card__head">
            <div>
              <strong>{{ d.title }}</strong>
              <p class="decision-card__summary">{{ d.summary || d.decision_type }}</p>
            </div>
            <span
              class="decision-chip"
              :class="userHasApproved(d) ? 'is-done' : 'is-wait'"
            >
              {{ d.approvals_received }}/{{ d.approvals_required }}
            </span>
          </header>

          <p class="decision-card__meta">
            Proposed by {{ d.proposed_by?.name || d.proposed_by?.email || '—' }}
            · {{ formatDate(d.created_at) }}
          </p>

          <ul v-if="d.approvals?.length" class="approval-list">
            <li v-for="a in d.approvals" :key="a.uuid">
              <i class="fas fa-check-circle"></i>
              {{ a.name || a.email }}
              <span v-if="a.user_uuid === myUuid" class="you-tag">you</span>
            </li>
          </ul>

          <div class="decision-card__actions">
            <button
              v-if="needsMyAction(d)"
              type="button"
              class="btn-decide"
              @click="openDecision(d)"
            >
              Review decision
              <i class="fas fa-arrow-right" aria-hidden="true"></i>
            </button>
            <span v-else class="signed-badge">
              <i class="fas fa-check" aria-hidden="true"></i>
              You approved — waiting on peer
            </span>
          </div>
        </article>
      </div>
    </DataPanel>

    <DecisionActionModal
      v-model:visible="showActionModal"
      :decision="activeDecision"
      :already-approved="activeDecision ? userHasApproved(activeDecision) : false"
      :busy="!!actingUuid"
      :busy-action="busyAction"
      :error="actionError"
      @approve="runApprove"
      @reject="runReject"
    />

    <GovernanceSubmittedModal
      v-model:visible="showResultModal"
      :state="resultState"
      :message="resultMessage"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import PageHeader from '@/components/admin/PageHeader.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import DecisionActionModal from '@/components/admin/DecisionActionModal.vue'
import GovernanceSubmittedModal from '@/components/admin/GovernanceSubmittedModal.vue'
import { governanceApi } from '@/api/governance'
import { useAuthStore } from '@/stores/auth'
import { usePageHeading } from '@/composables/usePageHeading'
import { parseApiError } from '@/utils/apiError'

const authStore = useAuthStore()
const { setPageHeading } = usePageHeading()
setPageHeading({
  title: 'Approvals',
  subtitle: 'Both Main ECs must approve before a decision is enrolled',
})

const loading = ref(false)
const status = ref(null)
const decisions = ref([])
const actingUuid = ref('')
const busyAction = ref('')
const showActionModal = ref(false)
const activeDecision = ref(null)
const actionError = ref('')
const showResultModal = ref(false)
const resultState = ref('enrolled')
const resultMessage = ref('')
const autoOpened = ref(false)

const myUuid = computed(() => authStore.user?.uuid)

const userHasApproved = (d) =>
  (d.approvals || []).some((a) => a.user_uuid === myUuid.value)

const needsMyAction = (d) => !userHasApproved(d)

const awaitingMine = computed(() => decisions.value.filter(needsMyAction))

const formatDate = (value) => {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

const openDecision = (d) => {
  activeDecision.value = d
  actionError.value = ''
  showActionModal.value = true
}

const load = async ({ openFirst = false } = {}) => {
  loading.value = true
  try {
    const [statusRes, listRes] = await Promise.all([
      governanceApi.status(),
      governanceApi.listDecisions({ status: 'pending' }),
    ])
    status.value = statusRes.data
    decisions.value = Array.isArray(listRes.data) ? listRes.data : []
    if (openFirst && !autoOpened.value) {
      const first = decisions.value.find(needsMyAction)
      if (first) {
        autoOpened.value = true
        await nextTick()
        openDecision(first)
      }
    }
  } catch (error) {
    console.error(error)
    decisions.value = []
  } finally {
    loading.value = false
  }
}

const runApprove = async (d) => {
  if (!d?.uuid) return
  actingUuid.value = d.uuid
  busyAction.value = 'approve'
  actionError.value = ''
  try {
    const { data } = await governanceApi.approve(d.uuid)
    showActionModal.value = false
    activeDecision.value = null
    if (data?.status === 'enrolled') {
      resultState.value = 'enrolled'
      resultMessage.value =
        data.message || 'Decision enrolled — both Main EC members approved.'
      showResultModal.value = true
    } else {
      resultState.value = 'pending'
      resultMessage.value =
        data.message || 'Approval recorded. Waiting for the other Main EC member.'
      showResultModal.value = true
    }
    await load()
  } catch (error) {
    actionError.value = parseApiError(error) || 'Could not approve.'
  } finally {
    actingUuid.value = ''
    busyAction.value = ''
  }
}

const runReject = async ({ decision, reason }) => {
  if (!decision?.uuid) return
  actingUuid.value = decision.uuid
  busyAction.value = 'reject'
  actionError.value = ''
  try {
    const { data } = await governanceApi.reject(decision.uuid, reason || '')
    showActionModal.value = false
    activeDecision.value = null
    resultState.value = 'rejected'
    resultMessage.value = data?.message || 'Decision rejected.'
    showResultModal.value = true
    await load()
  } catch (error) {
    actionError.value = parseApiError(error) || 'Could not reject.'
  } finally {
    actingUuid.value = ''
    busyAction.value = ''
  }
}

watch(showActionModal, (open) => {
  if (!open) actionError.value = ''
})

onMounted(() => load({ openFirst: true }))
</script>

<style scoped>
.gov-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.4rem 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 750;
}
.gov-pill.is-ready { background: #dcfce7; color: #166534; }
.gov-pill.is-blocked { background: #ffedd5; color: #9a3412; }

.gov-banner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.15rem;
  border-radius: 1rem;
  border: 1px solid var(--vb-line, #ebeae4);
}
.gov-banner.is-ready { background: #f0fdf4; border-color: #bbf7d0; }
.gov-banner.is-blocked { background: #fff7ed; border-color: #fed7aa; }
.gov-banner p { margin: 0.35rem 0 0; color: var(--vb-muted, #8a8a8a); font-size: 0.88rem; }
.gov-banner__stats {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
  font-weight: 700;
  text-align: right;
}

.decision-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.decision-card {
  padding: 1.1rem 1.15rem;
  border-radius: 1.05rem;
  border: 1px solid var(--vb-line, #ebeae4);
  background: #fff;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.decision-card.needs-you {
  border-color: rgba(61, 79, 68, 0.35);
  box-shadow: 0 10px 28px rgba(61, 79, 68, 0.08);
}

.decision-card.is-signed {
  border-color: #bbf7d0;
  background: linear-gradient(180deg, #f0fdf4 0%, #fff 55%);
}

.decision-card__head {
  display: flex;
  justify-content: space-between;
  gap: 0.85rem;
  align-items: flex-start;
}

.decision-card__summary {
  margin: 0.35rem 0 0;
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.85rem;
  line-height: 1.45;
}

.decision-card__meta {
  margin: 0.55rem 0 0;
  font-size: 0.75rem;
  color: var(--vb-muted, #8a8a8a);
}

.decision-chip {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  padding: 0.3rem 0.65rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 750;
}
.decision-chip.is-wait {
  background: #fff7ed;
  color: #9a3412;
}
.decision-chip.is-done {
  background: #dcfce7;
  color: #166534;
}

.approval-list {
  list-style: none;
  margin: 0.7rem 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem 0.9rem;
  font-size: 0.8rem;
  color: #166534;
}
.you-tag {
  margin-left: 0.25rem;
  font-size: 0.65rem;
  font-weight: 750;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #15803d;
  opacity: 0.85;
}

.decision-card__actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.95rem;
}

.btn-decide {
  appearance: none;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font: inherit;
  font-size: 0.84rem;
  font-weight: 750;
  padding: 0.65rem 1rem;
  border-radius: 0.75rem;
  background: var(--vb-accent, #3d4f44);
  color: #fff;
  box-shadow: 0 8px 18px rgba(61, 79, 68, 0.2);
  transition: transform 0.15s ease, background 0.15s ease;
}
.btn-decide:hover {
  background: var(--vb-accent-hover, #334239);
  transform: translateY(-1px);
}

.signed-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: #15803d;
  padding: 0.45rem 0.75rem;
  border-radius: 0.7rem;
  background: #dcfce7;
}

.empty-hint {
  color: var(--vb-muted, #8a8a8a);
  font-size: 0.9rem;
  padding: 0.5rem 0;
}
</style>
