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
      <BallotListSkeleton
        v-if="loading || showSkeleton"
        :hint="showSlowHint ? slowHint : ''"
      />

      <FriendlyLoadState
        v-else-if="error"
        tone="error"
        title="Couldn’t load your ballots"
        :message="error"
        action-label="Try again"
        @action="fetchElections"
      />

      <FriendlyLoadState
        v-else-if="!loading && !elections.length"
        tone="empty"
        title="No ballots open"
        message="When an election starts and you’re eligible, it will show up here."
        icon="far fa-calendar"
      />

      <div v-else-if="elections.length" class="ballot-list">
        <article
          v-for="election in elections"
          :key="election.uuid"
          class="ballot"
          :class="{ 'ballot--voted': election.has_voted }"
        >
          <!-- Voted: civic duty card -->
          <template v-if="election.has_voted">
            <div class="ballot-done">
              <div class="ballot-done__mark" aria-hidden="true">
                <i class="fas fa-check"></i>
              </div>

              <div class="ballot-done__body">
                <div class="ballot-done__head">
                  <p class="ballot-done__eyebrow">Ballot sealed</p>
                  <h2 class="ballot-done__title">{{ election.title }}</h2>
                </div>

                <p class="ballot-done__civic">
                  You’ve performed your civic duty.
                </p>
                <p class="ballot-done__sub">
                  Your vote is locked in. Sit back — nothing else is required from you for this election.
                </p>

                <p v-if="formatVotedAt(election.voted_at)" class="ballot-done__when">
                  Cast {{ formatVotedAt(election.voted_at) }}
                </p>

                <ElectionCountdown
                  :election="election"
                  variant="done"
                  label="Voting closes in"
                  :beep="false"
                />
              </div>

              <div class="ballot-done__footer">
                <button
                  type="button"
                  class="ballot-done__receipt"
                  @click="openConfirmation(election.uuid)"
                >
                  View receipt
                  <i class="fas fa-arrow-right" aria-hidden="true"></i>
                </button>
              </div>
            </div>
          </template>

          <!-- Open: ready to vote -->
          <template v-else>
            <div class="ballot-main">
              <div class="ballot-head">
                <h2>{{ election.title }}</h2>
                <span
                  v-if="election.status === 'open'"
                  class="ballot-live"
                  aria-label="Open for voting"
                >
                  <span class="ballot-live-dot" aria-hidden="true"></span>
                </span>
              </div>

              <p v-if="election.description" class="ballot-desc">{{ election.description }}</p>

              <ElectionCountdown :election="election" />
            </div>

            <div class="ballot-footer">
              <button
                type="button"
                class="ballot-action"
                :class="{ 'is-launching': launchingId === election.uuid }"
                :disabled="!canVote(election) || !!launchingId"
                @click="startVoting(election.uuid)"
              >
                <span class="ballot-action-label">{{ voteLabel(election) }}</span>
                <span class="ballot-action-arrow" aria-hidden="true">
                  <i class="fas fa-arrow-right"></i>
                </span>
              </button>
            </div>
          </template>
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
import { useFriendlyLoad } from '@/composables/useFriendlyLoad'
import ElectionCountdown from '@/components/student/ElectionCountdown.vue'
import BallotListSkeleton from '@/components/student/BallotListSkeleton.vue'
import FriendlyLoadState from '@/components/student/FriendlyLoadState.vue'

const router = useRouter()
const authStore = useAuthStore()

const elections = ref([])
const launchingId = ref('')
const {
  loading,
  showSkeleton,
  showSlowHint,
  slowHint,
  error,
  begin,
  succeed,
  fail,
} = useFriendlyLoad({ subject: 'your ballots', skeletonDelayMs: 0 })

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
  ].filter(Boolean)
})

function canVote(election) {
  if (election.has_voted) return false
  if (election.status !== 'open') return false
  const timing = getElectionTiming(election)
  return timing.phase === 'open' && !timing.expired
}

function voteLabel(election) {
  if (!canVote(election)) {
    const timing = getElectionTiming(election)
    if (timing.phase === 'upcoming') return 'Opens soon'
    return 'Closed'
  }
  return 'Vote'
}

function openConfirmation(electionUuid) {
  router.push(`/vote/${electionUuid}/confirmation`)
}

