<template>
  <div class="ceremony" role="dialog" aria-live="polite" aria-label="Ballot sealed">
    <div class="ceremony__stage">
      <div
        class="slip"
        :class="{
          'is-dropping': phase === 'drop',
          'is-gone': phase === 'catch' || phase === 'done',
        }"
        aria-hidden="true"
      >
        <span class="slip__left" />
        <span class="slip__right" />
      </div>

      <div class="bb" :class="{ 'is-catch': phase === 'catch' || phase === 'done' }">
        <div class="bb__lid">
          <div class="bb__rim" />
          <div class="bb__lid-body">
            <div class="bb__recess">
              <div class="bb__slot">
                <span class="bb__slot-shade" />
              </div>
            </div>
          </div>
        </div>

        <div class="bb__body">
          <span class="bb__shine bb__shine--l" aria-hidden="true" />
          <span class="bb__shine bb__shine--r" aria-hidden="true" />

          <div class="bb__label">
            <img
              class="bb__logo"
              :src="logoSrc"
              alt=""
              @error="onLogoError"
            />
            <p v-if="displayOrg" class="bb__org">{{ displayOrg }}</p>
            <p class="bb__election">{{ electionTitle }}</p>
            <p class="bb__position">{{ positionTitle }}</p>
          </div>

          <!-- Empty until cast; then a single folded ballot -->
          <div
            class="bb__papers"
            :class="{ 'is-visible': phase === 'catch' || phase === 'done' }"
            aria-hidden="true"
          >
            <span class="bb__paper" />
          </div>
        </div>

        <div class="bb__ground" aria-hidden="true" />

        <div class="bb__seal bb__seal--front" aria-hidden="true">
          <span class="bb__seal-top" />
          <span class="bb__seal-mid" />
          <span class="bb__seal-tail" />
        </div>
        <div class="bb__seal bb__seal--left" aria-hidden="true">
          <span class="bb__tie" />
          <span class="bb__lock" />
        </div>
        <div class="bb__seal bb__seal--right" aria-hidden="true">
          <span class="bb__tie" />
          <span class="bb__lock" />
        </div>
      </div>
    </div>

    <div class="ceremony__copy" :class="{ 'is-visible': phase === 'done' }">
      <p class="ceremony__eyebrow">Ballot sealed</p>
      <button type="button" class="ceremony__btn" @click="$emit('continue')">
        <span>{{ isLast ? 'Review & submit' : `Next: ${nextTitle}` }}</span>
        <i class="fas fa-arrow-right" aria-hidden="true"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { resolveMediaUrl } from '@/utils/media'

const props = defineProps({
  positionTitle: { type: String, default: 'Position' },
  nextTitle: { type: String, default: 'Next' },
  isLast: { type: Boolean, default: false },
  electionTitle: { type: String, default: 'Election' },
  electionYear: { type: [String, Number], default: '' },
  institutionName: { type: String, default: '' },
  institutionLogo: { type: String, default: '' },
})

defineEmits(['continue'])

const FALLBACK_LOGO = '/images/institution-logo.png'
const logoBroken = ref(false)
const phase = ref('idle')
let timers = []

const logoSrc = computed(() => {
  if (logoBroken.value) return FALLBACK_LOGO
  return resolveMediaUrl(props.institutionLogo) || FALLBACK_LOGO
})

const displayOrg = computed(() => {
  const name = String(props.institutionName || '').trim()
  if (!name) return ''
  const lower = name.toLowerCase()
  if (lower === 'voterb' || lower === 'votebridge') return ''
  return name
})

function onLogoError() {
  logoBroken.value = true
}

function wait(ms, fn) {
  const id = setTimeout(fn, ms)
  timers.push(id)
}

onMounted(() => {
  wait(60, () => { phase.value = 'drop' })
  wait(720, () => { phase.value = 'catch' })
  wait(1150, () => { phase.value = 'done' })
})

onUnmounted(() => {
  timers.forEach(clearTimeout)
  timers = []
})
</script>

<style scoped>
.ceremony {
  display: grid;
  gap: 0.9rem;
  justify-items: center;
  padding: 0.25rem 0.2rem 0.1rem;
  text-align: center;
  background: #fff;
}

.ceremony__stage {
  position: relative;
  width: min(100%, 11.25rem);
  padding-top: 0.35rem;
  background: #fff;
}

.slip {
  position: absolute;
  left: 50%;
  top: 0;
  z-index: 40;
  width: 1.1rem;
  height: 0.7rem;
  display: flex;
  transform: translateX(-50%) rotate(-6deg);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  pointer-events: none;
}

