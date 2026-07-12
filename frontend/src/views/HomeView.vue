<template>
  <div class="home">
    <div class="home-mesh" aria-hidden="true">
      <span class="home-mesh__blob home-mesh__blob--a" />
      <span class="home-mesh__blob home-mesh__blob--b" />
      <span class="home-mesh__blob home-mesh__blob--c" />
      <span class="home-mesh__grid" />
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
                Get started
                <i class="fas fa-arrow-right" aria-hidden="true"></i>
              </router-link>
              <router-link to="/verify" class="home-btn home-btn--ghost">
                Verify vote
              </router-link>
            </template>
          </div>
        </section>

        <section class="home-visual" aria-label="Election day">
          <div class="home-visual__stage">
            <span class="home-visual__aura" aria-hidden="true" />
            <div class="home-visual__frame">
              <picture>
                <source
                  type="image/webp"
                  srcset="/images/election-day-sm.webp 640w, /images/election-day.webp 900w"
                  sizes="(max-width: 900px) 90vw, 44vw"
                />
                <img
                  class="home-visual__img"
                  src="/images/election-day.jpg"
                  width="900"
                  height="599"
                  alt="Student holding a sealed Electoral Commission ballot box on election day"
                  decoding="async"
                  fetchpriority="high"
                />
              </picture>
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
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

.home-mesh {
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(120% 80% at 10% 15%, rgba(20, 184, 166, 0.22), transparent 55%),
    radial-gradient(90% 70% at 90% 20%, rgba(59, 130, 246, 0.16), transparent 50%),
    radial-gradient(80% 60% at 70% 90%, rgba(15, 118, 110, 0.18), transparent 55%),
    linear-gradient(160deg, #f7fbfa 0%, #eef6f4 42%, #e8f1f8 100%);
}

.home-mesh__blob {
  position: absolute;
  border-radius: 999px;
  filter: blur(48px);
  opacity: 0.55;
  animation: mesh-drift 18s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite alternate;
}

.home-mesh__blob--a {
  width: 28rem;
  height: 28rem;
  left: -8%;
  top: -12%;
  background: rgba(45, 212, 191, 0.45);
}

.home-mesh__blob--b {
  width: 22rem;
  height: 22rem;
  right: -6%;
  top: 18%;
  background: rgba(96, 165, 250, 0.35);
  animation-duration: 22s;
  animation-delay: -4s;
}

.home-mesh__blob--c {
  width: 26rem;
  height: 18rem;
  left: 28%;
  bottom: -14%;
  background: rgba(15, 118, 110, 0.28);
  animation-duration: 26s;
  animation-delay: -8s;
}

.home-mesh__grid {
  position: absolute;
  inset: 0;
  opacity: 0.28;
  background-image:
    linear-gradient(rgba(16, 42, 67, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16, 42, 67, 0.05) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 40%, #000 35%, transparent 80%);
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
  color: var(--home-ink);
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
  gap: 0.35rem;
  font-size: clamp(2.35rem, 7vw, 4.25rem);
  font-weight: 800;
  letter-spacing: -0.045em;
  line-height: 1.02;
  color: var(--home-ink);
}

.home-title__brand {
  font-size: clamp(2.7rem, 8vw, 4.75rem);
  letter-spacing: -0.05em;
  background: linear-gradient(120deg, #0f766e 0%, #0ea5a4 45%, #1d4ed8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
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

.home-btn--ghost {
  background: rgba(255, 255, 255, 0.55);
  color: var(--home-ink);
  border: 1px solid rgba(16, 42, 67, 0.1);
  backdrop-filter: blur(10px);
}

.home-btn--ghost:hover {
  transform: translateY(-2px);
  border-color: rgba(15, 118, 110, 0.35);
}

.home-visual {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 0;
}

.home-visual__stage {
  position: relative;
  width: min(100%, 34rem);
}

.home-visual__aura {
  position: absolute;
  inset: 12% -8% -10%;
  border-radius: 50%;
  background:
    radial-gradient(closest-side, rgba(20, 184, 166, 0.22), transparent 72%),
    radial-gradient(closest-side at 70% 40%, rgba(125, 211, 252, 0.18), transparent 70%);
  filter: blur(36px);
  z-index: 0;
  pointer-events: none;
}

.home-visual__frame {
  position: relative;
  z-index: 1;
  width: 100%;
  aspect-ratio: 900 / 599;
  border-radius: 1.5rem;
  overflow: hidden;
  background: #e8f2ef;
  box-shadow:
    0 2px 4px rgba(16, 42, 67, 0.04),
    0 18px 40px rgba(16, 42, 67, 0.1);
}

.home-visual__frame::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
  pointer-events: none;
  z-index: 2;
}

.home-visual__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: 70% center;
  display: block;
  transform: scale(1.05);
  transform-origin: 70% 42%;
  will-change: transform;
  animation: hero-zoom 16s cubic-bezier(0.22, 1, 0.36, 1) infinite alternate;
}

@keyframes hero-zoom {
  0% { transform: scale(1.03); }
  100% { transform: scale(1.1); }
}

@keyframes mesh-drift {
  0% { transform: translate3d(0, 0, 0) scale(1); }
  100% { transform: translate3d(3%, -4%, 0) scale(1.08); }
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

  .home-visual__stage {
    width: min(100%, 37rem);
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

  .home-visual__stage {
    width: min(100%, 28rem);
  }

  .home-visual__frame {
    border-radius: 1.25rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .home-mesh__blob,
  .home-visual__img,
  .home-copy,
  .home-visual__stage {
    animation: none !important;
  }

  .home-visual__img {
    transform: scale(1.04);
  }
}
</style>
