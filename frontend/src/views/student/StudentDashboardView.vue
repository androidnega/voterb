<template>
  <div class="student-home">
    <section class="hero">
      <div class="hero-copy">
        <p class="hero-eyebrow">Student portal</p>
        <h1 class="hero-title">Hello, {{ studentName }}</h1>
        <p v-if="campusLine" class="hero-meta">{{ campusLine }}</p>
      </div>
      <p class="hero-note">
        Cast your vote securely while an election is open. Each ballot closes automatically when the timer runs out.
      </p>
    </section>

    <section class="elections-panel">
      <div class="panel-head">
        <div>
          <h2>Your ballots</h2>
          <p>{{ elections.length ? `${elections.length} active election${elections.length === 1 ? '' : 's'}` : 'Nothing open right now' }}</p>
        </div>
        <span v-if="!loading && elections.length" class="live-pill">
          <span class="live-dot" aria-hidden="true"></span>
          Live
        </span>
      </div>

      <div v-if="loading" class="state-card">
        <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
        <span>Loading your elections…</span>
      </div>

      <div v-else-if="error" class="state-card state-card--error">
        <p>{{ error }}</p>
        <button type="button" class="btn-secondary" @click="fetchElections">Try again</button>
      </div>

      <div v-else-if="!elections.length" class="state-card state-card--empty">
        <div class="empty-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <h3>No open elections</h3>
        <p>You're not eligible for any active ballots right now. Check back when voting opens.</p>
      </div>

      <div v-else class="election-grid">
        <article
          v-for="election in elections"
          :key="election.uuid"
          class="election-card"
        >
          <div class="election-card-top">
            <div class="election-card-copy">
              <h3>{{ election.title }}</h3>
              <p>{{ election.description || 'No description provided.' }}</p>
            </div>
            <span class="status-pill" :class="`status-pill--${election.status}`">
              {{ election.status }}
            </span>
          </div>

          <ElectionCountdown :election="election" />

          <div class="election-card-actions">
            <button
              type="button"
              class="btn-vote"
              :disabled="!canVote(election)"
              @click="startVoting(election.uuid)"
            >
              <span>Cast vote</span>
              <i class="fas fa-arrow-right" aria-hidden="true"></i>
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
import { getElectionTiming } from '@/composables/useCountdown'
import ElectionCountdown from '@/components/student/ElectionCountdown.vue'

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

function canVote(election) {
  if (election.status !== 'open') return false
  const timing = getElectionTiming(election)
  return timing.phase === 'open' && !timing.expired
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
  gap: 1rem;
}

.hero {
  background: #fdfcfa;
  border: 1px solid #e5e2db;
  border-radius: 1rem;
  padding: 1.2rem 1.15rem;
  box-shadow: 0 1px 2px rgba(28, 25, 23, 0.04);
}

.hero-eyebrow {
  margin: 0;
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #78716c;
}

.hero-title {
  margin: 0.35rem 0 0;
  font-size: clamp(1.25rem, 4vw, 1.65rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #1c1917;
  line-height: 1.15;
}

.hero-meta {
  margin: 0.35rem 0 0;
  font-size: 0.74rem;
  color: #78716c;
  line-height: 1.4;
}

.hero-note {
  margin: 0.85rem 0 0;
  padding-top: 0.85rem;
  border-top: 1px solid #ece9e2;
  font-size: 0.74rem;
  line-height: 1.55;
  color: #78716c;
}

.elections-panel {
  display: grid;
  gap: 0.85rem;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.panel-head h2 {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 700;
  color: #1c1917;
}

.panel-head p {
  margin: 0.2rem 0 0;
  font-size: 0.72rem;
  color: #78716c;
}

.live-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.3rem 0.55rem;
  border-radius: 999px;
  background: #ecfdf5;
  border: 1px solid #99f6e4;
  color: var(--vb-accent, #0f766e);
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  flex-shrink: 0;
}

.live-dot {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 999px;
  background: var(--vb-accent, #0f766e);
  animation: pulse 1.6s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.45; transform: scale(0.85); }
}

.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  min-height: 10rem;
  padding: 1.35rem;
  border-radius: 1rem;
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
  font-size: 0.92rem;
  font-weight: 700;
  color: #1c1917;
}

.state-card--empty p {
  margin: 0.25rem 0 0;
  max-width: 20rem;
  line-height: 1.5;
}

.empty-icon {
  width: 2.6rem;
  height: 2.6rem;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f4f1;
  color: #a8a29e;
}

.empty-icon svg {
  width: 1.25rem;
  height: 1.25rem;
}

.btn-secondary {
  margin-top: 0.25rem;
  border: none;
  background: #b91c1c;
  color: #fff;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.48rem 0.85rem;
  border-radius: 0.45rem;
  cursor: pointer;
}

.election-grid {
  display: grid;
  gap: 0.85rem;
}

.election-card {
  background: #fdfcfa;
  border: 1px solid #e5e2db;
  border-radius: 1rem;
  padding: 1rem 1rem 0.95rem;
  box-shadow: 0 1px 2px rgba(28, 25, 23, 0.04);
  display: flex;
  flex-direction: column;
}

.election-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.election-card-copy h3 {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 700;
  color: #1c1917;
  line-height: 1.3;
}

.election-card-copy p {
  margin: 0.35rem 0 0;
  font-size: 0.74rem;
  line-height: 1.5;
  color: #78716c;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.status-pill {
  flex-shrink: 0;
  font-size: 0.56rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0.28rem 0.5rem;
  border-radius: 999px;
  background: #f5f4f1;
  color: #78716c;
}

.status-pill--open {
  background: var(--vb-accent-soft, #ecfdf5);
  color: var(--vb-accent, #0f766e);
}

.election-card-actions {
  margin-top: 0.9rem;
  padding-top: 0.9rem;
  border-top: 1px solid #ece9e2;
}

.btn-vote {
  width: 100%;
  border: none;
  background: var(--vb-accent, #0f766e);
  color: #fff;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.68rem 1rem;
  border-radius: 0.6rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  transition: background 0.2s ease, opacity 0.2s ease, transform 0.15s ease;
}

.btn-vote:hover:not(:disabled) {
  background: var(--vb-accent-hover, #0d6b64);
}

.btn-vote:active:not(:disabled) {
  transform: translateY(1px);
}

.btn-vote:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@media (min-width: 640px) {
  .hero {
    padding: 1.35rem 1.4rem;
  }

  .election-card {
    padding: 1.15rem 1.15rem 1.05rem;
  }

  .btn-vote {
    width: auto;
    min-width: 9.5rem;
    margin-left: auto;
    display: flex;
  }

  .election-card-actions {
    display: flex;
    justify-content: flex-end;
  }
}

@media (min-width: 900px) {
  .student-home {
    gap: 1.25rem;
  }

  .hero {
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 1.25rem;
    align-items: end;
    padding: 1.5rem 1.55rem;
  }

  .hero-note {
    margin: 0;
    padding: 0;
    border-top: none;
    align-self: center;
  }

  .election-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }

  .election-card {
    min-height: 100%;
  }
}
</style>
