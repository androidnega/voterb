<template>
  <div class="skel-wizard" aria-busy="true" aria-live="polite">
    <div class="skel-wizard__head">
      <div class="skel-line skel-line--eyebrow" />
      <div class="skel-line skel-line--title" />
    </div>
    <div class="skel-tabs">
      <div v-for="n in 3" :key="n" class="skel-tab" />
    </div>
    <article class="skel-card">
      <div class="skel-line skel-line--card-title" />
      <div class="skel-line skel-line--hint" />
      <div class="skel-grid">
        <div v-for="n in 4" :key="n" class="skel-candidate">
          <div class="skel-avatar" />
          <div class="skel-line skel-line--name" />
          <div class="skel-line skel-line--meta" />
        </div>
      </div>
      <div class="skel-nav">
        <div class="skel-nav__btn" />
        <div class="skel-nav__btn skel-nav__btn--primary" />
      </div>
    </article>
    <p v-if="hint" class="skel-hint">{{ hint }}</p>
  </div>
</template>

<script setup>
defineProps({
  hint: { type: String, default: '' },
})
</script>

<style scoped>
.skel-wizard {
  display: grid;
  gap: 0.9rem;
}

.skel-wizard__head {
  display: grid;
  gap: 0.45rem;
}

.skel-line,
.skel-tab,
.skel-avatar,
.skel-nav__btn {
  background: linear-gradient(90deg, #f0eeea 0%, #f7f6f3 45%, #f0eeea 90%);
  background-size: 200% 100%;
  animation: skel-shimmer 1.35s ease-in-out infinite;
  border-radius: 0.4rem;
}

.skel-line--eyebrow { height: 0.55rem; width: 5.5rem; }
.skel-line--title { height: 1.15rem; width: 70%; }
.skel-line--card-title { height: 0.95rem; width: 48%; }
.skel-line--hint { height: 0.65rem; width: 62%; }
.skel-line--name { height: 0.7rem; width: 72%; }
.skel-line--meta { height: 0.55rem; width: 48%; }

.skel-tabs {
  display: flex;
  gap: 0.45rem;
  overflow: hidden;
}

.skel-tab {
  height: 2rem;
  width: 5.5rem;
  border-radius: 999px;
  flex-shrink: 0;
}

.skel-card {
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 1rem;
  padding: 1.1rem;
  display: grid;
  gap: 0.75rem;
}

.skel-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem;
}

.skel-candidate {
  border: 1px solid #f0eeea;
  border-radius: 0.85rem;
  padding: 0.85rem 0.75rem;
  display: grid;
  justify-items: center;
  gap: 0.45rem;
}

.skel-avatar {
  width: 3.4rem;
  height: 3.4rem;
  border-radius: 999px;
}

.skel-nav {
  display: flex;
  justify-content: space-between;
  gap: 0.65rem;
  margin-top: 0.25rem;
}

.skel-nav__btn {
  height: 2.4rem;
  width: 5.5rem;
  border-radius: 0.7rem;
}

.skel-nav__btn--primary {
  width: 7.5rem;
  background: linear-gradient(90deg, #d7ebe7, #e8f5f2, #d7ebe7);
  background-size: 200% 100%;
}

.skel-hint {
  margin: 0;
  text-align: center;
  font-size: 0.74rem;
  color: #a8a29e;
}

@keyframes skel-shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .skel-line,
  .skel-tab,
  .skel-avatar,
  .skel-nav__btn {
    animation: none;
  }
}
</style>
