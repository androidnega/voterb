import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const adminRoles = ['admin', 'super_admin']
const ecViewerRoles = ['admin', 'auditor', 'super_admin']
const monitorRoles = ['admin', 'auditor', 'super_admin']
const auditorRoles = ['auditor', 'admin', 'super_admin']
const studentRoles = ['student', 'candidate']
const publicPaths = new Set(['/', '/login', '/otp', '/verify'])

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
    component: () => import('../views/PublicVerifyView.vue'),
    meta: { public: true },
  },

  studentLayoutRoute('/student', [
    { path: '', component: () => import('../views/student/StudentDashboardView.vue'), meta: { roles: studentRoles } },
    { path: 'results/:uuid', component: () => import('../views/student/StudentResultDetailView.vue'), meta: { roles: studentRoles } },
  ], { roles: studentRoles }),

  studentLayoutRoute('/vote/:uuid', [
    { path: '', component: () => import('../views/voting/VoteEntryView.vue'), meta: { roles: studentRoles } },
    { path: 'ballot', component: () => import('../views/voting/BallotWizardView.vue'), meta: { roles: studentRoles } },
    { path: 'confirmation', component: () => import('../views/voting/ConfirmationView.vue'), meta: { roles: studentRoles } },
  ], { roles: studentRoles }),

  layoutRoute('/dashboard', [
    { path: '', component: () => import('../views/DashboardView.vue'), meta: { roles: auditorRoles } },
  ], { roles: auditorRoles }),

  layoutRoute('/elections', [
    { path: '', component: () => import('../views/elections/ElectionListView.vue'), meta: { roles: ecViewerRoles } },
    { path: ':uuid', component: () => import('../views/elections/ElectionDetailView.vue'), meta: { roles: ecViewerRoles } },
  ], { roles: ecViewerRoles }),

  layoutRoute('/results', [
    { path: '', component: () => import('../views/results/ResultsListView.vue'), meta: { roles: ecViewerRoles } },
    { path: ':uuid', component: () => import('../views/results/ResultDetailView.vue'), meta: { roles: ecViewerRoles } },
  ], { roles: ecViewerRoles }),

  layoutRoute('/strongroom', [
    { path: '', component: () => import('../views/admin/StrongroomView.vue'), meta: { roles: auditorRoles } },
    { path: ':uuid', component: () => import('../views/admin/StrongroomDetailView.vue'), meta: { roles: auditorRoles } },
  ], { roles: auditorRoles }),

  layoutRoute('/users', [
    { path: '', component: () => import('../views/admin/UserManagementView.vue'), meta: { roles: ['super_admin'] } },
  ], { roles: ['super_admin'] }),

  layoutRoute('/fraud', [
    { path: '', component: () => import('../views/admin/FraudDashboardView.vue'), meta: { roles: adminRoles } },
  ], { roles: adminRoles }),

  layoutRoute('/ussd', [
    { path: '', component: () => import('../views/admin/USSDMonitorView.vue'), meta: { roles: adminRoles } },
    { path: ':uuid', component: () => import('../views/admin/USSDSessionDetailView.vue'), meta: { roles: adminRoles } },
  ], { roles: adminRoles }),

  layoutRoute('/audit', [
    { path: '', component: () => import('../views/admin/AuditLogsView.vue'), meta: { roles: auditorRoles } },
  ], { roles: auditorRoles }),

  layoutRoute('/operations', [
    { path: '', component: () => import('../views/admin/OperationsCenterView.vue'), meta: { roles: ['super_admin'] } },
  ], { roles: ['super_admin'] }),

  layoutRoute('/settings', [
    { path: '', component: () => import('../views/admin/SettingsView.vue'), meta: { roles: ['super_admin'] } },
  ], { roles: ['super_admin'] }),

  layoutRoute('/academic', [
    { path: '', component: () => import('../views/admin/AcademicStructureView.vue'), meta: { roles: ['super_admin'] } },
  ], { roles: ['super_admin'] }),

  {
    path: '/monitor/:uuid',
    component: () => import('../views/admin/ElectionMonitorRoom.vue'),
    meta: { requiresAuth: true, roles: monitorRoles },
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
  if (requiredRoles.some((r) => adminRoles.includes(r)) && authStore.isAdmin) return true
  if (requiredRoles.some((r) => ecViewerRoles.includes(r)) && (authStore.isAuditor || authStore.roleName === 'admin')) return true
  if (requiredRoles.some((r) => studentRoles.includes(r)) && authStore.isStudent) return true
  return false
}

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (!authStore.initialized) {
    await authStore.initialize()
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
    return to.path === '/login' ? true : '/login'
  }

  if (authStore.isAuthenticated && authStore.needsOnboarding) {
    if (to.path !== '/onboarding') {
      return to.path === '/onboarding' ? true : '/onboarding'
    }
    return true
  }

  if (authStore.isAuthenticated && to.path === '/onboarding' && !authStore.needsOnboarding) {
    return '/student'
  }

  const requiredRoles = getRequiredRoles(to)
  if (requiredRoles.length && !userHasRequiredRoles(authStore, requiredRoles)) {
    const home = authStore.homeRoute
    if (home === '/login') {
      authStore.clearLocalStorage()
      return '/login'
    }
    return to.path === home ? true : home
  }

  return true
})

export default router
