import { useEffect, useState, type ReactNode } from 'react'
import { loginUser, registerUser } from '../lib/api'
import type { SessionState } from '../types/api'
import { AuthContext } from './auth-context'

const SESSION_STORAGE_KEY = 'wallet-ledger-session'

function readStoredSession() {
  const stored = window.localStorage.getItem(SESSION_STORAGE_KEY)

  if (!stored) {
    return null
  }

  try {
    return JSON.parse(stored) as SessionState
  } catch {
    window.localStorage.removeItem(SESSION_STORAGE_KEY)
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<SessionState | null>(() => readStoredSession())

  useEffect(() => {
    if (!session) {
      window.localStorage.removeItem(SESSION_STORAGE_KEY)
      return
    }

    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session))
  }, [session])

  async function login(email: string, password: string) {
    const response = await loginUser({ email, password })

    setSession({
      accessToken: response.accessToken,
      user: response.user,
    })
  }

  async function register(payload: { name: string; email: string; password: string }) {
    await registerUser(payload)
    await login(payload.email, payload.password)
  }

  function logout() {
    setSession(null)
  }

  return (
    <AuthContext.Provider
      value={{
        session,
        isAuthenticated: Boolean(session?.accessToken),
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
