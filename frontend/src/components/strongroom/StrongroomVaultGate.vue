<template>
  <div class="vault-gate">
    <div class="vault-gate-bg" aria-hidden="true">
      <div class="vault-grid"></div>
    </div>

    <div class="vault-panel" :class="{ 'is-busy': authenticating }">
      <div class="vault-panel__head">
        <div class="vault-seal" :class="sealClass" aria-hidden="true">
          <i :class="sealIcon"></i>
        </div>
        <div class="vault-panel__titles">
          <p class="vault-classified">Custody unlock</p>
          <h1 class="vault-title">Strongroom vault</h1>
        </div>
      </div>

      <p class="vault-subtitle">
        Three-party unlock: EC password → peer EC confirm → nominee key. Seal inspection never reveals ballot choices.
      </p>

      <ol class="vault-steps" aria-label="Unlock steps">
        <li :class="{ 'is-done': stepIndex >= 1, 'is-active': stepIndex === 0 }">EC password</li>
        <li :class="{ 'is-done': stepIndex >= 2, 'is-active': stepIndex === 1 }">Peer confirm</li>
        <li :class="{ 'is-done': stepIndex >= 3, 'is-active': stepIndex === 2 }">Nominee key</li>
      </ol>

      <!-- Step 1: password -->
      <form v-if="stepIndex === 0" class="vault-cli" @submit.prevent="onPassword">
        <label class="vault-field">
          <span>Your EC password</span>
          <input
            ref="inputRef"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            :disabled="authenticating"
            required
          />
        </label>
        <p v-if="displayError" class="vault-error">{{ displayError }}</p>
        <button type="submit" class="vault-unlock-btn" :disabled="authenticating || !password">
          <i class="fas fa-unlock-alt"></i>
          Start unlock
        </button>
      </form>

      <!-- Step 2: peer waiting / confirm -->
      <div v-else-if="stepIndex === 1" class="vault-wait">
        <p class="vault-wait__copy">
          <template v-if="isInitiator">
            Waiting for the peer EC to confirm this unlock from their Strongroom session.
          </template>
          <template v-else>
            The other committee EC started an unlock. Confirm to continue.
          </template>
        </p>
        <p v-if="displayError" class="vault-error">{{ displayError }}</p>
        <button
          v-if="!isInitiator"
          type="button"
          class="vault-unlock-btn"
          :disabled="authenticating"
          @click="$emit('peer-confirm')"
        >
          <i class="fas fa-check-double"></i>
          Confirm as peer EC
        </button>
        <button
          v-else
          type="button"
          class="vault-unlock-btn vault-unlock-btn--ghost"
          :disabled="authenticating"
          @click="$emit('refresh')"
        >
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': authenticating }"></i>
          Check status
        </button>
      </div>

      <!-- Step 3: nominee key -->
      <form v-else class="vault-cli" @submit.prevent="onNomineeKey">
        <p class="vault-wait__copy">
          Enter the timed custody key sent to
          <strong>{{ challenge?.nominee_name || 'the nominee' }}</strong>.
        </p>
        <label class="vault-field">
          <span>Nominee key</span>
          <input
            v-model="nomineeKey"
            type="text"
            class="vault-key"
            placeholder="XXXX-XXXX"
            autocomplete="one-time-code"
            spellcheck="false"
            :disabled="authenticating"
            required
          />
        </label>
        <p v-if="challenge?.nominee_key_expires_at" class="vault-meta-line">
          Key valid until {{ formatMoment(challenge.nominee_key_expires_at) }}
        </p>
        <p v-if="displayError" class="vault-error">{{ displayError }}</p>
        <button type="submit" class="vault-unlock-btn" :disabled="authenticating || !nomineeKey">
          <i class="fas fa-key"></i>
          Open Strongroom
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  authenticating: { type: Boolean, default: false },
  sessionError: { type: String, default: '' },
  challenge: { type: Object, default: null },
})

const emit = defineEmits(['authenticate', 'peer-confirm', 'nominee-key', 'refresh'])

const authStore = useAuthStore()
const password = ref('')
const nomineeKey = ref('')
const showPassword = ref(false)
const inputRef = ref(null)

