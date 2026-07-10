<template>
  <div class="min-h-screen h-screen overflow-hidden bg-gradient-to-br from-slate-50 via-white to-emerald-50/30">
    <!-- Animated background particles -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div v-for="i in 6" :key="i" class="absolute rounded-full bg-emerald-200/20 animate-float"
        :class="[
          'w-' + (Math.random() * 32 + 16).toFixed(0) + ' h-' + (Math.random() * 32 + 16).toFixed(0),
          'top-' + (Math.random() * 80 + 10).toFixed(0) + ' left-' + (Math.random() * 80 + 10).toFixed(0)
        ]"
        :style="{
          animationDuration: (Math.random() * 10 + 15) + 's',
          animationDelay: (Math.random() * 5) + 's'
        }"
      ></div>
    </div>

    <!-- Main content - full viewport height -->
    <div class="relative h-full flex flex-col">
      <!-- Navigation -->
      <nav class="flex-shrink-0 px-4 sm:px-6 lg:px-8 py-4">
        <div class="max-w-7xl mx-auto flex justify-between items-center">
          <div class="flex items-center space-x-2.5">
            <div class="w-9 h-9 bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/25">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
            </div>
            <span class="text-xl font-bold text-gray-900 tracking-tight">Voter<span class="text-emerald-600">B</span></span>
          </div>
          <div class="flex items-center space-x-3 sm:space-x-4">
            <router-link to="/verify" class="hidden sm:block text-sm font-medium text-gray-500 hover:text-gray-700 transition-colors">
              Verify Vote
            </router-link>
            <router-link to="/login" class="px-5 py-2.5 bg-white text-gray-700 text-sm font-medium rounded-xl border border-gray-200 hover:border-emerald-300 hover:shadow-md transition-all duration-300 shadow-sm">
              Sign In
            </router-link>
            <router-link to="/login" class="px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white text-sm font-medium rounded-xl hover:shadow-lg hover:shadow-emerald-500/30 transition-all duration-300 shadow-sm">
              Get Started
            </router-link>
          </div>
        </div>
      </nav>

      <!-- Hero - centered vertically -->
      <div class="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-8">
        <div class="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          <!-- Left Content -->
          <div class="space-y-6">
            <div class="inline-flex items-center gap-2.5 bg-white/80 backdrop-blur-sm border border-gray-200/80 rounded-full px-4 py-1.5 shadow-sm">
              <span class="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></span>
              <span class="text-sm font-medium text-gray-700">Trusted • Secure • Transparent</span>
            </div>
            
            <h1 class="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-bold text-gray-900 leading-[1.1] tracking-tight">
              Your Voice,
              <br />
              <span class="bg-gradient-to-r from-emerald-500 to-teal-500 bg-clip-text text-transparent">Your Vote</span>
            </h1>
            
            <p class="text-lg sm:text-xl text-gray-500 max-w-lg leading-relaxed">
              Secure, transparent campus elections. Cast your vote with confidence 
              using our trusted multi-channel platform.
            </p>
            
            <div class="flex flex-wrap gap-4 pt-2">
              <router-link to="/login" class="group px-8 py-3.5 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-medium rounded-xl hover:shadow-xl hover:shadow-emerald-500/30 transition-all duration-300 flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                </svg>
                Vote Now
                <svg class="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
                </svg>
              </router-link>
              <router-link to="/verify" class="px-8 py-3.5 bg-white/80 backdrop-blur-sm border border-gray-200 text-gray-700 font-medium rounded-xl hover:border-emerald-300 hover:shadow-lg transition-all duration-300 flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>
                </svg>
                Verify Vote
              </router-link>
            </div>
            
            <div class="flex flex-wrap items-center gap-6 text-sm text-gray-400 pt-2">
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                </svg>
                <span>OTP Protected</span>
              </div>
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                </svg>
                <span>Blockchain-ready</span>
              </div>
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                </svg>
                <span>Instant Results</span>
              </div>
            </div>
          </div>

          <!-- Right - Ballot Visual -->
          <div class="flex justify-center lg:justify-end">
            <div class="relative w-full max-w-sm lg:max-w-md">
              <!-- Glass card -->
              <div class="bg-white/60 backdrop-blur-xl rounded-3xl border border-white/80 shadow-2xl p-6 sm:p-8">
                <!-- Header -->
                <div class="flex items-center justify-between mb-5">
                  <div class="flex items-center gap-2.5">
                    <div class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                    <span class="text-xs font-medium text-gray-400 tracking-wider uppercase">Live Ballot</span>
                  </div>
                  <span class="text-xs bg-emerald-100 text-emerald-700 px-2.5 py-0.5 rounded-full font-medium">✓ VERIFIED</span>
                </div>

                <!-- Ballot items -->
                <div class="space-y-3">
                  <div class="flex items-center gap-3.5 p-3.5 bg-white/80 rounded-xl border border-emerald-100/80 shadow-sm">
                    <div class="flex-shrink-0 w-5 h-5 border-2 border-emerald-500 rounded-full flex items-center justify-center">
                      <div class="w-2.5 h-2.5 bg-emerald-500 rounded-full"></div>
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-semibold text-gray-800">SRC Elections 2026</p>
                      <p class="text-xs text-gray-400">President • 3 candidates</p>
                    </div>
                    <span class="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">✓ VOTED</span>
                  </div>

                  <div class="flex items-center gap-3.5 p-3.5 bg-white/60 rounded-xl border border-gray-100/80">
                    <div class="flex-shrink-0 w-5 h-5 border-2 border-gray-300 rounded-full"></div>
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-semibold text-gray-800">Faculty Elections</p>
                      <p class="text-xs text-gray-400">Dean • 2 candidates</p>
                    </div>
                    <span class="text-xs text-gray-400">PENDING</span>
                  </div>

                  <div class="flex items-center gap-3.5 p-3.5 bg-white/60 rounded-xl border border-gray-100/80">
                    <div class="flex-shrink-0 w-5 h-5 border-2 border-gray-300 rounded-full"></div>
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-semibold text-gray-800">Departmental Elections</p>
                      <p class="text-xs text-gray-400">HoD • 4 candidates</p>
                    </div>
                    <span class="text-xs text-gray-400">PENDING</span>
                  </div>
                </div>

                <!-- Status bar -->
                <div class="mt-5 pt-4 border-t border-gray-100/60 flex items-center justify-between">
                  <div class="flex items-center gap-2 text-xs text-gray-400">
                    <svg class="w-3.5 h-3.5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                    </svg>
                    <span>End-to-end encrypted</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
                    <span class="text-xs text-gray-400 font-mono">● Live</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex-shrink-0 px-4 sm:px-6 lg:px-8 py-4 border-t border-gray-100/60">
        <div class="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-2 text-xs text-gray-400">
          <span>© 2026 VoterB — Campus Election Platform</span>
          <div class="flex items-center gap-4">
            <router-link to="/verify" class="hover:text-gray-600 transition-colors">Verify Vote</router-link>
            <router-link to="/login" class="hover:text-gray-600 transition-colors">Sign In</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// No logic needed – pure landing page
</script>

<style scoped>
@keyframes float {
  0%, 100% { transform: translateY(0px) scale(1); opacity: 0.3; }
  50% { transform: translateY(-30px) scale(1.1); opacity: 0.6; }
}

.animate-float {
  animation: float ease-in-out infinite;
}

/* Responsive adjustments */
@media (max-height: 700px) {
  .h-screen {
    min-height: 100vh;
    height: auto;
  }
  .flex-1 {
    padding-top: 1rem;
    padding-bottom: 1rem;
  }
}

@media (max-width: 640px) {
  .h-screen {
    min-height: 100vh;
    height: auto;
    overflow-y: auto;
  }
}
</style>
