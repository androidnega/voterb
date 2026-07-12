<template>
  <div class="ceremony" role="dialog" aria-live="polite" aria-label="Ballot sealed">
    <div class="ceremony__stage">
      <!-- Falling slip -->
      <div
        class="ceremony__slip"
        :class="{ 'is-dropping': phase !== 'idle', 'is-settled': phase === 'catch' || phase === 'done' }"
      >
        <span class="ceremony__slip-title">{{ positionTitle }}</span>
        <span class="ceremony__slip-name">{{ candidateLabel }}</span>
        <span class="ceremony__slip-seal">SEALED</span>
      </div>

      <div class="ceremony__box" :class="{ 'is-catch': phase === 'catch' || phase === 'done' }">
        <div class="ceremony__box-lid" />
        <div class="ceremony__box-slot" />
        <div class="ceremony__box-body">
          <!-- Papers already / settling inside the glass box -->
          <div class="ceremony__papers" aria-hidden="true">
            <span
              v-for="(paper, idx) in stackedPapers"
              :key="paper.id"
              class="ceremony__paper"
              :class="{ 'is-new': paper.fresh && (phase === 'catch' || phase === 'done') }"
              :style="paperStyle(idx, paper)"
            />
          </div>
          <div class="ceremony__glass-sheen" aria-hidden="true" />
          <span class="ceremony__box-logo">EC</span>
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
  candidateLabel: { type: String, default: 'Your selection' },
  nextTitle: { type: String, default: 'Next' },
  isLast: { type: Boolean, default: false },
  sealedCount: { type: Number, default: 1 },
})

defineEmits(['continue'])

const phase = ref('idle')
let timers = []

const stackedPapers = computed(() => {
  const prior = Math.max(0, Math.min(4, (props.sealedCount || 1) - 1))
  const papers = []
  for (let i = 0; i < prior; i += 1) {
    papers.push({ id: `p-${i}`, fresh: false, tilt: -10 + i * 7 })
  }
  papers.push({ id: 'fresh', fresh: true, tilt: 4 })
  return papers
})

function paperStyle(idx, paper) {
  const base = 0.55 + idx * 0.38
  return {
    bottom: `${base}rem`,
    transform: `rotate(${paper.tilt}deg)`,
    zIndex: idx + 1,
  }
}

function wait(ms, fn) {
  const id = setTimeout(fn, ms)
  timers.push(id)
}

onMounted(() => {
  wait(40, () => { phase.value = 'drop' })
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
  gap: 1.15rem;
  justify-items: center;
  padding: 1.1rem 0.5rem 0.35rem;
  text-align: center;
}

.ceremony__stage {
  position: relative;
  width: min(100%, 16rem);
  height: 14rem;
}

.ceremony__slip {
  position: absolute;
  left: 50%;
  top: 0.15rem;
  z-index: 5;
  width: 7.2rem;
  padding: 0.6rem 0.5rem 0.5rem;
  border-radius: 0.4rem;
  background: linear-gradient(180deg, #fffef9, #f3eee6);
  border: 1px solid #e7e0d2;
  box-shadow: 0 8px 18px rgba(28, 25, 23, 0.12);
  transform: translateX(-50%) translateY(0) rotate(-4deg) scale(1);
  opacity: 1;
  display: grid;
  gap: 0.18rem;
  text-align: left;
}

.ceremony__slip.is-dropping {
  animation: slip-drop 0.9s cubic-bezier(0.33, 0.9, 0.4, 1) forwards;
}

.ceremony__slip.is-settled {
  opacity: 0;
  pointer-events: none;
}

.ceremony__slip-title {
  font-size: 0.56rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #a8a29e;
}

.ceremony__slip-name {
  font-size: 0.7rem;
  font-weight: 750;
  color: #1c1917;
  line-height: 1.25;
}

.ceremony__slip-seal {
  margin-top: 0.15rem;
  width: fit-content;
  font-size: 0.52rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #059669;
  background: rgba(16, 185, 129, 0.14);
  border-radius: 999px;
  padding: 0.1rem 0.38rem;
}

.ceremony__box {
  position: absolute;
  left: 50%;
  bottom: 0;
  width: 11rem;
  transform: translateX(-50%);
  z-index: 1;
}

.ceremony__box.is-catch .ceremony__box-lid {
  transform: translateY(-1px);
}

.ceremony__box.is-catch .ceremony__box-body {
  animation: box-thump 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}

.ceremony__box-lid {
  height: 0.7rem;
  margin: 0 auto;
  width: 94%;
  border-radius: 0.55rem 0.55rem 0.2rem 0.2rem;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.72),
    rgba(236, 253, 245, 0.45)
  );
  border: 1px solid rgba(15, 118, 110, 0.18);
  border-bottom: none;
  backdrop-filter: blur(10px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
  transition: transform 0.3s ease;
}

.ceremony__box-slot {
  height: 0.38rem;
  margin: 0 auto;
  width: 58%;
  border-radius: 999px;
  background: rgba(28, 25, 23, 0.55);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.25);
  position: relative;
  z-index: 2;
}