const displayError = computed(() => props.sessionError)

const stepIndex = computed(() => {
  const status = props.challenge?.status
  if (status === 'awaiting_nominee') return 2
  if (status === 'awaiting_peer') return 1
  return 0
})

const isInitiator = computed(() => {
  const initUuid = props.challenge?.initiated_by?.uuid
  return !!initUuid && initUuid === authStore.user?.uuid
})

const sealClass = computed(() => {
  if (props.authenticating) return 'is-spin'
  if (displayError.value) return 'is-err'
  return ''
})

const sealIcon = computed(() => {
  if (props.authenticating) return 'fas fa-circle-notch fa-spin'
  if (displayError.value) return 'fas fa-times'
  return 'fas fa-shield-alt'
})

function formatMoment(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function onPassword() {
  emit('authenticate', password.value)
}

function onNomineeKey() {
  emit('nominee-key', nomineeKey.value.trim().toUpperCase())
}

watch(
  () => props.challenge?.status,
  async () => {
    await nextTick()
    if (stepIndex.value === 0) inputRef.value?.focus?.()
  },
)

onMounted(() => inputRef.value?.focus?.())
</script>

<style scoped>
.vault-gate {
  position: relative;
  min-height: min(70vh, 36rem);
  display: grid;
  place-items: center;
  padding: 1.5rem 1rem;
}

.vault-gate-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.vault-grid {
  position: absolute;
  inset: -20%;
  background:
    linear-gradient(rgba(61, 79, 68, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(61, 79, 68, 0.05) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: radial-gradient(circle at center, #000 30%, transparent 75%);
}

.vault-panel {
  position: relative;
  width: min(100%, 26rem);
  padding: 1.5rem 1.35rem 1.35rem;
  border-radius: 1.2rem;
  background: #fff;
  border: 1px solid rgba(61, 79, 68, 0.14);
  box-shadow: 0 24px 48px rgba(28, 28, 28, 0.08);
}

.vault-panel__head {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.vault-seal {
  width: 2.8rem;
  height: 2.8rem;
  border-radius: 0.85rem;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #3d4f44, #5a6f5f);
  color: #fff;
}

.vault-seal.is-err { background: #b91c1c; }
.vault-classified {
  margin: 0;
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #3d4f44;
}
.vault-title {
  margin: 0.15rem 0 0;
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}
.vault-subtitle {
  margin: 0.85rem 0 0;
  font-size: 0.82rem;
  line-height: 1.45;
  color: #8a8a8a;
}

.vault-steps {
  list-style: none;
  margin: 1rem 0 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.35rem;
}
.vault-steps li {
  text-align: center;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.45rem 0.25rem;
  border-radius: 0.55rem;
  background: #f7f6f2;
  color: #8a8a8a;
  border: 1px solid #ebeae4;
}
.vault-steps li.is-active {
  background: #e8efe6;
  color: #3d4f44;
  border-color: #c5d4bc;
}
.vault-steps li.is-done {
  background: #3d4f44;
  color: #fff;
  border-color: #3d4f44;
}

.vault-cli,
.vault-wait {
  margin-top: 1rem;
  display: grid;
  gap: 0.7rem;
}

.vault-field {
  display: grid;
  gap: 0.35rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: #8a8a8a;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.vault-field input {
  border: 1px solid #ebeae4;
  border-radius: 0.7rem;
  padding: 0.7rem 0.85rem;
  font-size: 0.92rem;
  font-weight: 600;
  color: #1c1c1c;
  text-transform: none;
  letter-spacing: normal;
}
.vault-key {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
}

.vault-wait__copy {
  margin: 0;
  font-size: 0.86rem;
  line-height: 1.45;
  color: #57534e;
}
.vault-meta-line {
  margin: 0;
  font-size: 0.74rem;
  color: #8a8a8a;
}
.vault-error {
  margin: 0;
  font-size: 0.8rem;
  color: #b91c1c;
}
.vault-unlock-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  border: none;
  border-radius: 0.75rem;
  padding: 0.75rem 1rem;
  background: #1c1c1c;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}
.vault-unlock-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.vault-unlock-btn--ghost {
  background: #f5f5f4;
  color: #57534e;
}
</style>
