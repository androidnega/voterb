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

      <div class="box" :class="{ 'is-catch': phase === 'catch' || phase === 'done' }">
        <img
          class="box__art"
          src="/images/ballot-box.png"
          alt=""
          draggable="false"
        />

        <div class="box__label">
          <p v-if="displayOrg" class="box__org">{{ displayOrg }}</p>
          <p class="box__election">{{ electionTitle }}</p>
          <p class="box__position">{{ positionTitle }}</p>
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

const phase = ref('idle')
let timers = []

const displayOrg = computed(() => {
  const name = String(props.institutionName || '').trim()
  if (!name) return ''
  const lower = name.toLowerCase()
  if (lower === 'voterb' || lower === 'votebridge') return ''
  return name
})

function wait(ms, fn) {
  const id = setTimeout(fn, ms)
  timers.push(id)
}

onMounted(() => {
  wait(60, () => { phase.value = 'drop' })
  wait(780, () => { phase.value = 'catch' })
  wait(1200, () => { phase.value = 'done' })
})

onUnmounted(() => {
  timers.forEach(clearTimeout)
  timers = []
})
</script>

<style scoped>
.ceremony {
  display: grid;
  gap: 0.95rem;
  justify-items: center;
  padding: 0.25rem 0.2rem 0.1rem;
  text-align: center;
}

.ceremony__stage {
  position: relative;
  width: min(100%, 20rem);
  aspect-ratio: 1 / 1;
}

.slip {
  position: absolute;
  left: 50%;
  top: 1%;
  z-index: 5;
  width: 1.75rem;
  height: 1.1rem;
  display: flex;
  transform: translateX(-50%) rotate(-6deg);
  filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.28));
  pointer-events: none;
}

.slip.is-dropping {
  animation: slip-drop 0.72s cubic-bezier(0.42, 0.05, 0.4, 1) forwards;
}

.slip.is-gone {
  opacity: 0;
  visibility: hidden;
}

.slip__left,
.slip__right {
  flex: 1;
  background: linear-gradient(180deg, #fff, #f3efe6);
  border: 1px solid #d7d0c4;
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

.box {
  position: relative;
  width: 100%;
  height: 100%;
}

.box__art {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  user-select: none;
  pointer-events: none;
}

/* Transparent text overlay on the art's white panel — no extra background */
.box__label {
  position: absolute;
  left: 26.3%;
  top: 42.5%;
  width: 48.7%;
  height: 28.9%;
  padding: 0.45rem 0.5rem 0.55rem;
  margin: 0;
  background: transparent;
  border: none;
  box-shadow: none;
  text-align: left;
  line-height: 1.25;
  z-index: 3;
  overflow: visible;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-end;
  gap: 0.22rem;
  box-sizing: border-box;
  pointer-events: none;
}

.box__org,
.box__election,
.box__position,
.box__year {
  margin: 0;
  background: transparent;
  color: #0f172a;
  word-break: break-word;
  overflow: visible;
  white-space: normal;
}

.box__org {
  font-size: 0.52rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.box__election {
  font-size: 0.5rem;
  font-weight: 750;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: #1e293b;
}

.box__position {
  font-size: 0.58rem;
  font-weight: 800;
  color: #0f172a;
}

.box.is-catch {
  animation: box-thump 0.38s cubic-bezier(0.22, 1, 0.36, 1);
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
  58% {
    transform: translateX(-50%) translateY(2.15rem) rotate(2deg) scale(0.82);
    opacity: 1;
  }
  100% {
    transform: translateX(-50%) translateY(2.85rem) rotate(0deg) scale(0.4);
    opacity: 0;
  }
}

@keyframes box-thump {
  0% { transform: translateY(0); }
  40% { transform: translateY(3px); }
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
  .box.is-catch,
  .ceremony__btn,
  .ceremony__btn i {
    animation: none !important;
  }

  .slip.is-dropping,
  .slip.is-gone {
    opacity: 0;
    visibility: hidden;
  }

  .ceremony__copy {
    opacity: 1;
    transform: none;
  }
}
</style>
