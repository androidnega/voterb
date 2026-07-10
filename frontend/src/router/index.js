import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const adminRoles = ['admin', 'super_admin']
const studentRoles = ['student', 'candidate']

function adminRoute(path, children, meta = {}) {
  return {
    path,
    component: () => import('../components/layouts/AdminLayout.vue'),
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
    meta: { public: true },
  },
  {
    path: '/verify',
    component: () => import('../views/PublicVerifyView.vue'),
    meta: { public: true },
  },

  {
    path: '/student',
    component: () => import('../views/student/StudentDashboardView.vue'),
    meta: { requiresAuth: true, roles: studentRoles },
  },
  {
    path: '/student/results/:uuid',
    component: () => import('../views/student/StudentResultDetailView.vue'),
    meta: { requiresAuth: true, roles: studentRoles },
  },
  {
    path: '/vote/:uuid',
    component: () => import('../views/voting/VoteEntryView.vue'),
    meta: { requiresAuth: true, roles: studentRoles },
  },
  {
    path: '/vote/:uuid/ballot',
    component: () => import('../views/voting/BallotWizardView.vue'),
    meta: { requiresAuth: true, roles: studentRoles },
  },
  {
    path: '/vote/:uuid/confirmation',
    component: () => import('../views/voting/ConfirmationView.vue'),
    meta: { requiresAuth: true, roles: studentRoles },
  },

  adminRoute('/dashboard', [
    { path: '', component: () => import('../views/DashboardView.vue'), meta: { roles: adminRoles } },
  ], { roles: adminRoles }),

  adminRoute('/elections', [
    { path: '', component: () => import('../views/elections/ElectionListView.vue'), meta: { roles: adminRoles } },
    { path: ':uuid', component: () => import('../views/elections/ElectionDetailView.vue'), meta: { roles: adminRoles } },
  ], { roles: adminRoles }),

  adminRoute('/results', [
    { path: '', component: () => import('../views/results/ResultsListView.vue'), meta: { roles: adminRoles } },
    { path: ':uuid', component: () => import('../views/results/ResultDetailView.vue'), meta: { roles: adminRoles } },
  ], { roles: adminRoles }),

  adminRoute('/strongroom', [
    { path: '', component: () => import('../views/admin/StrongroomView.vue'), meta: { roles: adminRoles } },
    { path: ':uuid', component: () => import('../views/admin/StrongroomDetailView.vue'), meta: { roles: adminRoles } },
  ], { roles: adminRoles }),

  adminRoute('/users', [
    { path: '', component: () => import('../views/admin/UserManagementView.vue'), meta: { roles: adminRoles } },
  ], { roles: adminRoles }),

  adminRoute('/fraud', [
    { path: '', component: () => import('../views/admin/FraudDashboardView.vue'), meta: { roles: adminRoles } },
  ], { roles: adminRoles }),

  adminRoute('/ussd', [
    { path: '', component: () => import('../views/admin/USSDMonitorView.vue'), meta: { roles: adminRoles } },
    { path: ':uuid', component: () => import('../views/admin/USSDSessionDetailView.vue'), meta: { roles: adminRoles } },
  ], { roles: adminRoles }),

  adminRoute('/audit', [
    { path: '', component: () => import('../views/admin/AuditLogsView.vue'), meta: { roles: adminRoles } },
  ], { roles: adminRoles }),

  adminRoute('/operations', [
    { path: '', component: () => import('../views/admin/OperationsCenterView.vue'), meta: { roles: ['super_admin'] } },
  ], { roles: ['super_admin'] }),

  adminRoute('/settings', [
    { path: '', component: () => import('../views/admin/SettingsView.vue'), meta: { roles: ['super_admin'] } },
  ], { roles: ['super_admin'] }),

  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function getRequiredRoles(to) {
  return [...new Set(to.matched.flatMap((record) => record.meta.roles || []))]
}

function userHasRequiredRoles(authStore, requiredRoles) {
  if (requiredRoles.length === 0) return true
  const role = authStore.roleName
  if (requiredRoles.includes(role)) return true
  if (requiredRoles.some((r) => adminRoles.includes(r)) && authStore.isAdmin) return true
  if (requiredRoles.some((r) => studentRoles.includes(r)) && authStore.isStudent) return true
  return false
}

function redirectForRole(authStore) {
  if (authStore.isStudent) return '/student'
  if (authStore.isAdmin) return '/dashboard'
  return '/login'
}

router.beforeEach((to) => {
  const authStore = useAuthStore()

  if (to.meta.public) return true

  if (!authStore.isAuthenticated) {
    return to.path === '/login' ? true : '/login'
  }

  const requiredRoles = getRequiredRoles(to)
  if (requiredRoles.length && !userHasRequiredRoles(authStore, requiredRoles)) {
    const dest = redirectForRole(authStore)
    return to.path === dest ? true : dest
  }

  return true
})

export default router
