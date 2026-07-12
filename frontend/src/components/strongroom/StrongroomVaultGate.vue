<template>
  <div class="vault-gate">
    <div class="vault-gate-bg" aria-hidden="true">
      <div class="vault-grid"></div>
    </div>

    <div class="vault-panel" :class="{ 'is-busy': phase !== 'idle' }">
      <div class="vault-panel__head">
        <div class="vault-seal" :class="sealClass" aria-hidden="true">
          <i :class="sealIcon"></i>
        </div>
        <div class="vault-panel__titles">
          <p class="vault-classified">Restricted Access</p>
          <h1 class="vault-title">Strongroom Vault</h1>
        </div>
      </div>

      <p class="vault-subtitle">
        Step-up authentication required. All access is logged and monitored.
      </p>

      <div class="vault-meta">
        <span><i class="fas fa-fingerprint"></i> Session tracked</span>
        <span><i class="fas fa-eye"></i> Audited reveals</span>
        <span><i class="fas fa-clock"></i> 30m TTL</span>
      </div>

      <form v-if="phase === 'idle' || phase === 'error'" class="vault-cli" @submit.prevent="submit">
        <div class="vault-cli__bar">
          <span class="vault-cli__prompt">vault@strongroom</span>
          <span class="vault-cli__sep">:~$</span>
          <span class="vault-cli__cmd">unlock</span>
          <input
            ref="inputRef"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            class="vault-cli__input"
            placeholder="••••••••••••"
            autocomplete="current-password"
            spellcheck="false"
            :disabled="authenticating"
            required
            @keydown.enter.prevent="submit"
          />
          <button type="button" class="vault-cli__eye" :aria-label="showPassword ? 'Hide' : 'Show'" @click="showPassword = !showPassword">
            <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
          </button>
        </div>

        <p v-if="displayError" class="vault-error">
          <span class="vault-cli__prompt">err</span>
          <span>{{ displayError }}</span>
        </p>

        <button type="submit" class="vault-unlock-btn" :disabled="authenticating || !password">
          <i class="fas fa-unlock-alt"></i>
          Unlock Vault
        </button>
      </form>

      <div v-else class="vault-authlog" aria-live="polite">
        <div class="vault-authlog__scroll">
          <p
            v-for="(line, idx) in logLines"
            :key="`${line.text}-${idx}`"
            class="vault-authlog__line"
            :class="line.tone"
          >
            <span class="vault-authlog__ts">{{ line.ts }}</span>
            <span class="vault-authlog__tag">{{ line.tag }}</span>
            <span>{{ line.text }}</span>
            <span v-if="line.pending" class="vault-authlog__cursor">█</span>
          </p>
        </div>
        <div class="vault-progress">
          <div class="vault-progress__fill" :style="{ width: `${progress}%` }"></div>
        </div>
      </div>

      <p class="vault-footer-note">
        Unauthorized access attempts are recorded and may trigger alerts.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'

const props = defineProps({
  authenticating: { type: Boolean, default: false },
  sessionError: { type: String, default: '' },
})

const emit = defineEmits(['authenticate'])

const password = ref('')
const showPassword = ref(false)
const inputRef = ref(null)
const phase = ref('idle') // idle | verifying | error | success
const logLines = ref([])
const progress = ref(0)
const localError = ref('')
let stepTimers = []

const displayError = computed(() => localError.value || props.sessionError)

const sealClass = computed(() => {
  if (phase.value === 'verifying') return 'is-spin'
  if (phase.value === 'success') return 'is-ok'
  if (phase.value === 'error') return 'is-err'
  return ''
})

const sealIcon = computed(() => {
  if (phase.value === 'success') return 'fas fa-check'
  if (phase.value === 'error') return 'fas fa-times'
  if (phase.value === 'verifying') return 'fas fa-circle-notch fa-spin'
  return 'fas fa-shield-alt'
})

const clearTimers = () => {
  stepTimers.forEach((id) => clearTimeout(id))
  stepTimers = []
}

const stamp = () => {
  const d = new Date()
  return d.toLocaleTimeString('en-GB', { hour12: false })
}

const pushLine = (tag, text, tone = '', pending = false) => {
  logLines.value = logLines.value.map((l) => ({ ...l, pending: false }))
  logLines.value.push({ ts: stamp(), tag, text, tone, pending })
}

const runVerifySequence = () => {
  clearTimers()
  phase.value = 'verifying'
  progress.value = 8
  logLines.value = []
  localError.value = ''

  const steps = [
    { at: 0, tag: 'auth', text: 'Receiving credentials…', progress: 12 },
    { at: 450, tag: 'hash', text: 'Deriving challenge response…', progress: 28 },
    { at: 950, tag: 'seal', text: 'Checking vault seal integrity…', progress: 48 },
    { at: 1450, tag: 'audit', text: 'Writing custody evidence trail…', progress: 68 },
    { at: 1900, tag: 'sess', text: 'Opening time-boxed vault session…', progress: 86, pending: true },
  ]

  steps.forEach((step) => {
    const id = setTimeout(() => {
      pushLine(step.tag, step.text, '', step.pending)
      progress.value = step.progress
    }, step.at)
    stepTimers.push(id)
  })

  const emitId = setTimeout(() => {
    emit('authenticate', password.value)
  }, 2100)
  stepTimers.push(emitId)
}

const submit = () => {
  if (!password.value || props.authenticating || phase.value === 'verifying') return
  runVerifySequence()
}

