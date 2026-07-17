import { defineStore } from 'pinia'
import api from '@/api/client'

/** Normalize role from API payloads (string, { name }, role_name, flags). */
export function resolveRoleName(user) {
  if (!user) return ''
  if (typeof user.role_name === 'string' && user.role_name) return user.role_name
  if (user.is_superuser) return 'super_admin'
  if (typeof user.role === 'string' && user.role) return user.role
  if (typeof user.role === 'object' && user.role?.name) return user.role.name
  if (user.is_staff) return 'admin'
  if (user.index_number) return 'student'
  const cached = localStorage.getItem('user_role')
  if (cached) return cached
  return ''
}

function isStaffRole(role, user) {
  return ['admin', 'sub_ec', 'super_admin', 'auditor'].includes(role) ||
    !!user?.is_staff ||
    !!user?.is_superuser
}

function isStudentRole(role, user) {
  return role === 'student' || role === 'candidate' ||
    (!!user?.index_number && !isStaffRole(role, user))
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    initialized: false,
    bootstrapping: false,
    pendingOtp: null,
    isNewUser: false,
    needsOnboarding: false,
    roleName: null,
    isSuperAdmin: false,
    isElectionManager: false,
    isMainEC: false,
    isSubEC: false,
    isAuditor: false,
    isStudent: false,
    institution: null,
    ecMemberships: [],
    governance: null,
    sessionTimeoutMinutes: 20,
  }),

  getters: {
    isAdmin: (state) => state.isElectionManager || state.isSuperAdmin || state.isAuditor,
    homeRoute: (state) => {
      if (isStudentRole(state.roleName, state.user)) {
        return '/student'
      }
      if (isStaffRole(state.roleName, state.user)) return '/dashboard'
      return '/login'
    },
  },

  actions: {
    async login(identifier, password = null) {
      try {
        const requestData = { identifier }
        if (password) requestData.password = password

        const response = await api.post('/accounts/auth/login/', requestData, {
          timeout: 12000,
        })

        if (response.data.requires_password) {
          return { requires_password: true }
        }

        if (response.data.requires_otp) {
          this.pendingOtp = response.data.otp_session_id
          this.isNewUser = response.data.is_new_user || false
          return { requires_otp: true }
        }

        await this.applyAuthResponse(response.data)
        return { success: true, homeRoute: this.homeRoute }
      } catch (error) {
        if (error.response?.data?.requires_password) {
          return { requires_password: true }
        }
        throw error
      }
    },

    async verifyOtp(otpSessionId, code) {
      const response = await api.post('/accounts/auth/otp/verify/', {
        otp_session_id: otpSessionId,
        code,
      })
      await this.applyAuthResponse(response.data)
      return { success: true, homeRoute: this.homeRoute }
    },

    async resendOtp(otpSessionId) {
      const response = await api.post('/accounts/auth/otp/resend/', {
        otp_session_id: otpSessionId,
      })
      this.pendingOtp = response.data.otp_session_id
      return { success: true }
    },

    async applyAuthResponse(data) {
      this.setTokens(data)
      try {
        await this.fetchMe()
      } catch (error) {
        // Tokens are valid enough to keep session; role already set from OTP payload.
        console.warn('Failed to hydrate /me after auth:', error)
      }
    },

    setTokens(data) {
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      if (data.user_uuid) localStorage.setItem('user_uuid', data.user_uuid)
      if (data.session_uuid) localStorage.setItem('session_uuid', data.session_uuid)

      const roleRaw = data.role ?? data.role_name
      const roleName = typeof roleRaw === 'string'
        ? roleRaw
        : (roleRaw?.name || '')

      if (roleName) localStorage.setItem('user_role', roleName)

      if (data.is_new_user || this.isNewUser) {
        this.isNewUser = true
        localStorage.setItem('is_new_user', 'true')
      }

      this.isAuthenticated = true
      this.pendingOtp = null
      localStorage.setItem('session_last_activity', String(Date.now()))

      // OTP returns role as a plain string — normalize before resolveRoles()
      this.user = {
        uuid: data.user_uuid,
        role: roleName ? { name: roleName } : null,
        role_name: roleName || null,
        is_superuser: !!data.is_superuser,
        is_staff: !!data.is_staff,
        index_number: data.index_number || null,
        onboarding_completed: data.onboarding_completed,
      }

      this.resolveRoles()
      this.syncOnboardingFlag()
    },

    async fetchMe() {
      const response = await api.get('/accounts/auth/me/')
      this.user = response.data
      this.isAuthenticated = true
      if (response.data?.session_timeout_minutes) {
        this.sessionTimeoutMinutes = Math.max(1, Number(response.data.session_timeout_minutes) || 20)
      }
      localStorage.setItem('session_last_activity', String(Date.now()))
      this.resolveRoles()
      this.syncOnboardingFlag()
      return this.user
    },

    resolveRoles() {
      const role = resolveRoleName(this.user)
      this.roleName = role || null
      this.isSuperAdmin = role === 'super_admin' || !!this.user?.is_superuser
      this.isMainEC = role === 'admin' || !!this.user?.is_main_ec
      this.isSubEC = role === 'sub_ec' || !!this.user?.is_sub_ec
      // Main EC and Sub EC can each manage elections in their own scope
      this.isElectionManager = this.isMainEC || this.isSubEC
      this.isAuditor = role === 'auditor'
      this.isStudent = isStudentRole(role, this.user)
      this.institution = this.user?.institution || null
      this.ecMemberships = Array.isArray(this.user?.ec_memberships) ? this.user.ec_memberships : []
      this.governance = this.user?.governance || null
      if (role) localStorage.setItem('user_role', role)
    },

    syncOnboardingFlag() {
      // Students authenticate via index + approved register + OTP.
      // Legacy faculty/department onboarding is retired.
      this.needsOnboarding = false
      this.isNewUser = false
      localStorage.removeItem('requires_onboarding')
      localStorage.removeItem('needs_onboarding')
      localStorage.removeItem('is_new_user')
      return false
    },

    clearLocalStorage() {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_uuid')
      localStorage.removeItem('session_uuid')
      localStorage.removeItem('user_role')
      localStorage.removeItem('is_new_user')
      localStorage.removeItem('needs_onboarding')
      localStorage.removeItem('requires_onboarding')
      localStorage.removeItem('session_last_activity')
      this.isAuthenticated = false
      this.user = null
      this.pendingOtp = null
      this.isNewUser = false
      this.needsOnboarding = false
      this.roleName = null
      this.isSuperAdmin = false
      this.isElectionManager = false
      this.isAuditor = false
      this.isStudent = false
    },

    async logout() {
      try {
        await api.post('/accounts/auth/logout/', {
          refresh: localStorage.getItem('refresh_token'),
        })
      } catch {
        // Ignore logout errors
      }
      this.clearLocalStorage()
      this.initialized = true
    },

    restoreCachedSession() {
      const accessToken = localStorage.getItem('access_token')
      const refreshToken = localStorage.getItem('refresh_token')
      if (!accessToken && !refreshToken) {
        return false
      }

      const cachedRole = localStorage.getItem('user_role') || ''
      this.user = {
        uuid: localStorage.getItem('user_uuid') || null,
        role_name: cachedRole || null,
        role: cachedRole ? { name: cachedRole } : null,
      }
      this.isAuthenticated = true
      this.resolveRoles()
      return true
    },

    async initialize() {
      if (this.initialized) return
      if (this.bootstrapping) {
        // Another bootstrap is in flight — wait briefly, then continue.
        const started = Date.now()
        while (this.bootstrapping && Date.now() - started < 8000) {
          await new Promise((r) => setTimeout(r, 40))
        }
        return
      }

      this.bootstrapping = true
      try {
        const hasStoredSession = this.restoreCachedSession()
        if (!hasStoredSession) {
          this.initialized = true
          return
        }

        try {
          await Promise.race([
            this.fetchMe(),
            new Promise((_, reject) =>
              setTimeout(() => reject(new Error('Auth bootstrap timeout')), 12000),
            ),
          ])
          this.isNewUser = localStorage.getItem('is_new_user') === 'true'
          this.syncOnboardingFlag()
        } catch (error) {
          const status = error?.response?.status
          const stillHasTokens = !!(
            localStorage.getItem('access_token') || localStorage.getItem('refresh_token')
          )
          if ((status === 401 || status === 403) && !stillHasTokens) {
            this.clearLocalStorage()
          } else if (status === 401 || status === 403) {
            // Refresh interceptor may have already cleared invalid tokens.
            if (!localStorage.getItem('access_token') && !localStorage.getItem('refresh_token')) {
              this.clearLocalStorage()
            } else {
              console.warn('Session hydration rejected; keeping cached login until next API call:', error)
            }
          } else {
            console.warn('Session hydration deferred; keeping cached login:', error)
          }
        }
        this.initialized = true
      } finally {
        this.bootstrapping = false
      }
    },
  },
})
