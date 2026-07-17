<template>
  <div class="home">
    <div class="home-bg" aria-hidden="true">
      <span
        v-for="orb in orbs"
        :key="orb.id"
        class="home-bg__orb"
        :style="orb.style"
      />
    </div>

    <div class="home-shell">
      <header class="home-brand">
        <span class="home-brand__mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
          </svg>
        </span>
        <span class="home-brand__name">Vote<span>Bridge</span></span>
      </header>

      <main class="home-main">
        <section class="home-copy">
          <p class="home-kicker">Campus elections</p>
          <h1 class="home-title">
            <span class="home-title__brand">VoteBridge</span>
            <em>Your vote. Your future.</em>
          </h1>
          <p class="home-lede">
            Secure, transparent student elections — cast your ballot with confidence.
          </p>

          <div class="home-actions">
            <router-link
              v-if="authStore.isAuthenticated"
              :to="authStore.homeRoute"
              class="home-btn home-btn--primary"
            >
              Go to dashboard
              <i class="fas fa-arrow-right" aria-hidden="true"></i>
            </router-link>
            <template v-else>
              <router-link to="/login" class="home-btn home-btn--primary">
                Sign in to vote
                <i class="fas fa-arrow-right" aria-hidden="true"></i>
              </router-link>
            </template>
          </div>
        </section>

        <section class="home-visual" aria-label="Sealed ballot box">
          <div class="home-visual__compose">
            <div class="home-orbit">
              <span class="home-orbit__glow" aria-hidden="true" />

              <span class="home-orbit__ring home-orbit__ring--a" aria-hidden="true">
                <span class="home-orbit__spoke" style="--a: 28deg">
                  <i class="home-orbit__node" />
                </span>
              </span>
              <span class="home-orbit__ring home-orbit__ring--b" aria-hidden="true">
                <span class="home-orbit__spoke" style="--a: 130deg">
                  <i class="home-orbit__node" />
                </span>
                <span class="home-orbit__spoke" style="--a: 255deg">
                  <i class="home-orbit__node home-orbit__node--soft" />
                </span>
              </span>
              <span class="home-orbit__ring home-orbit__ring--c" aria-hidden="true">
                <span class="home-orbit__spoke" style="--a: 200deg">
                  <i class="home-orbit__node" />
                </span>
              </span>
              <span class="home-orbit__ring home-orbit__ring--d" aria-hidden="true">
                <span class="home-orbit__spoke" style="--a: 70deg">
                  <i class="home-orbit__node home-orbit__node--soft" />
                </span>
              </span>

              <div class="home-orbit__core">
                <img
                  class="home-visual__img"
                  src="/images/ballot-box-hero.png?v=5"
                  width="1024"
                  height="1024"
                  alt="Transparent sealed Electoral Commission ballot box filled with ballots"
                  decoding="async"
                  fetchpriority="high"
                  draggable="false"
                />
              </div>
            </div>

            <div class="home-integrity" aria-label="Election integrity">
              <p class="home-integrity__kicker">Election integrity</p>
              <ul class="home-integrity__list">
                <li
                  v-for="line in integrityLines"
                  :key="line.id"
                  class="home-integrity__line"
                  :class="`from-${line.from}`"
                  :style="{ '--d': line.delay }"
                >
                  {{ line.text }}
                </li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>
</template><script setup>
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const integrityLines = [
  { id: 'sealed', text: 'Sealed. Counted. Trusted.', from: 'left', delay: '1.0s' },
  { id: 'one', text: 'One voter. One vote.', from: 'right', delay: '2.6s' },
  { id: 'chain', text: 'Tamper-evident audit trail', from: 'bottom', delay: '4.2s' },
  { id: 'truth', text: 'Integrity you can verify', from: 'top', delay: '5.8s' },
]

