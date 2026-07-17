<template>
  <div ref="rootRef" class="profile-menu">
    <button
      type="button"
      class="profile-trigger"
      :aria-expanded="open"
      aria-haspopup="true"
      @click="toggle"
    >
      <span class="profile-avatar" aria-hidden="true">{{ initials }}</span>
      <span class="profile-trigger-text">
        <span class="profile-name">{{ displayName }}</span>
        <span v-if="indexDisplay" class="profile-index">{{ indexDisplay }}</span>
      </span>
      <i class="fas fa-chevron-down profile-chevron" :class="{ 'is-open': open }" aria-hidden="true"></i>
    </button>

    <Transition name="profile-drop">
      <div v-if="open" class="profile-panel" role="menu">
        <div class="profile-panel-head">
          <span class="profile-panel-avatar" aria-hidden="true">{{ initials }}</span>
          <div class="profile-panel-copy">
            <p class="profile-panel-name">{{ displayName }}</p>
            <p v-if="indexDisplay" class="profile-panel-index">{{ indexDisplay }}</p>
          </div>
        </div>

        <ul v-if="details.length" class="profile-details">
          <li v-for="item in details" :key="item.label">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </li>
        </ul>

        <button type="button" class="profile-signout" role="menuitem" @click="handleLogout">
          Sign out
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { displayUserName } from '@/utils/user'
import { formatIndexDisplay } from '@/utils/index'

const router = useRouter()
const authStore = useAuthStore()

const open = ref(false)
const rootRef = ref(null)

const displayName = computed(() => displayUserName(authStore.user, 'Student'))
const indexDisplay = computed(() => formatIndexDisplay(authStore.user?.index_number))

const initials = computed(() => {
  const name = displayName.value.trim()
  if (!name) return 'S'
  const parts = name.split(/\s+/).filter(Boolean)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0] || ''}${parts[parts.length - 1][0] || ''}`.toUpperCase()
})

const details = computed(() => {
  const user = authStore.user
  if (!user) return []

  return [
    user.department?.name ? { label: 'Department', value: user.department.name } : null,
    user.faculty?.name ? { label: 'Faculty', value: user.faculty.name } : null,
    user.phone_number ? { label: 'Phone', value: user.phone_number } : null,
  ].filter(Boolean)
})

function toggle() {
  open.value = !open.value
}

function close() {
  open.value = false
}

function onDocumentClick(event) {
  if (!rootRef.value?.contains(event.target)) close()
}

function onEscape(event) {
  if (event.key === 'Escape') close()
}

async function handleLogout() {
  close()
  await authStore.logout()
  await router.replace('/login')
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onEscape)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onEscape)
})
</script>

<style scoped>
.profile-menu {
  position: relative;
  margin-left: auto;
}

.profile-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid #ebe8e2;
  background: #fff;
  border-radius: 999px;
  padding: 0.28rem 0.45rem 0.28rem 0.28rem;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.profile-trigger:hover,
.profile-trigger[aria-expanded='true'] {
  border-color: #ddd9d2;
  box-shadow: 0 2px 8px rgba(28, 25, 23, 0.05);
}

.profile-avatar {
  width: 1.85rem;
  height: 1.85rem;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--vb-accent-soft, #ecfdf5);
  color: var(--vb-accent, #0f766e);
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  flex-shrink: 0;
}

.profile-trigger-text {
  display: grid;
  gap: 0.05rem;
  text-align: left;
  min-width: 0;
}

.profile-name {
  font-size: 0.68rem;
  font-weight: 600;
  color: #1c1917;
  line-height: 1.1;
  max-width: 7.5rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.profile-index {
  font-size: 0.58rem;
  font-weight: 500;
  color: #a8a29e;
  line-height: 1.1;
}

.profile-chevron {
  font-size: 0.55rem;
  color: #a8a29e;
  transition: transform 0.2s ease;
  margin-right: 0.15rem;
}

.profile-chevron.is-open {
  transform: rotate(180deg);
}

.profile-panel {
  position: absolute;
  top: calc(100% + 0.45rem);
  right: 0;
  width: min(16rem, calc(100vw - 1.5rem));
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 0.85rem;
  box-shadow: 0 12px 32px rgba(28, 25, 23, 0.08);
  padding: 0.75rem;
  z-index: 40;
}

.profile-panel-head {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid #f0eeea;
}

.profile-panel-avatar {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--vb-accent-soft, #ecfdf5);
  color: var(--vb-accent, #0f766e);
  font-size: 0.72rem;
  font-weight: 700;
  flex-shrink: 0;
}

.profile-panel-copy {
  min-width: 0;
}

.profile-panel-name {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  color: #1c1917;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.profile-panel-index {
  margin: 0.15rem 0 0;
  font-size: 0.64rem;
  color: #a8a29e;
}

.profile-details {
  margin: 0.55rem 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.4rem;
}

.profile-details li {
  display: flex;
  justify-content: space-between;
  gap: 0.65rem;
  font-size: 0.66rem;
}

.profile-details span {
  color: #a8a29e;
}

.profile-details strong {
  color: #1c1917;
  font-weight: 600;
  text-align: right;
}

.profile-signout {
  width: 100%;
  margin-top: 0.65rem;
  border: 1px solid #ebe8e2;
  background: #fafaf9;
  color: #1c1917;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.55rem 0.75rem;
  border-radius: 0.55rem;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.profile-signout:hover {
  background: #f5f4f1;
  border-color: #e0ddd6;
}

.profile-drop-enter-active,
.profile-drop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.profile-drop-enter-from,
.profile-drop-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 480px) {
  .profile-trigger-text {
    display: none;
  }

  .profile-chevron {
    display: none;
  }

  .profile-trigger {
    padding: 0.2rem;
    border-radius: 999px;
  }

  .profile-avatar {
    width: 2rem;
    height: 2rem;
    font-size: 0.66rem;
  }
}
</style>
