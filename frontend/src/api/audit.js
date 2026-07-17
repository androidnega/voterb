import api from './client'
import { getVaultToken } from './strongroom'

function vaultHeaders() {
  const token = getVaultToken()
  return token ? { 'X-Vault-Token': token } : {}
}

export const auditApi = {
  getMFA() {
    return api.get('/audit/mfa/', { headers: vaultHeaders() })
  },
  getAudit(params = {}) {
    return api.get('/audit/audit/', { params, headers: vaultHeaders() })
  },
  getCombined(params = {}) {
    return api.get('/audit/combined/', { params, headers: vaultHeaders() })
  },
  getVoteDetail(auditId) {
    return api.get(`/audit/${auditId}/`, { headers: vaultHeaders() })
  },
}
