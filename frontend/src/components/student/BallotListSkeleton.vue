<template>
  <div class="skel-ballots" aria-busy="true" aria-live="polite">
    <p v-if="hint" class="skel-hint">{{ hint }}</p>
    <article v-for="n in count" :key="n" class="skel-ballot">
      <div class="skel-ballot__main">
        <div class="skel-line skel-line--title" />
        <div class="skel-line skel-line--body" />
        <div class="skel-line skel-line--meta" />
      </div>
      <div class="skel-ballot__foot">
        <div class="skel-pill" />
      </div>
    </article>
  </div>
</template>

<script setup>
defineProps({
  count: { type: Number, default: 2 },
  hint: { type: String, default: '' },
})
</script>

<style scoped>
.skel-ballots {
  display: grid;
  gap: 0.65rem;
}

.skel-hint {
  margin: 0 0 0.15rem;
  font-size: 0.74rem;
  font-weight: 500;
  color: #a8a29e;
  text-align: center;
}

.skel-ballot {
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 0.85rem;
  overflow: hidden;
}

.skel-ballot__main {
  padding: 1rem 1rem 0.85rem;
  display: grid;
  gap: 0.55rem;
}

.skel-ballot__foot {
  padding: 0.55rem 0.85rem 0.85rem;
  display: flex;
  justify-content: flex-end;
}

.skel-line,
.skel-pill {
  background: linear-gradient(90deg, #f0eeea 0%, #f7f6f3 45%, #f0eeea 90%);
  background-size: 200% 100%;
  animation: skel-shimmer 1.35s ease-in-out infinite;
  border-radius: 0.4rem;
}

.skel-line--title {
  height: 0.95rem;
  width: 68%;
}

.skel-line--body {
  height: 0.7rem;
  width: 92%;
}

.skel-line--meta {
  height: 0.65rem;
  width: 42%;
  margin-top: 0.15rem;
}

.skel-pill {
  height: 2.2rem;
  width: 5.5rem;
  border-radius: 999px;
}

@keyframes skel-shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .skel-line,
  .skel-pill {
    animation: none;
  }
}
</style>
