const TOKEN_KEY = 'prototree_token'
const LAST_EMAIL_KEY = 'prototree_last_email'
const REMOVED_TEST_EMAILS = new Set<string>()

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function getLastLoginEmail() {
  const value = localStorage.getItem(LAST_EMAIL_KEY) ?? ''
  if (REMOVED_TEST_EMAILS.has(value.trim().toLowerCase())) {
    localStorage.removeItem(LAST_EMAIL_KEY)
    return ''
  }
  return value
}

export function setLastLoginEmail(email: string) {
  const normalized = email.trim().toLowerCase()
  if (normalized && !REMOVED_TEST_EMAILS.has(normalized)) {
    localStorage.setItem(LAST_EMAIL_KEY, normalized)
  }
}

export function clearLastLoginEmail() {
  localStorage.removeItem(LAST_EMAIL_KEY)
}
