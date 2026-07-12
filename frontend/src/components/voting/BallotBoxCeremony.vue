<template>
  <div class="ceremony" role="dialog" aria-live="polite" aria-label="Ballot sealed">
    <div class="ceremony__stage">
      <div class="ceremony__slip" :class="{ 'is-dropping': phase !== 'idle' }">
        <span class="ceremony__slip-title">{{ positionTitle }}</span>
        <span class="ceremony__slip-name">{{ candidateLabel }}</span>
        <span class="ceremony__slip-seal">SEALED</span>
      </div>

      <div class="ceremony__box" :class="{ 'is-catch': phase === 'catch' || phase === 'done' }">
        <div class="ceremony__box-slot" />
        <div class="ceremony__box-body">
          <span class="ceremony__box-logo">EC</span>
          <span class="ceremony__box-label">Ballot box</span>
        </div>
        <div class="ceremony__box-lid" />
      </div>
    </div>

    <div class="ceremony__copy" :class="{ 'is-visible': phase === 'done' }">
      <p class="ceremony__eyebrow">Ballot sealed</p>
      <h2 class="ceremony__title">{{ positionTitle }} is in the box</h2>
      <p class="ceremony__sub">
        {{ isLast
          ? 'All positions are ready. Review and submit your vote.'
          : `Continue to the next position: ${nextTitle}.` }}
      </p>
      <button type="button" class="ceremony__btn" @click="$emit('continue')">
        {{ isLast ? 'Review & submit' : `Next: ${nextTitle}` }}
        <i class="fas fa-arrow-right" aria-hidden="true"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  positionTitle: { type: String, default: 'Position' },
  candidateLabel: { type: String, default: 'Your selection' },
  nextTitle: { type: String, default: 'Next' },
  isLast: { type: Boolean, default: false },
})

defineEmits(['continue'])

const phase = ref('idle')
let timers = []

function wait(ms, fn) {
  const id = setTimeout(fn, ms)
  timers.push(id)
}

onMounted(() => {
  wait(40, () => { phase.value = 'drop' })
  wait(720, () => { phase.value = 'catch' })
  wait(1180, () => { phase.value = 'done' })
})

onUnmounted(() => {
  timers.forEach(clearTimeout)
  timers = []
})
</script>

<style scoped>
.ceremony {
  display: grid;
  gap: 1.35rem;
  justify-items: center;
  padding: 1.25rem 0.5rem 0.5rem;
  text-align: center;
}

.ceremony__stage {
  position: relative;
  width: min(100%, 16rem);
  height: 13.5rem;
}

.ceremony__slip {
  position: absolute;
  left: 50%;
  top: 0.2rem;
  z-index: 2;
  width: 7.4rem;
  padding: 0.65rem 0.55rem 0.55rem;
  border-radius: 0.45rem;
  background: linear-gradient(180deg, #fffef9, #f5f0e6);
  border: 1px solid #e7e0d2;
  box-shadow: 0 8px 18px rgba(28, 25, 23, 0.12);
  transform: translateX(-50%) translateY(0) rotate(-4deg) scale(1);
  opacity: 1;
  display: grid;
  gap: 0.2rem;
  text-align: left;
}

.ceremony__slip.is-dropping {
  animation: slip-drop 0.85s cubic-bezier(0.33, 0.9, 0.4, 1) forwards;
}

.ceremony__slip-title {
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #a8a29e;
}

.ceremony__slip-name {
  font-size: 0.72rem;
  font-weight: 750;
  color: #1c1917;
  line-height: 1.25;
}

.ceremony__slip-seal {
  margin-top: 0.2rem;
  width: fit-content;
  font-size: 0.55rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #0f766e;
  background: rgba(16, 185, 129, 0.12);
  border-radius: 999px;
  padding: 0.12rem 0.4rem;
}

.ceremony__box {
  position: absolute;
  left: 50%;
  bottom: 0;
  width: 10.5rem;
  transform: translateX(-50%);
  z-index: 1;
}

.ceremony__box.is-catch .ceremony__box-lid {
  transform: rotate(-8deg) translateY(-2px);
}

.ceremony__box.is-catch .ceremony__box-body {
  animation: box-thump 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}

.ceremony__box-slot {
  height: 0.45rem;
  margin: 0 auto;
  width: 72%;
  border-radius: 999px;
  background: #1c1917;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.35);
}

.ceremony__box-lid {
  height: 0.55rem;
  margin: 0.15rem auto 0;
  width: 92%;
  border-radius: 0.35rem 0.35rem 0.15rem 0.15rem;
  background: linear-gradient(180deg, #3f3a36, #292524);
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1);
  transform-origin: left center;
}

.ceremony__box-body {
  margin-top: -0.1rem;
  height: 5.4rem;
  border-radius: 0.35rem 0.35rem 0.85rem 0.85rem;
  background:
    linear-gradient(180deg, #2a2623 0%, #1c1917 55%, #141210 100%);
  border: 1px solid #44403c;
  display: grid;
  place-content: center;
  gap: 0.2rem;
  box-shadow: 0 14px 28px rgba(28, 25, 23, 0.18);
}

.ceremony__box-logo {
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  border: 1.5px solid rgba(255, 255, 255, 0.35);
  display: grid;
  place-items: center;
  margin: 0 auto;
  font-size: 0.62rem;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 0.04em;
}

.ceremony__box-label {
  font-size: 0.62rem;
  font-weight: 650;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.55);
}

.ceremony__copy {
  opacity: 0;
  transform: translateY(0.6rem);
  transition:
    opacity 0.4s cubic-bezier(0.16, 1, 0.3, 1),
    transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
  display: grid;
  gap: 0.35rem;
  justify-items: center;
  max-width: 20rem;
}

.ceremony__copy.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.ceremony__eyebrow {
  margin: 0;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #0f766e;
}

.ceremony__title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #1c1917;
}

.ceremony__sub {
  margin: 0;
  font-size: 0.84rem;
  line-height: 1.45;
  color: #78716c;
}

.ceremony__btn {
  margin-top: 0.55rem;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border: none;
  border-radius: 999px;
  padding: 0.75rem 1.2rem;
  background: #1c1917;
  color: #fff;
  font-size: 0.86rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(28, 25, 23, 0.16);
}

.ceremony__btn i {
  font-size: 0.7rem;
}

@keyframes slip-drop {
  0% {
    transform: translateX(-50%) translateY(0) rotate(-4deg) scale(1);
    opacity: 1;
  }
  55% {
    transform: translateX(-50%) translateY(4.8rem) rotate(3deg) scale(0.92);
    opacity: 1;
  }
  85% {
    transform: translateX(-50%) translateY(6.6rem) rotate(1deg) scale(0.72);
    opacity: 0.55;
  }
  100% {
    transform: translateX(-50%) translateY(7.4rem) rotate(0deg) scale(0.35);
    opacity: 0;
  }
}

@keyframes box-thump {
  0% { transform: translateY(0); }
  40% { transform: translateY(3px); }
  100% { transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
  .ceremony__slip.is-dropping,
  .ceremony__box.is-catch .ceremony__box-body {
    animation: none;
  }

  .ceremony__slip.is-dropping {
    opacity: 0;
  }

  .ceremony__copy {
    opacity: 1;
    transform: none;
  }
}
</style>
