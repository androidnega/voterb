<template>
  <Teleport to="body">
    <Transition name="app-modal">
      <div
        v-if="visible && decision"
        class="dec-overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dec-action-title"
        @click.self="onDismiss"
        @keydown.esc.prevent="onDismiss"
      >
        <div class="dec-panel app-modal-panel" tabindex="-1" ref="panelRef">
          <div class="dec-glow" aria-hidden="true"></div>

          <header class="dec-header">
            <div class="dec-icon" aria-hidden="true">
              <i class="fas fa-balance-scale"></i>
            </div>
            <div class="dec-header__text">
              <p class="dec-eyebrow">Decision required</p>
              <h2 id="dec-action-title" class="dec-title">{{ decision.title }}</h2>
            </div>
            <button type="button" class="dec-close" aria-label="Close" @click="onDismiss">
              <i class="fas fa-times"></i>
            </button>
          </header>

          <p class="dec-summary">{{ decision.summary || decision.decision_type }}</p>

          <div class="dec-meta">
            <span>
              <i class="fas fa-user" aria-hidden="true"></i>
              {{ decision.proposed_by?.name || decision.proposed_by?.email || '—' }}
            </span>
            <span>
              <i class="fas fa-clock" aria-hidden="true"></i>
              {{ formatDate(decision.created_at) }}
            </span>
          </div>

          <div class="dec-progress" aria-label="Approval progress">
            <div class="dec-progress__bar">
              <span
                class="dec-progress__fill"
                :style="{ width: progressPct + '%' }"
              />
            </div>
            <p class="dec-progress__label">
              {{ decision.approvals_received || 0 }}/{{ decision.approvals_required || 2 }} approvals
            </p>
          </div>

          <ul v-if="decision.approvals?.length" class="dec-signers">
            <li v-for="a in decision.approvals" :key="a.uuid">
              <i class="fas fa-check-circle" aria-hidden="true"></i>
              {{ a.name || a.email }}
            </li>
          </ul>

          <label class="dec-note-label" for="dec-reject-reason">
            Rejection reason <span>(optional)</span>
          </label>
          <textarea
            id="dec-reject-reason"
            v-model="reason"
            class="dec-note"
            rows="2"
            placeholder="Only needed if you reject…"
            :disabled="busy"
          />

          <p v-if="error" class="dec-error">{{ error }}</p>

          <div class="dec-actions">
            <button
              type="button"
              class="dec-btn dec-btn--ghost"
              :disabled="busy"
              @click="onReject"
            >
              <i class="fas fa-times" aria-hidden="true"></i>
              Reject
            </button>
            <button
              type="button"
              class="dec-btn dec-btn--approve"
              :disabled="busy || alreadyApproved"
              @click="onApprove"
            >
              <i v-if="busyAction === 'approve'" class="fas fa-spinner fa-spin" aria-hidden="true"></i>
              <i v-else class="fas fa-check" aria-hidden="true"></i>
              {{ alreadyApproved ? 'You already approved' : 'Approve & enroll' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  decision: { type: Object, default: null },
  alreadyApproved: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
  busyAction: { type: String, default: '' },
  error: { type: String, default: '' },
})

const emit = defineEmits(['update:visible', 'dismiss', 'approve', 'reject'])

const panelRef = ref(null)
const reason = ref('')

const progressPct = computed(() => {
  const need = Number(props.decision?.approvals_required) || 2
  const got = Number(props.decision?.approvals_received) || 0
  return Math.min(100, Math.round((got / need) * 100))
})

const formatDate = (value) => {
  if (!value) return '—'
  return new Date(value).toLocaleString()
}

watch(
  () => props.visible,
  async (open) => {
    if (!open) return
    reason.value = ''
    await nextTick()
    panelRef.value?.focus?.()
  },
)

const onDismiss = () => {
  if (props.busy) return
  emit('update:visible', false)
  emit('dismiss')
}

const onApprove = () => emit('approve', props.decision)
const onReject = () => emit('reject', { decision: props.decision, reason: reason.value.trim() })
</script>

