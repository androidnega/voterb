<template>
  <div class="confirm-page">
    <div class="confirm-card">
      <div class="ink-mark" aria-hidden="true">
        <svg class="ink-mark__print" viewBox="0 0 120 140" fill="none">
          <!-- Thumbprint ridges -->
          <ellipse cx="60" cy="62" rx="34" ry="42" fill="#1c1917" opacity="0.92" />
          <path
            d="M40 38c8-10 32-10 40 0M36 50c12-12 36-12 48 0M34 62c14-12 38-12 52 0M34 74c14-11 38-11 52 0M36 86c12-10 36-10 48 0M42 98c8-8 28-8 36 0"
            stroke="#f5f5f4"
            stroke-width="2.2"
            stroke-linecap="round"
            opacity="0.55"
          />
          <path
            d="M46 44c6-6 22-6 28 0M44 56c8-7 24-7 32 0M42 68c9-7 27-7 36 0M42 80c9-6 27-6 36 0M46 92c6-5 22-5 28 0"
            stroke="#a8a29e"
            stroke-width="1.4"
            stroke-linecap="round"
            opacity="0.45"
          />
        </svg>

        <svg class="ink-mark__hand" viewBox="0 0 90 110" fill="none">
          <!-- Palm -->
          <path
            d="M28 58c0-10 6-16 14-16 4 0 7 1 10 3V28c0-5 4-9 9-9s9 4 9 9v22c2-2 5-3 8-3 5 0 9 4 9 9v8c0 18-12 32-30 32H40c-10 0-18-8-18-18V58z"
            fill="#f5d0b5"
          />
          <!-- Little finger (inked tip) -->
          <path
            d="M22 52c-1-10 4-18 11-18 5 0 8 4 8 9v22c-7 1-14 4-19 10V52z"
            fill="#efc09a"
          />
          <ellipse cx="26" cy="38" rx="7.5" ry="9" fill="#1c1917" />
          <path
            d="M22 34c3-3 8-3 11 0M21 39c3-2 9-2 12 0M22 44c3-2 8-2 10 0"
            stroke="#57534e"
            stroke-width="1"
            stroke-linecap="round"
            opacity="0.55"
          />
          <!-- Ink blot near pinky -->
          <circle cx="18" cy="30" r="3.2" fill="#1c1917" opacity="0.35" />
          <circle cx="14" cy="36" r="2" fill="#1c1917" opacity="0.22" />
        </svg>
      </div>

      <p class="confirm-eyebrow">Vote recorded</p>
      <h1 class="confirm-title">You’ve voted</h1>
      <p class="confirm-copy">
        Your ballot is sealed and counted. Keep your confirmation code for verification.
      </p>

      <div class="confirm-code">
        <span class="confirm-code__label">Confirmation code</span>
        <span class="confirm-code__value">{{ confirmationCode }}</span>
      </div>

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

onMounted(() => {
  confirmationCode.value = route.query.code || sessionStorage.getItem(`vote_confirm:${route.params.uuid}`) || '—'
})
</script>

<style scoped>
.confirm-page {
  width: min(26rem, 100%);
  margin: 0 auto;
  padding: 0.5rem 0 2rem;
}

.confirm-card {
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 1.35rem;
  padding: 1.75rem 1.35rem 1.5rem;
  text-align: center;
  box-shadow: 0 8px 24px rgba(28, 25, 23, 0.04);
  display: grid;
  gap: 0.55rem;
  justify-items: center;
}

.ink-mark {
  position: relative;
  width: 8.5rem;
  height: 8.5rem;
  margin-bottom: 0.35rem;
  animation: ink-rise 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.ink-mark__print {
  width: 5.6rem;
  height: auto;
  filter: drop-shadow(0 10px 18px rgba(28, 25, 23, 0.18));
  animation: print-stamp 0.55s cubic-bezier(0.22, 1, 0.36, 1) 0.15s both;
}

.ink-mark__hand {
  position: absolute;
  right: -0.15rem;
  bottom: -0.2rem;
  width: 3.6rem;
  height: auto;
  filter: drop-shadow(0 6px 10px rgba(28, 25, 23, 0.12));
  animation: hand-in 0.65s cubic-bezier(0.16, 1, 0.3, 1) 0.28s both;
}

.confirm-eyebrow {
  margin: 0;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #0f766e;
}

.confirm-title {
  margin: 0;
  font-size: 1.55rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #1c1917;
}

.confirm-copy {
  margin: 0;
  max-width: 18rem;
  font-size: 0.88rem;
  line-height: 1.5;
  color: #78716c;
}

.confirm-code {
  margin-top: 0.45rem;
  width: 100%;
  padding: 0.85rem 1rem;
  border-radius: 0.95rem;
  background: #fafaf9;
  border: 1px solid #ebe8e2;
  display: grid;
  gap: 0.25rem;
}

.confirm-code__label {
  font-size: 0.7rem;
  font-weight: 650;
  color: #a8a29e;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.confirm-code__value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 1.05rem;
  font-weight: 750;
  color: #1c1917;
  letter-spacing: 0.02em;
}

.confirm-btn {
  margin-top: 0.55rem;
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2.85rem;
  border-radius: 999px;
  background: #1c1917;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 700;
  text-decoration: none;
}

@keyframes ink-rise {
  from { opacity: 0; transform: translateY(0.6rem); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes print-stamp {
  0% { opacity: 0; transform: scale(1.25) rotate(-8deg); }
  100% { opacity: 1; transform: scale(1) rotate(0deg); }
}

@keyframes hand-in {
  from { opacity: 0; transform: translate(0.5rem, 0.4rem) rotate(8deg); }
  to { opacity: 1; transform: translate(0, 0) rotate(0deg); }
}

@media (prefers-reduced-motion: reduce) {
  .ink-mark,
  .ink-mark__print,
  .ink-mark__hand {
    animation: none;
  }
}
</style>
