<template>
  <div class="student-home">
    <section class="welcome-card">
      <p class="welcome-eyebrow">Student portal</p>
      <h1 class="welcome-title">Hello, {{ studentName }}</h1>
      <p v-if="campusLine" class="welcome-meta">{{ campusLine }}</p>
      <p class="welcome-copy">
        Vote in elections you're eligible for. When one is open, tap <strong>Cast vote</strong> to begin.
      </p>
    </section>

    <section class="elections-section">
      <div class="section-head">
        <h2>Open elections</h2>
        <p>Active ballots you can participate in right now.</p>
      </div>

      <div v-if="loading" class="state-card">
        <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
        <span>Loading elections…</span>
      </div>

      <div v-else-if="error" class="state-card state-card--error">
        <p>{{ error }}</p>
        <button type="button" class="btn-retry" @click="fetchElections">Try again</button>
      </div>

      <div v-else-if="!elections.length" class="state-card state-card--empty">
        <div class="empty-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
          </svg>
        </div>
        <h3>No open elections</h3>
        <p>You're not eligible for any active ballots right now. Check back when voting opens.</p>
      </div>

      <div v-else class="election-list">
        <article
          v-for="election in elections"
          :key="election.uuid"
          class="election-card"
        >
          <div class="election-card-head">
            <div class="election-card-copy">
              <h3>{{ election.title }}</h3>
              <p>{{ election.description || 'No description provided.' }}</p>
            </div>
            <span class="status-pill" :class="`status-pill--${election.status}`">
              {{ election.status }}
            </span>
          </div>

          <dl class="election-meta">
            <div>
              <dt>Opens</dt>
              <dd>{{ formatDate(election.start_date) }}</dd>
            </div>
            <div>
              <dt>Closes</dt>
              <dd>{{ formatDate(election.end_date) }}</dd>
            </div>
          </dl>

          <div class="election-card-actions">
            <button
              type="button"
              class="btn-vote"
              :disabled="election.status !== 'open'"
              @click="startVoting(election.uuid)"
            >
              Cast vote
            </button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { votingApi } from '@/api/voting'
import { displayUserName } from '@/utils/user'

const router = useRouter()
const authStore = useAuthStore()

const elections = ref([])
const loading = ref(true)
const error = ref('')

const studentName = computed(() => displayUserName(authStore.user, 'Student'))

const campusLine = computed(() => {
  const user = authStore.user
  if (!user) return ''

  const parts = [
    user.department?.name,
    user.faculty?.name,
    user.level?.name,
  ].filter(Boolean)

  return parts.join(' · ')
})

function formatDate(date) {
  if (!date) return 'TBA'
  return new Date(date).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

async function fetchElections() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await votingApi.getEligibleElections()
    elections.value = data || []
  } catch (err) {
    console.error('Failed to fetch elections:', err)
    error.value = err.response?.data?.error || 'Could not load elections. Please try again.'
  } finally {
    loading.value = false
  }
}

function startVoting(electionUuid) {
  router.push(`/vote/${electionUuid}`)
}

onMounted(fetchElections)
</script>

<style scoped>
.student-home {
  display: grid;
  gap: 1.15rem;
}

.welcome-card {
  background: #fdfcfa;
  border: 1px solid #e5e2db;
  border-radius: 0.85rem;
  padding: 1.15rem 1.1rem;
  box-shadow: 0 1px 2px rgba(28, 25, 23, 0.04);
}

.welcome-eyebrow {
  margin: 0;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: #78716c;
}

.welcome-title {
  margin: 0.35rem 0 0;
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #1c1917;
}

.welcome-meta {
  margin: 0.35rem 0 0;
  font-size: 0.75rem;
  color: #78716c;
}

.welcome-copy {
  margin: 0.7rem 0 0;
  font-size: 0.78rem;
  line-height: 1.5;
  color: #78716c;
}

.welcome-copy strong {
  color: #1c1917;
  font-weight: 600;
}

.elections-section {
  display: grid;
  gap: 0.85rem;
}

.section-head h2 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: #1c1917;
}

.section-head p {
  margin: 0.2rem 0 0;
  font-size: 0.72rem;
  color: #78716c;
}

.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  min-height: 9rem;
  padding: 1.25rem;
  border-radius: 0.85rem;
  border: 1px solid #e5e2db;
  background: #fdfcfa;
  color: #78716c;
  font-size: 0.78rem;
  text-align: center;
}

.state-card i {
  color: var(--vb-accent, #0f766e);
  font-size: 1rem;
}

.state-card--error {
  border-color: #fecaca;
  background: #fef2f2;
  color: #b91c1c;
}

.state-card--empty h3 {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: #1c1917;
}

.state-card--empty p {
  margin: 0.25rem 0 0;
  max-width: 18rem;
  line-height: 1.45;
}

.empty-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f4f1;
  color: #a8a29e;
}

.empty-icon svg {
  width: 1.2rem;
  height: 1.2rem;
}

.btn-retry {
  margin-top: 0.25rem;
  border: none;
  background: #b91c1c;
  color: #fff;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.45rem 0.8rem;
  border-radius: 0.45rem;
  cursor: pointer;
}

.election-list {
  display: grid;
  gap: 0.75rem;
}

.election-card {
  background: #fdfcfa;
  border: 1px solid #e5e2db;
  border-radius: 0.85rem;
  padding: 1rem;
  box-shadow: 0 1px 2px rgba(28, 25, 23, 0.04);
}

.election-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.election-card-copy h3 {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 700;
  color: #1c1917;
  line-height: 1.35;
}

.election-card-copy p {
  margin: 0.3rem 0 0;
  font-size: 0.72rem;
  line-height: 1.45;
  color: #78716c;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.status-pill {
  flex-shrink: 0;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 0.25rem 0.45rem;
  border-radius: 999px;
  background: #f5f4f1;
  color: #78716c;
}

.status-pill--open {
  background: var(--vb-accent-soft, #ecfdf5);
  color: var(--vb-accent, #0f766e);
}

.election-meta {
  margin: 0.85rem 0 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.election-meta div {
  padding: 0.55rem 0.65rem;
  border-radius: 0.55rem;
  background: #f7f6f3;
  border: 1px solid #ece9e2;
}

.election-meta dt {
  margin: 0;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #a8a29e;
}

.election-meta dd {
  margin: 0.15rem 0 0;
  font-size: 0.75rem;
  font-weight: 600;
  color: #1c1917;
}

.election-card-actions {
  margin-top: 0.85rem;
  padding-top: 0.85rem;
  border-top: 1px solid #ece9e2;
  display: flex;
  justify-content: flex-end;
}

.btn-vote {
  border: none;
  background: var(--vb-accent, #0f766e);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.55rem 0.95rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.2s ease, opacity 0.2s ease;
}

.btn-vote:hover:not(:disabled) {
  background: var(--vb-accent-hover, #0d6b64);
}

.btn-vote:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
