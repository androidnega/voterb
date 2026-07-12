<template>
  <div class="skel-svt" aria-busy="true" aria-live="polite">
    <div class="skel-svt__back" />
    <article class="skel-svt__card">
      <div class="skel-svt__shield" />
      <div class="skel-line skel-line--eyebrow" />
      <div class="skel-line skel-line--title" />
      <div class="skel-line skel-line--sub" />
      <div class="skel-note">
        <div class="skel-note__icon" />
        <div class="skel-note__copy">
          <div class="skel-line skel-line--note-a" />
          <div class="skel-line skel-line--note-b" />
        </div>
      </div>
      <div class="skel-btn" />
      <p v-if="hint" class="skel-hint">{{ hint }}</p>
    </article>
  </div>
</template>

<script setup>
defineProps({
  hint: { type: String, default: '' },
})
</script>

<style scoped>
.skel-svt {
  width: min(28rem, 100%);
  margin: 0 auto;
  padding: 0.5rem 0 2rem;
}

.skel-svt__back {
  width: 4.5rem;
  height: 0.9rem;
  border-radius: 0.35rem;
  margin-bottom: 1rem;
  background: linear-gradient(90deg, #ebe8e2, #f5f4f1, #ebe8e2);
  background-size: 200% 100%;
  animation: skel-shimmer 1.35s ease-in-out infinite;
}

.skel-svt__card {
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 1.5rem;
  padding: 1.5rem 1.35rem 1.45rem;
  display: grid;
  gap: 0.65rem;
  box-shadow: 0 10px 30px rgba(28, 25, 23, 0.04);
}

.skel-svt__shield {
  width: 2.6rem;
  height: 2.6rem;
  border-radius: 0.85rem;
  background: linear-gradient(90deg, #e8f5f2, #f3faf8, #e8f5f2);
  background-size: 200% 100%;
  animation: skel-shimmer 1.35s ease-in-out infinite;
}

.skel-line {
  border-radius: 0.4rem;
  background: linear-gradient(90deg, #f0eeea 0%, #f7f6f3 45%, #f0eeea 90%);
  background-size: 200% 100%;
  animation: skel-shimmer 1.35s ease-in-out infinite;
}

.skel-line--eyebrow { height: 0.55rem; width: 38%; }
.skel-line--title { height: 1.05rem; width: 72%; }
.skel-line--sub { height: 0.7rem; width: 88%; margin-bottom: 0.35rem; }
.skel-line--note-a { height: 0.65rem; width: 55%; }
.skel-line--note-b { height: 0.6rem; width: 90%; }

.skel-note {
  display: flex;
  gap: 0.75rem;
  padding: 0.85rem;
  border-radius: 0.85rem;
  background: #fafaf8;
  border: 1px solid #f0eeea;
}

.skel-note__icon {
  width: 1.35rem;
  height: 1.35rem;
  border-radius: 999px;
  flex-shrink: 0;
  background: #ebe8e2;
}

.skel-note__copy {
  flex: 1;
  display: grid;
  gap: 0.4rem;
  align-content: start;
}

.skel-btn {
  height: 2.75rem;
  border-radius: 0.85rem;
  margin-top: 0.25rem;
  background: linear-gradient(90deg, #d7ebe7, #e8f5f2, #d7ebe7);
  background-size: 200% 100%;
  animation: skel-shimmer 1.35s ease-in-out infinite;
}

.skel-hint {
  margin: 0.35rem 0 0;
  text-align: center;
  font-size: 0.74rem;
  color: #a8a29e;
}

@keyframes skel-shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .skel-svt__back,
  .skel-svt__shield,
  .skel-line,
  .skel-btn {
    animation: none;
  }
}
</style>
