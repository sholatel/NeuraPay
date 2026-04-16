import { createContext, useContext } from 'react'
import type { SessionState } from '../types/api'

export interface AuthContextValue {
  session: SessionState | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (payload: { name: string; email: string; password: string }) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }

  return context
}