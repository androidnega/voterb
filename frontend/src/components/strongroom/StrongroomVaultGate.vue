<template>
  <div class="vault-gate">
    <div class="vault-gate-bg">
      <div class="vault-scanline"></div>
      <div class="vault-grid"></div>
    </div>

    <div class="vault-gate-panel">
      <div class="vault-lock-ring" :class="{ authenticating }">
        <div class="vault-lock-inner">
          <i class="fas fa-shield-alt"></i>
        </div>
      </div>

      <p class="vault-classified">Restricted Access</p>
      <h1 class="vault-title">Strongroom Vault</h1>
      <p class="vault-subtitle">
        Step-up authentication required. All access is logged and monitored.
      </p>

      <div class="vault-warnings">
        <div class="vault-warning">
          <i class="fas fa-fingerprint"></i>
          <span>Biometric-grade session tracking enabled</span>
        </div>
        <div class="vault-warning">
          <i class="fas fa-eye"></i>
          <span>Seal reveals are audited with custody evidence</span>
        </div>
        <div class="vault-warning">
          <i class="fas fa-clock"></i>
          <span>Sessions auto-expire after 30 minutes</span>
        </div>
      </div>

      <form class="vault-form" @submit.prevent="submit">
        <label class="vault-label">Confirm your password to unlock</label>
        <div class="vault-input-wrap">
          <i class="fas fa-lock"></i>
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            class="vault-input"
            placeholder="Enter your account password"
            autocomplete="current-password"
            :disabled="authenticating"
            required
          />
          <button type="button" class="vault-toggle-pw" @click="showPassword = !showPassword">
            <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
          </button>
        </div>

        <p v-if="sessionError" class="vault-error">
          <i class="fas fa-exclamation-circle"></i>
          {{ sessionError }}
        </p>

        <button type="submit" class="vault-unlock-btn" :disabled="authenticating || !password">
          <i :class="authenticating ? 'fas fa-spinner fa-spin' : 'fas fa-unlock-alt'"></i>
          {{ authenticating ? 'Verifying identity…' : 'Unlock Vault' }}
        </button>
      </form>

      <p class="vault-footer-note">
        <i class="fas fa-info-circle"></i>
        Unauthorized access attempts are recorded and may trigger alerts.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  authenticating: { type: Boolean, default: false },
  sessionError: { type: String, default: '' },
})

const emit = defineEmits(['authenticate'])

const password = ref('')
const showPassword = ref(false)

const submit = () => {
  if (password.value) emit('authenticate', password.value)
}
</script>

<style scoped>
.vault-gate {
  position: relative;
  min-height: calc(100vh - 8rem);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  overflow: hidden;
}

.vault-gate-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(160deg, #0c1222 0%, #111827 40%, #0f172a 100%);
  border-radius: 1rem;
}

.vault-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(16, 185, 129, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16, 185, 129, 0.04) 1px, transparent 1px);
  background-size: 32px 32px;
}

.vault-scanline {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.08) 2px,
    rgba(0, 0, 0, 0.08) 4px
  );
  pointer-events: none;
  animation: scan 8s linear infinite;
}

@keyframes scan {
  0% { transform: translateY(0); }
  100% { transform: translateY(32px); }
}

.vault-gate-panel {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 28rem;
  padding: 2.5rem 2rem;
  border-radius: 1.25rem;
  background: rgba(15, 23, 42, 0.88);
  border: 1px solid rgba(16, 185, 129, 0.25);
  box-shadow:
    0 0 0 1px rgba(16, 185, 129, 0.08),
    0 25px 50px -12px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
  text-align: center;
}

.vault-lock-ring {
  width: 5rem;
  height: 5rem;
  margin: 0 auto 1.25rem;
  border-radius: 9999px;
  border: 2px solid rgba(16, 185, 129, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pulse-ring 2.5s ease-in-out infinite;
}

.vault-lock-ring.authenticating {
  animation: spin-ring 1.2s linear infinite;
  border-color: rgba(16, 185, 129, 0.6);
}

@keyframes pulse-ring {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.25); }
  50% { box-shadow: 0 0 0 12px rgba(16, 185, 129, 0); }
}

@keyframes spin-ring {
  to { transform: rotate(360deg); }
}

.vault-lock-inner {
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 9999px;
  background: rgba(16, 185, 129, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: #34d399;
}

.vault-classified {
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #f59e0b;
  margin-bottom: 0.35rem;
}

.vault-title {
  font-size: 1.65rem;
  font-weight: 800;
  color: #f8fafc;
  letter-spacing: -0.02em;
}

.vault-subtitle {
  font-size: 0.82rem;
  color: #94a3b8;
  margin-top: 0.5rem;
  line-height: 1.5;
}

.vault-warnings {
  margin: 1.5rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;
}

.vault-warning {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.72rem;
  color: #64748b;
  padding: 0.45rem 0.65rem;
  border-radius: 0.5rem;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(51, 65, 85, 0.5);
}

.vault-warning i {
  color: #10b981;
  width: 1rem;
  text-align: center;
}

.vault-form {
  text-align: left;
}

.vault-label {
  display: block;
  font-size: 0.72rem;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 0.45rem;
  letter-spacing: 0.03em;
}

.vault-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.vault-input-wrap > i.fa-lock {
  position: absolute;
  left: 0.85rem;
  color: #64748b;
  font-size: 0.85rem;
}

.vault-input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 2.35rem;
  border-radius: 0.65rem;
  border: 1px solid rgba(51, 65, 85, 0.8);
  background: rgba(15, 23, 42, 0.9);
  color: #f1f5f9;
  font-size: 0.88rem;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.vault-input:focus {
  border-color: rgba(16, 185, 129, 0.5);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.12);
}

.vault-toggle-pw {
  position: absolute;
  right: 0.65rem;
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.25rem;
}

.vault-error {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.65rem;
  font-size: 0.78rem;
  color: #f87171;
}

.vault-unlock-btn {
  width: 100%;
  margin-top: 1rem;
  padding: 0.8rem 1rem;
  border: none;
  border-radius: 0.65rem;
  background: linear-gradient(135deg, #059669, #10b981);
  color: #fff;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.vault-unlock-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.vault-unlock-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.vault-footer-note {
  margin-top: 1.25rem;
  font-size: 0.68rem;
  color: #475569;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
}
</style>
