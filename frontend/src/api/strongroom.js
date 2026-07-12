import api from './client'

const VAULT_TOKEN_KEY = 'strongroom_vault_token'

export function getVaultToken() {
  return sessionStorage.getItem(VAULT_TOKEN_KEY)
}

export function setVaultToken(token) {
  if (token) sessionStorage.setItem(VAULT_TOKEN_KEY, token)
  else sessionStorage.removeItem(VAULT_TOKEN_KEY)
}

function vaultHeaders() {
  const token = getVaultToken()
  return token ? { 'X-Vault-Token': token } : {}
}

export const strongroomApi = {
  authenticate(password) {
    return api.post('/strongroom/vault/authenticate/', { password })
  },

  sessionStatus() {
    return api.get('/strongroom/vault/session/status/', { headers: vaultHeaders() })
  },

  closeSession() {
    return api.post('/strongroom/vault/session/close/', {}, { headers: vaultHeaders() })
  },

  list() {
    return api.get('/strongroom/elections/', { headers: vaultHeaders() })
  },

  detail(uuid) {
    return api.get(`/strongroom/elections/${uuid}/`, { headers: vaultHeaders() })
  },

  requestAccess(uuid, reason) {
    return api.post(`/strongroom/elections/${uuid}/access/`, { reason }, { headers: vaultHeaders() })
  },

  revealSeal(uuid, sealType, sealUuid) {
    return api.post(
      `/strongroom/elections/${uuid}/reveal-seal/`,
      { seal_type: sealType, seal_uuid: sealUuid },
      { headers: vaultHeaders() },
    )
  },

  lock(uuid) {
    return api.post(`/strongroom/elections/${uuid}/lock/`, {}, { headers: vaultHeaders() })
  },

  verifySeal(sealHash) {
    return api.post('/strongroom/public/verify/', { seal_hash: sealHash })
  },
}
