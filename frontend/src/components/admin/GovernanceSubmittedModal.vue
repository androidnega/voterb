<template>
  <Teleport to="body">
    <Transition name="app-modal">
      <div
        v-if="visible"
        class="gov-submit-overlay"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        @click.self="onDismiss"
        @keydown.esc.prevent="onDismiss"
      >
        <div
          class="gov-submit-panel app-modal-panel"
          :class="`is-${state}`"
          tabindex="-1"
          ref="panelRef"
        >
          <div class="gov-submit-glow" aria-hidden="true"></div>

          <div v-if="state === 'enrolled'" class="fp-seal" aria-hidden="true">
            <svg class="fp-seal__svg" viewBox="0 0 64 64" fill="none">
              <circle class="fp-seal__ring" cx="32" cy="32" r="28" />
              <g class="fp-seal__print" stroke="currentColor" stroke-linecap="round" fill="none">
                <path d="M32 18c-6.2 0-11 5-11 11.5 0 8.2 4.2 14.5 8.2 20.2" stroke-width="2.2" />
                <path d="M32 18c6.2 0 11 5 11 11.5 0 8.2-4.2 14.5-8.2 20.2" stroke-width="2.2" />
                <path d="M32 22.5c-3.8 0-6.8 3.2-6.8 7.2 0 5.8 2.8 10.6 5.6 15.2" stroke-width="1.8" />
                <path d="M32 22.5c3.8 0 6.8 3.2 6.8 7.2 0 5.8-2.8 10.6-5.6 15.2" stroke-width="1.8" />
                <path d="M32 27c-1.8 0-3.2 1.6-3.2 3.6 0 3.4 1.4 6.4 3.2 9.4" stroke-width="1.6" />
                <path d="M32 27c1.8 0 3.2 1.6 3.2 3.6 0 3.4-1.4 6.4-3.2 9.4" stroke-width="1.6" />
                <path d="M26 20.5c-2.4 1.8-4 4.6-4 7.8 0 4.6 1.6 8.6 3.6 12.4" stroke-width="1.5" opacity="0.75" />
                <path d="M38 20.5c2.4 1.8 4 4.6 4 7.8 0 4.6-1.6 8.6-3.6 12.4" stroke-width="1.5" opacity="0.75" />
              </g>
              <line class="fp-seal__scan" x1="14" y1="20" x2="50" y2="20" />
            </svg>
            <span class="fp-seal__check">
              <i class="fas fa-check"></i>
            </span>
          </div>

          <div v-else class="gov-submit-icon" aria-hidden="true">
            <span class="gov-submit-icon__ring"></span>
            <i :class="iconClass"></i>
          </div>

          <p class="gov-submit-eyebrow">{{ eyebrow }}</p>
          <h2 :id="titleId" class="gov-submit-title">{{ heading }}</h2>

          <p class="gov-submit-body">
            {{ message }}
          </p>

          <div v-if="state === 'pending'" class="gov-submit-progress" aria-label="Approval progress">
            <div class="gov-submit-step is-done">
              <span class="gov-submit-dot"><i class="fas fa-check"></i></span>
              <span>You approved</span>
            </div>
            <div class="gov-submit-rail" aria-hidden="true"></div>
            <div class="gov-submit-step is-wait">
              <span class="gov-submit-dot">2</span>
              <span>Peer approval</span>
            </div>
          </div>

          <div v-else-if="state === 'enrolled'" class="gov-submit-progress is-complete" aria-label="Approved">
            <div class="gov-submit-step is-done">
              <span class="gov-submit-dot"><i class="fas fa-fingerprint"></i></span>
              <span>Approved</span>
            </div>
            <div class="gov-submit-rail is-complete" aria-hidden="true"></div>
            <div class="gov-submit-step is-done">
              <span class="gov-submit-dot"><i class="fas fa-check"></i></span>
              <span>Enrolled</span>
            </div>
          </div>

          <div class="gov-submit-actions">
            <button type="button" class="gov-submit-secondary" @click="onDismiss">
              {{ state === 'enrolled' ? 'Close' : 'Stay here' }}
            </button>
            <button
              v-if="state === 'pending'"
              type="button"
              class="gov-submit-primary"
              @click="onReview"
            >
              Review approvals
              <i class="fas fa-arrow-right" aria-hidden="true"></i>
            </button>
            <button
              v-else-if="state === 'enrolled'"
              type="button"
              class="gov-submit-primary is-green"
              @click="onDismiss"
            >
              Done
              <i class="fas fa-check" aria-hidden="true"></i>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  visible: { type: Boolean, default: false },
  /** pending | enrolled | rejected */
  state: { type: String, default: 'pending' },
  message: {
    type: String,
    default:
      'Submitted for approval. Your approval is recorded; the other institutional EC member must also approve before enrollment.',
  },
  approvalsPath: { type: String, default: '/approvals' },
})

const emit = defineEmits(['update:visible', 'dismiss', 'review'])

