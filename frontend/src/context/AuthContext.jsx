import { useCallback, useEffect, useMemo, useState } from 'react'

import { api, clearAuthToken, readAuthToken, setUnauthorizedHandler, storeAuthToken } from '../lib/api'
import { AuthContext, ROLE_HOME } from './auth-context'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isReady, setIsReady] = useState(() => !readAuthToken())

  const logout = useCallback(() => {
    clearAuthToken()
    setUser(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(logout)
    return () => setUnauthorizedHandler(null)
  }, [logout])

  useEffect(() => {
    const token = readAuthToken()
    if (!token) {
      return
    }

    let isCancelled = false
    api
      .me()
      .then((currentUser) => {
        if (!isCancelled) {
          setUser(currentUser)
        }
      })
      .catch(() => {
        if (!isCancelled) {
          clearAuthToken()
          setUser(null)
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setIsReady(true)
        }
      })

    return () => {
      isCancelled = true
    }
  }, [])

  const login = useCallback(async (credentials) => {
    const payload = await api.login(credentials)
    storeAuthToken(payload.accessToken)
    setUser(payload.user)
    return payload.user
  }, [])

  const value = useMemo(
    () => ({
      user,
      isReady,
      isAuthenticated: Boolean(user),
      defaultPath: user ? ROLE_HOME[user.role] || '/dashboard' : '/login',
      login,
      logout,
      hasRole: (roles) => {
        const allowedRoles = Array.isArray(roles) ? roles : [roles]
        return Boolean(user && allowedRoles.includes(user.role))
      },
    }),
    [isReady, login, logout, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
