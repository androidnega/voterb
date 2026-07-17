<template>
  <div class="confirm-page">
    <div class="confirm-bg" aria-hidden="true">
      <span
        v-for="orb in orbs"
        :key="orb.id"
        class="confirm-bg__orb"
        :style="orb.style"
      />
    </div>

    <div class="confirm-card">
      <img
        class="confirm-finger"
        src="/images/voted-finger.png"
        alt=""
        draggable="false"
        aria-hidden="true"
      />

      <h1 class="confirm-title">You’ve voted</h1>
      <p class="confirm-copy">Your ballot is sealed and counted.</p>

      <div v-if="confirmationCode !== '—'" class="confirm-code">
        <span class="confirm-code__label">Confirmation</span>
        <span class="confirm-code__value">{{ confirmationCode }}</span>
      </div>
      <p v-else class="confirm-copy confirm-copy--soft">
        Your vote for this election is already on record.
      </p>

      <router-link to="/student" class="confirm-btn">
        Back to my ballots
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const confirmationCode = ref('—')

const orbs = [
  { id: 1, style: { width: '200px', height: '200px', top: '10%', left: '6%', animationDuration: '18s', animationDelay: '0s' } },
  { id: 2, style: { width: '260px', height: '260px', top: '55%', left: '14%', animationDuration: '22s', animationDelay: '2s' } },
  { id: 3, style: { width: '180px', height: '180px', top: '16%', left: '70%', animationDuration: '16s', animationDelay: '1s' } },
  { id: 4, style: { width: '240px', height: '240px', top: '58%', left: '66%', animationDuration: '24s', animationDelay: '3.5s' } },
  { id: 5, style: { width: '150px', height: '150px', top: '38%', left: '46%', animationDuration: '20s', animationDelay: '5s' } },
]

onMounted(() => {
  confirmationCode.value =
    route.query.code || sessionStorage.getItem(`vote_confirm:${route.params.uuid}`) || '—'
})
</script>

<style scoped>
.confirm-page {
  /* Break out of student-main max-width so the effect spans the full viewport */
  position: relative;
  left: 50%;
  right: 50%;
  width: 100vw;
  margin-left: -50vw;
  margin-right: -50vw;
  min-height: calc(100dvh - 3.5rem);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem 1rem 1.75rem;
  box-sizing: border-box;
  overflow: visible;
}

.confirm-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
  background: linear-gradient(to bottom right, #f8fafc, #ffffff, rgba(236, 253, 245, 0.55));
}

.confirm-bg__orb {
  position: absolute;
  border-radius: 999px;
  background: rgba(167, 243, 208, 0.28);
  animation: confirm-float ease-in-out infinite;
  will-change: transform, opacity;
}

.confirm-card {
  position: relative;
  z-index: 1;
  width: min(22rem, calc(100vw - 2rem));
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid #ebe8e2;
  border-radius: 1.25rem;
  padding: 1.35rem 1.25rem 1.35rem;
  text-align: center;
  box-shadow: none;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: grid;
  gap: 0.45rem;
  justify-items: center;
}

.confirm-finger {
  width: 4.25rem;
  height: auto;
  object-fit: contain;
  background: transparent;
  margin-bottom: 0.2rem;
  filter: brightness(1.18) contrast(1.08) saturate(1.12);
  animation: finger-in 0.55s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.confirm-title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #1c1917;
}

.confirm-copy {
  margin: 0 0 0.25rem;
  font-size: 0.86rem;
  line-height: 1.45;
  color: #78716c;
}

.confirm-copy--soft {
  margin-top: 0.35rem;
  margin-bottom: 0.5rem;
  max-width: 18rem;
}

.confirm-code {
  width: 100%;
  padding: 0.75rem 0.9rem;
  border-radius: 0.85rem;
  background: #fafaf9;
  border: 1px solid #f0eeea;
  display: grid;
  gap: 0.2rem;
}

.confirm-code__label {
  font-size: 0.68rem;
  font-weight: 650;
  color: #059669;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.confirm-code__value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.98rem;
  font-weight: 750;
  color: #1c1917;
  letter-spacing: 0.02em;
}

.confirm-btn {
  margin-top: 0.2rem;
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2.7rem;
  border-radius: 999px;
  background: #1c1917;
  color: #fff;
  font-size: 0.88rem;
  font-weight: 700;
  text-decoration: none;
}

@keyframes confirm-float {
  0%, 100% {
    transform: translate3d(0, 0, 0) scale(1);
    opacity: 0.45;
  }
  50% {
    transform: translate3d(0, -36px, 0) scale(1.14);
    opacity: 0.85;
  }
}

@keyframes finger-in {
  from {
    opacity: 0;
    transform: translateY(0.45rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 900px) {
  .confirm-page {
    min-height: calc(100dvh - 3.75rem);
  }
}

@media (prefers-reduced-motion: reduce) {
  .confirm-bg__orb,
  .confirm-finger {
    animation: none !important;
  }

  .confirm-bg__orb {
    opacity: 0.5;
  }
}
</style>
