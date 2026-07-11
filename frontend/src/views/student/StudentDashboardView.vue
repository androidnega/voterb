<template>
  <div class="student-home">
    <header class="page-intro">
      <p class="page-greeting">Your ballots</p>
      <h1 class="page-title">Hello, {{ firstName }}</h1>
      <div v-if="campusTags.length" class="page-tags">
        <span v-for="tag in campusTags" :key="tag">{{ tag }}</span>
      </div>
    </header>

    <section class="ballots">
      <div v-if="loading" class="state">
        <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
        <span>Loading ballots…</span>
      </div>

      <div v-else-if="error" class="state state--error">
        <p>{{ error }}</p>
        <button type="button" class="btn-ghost" @click="fetchElections">Try again</button>
      </div>

      <div v-else-if="!elections.length" class="state state--empty">
        <p class="state-title">No ballots open</p>
        <p class="state-copy">When an election starts and you're eligible, it will show up here.</p>
      </div>

      <div v-else class="ballot-list">
        <article
          v-for="election in elections"
          :key="election.uuid"
          class="ballot"
        >
          <div class="ballot-main">
            <div class="ballot-head">
              <h2>{{ election.title }}</h2>
              <span v-if="election.status === 'open'" class="ballot-live" aria-label="Open for voting">
                <span class="ballot-live-dot" aria-hidden="true"></span>
              </span>
            </div>

            <p v-if="election.description" class="ballot-desc">{{ election.description }}</p>

            <ElectionCountdown :election="election" />
          </div>

          <button
            type="button"
            class="ballot-action"
            :disabled="!canVote(election)"
            @click="startVoting(election.uuid)"
          >
            Cast vote
          </button>
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

const firstName = computed(() => {
  const name = displayUserName(authStore.user, 'Student').trim()
  if (!name) return 'there'
  return name.split(/\s+/)[0]
})

const campusTags = computed(() => {
  const user = authStore.user
  if (!user) return []

  return [
    user.department?.name,
    user.faculty?.name,
    user.level?.name,
  ].filter(Boolean)
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
    error.value = err.response?.data?.error || 'Could not load ballots.'
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
  gap: 1.5rem;
}

.page-intro {
  display: grid;
  gap: 0.35rem;
}

.page-greeting {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 500;
  color: #a8a29e;
}

.page-title {
  margin: 0;
  font-size: clamp(1.35rem, 5vw, 1.85rem);
  font-weight: 700;
  letter-spacing: -0.035em;
  color: #1c1917;
  line-height: 1.1;
}

.page-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.35rem;
}

.page-tags span {
  font-size: 0.64rem;
  font-weight: 500;
  color: #78716c;
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 999px;
  padding: 0.28rem 0.55rem;
  line-height: 1.2;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ballots {
  display: grid;
  gap: 0.75rem;
}

.state {
  display: grid;
  justify-items: center;
  gap: 0.5rem;
  padding: 2.5rem 1rem;
  text-align: center;
  color: #78716c;
  font-size: 0.78rem;
}

.state i {
  color: var(--vb-accent, #0f766e);
}

.state--error {
  color: #b91c1c;
}

.state-title {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 600;
  color: #1c1917;
}

.state-copy {
  margin: 0;
  max-width: 16rem;
  line-height: 1.5;
  color: #a8a29e;
}

.btn-ghost {
  border: 1px solid #e5e2db;
  background: #fff;
  color: #1c1917;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.45rem 0.8rem;
  border-radius: 0.45rem;
  cursor: pointer;
}

.ballot-list {
  display: grid;
  gap: 0.65rem;
}

.ballot {
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 0.85rem;
  overflow: hidden;
}

.ballot-main {
  padding: 1rem 1rem 0.9rem;
  display: grid;
  gap: 0.55rem;
}

.ballot-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.65rem;
}

.ballot-head h2 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #1c1917;
  line-height: 1.3;
}

.ballot-live {
  flex-shrink: 0;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0fdf9;
}

.ballot-live-dot {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 999px;
  background: var(--vb-accent, #0f766e);
  animation: live-pulse 2s ease-in-out infinite;
}

@keyframes live-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

.ballot-desc {
  margin: 0;
  font-size: 0.74rem;
  line-height: 1.5;
  color: #78716c;
}

.ballot-action {
  width: 100%;
  border: none;
  border-top: 1px solid #f0eeea;
  background: #fafaf9;
  color: #1c1917;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.82rem 1rem;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
}

.ballot-action:hover:not(:disabled) {
  background: var(--vb-accent, #0f766e);
  color: #fff;
}

.ballot-action:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Mobile: edge-tight, no clutter */
@media (max-width: 639px) {
  .student-home {
    gap: 1.25rem;
  }

  .page-tags span {
    font-size: 0.62rem;
    padding: 0.24rem 0.5rem;
  }

  .ballot {
    border-radius: 0.75rem;
  }

  .ballot-main {
    padding: 0.9rem 0.9rem 0.8rem;
  }

  .ballot-head h2 {
    font-size: 0.9rem;
  }
}

/* Desktop: focused column, airy spacing */
@media (min-width: 768px) {
  .student-home {
    gap: 2rem;
    max-width: 34rem;
    margin: 0 auto;
    width: 100%;
  }

  .page-intro {
    gap: 0.45rem;
  }

  .page-greeting {
    font-size: 0.78rem;
  }

  .page-tags {
    margin-top: 0.5rem;
    gap: 0.45rem;
  }

  .page-tags span {
    font-size: 0.68rem;
    padding: 0.32rem 0.65rem;
  }

  .ballot {
    border-radius: 1rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  .ballot:hover {
    border-color: #e0ddd6;
    box-shadow: 0 8px 24px rgba(28, 25, 23, 0.04);
  }

  .ballot-main {
    padding: 1.2rem 1.25rem 1rem;
    gap: 0.65rem;
  }

  .ballot-head h2 {
    font-size: 1.05rem;
  }

  .ballot-desc {
    font-size: 0.78rem;
  }

  .ballot-action {
    padding: 0.9rem 1.25rem;
    font-size: 0.8rem;
  }
}

@media (min-width: 1100px) {
  .student-home {
    max-width: 36rem;
  }

  .ballot-list {
    gap: 0.85rem;
  }
}
</style>