.ceremony__box-body {
  position: relative;
  margin-top: -0.05rem;
  height: 6.1rem;
  border-radius: 0.35rem 0.35rem 1rem 1rem;
  overflow: hidden;
  background: linear-gradient(
    165deg,
    rgba(255, 255, 255, 0.42) 0%,
    rgba(236, 253, 245, 0.28) 40%,
    rgba(203, 213, 225, 0.22) 100%
  );
  border: 1.5px solid rgba(255, 255, 255, 0.65);
  box-shadow:
    0 14px 28px rgba(28, 25, 23, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.75),
    inset 0 -8px 20px rgba(15, 118, 110, 0.06);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.ceremony__papers {
  position: absolute;
  left: 50%;
  bottom: 0.85rem;
  width: 6.4rem;
  height: 3.4rem;
  transform: translateX(-50%);
  z-index: 1;
}

.ceremony__paper {
  position: absolute;
  left: 50%;
  width: 5.6rem;
  height: 0.85rem;
  margin-left: -2.8rem;
  border-radius: 0.18rem;
  background: linear-gradient(180deg, #fffefb, #efe8dc);
  border: 1px solid #e4dccf;
  box-shadow: 0 2px 6px rgba(28, 25, 23, 0.1);
  opacity: 0.95;
}

.ceremony__paper.is-new {
  animation: paper-land 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.ceremony__glass-sheen {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    115deg,
    rgba(255, 255, 255, 0.45) 0%,
    rgba(255, 255, 255, 0.08) 28%,
    transparent 48%,
    rgba(255, 255, 255, 0.12) 100%
  );
  pointer-events: none;
  z-index: 3;
}

.ceremony__box-logo {
  position: absolute;
  top: 0.55rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 4;
  width: 1.7rem;
  height: 1.7rem;
  border-radius: 999px;
  border: 1.5px solid rgba(15, 118, 110, 0.35);
  display: grid;
  place-items: center;
  font-size: 0.55rem;
  font-weight: 800;
  color: #0f766e;
  background: rgba(255, 255, 255, 0.55);
  letter-spacing: 0.04em;
}

.ceremony__copy {
  opacity: 0;
  transform: translateY(0.55rem);
  transition:
    opacity 0.4s cubic-bezier(0.16, 1, 0.3, 1),
    transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
  display: grid;
  gap: 0.75rem;
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
  color: #059669;
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
    transform: translateX(-50%) translateY(0) rotate(-4deg) scale(1);
    opacity: 1;
  }
  60% {
    transform: translateX(-50%) translateY(5.2rem) rotate(2deg) scale(0.9);
    opacity: 1;
  }
  100% {
    transform: translateX(-50%) translateY(7.6rem) rotate(0deg) scale(0.55);
    opacity: 0;
  }
}

@keyframes paper-land {
  0% {
    opacity: 0;
    transform: rotate(8deg) translateY(-1.2rem) scale(1.1);
  }
  100% {
    opacity: 0.95;
    transform: rotate(4deg) translateY(0) scale(1);
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
    box-shadow: 0 14px 28px rgba(5, 150, 105, 0.22);
  }
}

@keyframes btn-nudge {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(3px); }
}

@media (prefers-reduced-motion: reduce) {
  .ceremony__slip.is-dropping,
  .ceremony__paper.is-new,
  .ceremony__box.is-catch .ceremony__box-body,
  .ceremony__btn,
  .ceremony__btn i {
    animation: none !important;
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
