import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

/** Election Committee only — fraud / USSD ops */
const ecRoles = ['admin', 'sub_ec']
/** EC + auditor — elections, results, monitor */
const electionViewerRoles = ['admin', 'sub_ec', 'auditor']
/** Election custody belongs to EC and auditors, never platform Super Admin. */
const strongroomRoles = ['admin', 'sub_ec', 'auditor']
/** Platform + election oversight dashboards and audit */
const staffDashboardRoles = ['auditor', 'admin', 'sub_ec', 'super_admin']
const studentRoles = ['student', 'candidate']
const publicPaths = new Set(['/', '/login', '/otp'])

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
    { path: '', component: () => import('../views/admin/AuditLogsView.vue'), meta: { roles: staffDashboardRoles } },
  ], { roles: staffDashboardRoles }),

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
    // Role flags can be missing right after OTP if /me hydrate is slow — retry once
    if (authStore.isAuthenticated && !authStore.roleName) {
      try {
        await authStore.fetchMe()
      } catch {
        // fall through
      }
      if (userHasRequiredRoles(authStore, requiredRoles)) {
        return true
      }
    }
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