<style scoped>
.dec-overlay {
  position: fixed;
  inset: 0;
  z-index: 1210;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  background: rgba(28, 28, 28, 0.45);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.dec-panel {
  position: relative;
  width: min(100%, 28rem);
  overflow: hidden;
  padding: 1.55rem 1.55rem 1.4rem;
  border-radius: 1.35rem;
  background: #fff;
  border: 1px solid rgba(61, 79, 68, 0.12);
  box-shadow: 0 28px 64px rgba(28, 28, 28, 0.2);
  outline: none;
}

.dec-glow {
  position: absolute;
  inset: -35% -15% auto;
  height: 10rem;
  background: radial-gradient(ellipse at center, rgba(163, 177, 138, 0.22), transparent 70%);
  pointer-events: none;
}

.dec-header {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
}

.dec-icon {
  flex-shrink: 0;
  width: 2.75rem;
  height: 2.75rem;
  display: grid;
  place-items: center;
  border-radius: 0.9rem;
  background: linear-gradient(145deg, #3d4f44, #5a6f5f);
  color: #fff;
  font-size: 1rem;
}

.dec-header__text {
  flex: 1;
  min-width: 0;
}

.dec-eyebrow {
  margin: 0;
  font-size: 0.65rem;
  font-weight: 750;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--vb-accent, #3d4f44);
}

.dec-title {
  margin: 0.2rem 0 0;
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--vb-ink, #1c1c1c);
  line-height: 1.3;
}

.dec-close {
  appearance: none;
  border: none;
  background: transparent;
  color: var(--vb-muted, #8a8a8a);
  width: 2rem;
  height: 2rem;
  border-radius: 0.55rem;
  cursor: pointer;
}
.dec-close:hover {
  background: var(--vb-panel, #f7f6f2);
  color: var(--vb-ink, #1c1c1c);
}

.dec-summary {
  margin: 1rem 0 0;
  font-size: 0.88rem;
  line-height: 1.5;
  color: var(--vb-muted, #8a8a8a);
}

.dec-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem 1.1rem;
  margin-top: 0.75rem;
  font-size: 0.75rem;
  color: var(--vb-muted, #8a8a8a);
}
.dec-meta i {
  margin-right: 0.3rem;
  opacity: 0.7;
}

.dec-progress {
  margin-top: 1.15rem;
  padding: 0.85rem 0.95rem;
  border-radius: 0.9rem;
  background: var(--vb-panel, #f7f6f2);
  border: 1px solid var(--vb-line, #ebeae4);
}

.dec-progress__bar {
  height: 0.4rem;
  border-radius: 999px;
  background: rgba(61, 79, 68, 0.12);
  overflow: hidden;
}

.dec-progress__fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #3d4f44, #a3b18a);
  transition: width 0.35s ease;
}

.dec-progress__label {
  margin: 0.45rem 0 0;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--vb-accent, #3d4f44);
}

.dec-signers {
  list-style: none;
  margin: 0.75rem 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: #15803d;
}
.dec-signers i {
  margin-right: 0.35rem;
}

.dec-note-label {
  display: block;
  margin-top: 1.1rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--vb-ink, #1c1c1c);
}
.dec-note-label span {
  font-weight: 500;
  color: var(--vb-muted, #8a8a8a);
}

.dec-note {
  display: block;
  width: 100%;
  margin-top: 0.4rem;
  padding: 0.65rem 0.75rem;
  border-radius: 0.7rem;
  border: 1px solid var(--vb-line, #ebeae4);
  font: inherit;
  font-size: 0.85rem;
  resize: vertical;
  min-height: 2.75rem;
  background: #fff;
}
.dec-note:focus {
  outline: none;
  border-color: rgba(61, 79, 68, 0.45);
  box-shadow: 0 0 0 3px rgba(61, 79, 68, 0.1);
}

.dec-error {
  margin: 0.65rem 0 0;
  font-size: 0.8rem;
  color: #b91c1c;
}

.dec-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  justify-content: flex-end;
  margin-top: 1.2rem;
}

.dec-btn {
  appearance: none;
  border: none;
  cursor: pointer;
  font: inherit;
  font-size: 0.84rem;
  font-weight: 700;
  border-radius: 0.75rem;
  padding: 0.7rem 1.05rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: transform 0.15s ease, background 0.15s ease, opacity 0.15s ease;
}
.dec-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.dec-btn--ghost {
  background: transparent;
  color: #9a3412;
  border: 1px solid #fed7aa;
}
.dec-btn--ghost:hover:not(:disabled) {
  background: #fff7ed;
}

.dec-btn--approve {
  background: #16a34a;
  color: #fff;
  box-shadow: 0 10px 22px rgba(22, 163, 74, 0.28);
}
.dec-btn--approve:hover:not(:disabled) {
  background: #15803d;
  transform: translateY(-1px);
}

@media (max-width: 420px) {
  .dec-actions {
    flex-direction: column-reverse;
  }
  .dec-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