function formatVotedAt(value) {
  if (!value) return ''
  try {
    return new Date(value).toLocaleString('en-GB', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return ''
  }
}

async function fetchElections() {
  begin()
  try {
    const { data } = await votingApi.getEligibleElections()
    elections.value = data || []
    succeed()
  } catch (err) {
    console.error('Failed to fetch elections:', err)
    elections.value = []
    fail(err)
  }
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function startVoting(electionUuid) {
  const election = elections.value.find((e) => String(e.uuid) === String(electionUuid))
  if (election?.has_voted) {
    openConfirmation(electionUuid)
    return
  }
  if (launchingId.value) return
  launchingId.value = electionUuid

  const reduced = typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  try {
    await wait(reduced ? 30 : 180)
    await router.push(`/vote/${electionUuid}`)
  } catch (err) {
    launchingId.value = ''
    console.error('Failed to open ballot:', err)
  }
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

.ballot--voted {
  border-color: #d1fae5;
  background:
    linear-gradient(165deg, #f0fdf9 0%, #fff 42%, #fff 100%);
  box-shadow: 0 1px 0 rgba(16, 185, 129, 0.06);
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

.ballot-footer {
  padding: 0.65rem 0.85rem 0.85rem;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

/* Voted / civic duty card */
.ballot-done {
  display: grid;
  gap: 0.85rem;
  padding: 1.05rem 1rem 0.95rem;
}

.ballot-done__mark {
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: #0f766e;
  color: #fff;
  font-size: 0.78rem;
  box-shadow: 0 6px 16px rgba(15, 118, 110, 0.22);
  animation: done-pop 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.ballot-done__body {
  display: grid;
  gap: 0.4rem;
}

.ballot-done__eyebrow {
  margin: 0;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #0f766e;
}

.ballot-done__title {
  margin: 0;
  font-size: 1rem;
  font-weight: 750;
  letter-spacing: -0.025em;
  color: #1c1917;
  line-height: 1.25;
}

.ballot-done__civic {
  margin: 0.35rem 0 0;
  font-size: 0.92rem;
  font-weight: 650;
  letter-spacing: -0.02em;
  color: #134e4a;
  line-height: 1.35;
}

.ballot-done__sub {
  margin: 0;
  font-size: 0.76rem;
  line-height: 1.5;
  color: #78716c;
  max-width: 28rem;
}

.ballot-done__when {
  margin: 0.15rem 0 0.2rem;
  font-size: 0.68rem;
  font-weight: 500;
  color: #a8a29e;
}

.ballot-done__footer {
  display: flex;
  justify-content: flex-start;
  padding-top: 0.15rem;
}

.ballot-done__receipt {
  border: 1px solid #d1fae5;
  background: #fff;
  color: #0f766e;
  font-size: 0.74rem;
  font-weight: 650;
  padding: 0.5rem 0.85rem;
  border-radius: 999px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.15s ease;
}

.ballot-done__receipt i {
  font-size: 0.58rem;
}

.ballot-done__receipt:hover {
  background: #ecfdf5;
  border-color: #a7f3d0;
  transform: translateY(-1px);
}

@keyframes done-pop {
  from {
    opacity: 0;
    transform: scale(0.7);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .ballot-done__mark {
    animation: none;
  }
}

.ballot-action {
  border: none;
  background: var(--vb-accent, #0f766e);
  color: #fff;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  padding: 0.55rem 0.55rem 0.55rem 1rem;
  border-radius: 999px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  box-shadow: 0 4px 14px rgba(15, 118, 110, 0.2);
  transition: background 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease;
  position: relative;
  overflow: hidden;
}

.ballot-action::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    110deg,
    transparent 30%,
    rgba(255, 255, 255, 0.18) 48%,
    transparent 65%
  );
  transform: translateX(-120%);
  animation: vote-sheen 2.8s ease-in-out infinite;
  pointer-events: none;
}

.ballot-action-label {
  position: relative;
  z-index: 1;
}

.ballot-action-arrow {
  position: relative;
  z-index: 1;
  width: 1.7rem;
  height: 1.7rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ballot-action-arrow i {
  font-size: 0.65rem;
  animation: vote-nudge 1.4s ease-in-out infinite;
}

@keyframes vote-nudge {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(3px); }
}

@keyframes vote-sheen {
  0%, 55% { transform: translateX(-120%); }
  100% { transform: translateX(120%); }
}

.ballot-action:hover:not(:disabled) {
  background: var(--vb-accent-hover, #0d6b64);
  box-shadow: 0 6px 18px rgba(15, 118, 110, 0.28);
  transform: translateY(-1px);
}

.ballot-action:hover:not(:disabled) .ballot-action-arrow i {
  animation-duration: 0.7s;
}

.ballot-action:active:not(:disabled) {
  transform: translateY(0);
}

.ballot-action:disabled {
  opacity: 0.42;
  cursor: not-allowed;
  box-shadow: none;
}

.ballot-action:disabled::before,
.ballot-action:disabled .ballot-action-arrow i {
  animation: none;
}

.ballot-action.is-launching {
  opacity: 1;
  transform: scale(0.96);
  box-shadow: 0 2px 10px rgba(15, 118, 110, 0.18);
}

.ballot-action.is-launching .ballot-action-arrow i {
  animation: vote-launch 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes vote-launch {
  0% { transform: translateX(0); opacity: 1; }
  55% { transform: translateX(5px); opacity: 1; }
  100% { transform: translateX(10px); opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .ballot-action.is-launching .ballot-action-arrow i {
    animation: none;
  }
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
    padding: 0.9rem 0.9rem 0.65rem;
  }

  .ballot-done {
    padding: 0.95rem 0.9rem 0.9rem;
    gap: 0.75rem;
  }

  .ballot-done__civic {
    font-size: 0.88rem;
  }

  .ballot-footer {
    padding: 0 0.85rem 0.9rem;
  }

  .ballot-action {
    font-size: 0.76rem;
    padding: 0.5rem 0.5rem 0.5rem 0.95rem;
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

  .ballot--voted:hover {
    border-color: #a7f3d0;
    box-shadow: 0 8px 24px rgba(15, 118, 110, 0.08);
  }

  .ballot-main {
    padding: 1.2rem 1.25rem 0.85rem;
    gap: 0.65rem;
  }

  .ballot-done {
    padding: 1.25rem 1.25rem 1.15rem;
    gap: 0.95rem;
  }

  .ballot-done__title {
    font-size: 1.08rem;
  }

  .ballot-done__civic {
    font-size: 0.98rem;
  }

  .ballot-footer {
    padding: 0 1.25rem 1.15rem;
  }

  .ballot-head h2 {
    font-size: 1.05rem;
  }

  .ballot-desc {
    font-size: 0.78rem;
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
