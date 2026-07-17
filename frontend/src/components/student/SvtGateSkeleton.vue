<template>
  <div class="skel-svt" aria-busy="true" aria-live="polite">
    <div class="skel-svt__back" />
    <article class="skel-svt__card">
      <div class="skel-svt__head">
        <div class="skel-svt__shield" />
        <div class="skel-svt__head-copy">
          <div class="skel-line skel-line--eyebrow" />
          <div class="skel-line skel-line--title" />
        </div>
      </div>
      <div class="skel-line skel-line--sub" />
      <div class="skel-line skel-line--meta" />
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
  width: min(24.5rem, 100%);
  margin: 0 auto;
  padding: 0.35rem 0 1.5rem;
}

.skel-svt__back {
  width: 4rem;
  height: 0.8rem;
  border-radius: 0.3rem;
  margin-bottom: 0.7rem;
  background: linear-gradient(90deg, #ebe8e2, #f5f4f1, #ebe8e2);
  background-size: 200% 100%;
  animation: skel-shimmer 1.35s ease-in-out infinite;
}

.skel-svt__card {
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 1rem;
  padding: 1rem 1.05rem 1.05rem;
  display: grid;
  gap: 0.55rem;
  box-shadow: 0 3px 12px rgba(28, 25, 23, 0.04);
}

.skel-svt__head {
  display: flex;
  align-items: center;
  gap: 0.7rem;
}

.skel-svt__shield {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.7rem;
  flex-shrink: 0;
  background: linear-gradient(90deg, #e8f5f2, #f3faf8, #e8f5f2);
  background-size: 200% 100%;
  animation: skel-shimmer 1.35s ease-in-out infinite;
}

.skel-svt__head-copy {
  flex: 1;
  display: grid;
  gap: 0.35rem;
}

.skel-line {
  border-radius: 0.35rem;
  background: linear-gradient(90deg, #f0eeea 0%, #f7f6f3 45%, #f0eeea 90%);
  background-size: 200% 100%;
  animation: skel-shimmer 1.35s ease-in-out infinite;
}

.skel-line--eyebrow { height: 0.45rem; width: 42%; }
.skel-line--title { height: 0.85rem; width: 78%; }
.skel-line--sub { height: 0.6rem; width: 92%; }
.skel-line--meta { height: 0.55rem; width: 70%; margin-top: 0.15rem; }

.skel-btn {
  height: 2.45rem;
  border-radius: 0.7rem;
  margin-top: 0.15rem;
  background: linear-gradient(90deg, #ebe8e2, #f5f4f1, #ebe8e2);
  background-size: 200% 100%;
  animation: skel-shimmer 1.35s ease-in-out infinite;
}

.skel-hint {
  margin: 0.1rem 0 0;
  text-align: center;
  font-size: 0.72rem;
  color: #a8a29e;
}

@keyframes skel-shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}
</style>