const orbs = [
  { id: 1, style: { width: '220px', height: '220px', top: '12%', left: '8%', animationDuration: '18s', animationDelay: '0s' } },
  { id: 2, style: { width: '280px', height: '280px', top: '58%', left: '18%', animationDuration: '22s', animationDelay: '2s' } },
  { id: 3, style: { width: '190px', height: '190px', top: '18%', left: '72%', animationDuration: '16s', animationDelay: '1s' } },
  { id: 4, style: { width: '260px', height: '260px', top: '62%', left: '68%', animationDuration: '24s', animationDelay: '3.5s' } },
  { id: 5, style: { width: '160px', height: '160px', top: '40%', left: '48%', animationDuration: '20s', animationDelay: '5s' } },
]
</script>

<style scoped>
.home {
  --home-ink: #102a43;
  --home-muted: #627d98;
  --home-accent: #0f766e;
  --home-accent-soft: #14b8a6;

  position: relative;
  isolation: isolate;
  min-height: 100vh;
  min-height: 100dvh;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  color: var(--home-ink);
  font-family: 'Plus Jakarta Sans', ui-sans-serif, system-ui, sans-serif;
}

.home-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
  background: linear-gradient(to bottom right, #f8fafc, #ffffff, rgba(236, 253, 245, 0.55));
}

.home-bg__orb {
  position: absolute;
  border-radius: 999px;
  background: rgba(167, 243, 208, 0.18);
  animation: home-float ease-in-out infinite;
  will-change: transform, opacity;
  opacity: 0.55;
}

.home-shell {
  position: relative;
  z-index: 1;
  height: 100%;
  max-width: 72rem;
  margin: 0 auto;
  padding: 1.25rem 1.25rem 1.5rem;
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 0.75rem;
}

.home-brand {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  width: fit-content;
}

.home-brand__mark {
  width: 2.15rem;
  height: 2.15rem;
  border-radius: 0.7rem;
  display: grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(145deg, var(--home-accent-soft), var(--home-accent));
  box-shadow: 0 10px 24px rgba(15, 118, 110, 0.22);
}

.home-brand__mark svg {
  width: 1.05rem;
  height: 1.05rem;
}

.home-brand__name {
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1.25;
  color: var(--home-ink);
  overflow: visible;
}

.home-brand__name span {
  color: var(--home-accent);
}

.home-main {
  display: grid;
  align-items: center;
  gap: 1.5rem;
  min-height: 0;
}

.home-copy {
  display: grid;
  gap: 0.85rem;
  max-width: 34rem;
  animation: copy-rise 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.home-kicker {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--home-accent);
}

.home-title {
  margin: 0;
  display: grid;
  gap: 0.45rem;
  font-size: clamp(2.35rem, 7vw, 4.25rem);
  font-weight: 800;
  letter-spacing: -0.045em;
  line-height: 1.15;
  color: var(--home-ink);
  overflow: visible;
}

.home-title__brand {
  display: block;
  font-size: clamp(2.7rem, 8vw, 4.75rem);
  letter-spacing: -0.05em;
  line-height: 1.2;
  padding: 0.06em 0.02em 0.14em 0;
  /* Keep descenders (g) fully visible with clipped gradient text */
  background: linear-gradient(120deg, #0f766e 0%, #0ea5a4 45%, #1d4ed8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
  overflow: visible;
}

.home-title em {
  display: block;
  font-style: normal;
  font-size: 0.52em;
  font-weight: 650;
  letter-spacing: -0.03em;
  color: var(--home-muted);
  max-width: 14ch;
}

.home-lede {
  margin: 0;
  max-width: 28rem;
  font-size: clamp(0.95rem, 2.2vw, 1.12rem);
  line-height: 1.55;
  color: var(--home-muted);
}

.home-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  padding-top: 0.35rem;
}

.home-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-height: 2.85rem;
  padding: 0.7rem 1.2rem;
  border-radius: 999px;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  text-decoration: none;
  transition:
    transform 0.25s cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 0.25s ease,
    background 0.2s ease,
    border-color 0.2s ease;
}