.slip.is-dropping {
  animation: slip-drop 0.68s cubic-bezier(0.42, 0.05, 0.4, 1) forwards;
}

.slip.is-gone {
  opacity: 0;
  visibility: hidden;
}

.slip__left,
.slip__right {
  flex: 1;
  background: linear-gradient(180deg, #fff, #f3efe6);
  border: 1px solid #b0b5b9;
}

.slip__left {
  border-right: none;
  border-radius: 0.08rem 0 0 0.08rem;
  transform: skewY(-12deg);
  transform-origin: right bottom;
}

.slip__right {
  border-left: none;
  border-radius: 0 0.08rem 0.08rem 0;
  transform: skewY(12deg);
  transform-origin: left bottom;
  background: linear-gradient(180deg, #f7f3eb, #e8e0d4);
}

.bb {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bb__lid {
  position: relative;
  z-index: 20;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bb__rim {
  width: 90%;
  height: 0.35rem;
  background: #7a828a;
  border: 2px solid #2d3135;
  border-bottom: none;
  border-radius: 0.45rem 0.45rem 0 0;
}

.bb__lid-body {
  position: relative;
  width: 88%;
  height: 1.65rem;
  background: #a1a8af;
  border: 2px solid #2d3135;
  border-top: none;
  border-radius: 0 0 0.45rem 0.45rem;
  box-shadow: 0 2px 5px rgba(45, 49, 53, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
}

.bb__recess {
  width: 85%;
  height: 62%;
  border: 1.5px solid #7a828a;
  border-radius: 0.22rem;
  background: #a1a8af;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bb__slot {
  width: 58%;
  height: 0.42rem;
  background: #555b61;
  border: 1.5px solid #2d3135;
  border-radius: 0.1rem;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.35);
  position: relative;
  overflow: hidden;
}

.bb__slot-shade {
  display: block;
  width: 100%;
  height: 0.16rem;
  background: #1a1c1e;
  opacity: 0.55;
}

.bb__body {
  position: relative;
  z-index: 10;
  width: 78%;
  margin-top: -1px;
  height: 7.35rem;
  background: linear-gradient(180deg, rgba(229, 231, 235, 0.35), rgba(209, 213, 219, 0.12));
  border: 2px solid #7a828a;
  border-top: none;
  border-radius: 0 0 1.05rem 1.05rem;
  box-shadow: 0 6px 14px rgba(45, 49, 53, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 0.85rem;
  overflow: hidden;
}

.bb__shine {
  position: absolute;
  top: 0;
  bottom: 0;
  border-radius: 999px;
  pointer-events: none;
}

.bb__shine--l {
  left: 0.32rem;
  width: 0.14rem;
  background: rgba(255, 255, 255, 0.65);
}

.bb__shine--r {
  right: 0.32rem;
  width: 0.1rem;
  background: rgba(255, 255, 255, 0.3);
}

.bb__label {
  width: 74%;
  min-height: 4rem;
  background: #fff;
  border: 1.5px solid #7a828a;
  border-radius: 0.12rem;
  box-shadow: 0 1px 3px rgba(45, 49, 53, 0.08);
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.12rem;
  padding: 0.4rem 0.35rem 0.45rem;
  text-align: center;
  box-sizing: border-box;
}

.bb__logo {
  width: 1.55rem;
  height: 1.55rem;
  object-fit: contain;
  background: transparent;
  margin-bottom: 0.12rem;
  flex-shrink: 0;
}

.bb__org,
.bb__election,
.bb__position {
  margin: 0;
  max-width: 100%;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  word-break: break-word;
}

.bb__org {
  font-size: 0.34rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #6b7280;
  -webkit-line-clamp: 1;
}

.bb__election {
  font-size: 0.4rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: #374151;
  -webkit-line-clamp: 2;
  line-height: 1.2;
}

.bb__position {
  font-size: 0.5rem;
  font-weight: 800;
  color: #111827;
  -webkit-line-clamp: 2;
  line-height: 1.15;
  margin-top: 0.05rem;
}

.bb__papers {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0.55rem;
  height: 1.7rem;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  pointer-events: none;
  opacity: 0;
  transform: translateY(0.45rem) scale(0.85);
  transition:
    opacity 0.35s ease,
    transform 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}

.bb__papers.is-visible {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.bb__paper {
  display: block;
  width: 3.2rem;
  height: 1.25rem;
  background:
    linear-gradient(105deg, transparent 46%, rgba(0, 0, 0, 0.05) 50%, transparent 54%),
    linear-gradient(180deg, #fffefb, #efe8dc);
  border: 1.5px solid #b0b5b9;
  border-radius: 0.1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
  transform: rotate(-8deg);
  clip-path: polygon(0 32%, 50% 0, 100% 32%, 100% 100%, 0 100%);
}

.bb__ground {
  width: 72%;
  height: 0.28rem;
  margin-top: 0.15rem;
  background: rgba(209, 213, 219, 0.55);
  border-radius: 999px;
  filter: blur(2px);
  z-index: 0;
}

.bb__seal {
  position: absolute;
  z-index: 30;
  pointer-events: none;
}

.bb__seal--front {
  top: -0.28rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bb__seal-top {
  width: 0.22rem;
  height: 0.42rem;
  background: #3b8751;
  border: 1.5px solid #1e4629;
  border-radius: 0.12rem 0.12rem 0 0;
}

.bb__seal-mid {
  width: 0.55rem;
  height: 0.58rem;
  background: #3b8751;
  border: 1.5px solid #1e4629;
  border-radius: 0.1rem;
  margin-top: -1px;
}

.bb__seal-tail {
  width: 0.18rem;
  height: 0.38rem;
  background: #3b8751;
  border: 1.5px solid #1e4629;
  border-top: none;
  margin-top: -1px;
}

.bb__seal--left {
  top: 0.9rem;
  left: 1.5%;
  transform: rotate(-35deg);
  display: flex;
  align-items: center;
}

.bb__seal--right {
  top: 0.9rem;
  right: 1.5%;
  transform: rotate(35deg);
  display: flex;
  align-items: center;
  flex-direction: row-reverse;
}

.bb__tie {
  width: 1.2rem;
  height: 0.22rem;
  background: #3b8751;
  border: 1.5px solid #1e4629;
  border-radius: 999px;
}

.bb__lock {
  width: 0.42rem;
  height: 0.42rem;
  background: #3b8751;
  border: 1.5px solid #1e4629;
  border-radius: 0.08rem;
  margin: -0.1rem -0.12rem 0;
}

.bb.is-catch .bb__body {
  animation: box-thump 0.38s cubic-bezier(0.22, 1, 0.36, 1);
}

.bb.is-catch .bb__lid {
  animation: lid-nudge 0.38s cubic-bezier(0.22, 1, 0.36, 1);
}

.ceremony__copy {
  opacity: 0;
  transform: translateY(0.5rem);
  transition:
    opacity 0.4s cubic-bezier(0.16, 1, 0.3, 1),
    transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
  display: grid;
  gap: 0.7rem;
  justify-items: center;
}

.ceremony__copy.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.ceremony__eyebrow {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 750;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #16a34a;
}

.ceremony__btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  border: none;
  border-radius: 999px;
  padding: 0.78rem 1.25rem;
  background: #1c1917;
  color: #fff;
  font-size: 0.86rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(28, 25, 23, 0.16);
  animation: btn-pulse 1.6s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite;
}

.ceremony__btn i {
  font-size: 0.7rem;
  animation: btn-nudge 1.2s ease-in-out infinite;
}

.ceremony__copy:not(.is-visible) .ceremony__btn {
  animation: none;
}

@keyframes slip-drop {
  0% {
    transform: translateX(-50%) translateY(0) rotate(-6deg) scale(1);
    opacity: 1;
  }
  55% {
    transform: translateX(-50%) translateY(1.45rem) rotate(2deg) scale(0.85);
    opacity: 1;
  }
  100% {
    transform: translateX(-50%) translateY(1.95rem) rotate(0deg) scale(0.4);
    opacity: 0;
  }
}

@keyframes box-thump {
  0% { transform: translateY(0); }
  40% { transform: translateY(3px); }
  100% { transform: translateY(0); }
}

@keyframes lid-nudge {
  0% { transform: translateY(0); }
  35% { transform: translateY(-2px); }
  100% { transform: translateY(0); }
}

@keyframes btn-pulse {
  0%, 100% {
    transform: translateY(0);
    box-shadow: 0 10px 22px rgba(28, 25, 23, 0.16);
  }
  50% {
    transform: translateY(-2px);
    box-shadow: 0 14px 28px rgba(22, 163, 74, 0.22);
  }
}

@keyframes btn-nudge {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(3px); }
}

@media (prefers-reduced-motion: reduce) {
  .slip.is-dropping,
  .bb.is-catch .bb__body,
  .bb.is-catch .bb__lid,
  .ceremony__btn,
  .ceremony__btn i {
    animation: none !important;
  }

  .slip.is-dropping,
  .slip.is-gone {
    opacity: 0;
    visibility: hidden;
  }

  .bb__papers {
    opacity: 1;
    transform: none;
  }

  .ceremony__copy {
    opacity: 1;
    transform: none;
  }
}
</style>
