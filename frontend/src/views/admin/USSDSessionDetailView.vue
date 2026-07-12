<template>
  <div v-if="session" class="admin-page">
    <PageHeader
      title="Session details"
      :subtitle="`USSD session for ${session.msisdn}`"
      icon="fas fa-mobile-alt"
      icon-tone="tone-blue"
      :show-refresh="false"
    >
      <template #actions>
        <button type="button" class="btn-back" @click="router.push('/ussd')">
          <i class="fas fa-arrow-left"></i>
          <span>Back</span>
        </button>
      </template>
    </PageHeader>

    <div class="detail-grid">
      <div class="detail-field">
        <p class="detail-field-label">MSISDN</p>
        <p class="detail-field-value mono">{{ session.msisdn }}</p>
      </div>
      <div class="detail-field">
        <p class="detail-field-label">User</p>
        <p class="detail-field-value">{{ session.user_email || 'Anonymous' }}</p>
      </div>
      <div class="detail-field">
        <p class="detail-field-label">Election</p>
        <p class="detail-field-value">{{ session.election_title || '—' }}</p>
      </div>
      <div class="detail-field">
        <p class="detail-field-label">Status</p>
        <p class="detail-field-value">
          <span class="admin-badge" :class="statusBadge(session.status)">{{ session.status }}</span>
        </p>
      </div>
      <div class="detail-field detail-field-wide">
        <p class="detail-field-label">Current step</p>
        <p class="detail-field-value">{{ session.current_step || '—' }}</p>
      </div>
      <div class="detail-field detail-field-wide">
        <p class="detail-field-label">State data</p>
        <pre class="code-block">{{ JSON.stringify(session.state_data, null, 2) }}</pre>
      </div>
    </div>

    <DataPanel title="Request logs" :subtitle="`${logs.length} interaction${logs.length === 1 ? '' : 's'}`" no-padding>
      <div v-if="logs.length" class="log-list">
        <article v-for="log in logs" :key="log.uuid" class="log-item">
          <div class="log-head">
            <span class="mono text-muted">{{ formatDate(log.timestamp) }}</span>
            <span class="admin-badge" :class="log.outcome === 'success' ? 'success' : 'danger'">
              {{ log.outcome || 'unknown' }}
            </span>
          </div>
          <div class="log-section">
            <p class="log-label">Request</p>
            <pre class="code-block">{{ JSON.stringify(log.request_payload, null, 2) }}</pre>
          </div>
          <div class="log-section">
            <p class="log-label">Response</p>
            <pre class="code-block">{{ log.response_text || '—' }}</pre>
          </div>
        </article>
      </div>
      <EmptyState v-else icon="fas fa-list" title="No logs" message="Request logs for this session are not available." />
    </DataPanel>
  </div>

  <div v-else class="loading-state">
    <i class="fas fa-spinner fa-spin"></i>
    <p>Loading session…</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ussdApi } from '@/api/ussd'
import PageHeader from '@/components/admin/PageHeader.vue'
import DataPanel from '@/components/admin/DataPanel.vue'
import EmptyState from '@/components/admin/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const session = ref(null)
const logs = ref([])

const fetchSession = async () => {
  try {
    const response = await ussdApi.getSession(route.params.uuid)
    session.value = response.data
    const logsResponse = await ussdApi.getSessionLogs(route.params.uuid)
    logs.value = logsResponse.data
  } catch (error) {
    console.error('Failed to fetch session:', error)
    router.push('/ussd')
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
    second: '2-digit',
  })
}

const statusBadge = (status) => {
  const map = { active: 'success', completed: 'info', expired: 'warning', error: 'danger' }
  return map[status] || 'neutral'
}

onMounted(fetchSession)
</script>