.home-btn--primary {
  background: var(--home-ink);
  color: #fff;
  box-shadow: 0 12px 28px rgba(16, 42, 67, 0.18);
}

.home-btn--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 32px rgba(16, 42, 67, 0.22);
}

.home-btn--primary i {
  font-size: 0.72rem;
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.home-btn--primary:hover i {
  transform: translateX(3px);
}

.home-visual {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 0;
}

.home-visual__compose {
  position: relative;
  width: min(100%, 30rem);
  display: grid;
  justify-items: center;
}

.home-orbit {
  --orbit-node: #0f766e;
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  /* Leave room so the caption plate can sit in the lower frame */
  padding-bottom: 2.75rem;
}

.home-integrity {
  position: absolute;
  left: 50%;
  bottom: 0.15rem;
  z-index: 4;
  width: min(92%, 21.5rem);
  padding: 0.9rem 1.1rem 0.95rem;
  border-radius: 1rem;
  background:
    linear-gradient(165deg, rgba(255, 255, 255, 0.96), rgba(236, 253, 245, 0.88));
  border: 1px solid rgba(15, 118, 110, 0.14);
  box-shadow:
    0 16px 36px rgba(16, 42, 67, 0.1),
    0 1px 0 rgba(255, 255, 255, 0.95) inset;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  animation: integrity-panel-in 0.85s cubic-bezier(0.16, 1, 0.3, 1) 0.45s both;
}

.home-integrity__kicker {
  margin: 0 0 0.55rem;
  font-size: 0.66rem;
  font-weight: 750;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--home-accent);
}

.home-integrity__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.4rem;
}

.home-integrity__line {
  margin: 0;
  font-size: clamp(0.92rem, 1.45vw, 1.05rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.3;
  color: #1f2937;
  opacity: 0;
  animation: integrity-in 1.05s cubic-bezier(0.16, 1, 0.3, 1) var(--d, 1s) both;
  will-change: transform, opacity, filter;
}

.home-integrity__line.from-left {
  --ox: -1.5rem;
  --oy: 0;
}

.home-integrity__line.from-right {
  --ox: 1.5rem;
  --oy: 0;
}

.home-integrity__line.from-top {
  --ox: 0;
  --oy: -1.15rem;
}

.home-integrity__line.from-bottom {
  --ox: 0;
  --oy: 1.15rem;
}

.home-orbit__glow {
  position: absolute;
  inset: 18%;
  border-radius: 999px;
  background: radial-gradient(closest-side, rgba(16, 185, 129, 0.12), transparent 72%);
  filter: blur(22px);
  z-index: 0;
  pointer-events: none;
}

.home-orbit__ring {
  position: absolute;
  inset: var(--inset, 6%);
  border-radius: 999px;
  border: 1px solid rgba(15, 118, 110, 0.2);
  pointer-events: none;
  z-index: 1;
  animation: orbit-spin var(--spin, 28s) linear infinite;
  will-change: transform;
}

.home-orbit__ring--a {
  --inset: 2%;
  --spin: 44s;
  border-color: rgba(15, 118, 110, 0.12);
}

.home-orbit__ring--b {
  --inset: 8%;
  --spin: 34s;
  animation-direction: reverse;
  border-color: rgba(15, 118, 110, 0.18);
}

.home-orbit__ring--c {
  --inset: 15%;
  --spin: 26s;
  border-color: rgba(15, 118, 110, 0.24);
}

.home-orbit__ring--d {
  --inset: 22%;
  --spin: 38s;
  animation-direction: reverse;
  border-color: rgba(16, 42, 67, 0.1);
}

.home-orbit__spoke {
  position: absolute;
  inset: 0;
  transform: rotate(var(--a, 0deg));
}

.home-orbit__node {
  position: absolute;
  top: 0;
  left: 50%;
  width: 0.52rem;
  height: 0.52rem;
  margin: -0.26rem 0 0 -0.26rem;
  border-radius: 999px;
  background: var(--orbit-node);
  box-shadow:
    0 0 0 3px rgba(15, 118, 110, 0.1),
    0 0 10px rgba(15, 118, 110, 0.28);
}

.home-orbit__node--soft {
  width: 0.36rem;
  height: 0.36rem;
  margin: -0.18rem 0 0 -0.18rem;
  background: #14b8a6;
  opacity: 0.85;
  box-shadow:
    0 0 0 2px rgba(20, 184, 166, 0.12),
    0 0 8px rgba(20, 184, 166, 0.25);
}

.home-orbit__core {
  position: relative;
  z-index: 2;
  width: 66%;
  aspect-ratio: 1;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 50% 40%, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.72) 68%, transparent);
  box-shadow:
    0 0 0 1px rgba(15, 118, 110, 0.1),
    0 12px 32px rgba(16, 42, 67, 0.08);
  overflow: hidden;
  animation: hero-float 7s ease-in-out infinite;
  will-change: transform;
}