const router = useRouter()
const panelRef = ref(null)
const titleId = 'gov-submit-title'

const eyebrow = computed(() => {
  if (props.state === 'enrolled') return 'Approved'
  if (props.state === 'rejected') return 'Rejected'
  return 'Approvals'
})

const heading = computed(() => {
  if (props.state === 'enrolled') return 'Decision enrolled'
  if (props.state === 'rejected') return 'Decision rejected'
  return 'Awaiting approval'
})

const iconClass = computed(() => {
  if (props.state === 'enrolled') return 'fas fa-check'
  if (props.state === 'rejected') return 'fas fa-times'
  return 'fas fa-user-check'
})

watch(
  () => props.visible,
  async (open) => {
    if (!open) return
    await nextTick()
    panelRef.value?.focus?.()
  },
)

const close = () => {
  emit('update:visible', false)
}

const onDismiss = () => {
  close()
  emit('dismiss')
}

const onReview = () => {
  close()
  emit('review')
  router.push(props.approvalsPath)
}
</script>

<style scoped>
.gov-submit-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  background: rgba(28, 28, 28, 0.42);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.gov-submit-panel {
  position: relative;
  width: min(100%, 26.5rem);
  overflow: hidden;
  padding: 2rem 1.75rem 1.55rem;
  border-radius: 1.35rem;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), #fff),
    #fff;
  border: 1px solid rgba(61, 79, 68, 0.12);
  box-shadow:
    0 28px 64px rgba(28, 28, 28, 0.18),
    0 1px 0 rgba(255, 255, 255, 0.7) inset;
  text-align: center;
  outline: none;
  transform-origin: center center;
  will-change: transform, opacity;
}

.gov-submit-panel.is-enrolled {
  border-color: rgba(22, 163, 74, 0.28);
}

.gov-submit-glow {
  position: absolute;
  inset: -40% -20% auto;
  height: 12rem;
  background: radial-gradient(ellipse at center, rgba(163, 177, 138, 0.28), transparent 68%);
  pointer-events: none;
}

.gov-submit-panel.is-enrolled .gov-submit-glow {
  background: radial-gradient(ellipse at center, rgba(34, 197, 94, 0.28), transparent 68%);
}

.fp-seal {
  position: relative;
  width: 5.25rem;
  height: 5.25rem;
  margin: 0 auto 1.15rem;
  display: grid;
  place-items: center;
  color: #15803d;
}

.fp-seal__svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.fp-seal__ring {
  stroke: rgba(22, 163, 74, 0.28);
  stroke-width: 1.5;
  fill: rgba(240, 253, 244, 0.9);
  animation: fp-ring 1.1s ease-out both;
}

.fp-seal__print path {
  stroke-dasharray: 80;
  stroke-dashoffset: 80;
  animation: fp-draw 1.05s ease-out forwards;
}

.fp-seal__print path:nth-child(1) { animation-delay: 0.05s; }
.fp-seal__print path:nth-child(2) { animation-delay: 0.1s; }
.fp-seal__print path:nth-child(3) { animation-delay: 0.15s; }
.fp-seal__print path:nth-child(4) { animation-delay: 0.2s; }
.fp-seal__print path:nth-child(5) { animation-delay: 0.25s; }
.fp-seal__print path:nth-child(6) { animation-delay: 0.3s; }
.fp-seal__print path:nth-child(7) { animation-delay: 0.35s; }
.fp-seal__print path:nth-child(8) { animation-delay: 0.4s; }

.fp-seal__scan {
  stroke: rgba(22, 163, 74, 0.55);
  stroke-width: 1.5;
  stroke-linecap: round;
  filter: drop-shadow(0 0 4px rgba(34, 197, 94, 0.45));
  animation: fp-scan 1.6s ease-in-out 0.35s infinite;
}

.fp-seal__check {
  position: absolute;
  right: -0.1rem;
  bottom: 0.05rem;
  width: 1.55rem;
  height: 1.55rem;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: #16a34a;
  color: #fff;
  font-size: 0.7rem;
  box-shadow: 0 6px 14px rgba(22, 163, 74, 0.35);
  animation: fp-check 0.45s ease-out 0.85s both;
}

