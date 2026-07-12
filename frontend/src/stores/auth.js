import { defineStore } from 'pinia'
import api from '@/api/client'

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

function isAdminRole(role, user) {
  return ['admin', 'super_admin', 'auditor'].includes(role) ||
    !!user?.is_staff || !!user?.is_superuser
}

function isStudentRole(role, user) {
  return role === 'student' || role === 'candidate' ||
    (!!user?.index_number && !isAdminRole(role, user))
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    pendingOtp: null,
    isNewUser: false,
    requiresOnboarding: false,
    initialized: false,
    initPromise: null,
    bootstrapping: false,
  }),

  getters: {
    roleName: (state) => resolveRoleName(state.user),
    needsOnboarding: (state) => {
      if (!isStudentRole(resolveRoleName(state.user), state.user)) return false
      return state.requiresOnboarding || !state.user?.onboarding_completed
    },
    isSuperAdmin: (state) => {
      const role = resolveRoleName(state.user)
      return role === 'super_admin' || !!state.user?.is_superuser
    },
    isElectionManager: (state) => resolveRoleName(state.user) === 'admin',
    isAuditor: (state) => resolveRoleName(state.user) === 'auditor',
    isAdmin: (state) => isAdminRole(resolveRoleName(state.user), state.user),
    isStudent: (state) => isStudentRole(resolveRoleName(state.user), state.user),
    homeRoute: (state) => {
      const role = resolveRoleName(state.user)
      if (isStudentRole(role, state.user)) {
        if (state.requiresOnboarding || !state.user?.onboarding_completed) return '/onboarding'
        return '/student'
      }
      if (isAdminRole(role, state.user)) return '/dashboard'
      return '/login'
    },
  },

  actions: {
    async login(identifier, password = null) {
      const requestData = { identifier }
      if (password) requestData.password = password

      const response = await api.post('/accounts/auth/login/', requestData)

      if (response.data.requires_password) {
        return { requires_password: true }
      }

      if (response.data.requires_otp) {
        this.pendingOtp = response.data.otp_session_id
        this.isNewUser = response.data.is_new_user || false
        this.requiresOnboarding = response.data.requires_onboarding || false
        return {
          requires_otp: true,
          is_staff: response.data.is_staff,
          requires_onboarding: response.data.requires_onboarding || false,
        }
      }

      this.setTokens(response.data)
      await this.fetchMe()
      return { success: true, homeRoute: this.homeRoute }
    },

    async verifyOtp(otpSessionId, code) {
      const response = await api.post('/accounts/auth/otp/verify/', {
        otp_session_id: otpSessionId,
        code,
      })
      this.isNewUser = response.data.is_new_user || false
      this.requiresOnboarding = response.data.requires_onboarding || false
      await this.applyAuthResponse(response.data)
      return {
        success: true,
        homeRoute: this.homeRoute,
        requires_onboarding: this.requiresOnboarding,
      }
    },

    async applyAuthResponse(data) {
      this.setTokens(data)
      try {
        await this.fetchMe()
      } catch (error) {
        // Keep session from OTP/login payload if /me is temporarily unavailable
        console.warn('Profile fetch failed after auth; using token payload.', error)
        this.hydrateUserFromTokenPayload(data)
      }
    },

    hydrateUserFromTokenPayload(data) {
      this.user = {
        uuid: data.user_uuid,
        role_name: data.role_name || data.role || localStorage.getItem('user_role'),
        role: data.role_name || data.role ? { name: data.role_name || data.role } : null,
        is_staff: data.is_staff,
        is_superuser: data.is_superuser,
        index_number: data.index_number || null,
        onboarding_completed: data.onboarding_completed ?? false,
      }
      this.isAuthenticated = true
    },

    setTokens(data) {
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      localStorage.setItem('user_uuid', data.user_uuid)
      localStorage.setItem('session_uuid', data.session_uuid)

      const role = data.role_name || data.role
      if (role) localStorage.setItem('user_role', role)

      if (this.isNewUser) {
        localStorage.setItem('is_new_user', 'true')
      }
      if (this.requiresOnboarding) {
        localStorage.setItem('requires_onboarding', 'true')
      } else {
        localStorage.removeItem('requires_onboarding')
      }

      this.isAuthenticated = true
      this.pendingOtp = null
      this.hydrateUserFromTokenPayload(data)
    },

    async fetchMe() {
      const response = await api.get('/accounts/auth/me/')
      this.user = response.data
      this.isAuthenticated = true
      this.requiresOnboarding = !response.data.onboarding_completed && isStudentRole(
        resolveRoleName(this.user),
        this.user
      )
      const role = resolveRoleName(this.user)
      if (role) localStorage.setItem('user_role', role)
      return this.user
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
    },

    clearLocalStorage() {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_uuid')
      localStorage.removeItem('session_uuid')
      localStorage.removeItem('user_role')
      localStorage.removeItem('is_new_user')
      localStorage.removeItem('requires_onboarding')
      this.isAuthenticated = false
      this.user = null
      this.pendingOtp = null
      this.isNewUser = false
      this.requiresOnboarding = false
      this.initialized = false
      this.initPromise = null
      this.bootstrapping = false
    },

    async resendOtp() {
      return { success: false, error: 'Resend is not available yet. Please log in again.' }
    },

    async initialize() {
      if (this.initialized) return
      if (this.initPromise) return this.initPromise

      const token = localStorage.getItem('access_token')
      if (!token) {
        this.initialized = true
        return
      }

      this.initPromise = (async () => {
        try {
          await this.fetchMe()
        } catch {
          const role = localStorage.getItem('user_role')
          const userUuid = localStorage.getItem('user_uuid')
          if (token && userUuid) {
            this.isAuthenticated = true
            this.user = {
              uuid: userUuid,
              role_name: role,
              role: role ? { name: role } : null,
              is_staff: ['admin', 'super_admin', 'auditor'].includes(role),
              is_superuser: role === 'super_admin',
            }
          } else {
            this.clearLocalStorage()
          }
        } finally {
          this.initialized = true
          this.initPromise = null
        }
      })()

      return this.initPromise
    },
  },
})
