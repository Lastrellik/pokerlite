import { useState } from 'react'
import './LoginModal.css'

const LOBBY_URL = import.meta.env.VITE_LOBBY_URL || 'http://localhost:8000'

export default function LoginModal({ onClose, onSuccess }) {
  const [isRegister, setIsRegister] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login'

      let body
      let headers = {}

      if (isRegister) {
        // Register uses JSON
        body = JSON.stringify({ username, password, email: email || null })
        headers['Content-Type'] = 'application/json'
      } else {
        // Login uses form data (OAuth2PasswordRequestForm)
        body = new URLSearchParams({ username, password })
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
      }

      const response = await fetch(`${LOBBY_URL}${endpoint}`, {
        method: 'POST',
        headers,
        body
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed')
      }

      // Store token and user info
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('username', data.user.username)
      localStorage.setItem('user_id', data.user.id)
      localStorage.setItem('avatar_id', data.user.avatar_id)

      onSuccess(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleGuestPlay = () => {
    // Clear any existing auth
    localStorage.removeItem('auth_token')
    localStorage.removeItem('username')
    localStorage.removeItem('user_id')
    localStorage.removeItem('avatar_id')
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content login-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>

        <h2>{isRegister ? 'Create Account' : 'Login'}</h2>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              required
              minLength={3}
              maxLength={50}
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
              minLength={6}
              autoComplete={isRegister ? 'new-password' : 'current-password'}
            />
          </div>

          {isRegister && (
            <div className="form-group">
              <label htmlFor="email">Email (optional)</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter email"
                autoComplete="email"
              />
            </div>
          )}

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Please wait...' : (isRegister ? 'Create Account' : 'Login')}
          </button>
        </form>

        <div className="auth-toggle">
          {isRegister ? (
            <>
              Already have an account?{' '}
              <button className="link-button" onClick={() => setIsRegister(false)}>
                Login
              </button>
            </>
          ) : (
            <>
              Don't have an account?{' '}
              <button className="link-button" onClick={() => setIsRegister(true)}>
                Sign up
              </button>
            </>
          )}
        </div>

        <div className="guest-option">
          <button className="btn-secondary" onClick={handleGuestPlay}>
            Continue as Guest
          </button>
        </div>
      </div>
    </div>
  )
}
