import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'

import { ROLE_LABELS } from '../context/auth-context'
import { useAuth } from '../context/useAuth'

const demoAccounts = [
  { email: 'admin.rh@demo.local', password: 'Admin123!', role: 'ADMIN_RH' },
  { email: 'analyste.rh@demo.local', password: 'Analyste123!', role: 'ANALYSTE_RH' },
  { email: 'manager.rh@demo.local', password: 'Manager123!', role: 'MANAGER_RH' },
  { email: 'dirigeant.rh@demo.local', password: 'Dirigeant123!', role: 'DIRIGEANT' },
]

export function LoginPage() {
  const { defaultPath, isAuthenticated, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('admin.rh@demo.local')
  const [password, setPassword] = useState('Admin123!')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (isAuthenticated) {
    return <Navigate to={defaultPath} replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setIsSubmitting(true)
    setError('')
    try {
      const user = await login({ email, password })
      const fallback = location.state?.from?.pathname || defaultPath
      navigate(fallback === '/login' ? defaultPath : fallback || defaultPath, { replace: true })
      return user
    } catch (apiError) {
      setError(apiError.message)
      return null
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleDemoAccount(account) {
    setEmail(account.email)
    setPassword(account.password)
    setError('')
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div>
          <p className="eyebrow">Acces securise</p>
          <h1>Pulse Workforce</h1>
          <p className="muted-copy">Connectez-vous avec un compte de demonstration pour acceder aux modules RH.</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email</span>
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" />
          </label>
          <label className="field">
            <span>Mot de passe</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
            />
          </label>
          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Connexion...' : 'Se connecter'}
          </button>
          {error ? <div className="error-banner">{error}</div> : null}
        </form>

        <div className="demo-account-grid">
          {demoAccounts.map((account) => (
            <button className="history-item" type="button" key={account.role} onClick={() => handleDemoAccount(account)}>
              <strong>{ROLE_LABELS[account.role]}</strong>
              <span>{account.email}</span>
            </button>
          ))}
        </div>
      </section>
    </main>
  )
}