.gov-submit-icon {
  position: relative;
  width: 3.6rem;
  height: 3.6rem;
  margin: 0 auto 1.1rem;
  display: grid;
  place-items: center;
  border-radius: 1.15rem;
  background: linear-gradient(145deg, #3d4f44, #5a6f5f);
  color: #fff;
  font-size: 1.2rem;
  box-shadow: 0 12px 28px rgba(61, 79, 68, 0.28);
}

.gov-submit-panel.is-rejected .gov-submit-icon {
  background: linear-gradient(145deg, #9a3412, #ea580c);
  box-shadow: 0 12px 28px rgba(194, 65, 12, 0.28);
}

.gov-submit-icon__ring {
  position: absolute;
  inset: -0.35rem;
  border-radius: 1.35rem;
  border: 1.5px solid rgba(61, 79, 68, 0.22);
  animation: gov-ring 2.4s ease-out infinite;
}

.gov-submit-eyebrow {
  margin: 0;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--vb-accent, #3d4f44);
}

.gov-submit-panel.is-enrolled .gov-submit-eyebrow {
  color: #15803d;
}

.gov-submit-title {
  margin: 0.35rem 0 0;
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--vb-ink, #1c1c1c);
}

.gov-submit-body {
  margin: 0.75rem auto 0;
  max-width: 22rem;
  font-size: 0.9rem;
  line-height: 1.55;
  color: var(--vb-muted, #8a8a8a);
}

.gov-submit-progress {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  margin: 1.35rem auto 0;
  padding: 0.85rem 1rem;
  max-width: 22rem;
  border-radius: 1rem;
  background: var(--vb-panel, #f7f6f2);
  border: 1px solid var(--vb-line, #ebeae4);
}

.gov-submit-progress.is-complete {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.gov-submit-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  min-width: 5.5rem;
  font-size: 0.72rem;
  font-weight: 650;
  color: var(--vb-muted, #8a8a8a);
}

.gov-submit-step.is-done {
  color: var(--vb-accent, #3d4f44);
}

.gov-submit-progress.is-complete .gov-submit-step.is-done {
  color: #15803d;
}

.gov-submit-dot {
  width: 1.7rem;
  height: 1.7rem;
  display: grid;
  place-items: center;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 800;
  background: #fff;
  border: 1.5px solid var(--vb-line, #ebeae4);
  color: var(--vb-muted, #8a8a8a);
}

.gov-submit-step.is-done .gov-submit-dot {
  background: var(--vb-accent, #3d4f44);
  border-color: var(--vb-accent, #3d4f44);
  color: #fff;
}

.gov-submit-progress.is-complete .gov-submit-step.is-done .gov-submit-dot {
  background: #16a34a;
  border-color: #16a34a;
}

.gov-submit-step.is-wait .gov-submit-dot {
  border-style: dashed;
  border-color: rgba(61, 79, 68, 0.35);
  animation: gov-pulse 1.8s ease-in-out infinite;
}

.gov-submit-rail {
  flex: 1;
  height: 2px;
  max-width: 3.5rem;
  margin-bottom: 1.1rem;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--vb-accent, #3d4f44), rgba(61, 79, 68, 0.2));
}

.gov-submit-rail.is-complete {
  background: linear-gradient(90deg, #16a34a, #86efac);
}

.gov-submit-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  justify-content: center;
  margin-top: 1.45rem;
}

.gov-submit-secondary,
.gov-submit-primary {
  appearance: none;
  border: none;
  cursor: pointer;
  font: inherit;
  font-size: 0.84rem;
  font-weight: 700;
  border-radius: 0.75rem;
  padding: 0.7rem 1.1rem;
  transition: transform 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.gov-submit-secondary {
  background: transparent;
  color: var(--vb-muted, #8a8a8a);
  border: 1px solid var(--vb-line, #ebeae4);
}

.gov-submit-secondary:hover {
  color: var(--vb-ink, #1c1c1c);
  background: var(--vb-panel, #f7f6f2);
}

.gov-submit-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: var(--vb-accent, #3d4f44);
  color: #fff;
  box-shadow: 0 10px 22px rgba(61, 79, 68, 0.22);
}

.gov-submit-primary.is-green {
  background: #16a34a;
  box-shadow: 0 10px 22px rgba(22, 163, 74, 0.28);
}

.gov-submit-primary:hover {
  background: var(--vb-accent-hover, #334239);
  transform: translateY(-1px);
}

.gov-submit-primary.is-green:hover {
  background: #15803d;
}

.gov-submit-primary:active,
.gov-submit-secondary:active {
  transform: translateY(0);
}

@keyframes fp-draw {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes fp-scan {
  0% {
    transform: translateY(0);
    opacity: 0;
  }
  15% {
    opacity: 1;
  }
  85% {
    opacity: 1;
  }
  100% {
    transform: translateY(24px);
    opacity: 0;
  }
}

@keyframes fp-ring {
  from {
    transform: scale(0.86);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes fp-check {
  from {
    transform: scale(0.4);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes gov-ring {
  0% {
    transform: scale(0.92);
    opacity: 0.7;
  }
  70% {
    transform: scale(1.12);
    opacity: 0;
  }
  100% {
    transform: scale(1.12);
    opacity: 0;
  }
}

@keyframes gov-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(61, 79, 68, 0.18);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(61, 79, 68, 0);
  }
}

@media (max-width: 420px) {
  .gov-submit-panel {
    padding: 1.65rem 1.2rem 1.35rem;
  }

  .gov-submit-actions {
    flex-direction: column-reverse;
  }

  .gov-submit-secondary,
  .gov-submit-primary {
    width: 100%;
    justify-content: center;
  }
}
</style>