watch(
  () => [props.authenticating, props.sessionError],
  ([busy, err], [wasBusy]) => {
    if (phase.value !== 'verifying' && phase.value !== 'success') return

    if (wasBusy && !busy) {
      clearTimers()
      if (err) {
        phase.value = 'error'
        progress.value = 100
        pushLine('fail', err, 'is-fail')
        localError.value = err
        const id = setTimeout(() => {
          phase.value = 'idle'
          logLines.value = []
          progress.value = 0
          nextTick(() => inputRef.value?.focus())
        }, 1600)
        stepTimers.push(id)
      } else {
        phase.value = 'success'
        progress.value = 100
        pushLine('ok', 'Seal verified. Vault unlocked.', 'is-ok')
      }
    }
  },
)

onMounted(() => {
  nextTick(() => inputRef.value?.focus())
})
</script>

<style scoped>
.vault-gate {
  position: relative;
  min-height: calc(100vh - 10rem);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem 1rem;
  overflow: hidden;
}

.vault-gate-bg {
  position: absolute;
  inset: 0;
  border-radius: 1.25rem;
  background: linear-gradient(160deg, #0b1220 0%, #111827 55%, #0f172a 100%);
}

.vault-grid {
  position: absolute;
  inset: 0;
  opacity: 0.55;
  background-image:
    linear-gradient(rgba(16, 185, 129, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16, 185, 129, 0.045) 1px, transparent 1px);
  background-size: 28px 28px;
}

.vault-panel {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 32rem;
  padding: 1.15rem 1.25rem 1rem;
  border-radius: 1rem;
  background: rgba(15, 23, 42, 0.92);
  border: 1px solid rgba(16, 185, 129, 0.22);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35);
}

.vault-panel__head {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.vault-seal {
  width: 2.65rem;
  height: 2.65rem;
  border-radius: 9999px;
  border: 1.5px solid rgba(16, 185, 129, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #34d399;
  background: rgba(16, 185, 129, 0.1);
  flex-shrink: 0;
  font-size: 1rem;
  transition: border-color 0.2s ease, background 0.2s ease, color 0.2s ease;
}

.vault-seal.is-spin {
  border-color: rgba(52, 211, 153, 0.7);
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.12);
}

.vault-seal.is-ok {
  border-color: rgba(52, 211, 153, 0.85);
  background: rgba(16, 185, 129, 0.22);
  color: #6ee7b7;
}

.vault-seal.is-err {
  border-color: rgba(248, 113, 113, 0.7);
  background: rgba(127, 29, 29, 0.35);
  color: #fca5a5;
}

.vault-classified {
  margin: 0;
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #f59e0b;
}

.vault-title {
  margin: 0.1rem 0 0;
  font-size: 1.15rem;
  font-weight: 800;
  color: #f8fafc;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.vault-subtitle {
  margin: 0.65rem 0 0;
  font-size: 0.78rem;
  color: #94a3b8;
  line-height: 1.45;
}

.vault-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem 0.85rem;
  margin-top: 0.7rem;
  font-size: 0.68rem;
  color: #64748b;
}

.vault-meta i {
  color: #10b981;
  margin-right: 0.25rem;
}

.vault-cli {
  margin-top: 0.9rem;
}

.vault-cli__bar {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 0.65rem;
  border-radius: 0.45rem;
  background: #020617;
  border: 1px solid rgba(51, 65, 85, 0.9);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.78rem;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.vault-cli__prompt {
  color: #34d399;
  font-weight: 700;
  flex-shrink: 0;
}

.vault-cli__sep {
  color: #64748b;
  flex-shrink: 0;
}

.vault-cli__cmd {
  color: #93c5fd;
  flex-shrink: 0;
}

.vault-cli__input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  color: #e2e8f0;
  font: inherit;
  letter-spacing: 0.08em;
  caret-color: #34d399;
}

.vault-cli__input::placeholder {
  color: #475569;
  letter-spacing: 0.12em;
}

.vault-cli__eye {
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  padding: 0.15rem;
  flex-shrink: 0;
}

.vault-cli__eye:hover {
  color: #94a3b8;
}

.vault-error {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin: 0.55rem 0 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.72rem;
  color: #f87171;
}

.vault-unlock-btn {
  margin-top: 0.75rem;
  width: 100%;
  padding: 0.65rem 0.9rem;
  border: none;
  border-radius: 0.55rem;
  background: linear-gradient(135deg, #059669, #10b981);
  color: #fff;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
}

.vault-unlock-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.vault-authlog {
  margin-top: 0.85rem;
  border-radius: 0.45rem;
  background: #020617;
  border: 1px solid rgba(51, 65, 85, 0.9);
  overflow: hidden;
}

.vault-authlog__scroll {
  min-height: 7.5rem;
  max-height: 8.5rem;
  padding: 0.65rem 0.75rem;
  overflow-y: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.72rem;
  line-height: 1.55;
}

.vault-authlog__line {
  margin: 0 0 0.2rem;
  color: #cbd5e1;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.vault-authlog__ts {
  color: #475569;
}

.vault-authlog__tag {
  color: #34d399;
  font-weight: 700;
  text-transform: uppercase;
  min-width: 2.4rem;
}

.vault-authlog__line.is-ok .vault-authlog__tag {
  color: #6ee7b7;
}

.vault-authlog__line.is-fail {
  color: #fca5a5;
}

.vault-authlog__line.is-fail .vault-authlog__tag {
  color: #f87171;
}

.vault-authlog__cursor {
  color: #34d399;
  animation: blink 0.9s steps(1) infinite;
}

@keyframes blink {
  50% { opacity: 0; }
}

.vault-progress {
  height: 2px;
  background: rgba(51, 65, 85, 0.8);
}

.vault-progress__fill {
  height: 100%;
  background: linear-gradient(90deg, #059669, #34d399);
  transition: width 0.35s ease;
}

.vault-footer-note {
  margin: 0.75rem 0 0;
  font-size: 0.65rem;
  color: #475569;
  text-align: center;
}
</style>
