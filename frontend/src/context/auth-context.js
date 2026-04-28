import { createContext } from 'react'

export const AuthContext = createContext(null)

export const ROLE_LABELS = {
  ADMIN_RH: 'Administrateur RH',
  ANALYSTE_RH: 'Analyste RH',
  MANAGER_RH: 'Manager RH',
  DIRIGEANT: 'Dirigeant',
}

export const ROLE_HOME = {
  ADMIN_RH: '/imports',
  ANALYSTE_RH: '/analytics',
  MANAGER_RH: '/dashboard',
  DIRIGEANT: '/dashboard',
}
