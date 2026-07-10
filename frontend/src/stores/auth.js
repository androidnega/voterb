import { defineStore } from 'pinia'
import api from '@/api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    pendingOtp: null,
  }),
  actions: {
    async login(identifier, password = null) {
      try {
        const requestData = { identifier }
        if (password) {
          requestData.password = password
        }
        
        const response = await api.post('/accounts/auth/login/', requestData)
        
        if (response.data.requires_password) {
          return { requires_password: true }
        }
        
        if (response.data.requires_otp) {
          this.pendingOtp = response.data.otp_session_id
          return { requires_otp: true }
        }
        
        this.setTokens(response.data)
        return { success: true }
      } catch (error) {
        if (error.response?.data?.requires_password) {
          return { requires_password: true }
        }
        throw error
      }
    },
    async verifyOtp(otpSessionId, code) {
      try {
        const response = await api.post('/accounts/auth/otp/verify/', { 
          otp_session_id: otpSessionId, 
          code 
        })
        this.setTokens(response.data)
        return { success: true }
      } catch (error) {
        console.error('OTP verification error:', error)
        throw error
      }
    },
    setTokens(data) {
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      localStorage.setItem('user_uuid', data.user_uuid)
      localStorage.setItem('session_uuid', data.session_uuid)
      if (data.role) {
        localStorage.setItem('user_role', data.role)
      }
      this.isAuthenticated = true
      this.user = { uuid: data.user_uuid, role: data.role }
      this.pendingOtp = null
    },
    clearLocalStorage() {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_uuid')
      localStorage.removeItem('session_uuid')
      localStorage.removeItem('user_role')
      this.isAuthenticated = false
      this.user = null
      this.pendingOtp = null
    },
    async logout() {
      try {
        await api.post('/accounts/auth/logout/', { 
          refresh: localStorage.getItem('refresh_token') 
        })
      } catch (e) {
        // Ignore errors on logout
      }
      this.clearLocalStorage()
    },
    async initialize() {
      const token = localStorage.getItem('access_token')
      if (!token) return
      try {
        const response = await api.get('/accounts/auth/me/')
        this.user = response.data
        this.isAuthenticated = true
      } catch (error) {
        console.error('Token validation failed, clearing session:', error)
        this.clearLocalStorage()
      }
    }
  }
})
