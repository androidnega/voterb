<template>
  <div class="admin-page">
    <PageHeader :loading="loading" @refresh="fetchResults" />

    <div class="kpi-strip">
      <div class="kpi-item">
        <p class="kpi-label">Total</p>
        <p class="kpi-value">{{ stats.total }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Pending</p>
        <p class="kpi-value is-warn">{{ stats.pending }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Certified</p>
        <p class="kpi-value is-info">{{ stats.certified }}</p>
      </div>
      <div class="kpi-item">
        <p class="kpi-label">Published</p>
        <p class="kpi-value is-ok">{{ stats.published }}</p>
      </div>
    </div>

    <section class="table-surface">
      <div class="admin-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Election</th>
              <th>Status</th>
              <th>Turnout</th>
              <th>Certified By</th>
              <th class="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="result in results" :key="result.uuid">
              <td class="font-medium">{{ result.election.title }}</td>
              <td>
                <span class="admin-badge" :class="statusBadge(result.status)">{{ result.status }}</span>
              </td>
              <td class="text-muted">{{ result.turnout_percentage || 0 }}%</td>
              <td class="text-muted">{{ certifiedByLabel(result) }}</td>
              <td>
                <div class="row-actions">
                  <button type="button" class="admin-icon-btn" title="View" @click="viewResult(result.election.uuid)">
                    <i class="fas fa-eye"></i>
                  </button>
                  <button
                    v-if="result.status === 'generated' && canManageResults"
                    type="button"
                    class="admin-icon-btn"
                    title="Certify"
                    @click="certifyResult(result.election.uuid)"
                  >
                    <i class="fas fa-check"></i>
                  </button>
                  <button
                    v-if="result.status === 'certified' && canManageResults"
                    type="button"
                    class="admin-icon-btn"
                    title="Publish"
                    @click="publishResult(result.election.uuid)"
                  >
                    <i class="fas fa-globe"></i>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="results.length === 0 && !loading">
              <td colspan="5">
                <EmptyState
                  icon="fas fa-inbox"
                  title="No results available"
                  message="Generate results after closing an election."
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { resultsApi } from '@/api/results'
import PageHeader from '@/components/admin/PageHeader.vue'
import EmptyState from '@/components/admin/EmptyState.vue'

const router = useRouter()
const authStore = useAuthStore()
const results = ref([])
const loading = ref(false)
const canManageResults = computed(() => authStore.isElectionManager)

const stats = computed(() => {
  const total = results.value.length
  const pending = results.value.filter((r) => r.status === 'generated' || r.status === 'pending_certification').length
  const certified = results.value.filter((r) => r.status === 'certified').length
  const published = results.value.filter((r) => r.status === 'published').length
  return { total, pending, certified, published }
})

const fetchResults = async () => {
  loading.value = true
  try {
    const response = await resultsApi.list()
    results.value = response.data
  } catch (error) {
    console.error('Failed to fetch results:', error)
  } finally {
    loading.value = false
  }
}

const statusBadge = (s) => ({
  generated: 'warning',
  pending_certification: 'warning',
  certified: 'info',
  published: 'success',
}[s] || 'neutral')

const certifiedByLabel = (result) =>
  result.certified_by_email
  || result.certified_by?.email
  || result.certified_by_name
  || result.certified_by?.display_name
  || '—'

const viewResult = (uuid) => router.push(`/results/${uuid}`)

const certifyResult = (uuid) => {
  router.push(`/results/${uuid}/certify`)
}

const publishResult = async (uuid) => {
  if (!confirm('Publish these results?')) return
  try {
    await resultsApi.publish(uuid)
    await fetchResults()
  } catch {
    alert('Failed to publish results.')
  }
}

onMounted(fetchResults)
</script>

<style scoped>
.font-medium {
  font-weight: 650;
  color: var(--vb-ink, #1c1c1c);
}
</style>
