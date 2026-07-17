import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

/** Election Committee only — fraud / USSD ops */
const ecRoles = ['admin', 'sub_ec']
/** EC + auditor — elections, results, monitor */
const electionViewerRoles = ['admin', 'sub_ec', 'auditor']
/** Election custody belongs to EC and auditors, never platform Super Admin. */
const strongroomRoles = ['admin', 'sub_ec', 'auditor']
/** Vote-cast audits require vault unlock — Super Admin excluded. */
const auditVaultRoles = ['admin', 'sub_ec', 'auditor']
/** Platform + election oversight dashboards */
const staffDashboardRoles = ['auditor', 'admin', 'sub_ec', 'super_admin']
const studentRoles = ['student', 'candidate']
const publicPaths = new Set(['/', '/login', '/otp'])

const INIT_GUARD_TIMEOUT_MS = 6000

function withTimeout(promise, ms) {
  return Promise.race([
    promise,
    new Promise((resolve) => setTimeout(resolve, ms)),
  ])
}

function layoutRoute(path, children, meta = {}) {
  return {
    path,
    component: () => import('../components/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, ...meta },
    children,
  }
}

function studentLayoutRoute(path, children, meta = {}) {
  return {
    path,
    component: () => import('../components/layouts/StudentLayout.vue'),
    meta: { requiresAuth: true, ...meta },
    children,
  }
}

const routes = [
  {
    path: '/',
    component: () => import('../views/HomeView.vue'),
    meta: { public: true },
  },
  {
    path: '/login',
    component: () => import('../views/auth/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/otp',
    component: () => import('../views/auth/OTPView.vue'),
    meta: { public: true, otpFlow: true },
  },
  {
    path: '/onboarding',
    component: () => import('../views/auth/StudentOnboardingView.vue'),
    meta: { requiresAuth: true, roles: studentRoles, onboarding: true },
  },
  {
    path: '/verify',
    redirect: '/strongroom',
  },

  studentLayoutRoute('/student', [
    { path: '', component: () => import('../views/student/StudentDashboardView.vue'), meta: { roles: studentRoles } },
    { path: 'results', component: () => import('../views/student/StudentResultsView.vue'), meta: { roles: studentRoles } },
    { path: 'results/:uuid', component: () => import('../views/student/StudentResultDetailView.vue'), meta: { roles: studentRoles } },
    // Absolute child paths keep StudentLayout mounted for sleek page transitions
    { path: '/vote/:uuid', component: () => import('../views/voting/VoteEntryView.vue'), meta: { roles: studentRoles } },
    { path: '/vote/:uuid/presence', component: () => import('../views/voting/PresenceCaptureView.vue'), meta: { roles: studentRoles } },
    { path: '/vote/:uuid/ballot', component: () => import('../views/voting/BallotWizardView.vue'), meta: { roles: studentRoles } },
    { path: '/vote/:uuid/confirmation', component: () => import('../views/voting/ConfirmationView.vue'), meta: { roles: studentRoles } },
  ], { roles: studentRoles }),

  layoutRoute('/dashboard', [
    { path: '', component: () => import('../views/DashboardView.vue'), meta: { roles: staffDashboardRoles } },
  ], { roles: staffDashboardRoles }),

  layoutRoute('/elections', [
    { path: '', component: () => import('../views/elections/ElectionListView.vue'), meta: { roles: electionViewerRoles } },
    { path: ':uuid', component: () => import('../views/elections/ElectionDetailView.vue'), meta: { roles: electionViewerRoles } },
  ], { roles: electionViewerRoles }),

  layoutRoute('/results', [
    { path: '', component: () => import('../views/results/ResultsListView.vue'), meta: { roles: electionViewerRoles } },
    {
      path: ':uuid/certify',
      component: () => import('../views/results/CertificationCeremony.vue'),
      meta: { requiresAuth: true, roles: ['admin'] },
    },
    { path: ':uuid', component: () => import('../views/results/ResultDetailView.vue'), meta: { roles: electionViewerRoles } },
  ], { roles: electionViewerRoles }),

  layoutRoute('/strongroom', [
    { path: '', component: () => import('../views/admin/StrongroomView.vue'), meta: { roles: strongroomRoles } },
    { path: ':uuid', component: () => import('../views/admin/StrongroomDetailView.vue'), meta: { roles: strongroomRoles } },
  ], { roles: strongroomRoles }),

  layoutRoute('/users', [
    { path: '', component: () => import('../views/admin/UserManagementView.vue'), meta: { roles: ['super_admin'] } },
  ], { roles: ['super_admin'] }),

  layoutRoute('/institutions', [
    { path: '', component: () => import('../views/admin/InstitutionsView.vue'), meta: { roles: ['super_admin'] } },
    { path: ':uuid', component: () => import('../views/admin/InstitutionDetailView.vue'), meta: { roles: ['super_admin'] } },
  ], { roles: ['super_admin'] }),

  layoutRoute('/approvals', [
    { path: '', component: () => import('../views/admin/ECApprovalsView.vue'), meta: { roles: ['admin'] } },
  ], { roles: ['admin'] }),

  layoutRoute('/sub-ec', [
    { path: '', component: () => import('../views/admin/ECStructureView.vue'), meta: { roles: ['admin'] } },
  ], { roles: ['admin'] }),

  layoutRoute('/fraud', [
    { path: '', component: () => import('../views/admin/FraudDashboardView.vue'), meta: { roles: ecRoles } },
  ], { roles: ecRoles }),

  layoutRoute('/ussd', [
    { path: '', component: () => import('../views/admin/USSDMonitorView.vue'), meta: { roles: ecRoles } },
    { path: ':uuid', component: () => import('../views/admin/USSDSessionDetailView.vue'), meta: { roles: ecRoles } },
  ], { roles: ecRoles }),

  layoutRoute('/audit', [
    { path: '', component: () => import('../views/admin/AuditLogsView.vue'), meta: { roles: auditVaultRoles } },
  ], { roles: auditVaultRoles }),

  layoutRoute('/operations', [
    { path: '', component: () => import('../views/admin/OperationsCenterView.vue'), meta: { roles: ['super_admin'] } },
  ], { roles: ['super_admin'] }),

  layoutRoute('/settings', [
    { path: '', component: () => import('../views/admin/SettingsView.vue'), meta: { roles: ['super_admin'] } },
  ], { roles: ['super_admin'] }),

  layoutRoute('/categories', [
    { path: '', component: () => import('../views/admin/AcademicStructureView.vue'), meta: { roles: ['super_admin', 'admin'] } },
  ], { roles: ['super_admin', 'admin'] }),

  layoutRoute('/register', [
    { path: '', component: () => import('../views/admin/InstitutionRegisterView.vue'), meta: { roles: ['admin'] } },
  ], { roles: ['admin'] }),

  // Architecture naming aliases (old paths)
  { path: '/academic', redirect: '/categories' },
  { path: '/ec-structure', redirect: '/sub-ec' },

  {
    path: '/monitor/:uuid',
    component: () => import('../views/admin/ElectionMonitorRoom.vue'),
    meta: { requiresAuth: true, roles: electionViewerRoles },
  },
  {
    path: '/elections/:uuid/monitor',
    redirect: (to) => `/monitor/${to.params.uuid}`,
  },

  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, saved) {
    if (saved) return saved
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
})

function isPublicRoute(to) {
  if (publicPaths.has(to.path)) return true
  return to.matched.some((record) => record.meta.public)
}

function requiresAuth(to) {
  return to.matched.some((record) => record.meta.requiresAuth)
}

function getRequiredRoles(to) {
  return [...new Set(to.matched.flatMap((record) => record.meta.roles || []))]
}

function userHasRequiredRoles(authStore, requiredRoles) {
  if (requiredRoles.length === 0) return true
  const role = authStore.roleName
  if (requiredRoles.includes(role)) return true
  if (requiredRoles.includes('super_admin') && authStore.isSuperAdmin) return true
  if (requiredRoles.includes('admin') && authStore.isElectionManager) return true
  if (requiredRoles.includes('sub_ec') && authStore.isSubEC) return true
  if (requiredRoles.includes('auditor') && authStore.isAuditor) return true
  if (requiredRoles.some((r) => studentRoles.includes(r)) && authStore.isStudent) return true
  return false
}

function clearStuckOverlays() {
  if (typeof document === 'undefined') return
  document.querySelectorAll('.p-dialog-mask').forEach((el) => {
    if (!el.querySelector('.p-dialog')) el.remove()
  })
  document.body.classList.remove('p-overflow-hidden')
  document.documentElement.style.removeProperty('overflow')
  document.body.style.removeProperty('overflow')
  document.body.style.removeProperty('pointer-events')
}

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  // Always sync-restore tokens first so a refresh never looks logged-out.
  if (!authStore.isAuthenticated) {
    authStore.restoreCachedSession()
  }

  if (!authStore.initialized) {
    await withTimeout(authStore.initialize(), INIT_GUARD_TIMEOUT_MS)
    if (!authStore.initialized) {
      authStore.initialized = true
    }
    // Re-apply cache after initialize in case an error cleared flags incorrectly.
    if (!authStore.isAuthenticated) {
      authStore.restoreCachedSession()
    }
  }

  // Always allow OTP page during verification
  if (to.path === '/otp' && (to.query.sessionId || authStore.pendingOtp)) {
    return true
  }

  if (isPublicRoute(to)) {
    // Signed-in users should not stay on login
    if (to.path === '/login' && authStore.isAuthenticated && authStore.homeRoute !== '/login') {
      return authStore.homeRoute
    }
    return true
  }

  if (requiresAuth(to) && !authStore.isAuthenticated) {
    if (authStore.restoreCachedSession()) {
      return true
    }
    return to.path === '/login' ? true : '/login'
  }

  if (authStore.isAuthenticated && to.path === '/onboarding') {
    return '/student'
  }

  const requiredRoles = getRequiredRoles(to)
  if (requiredRoles.length && !userHasRequiredRoles(authStore, requiredRoles)) {
    // Role flags can be missing right after OTP if /me hydrate is slow — retry once
    if (authStore.isAuthenticated && !authStore.roleName) {
      try {
        await withTimeout(authStore.fetchMe(), 4000)
      } catch {
        // fall through
      }
      if (userHasRequiredRoles(authStore, requiredRoles)) {
        return true
      }
    }
    const hasStoredTokens = !!(
      localStorage.getItem('access_token') || localStorage.getItem('refresh_token')
    )
    const home = authStore.homeRoute
    if (home === '/login') {
      if (!hasStoredTokens) {
        authStore.clearLocalStorage()
        return '/login'
      }
      // Tokens exist but role is not hydrated yet — allow navigation instead of forcing logout.
      return true
    }
    return to.path === home ? true : home
  }

  return true
})

router.afterEach(() => {
  clearStuckOverlays()
})

router.onError((error) => {
  const message = String(error?.message || error || '')
  const isChunkError = /Failed to fetch dynamically imported module|Importing a module script failed|Loading chunk|ChunkLoadError/i.test(message)
  if (isChunkError && typeof window !== 'undefined') {
    const key = 'vb_chunk_reload'
    const last = Number(sessionStorage.getItem(key) || 0)
    if (Date.now() - last > 10000) {
      sessionStorage.setItem(key, String(Date.now()))
      window.location.reload()
    }
  }
})

export default router
