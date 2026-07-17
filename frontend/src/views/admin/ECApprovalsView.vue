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
        <span>{{ status.pending_decisions || 0 }} pending</span>
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
        <article v-for="d in decisions" :key="d.uuid" class="decision-card">
          <header>
            <strong>{{ d.title }}</strong>
            <span class="admin-badge warning">
              {{ d.approvals_received }}/{{ d.approvals_required }} approvals
            </span>
          </header>
          <p class="decision-card__summary">{{ d.summary || d.decision_type }}</p>
          <p class="decision-card__meta">
            Proposed by {{ d.proposed_by?.name || d.proposed_by?.email || '—' }}
            · {{ formatDate(d.created_at) }}
          </p>
          <ul v-if="d.approvals?.length" class="approval-list">
            <li v-for="a in d.approvals" :key="a.uuid">
              <i class="fas fa-check-circle"></i>
              {{ a.name || a.email }}
            </li>
          </ul>
          <div class="decision-card__actions">
            <button
              type="button"
              class="btn btn-primary"
              :disabled="actingUuid === d.uuid || userHasApproved(d)"
              @click="approve(d)"
            >
              {{ userHasApproved(d) ? 'You approved' : 'Approve' }}
            </button>
            <button
              type="button"
              class="btn btn-ghost"
              :disabled="actingUuid === d.uuid"
              @click="reject(d)"
            >
              Reject
            </button>
          </div>
        </article>
      </div>
    </DataPanel>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/admin/PageHeader.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import { governanceApi } from '@/api/governance'
import { useAuthStore } from '@/stores/auth'
import { usePageHeading } from '@/composables/usePageHeading'
import { parseApiError } from '@/utils/apiError'

const authStore = useAuthStore()
const { setPageHeading } = usePageHeading()
setPageHeading({
  title: 'Dual Approvals',
  subtitle: 'Both Main ECs must approve before a decision is enrolled',
})

const loading = ref(false)
const status = ref(null)
const decisions = ref([])
const actingUuid = ref('')

const myUuid = computed(() => authStore.user?.uuid)

const userHasApproved = (d) =>
  (d.approvals || []).some((a) => a.user_uuid === myUuid.value)

const formatDate = (value) => {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

const load = async () => {
  loading.value = true
  try {
    const [statusRes, listRes] = await Promise.all([
      governanceApi.status(),
      governanceApi.listDecisions({ status: 'pending' }),
    ])
    status.value = statusRes.data
    decisions.value = Array.isArray(listRes.data) ? listRes.data : []
  } catch (error) {
    console.error(error)
    decisions.value = []
  } finally {
    loading.value = false
  }
}

const approve = async (d) => {
  actingUuid.value = d.uuid
  try {
    const { data } = await governanceApi.approve(d.uuid)
    alert(data.message || 'Approval recorded.')
    await load()
  } catch (error) {
    alert(parseApiError(error) || 'Could not approve.')
  } finally {
    actingUuid.value = ''
  }
}

const reject = async (d) => {
  const reason = prompt('Reason for rejection (optional):') ?? ''
  if (reason === null) return
  actingUuid.value = d.uuid
  try {
    await governanceApi.reject(d.uuid, reason)
    await load()
  } catch (error) {
    alert(parseApiError(error) || 'Could not reject.')
  } finally {
    actingUuid.value = ''
  }
}

onMounted(load)
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

.decision-list { display: flex; flex-direction: column; gap: 0.85rem; }
.decision-card {
  padding: 1rem 1.1rem;
  border-radius: 0.9rem;
  border: 1px solid var(--vb-line, #ebeae4);
  background: #fff;
}
.decision-card header {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
}
.decision-card__summary { margin: 0.45rem 0 0; color: var(--vb-muted, #8a8a8a); font-size: 0.85rem; }
.decision-card__meta { margin: 0.35rem 0 0; font-size: 0.75rem; color: var(--vb-muted, #8a8a8a); }
.approval-list {
  list-style: none;
  margin: 0.65rem 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  font-size: 0.8rem;
  color: #166534;
}
.decision-card__actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.85rem;
}
.empty-hint { color: var(--vb-muted, #8a8a8a); font-size: 0.9rem; padding: 0.5rem 0; }
</style>