.home-visual__img {
  width: 90%;
  height: 90%;
  object-fit: contain;
  display: block;
  background: transparent;
  user-select: none;
  -webkit-user-drag: none;
}

@keyframes orbit-spin {
  to { transform: rotate(360deg); }
}

@keyframes hero-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-0.45rem); }
}

@keyframes home-float {
  0%, 100% {
    transform: translate3d(0, 0, 0) scale(1);
    opacity: 0.4;
  }
  50% {
    transform: translate3d(0, -32px, 0) scale(1.1);
    opacity: 0.62;
  }
}

@keyframes copy-rise {
  from {
    opacity: 0;
    transform: translate3d(0, 1.1rem, 0);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
}

@keyframes integrity-panel-in {
  from {
    opacity: 0;
    transform: translateX(-50%) translate3d(0, 0.85rem, 0);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translate3d(0, 0, 0);
  }
}

@keyframes integrity-in {
  0% {
    opacity: 0;
    transform: translate3d(var(--ox, 0), var(--oy, 0.7rem), 0);
    filter: blur(5px);
  }
  60% {
    filter: blur(0);
  }
  100% {
    opacity: 1;
    transform: translate3d(0, 0, 0);
    filter: blur(0);
  }
}

@media (min-width: 960px) {
  .home-shell {
    padding: 1.5rem 2rem 1.75rem;
  }

  .home-main {
    grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr);
    gap: 2.75rem;
  }

  .home-visual {
    justify-content: flex-end;
  }

  .home-orbit {
    width: min(100%, 30rem);
    animation: frame-rise 1s cubic-bezier(0.16, 1, 0.3, 1) 0.12s both;
  }
}

@keyframes frame-rise {
  from {
    opacity: 0;
    transform: translate3d(1rem, 0.4rem, 0);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
}

@media (max-width: 959px) {
  .home {
    height: auto;
    min-height: 100vh;
    min-height: 100dvh;
    overflow: auto;
  }

  .home-shell {
    height: auto;
    min-height: 100vh;
    min-height: 100dvh;
  }

  .home-main {
    padding-bottom: 1.25rem;
  }

  .home-orbit {
    width: min(100%, 20rem);
  }
}

@media (prefers-reduced-motion: reduce) {
  .home-bg__orb,
  .home-visual__img,
  .home-orbit__core,
  .home-orbit__ring,
  .home-copy,
  .home-orbit,
  .home-integrity,
  .home-integrity__line {
    animation: none !important;
  }

  .home-bg__orb {
    opacity: 0.4;
  }

  .home-orbit__core {
    transform: none;
  }

  .home-integrity,
  .home-integrity__line {
    opacity: 1;
    filter: none;
  }

  .home-integrity {
    transform: translateX(-50%);
  }
}
</style>
