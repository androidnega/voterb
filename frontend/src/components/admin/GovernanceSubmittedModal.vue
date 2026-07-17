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

          <div class="gov-submit-icon" aria-hidden="true">
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

          <div v-else-if="state === 'enrolled'" class="gov-submit-progress is-complete" aria-label="Enrolled">
            <div class="gov-submit-step is-done">
              <span class="gov-submit-dot"><i class="fas fa-check"></i></span>
              <span>Both approved</span>
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
      'Submitted for dual Main EC approval. Your approval is recorded; the other institutional EC member must also approve before enrollment.',
  },
  approvalsPath: { type: String, default: '/approvals' },
})

const emit = defineEmits(['update:visible', 'dismiss', 'review'])

const router = useRouter()
const panelRef = ref(null)
const titleId = 'gov-submit-title'

const eyebrow = computed(() => {
  if (props.state === 'enrolled') return 'Enrolled'
  if (props.state === 'rejected') return 'Rejected'
  return 'Dual Main EC'
})

const heading = computed(() => {
  if (props.state === 'enrolled') return 'Decision enrolled'
  if (props.state === 'rejected') return 'Decision rejected'
  return 'Awaiting co-approval'
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

.gov-submit-panel.is-enrolled .gov-submit-icon {
  background: linear-gradient(145deg, #15803d, #22c55e);
  box-shadow: 0 12px 28px rgba(22, 163, 74, 0.32);
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

.gov-submit-panel.is-enrolled .gov-submit-icon__ring {
  border-color: rgba(22, 163, 74, 0.35);
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
