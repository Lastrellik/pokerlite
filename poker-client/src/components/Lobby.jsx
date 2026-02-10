/**
 * Lobby component - displays list of tables and allows creation/joining.
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLobby } from '../hooks/useLobby'
import CreateTableModal from './CreateTableModal'
import LoginModal from './LoginModal'
import './Lobby.css'

export default function Lobby() {
  const navigate = useNavigate()
  const { tables, loading, error, fetchTables } = useLobby()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [authToken, setAuthToken] = useState(localStorage.getItem('auth_token'))
  const [authUsername, setAuthUsername] = useState(localStorage.getItem('username'))
  const [chipCount, setChipCount] = useState(null)

  const LOBBY_URL = import.meta.env.VITE_LOBBY_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchTables()
    // Refresh table list every 5 seconds
    const interval = setInterval(fetchTables, 5000)
    return () => clearInterval(interval)
  }, [fetchTables])

  // Fetch chip count when authenticated
  useEffect(() => {
    if (authToken && authUsername) {
      fetch(`${LOBBY_URL}/api/auth/stack`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })
        .then(res => res.json())
        .then(data => {
          if (data.stack !== undefined) {
            setChipCount(data.stack)
          }
        })
        .catch(err => {
          console.error('Failed to fetch chip count:', err)
        })
    } else {
      setChipCount(null)
    }
  }, [authToken, authUsername, LOBBY_URL])

  const handleLoginSuccess = (token, username, userId, avatarId) => {
    setAuthToken(token)
    setAuthUsername(username)
    localStorage.setItem('auth_token', token)
    localStorage.setItem('username', username)
    localStorage.setItem('user_id', userId)
    localStorage.setItem('avatar_id', avatarId)
    setShowLoginModal(false)
  }

  const handleLogout = () => {
    setAuthToken(null)
    setAuthUsername(null)
    setChipCount(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('username')
    localStorage.removeItem('user_id')
    localStorage.removeItem('avatar_id')
  }

  const handleJoinTable = (tableId) => {
    navigate(`/table/${tableId}`)
  }

  return (
    <div className="lobby">
      <div className="lobby-header">
        <h1>🃏 PokerLite Lobby</h1>
        <div className="lobby-actions">
          {authToken && authUsername ? (
            <div className="auth-info">
              <span className="auth-username">{authUsername}</span>
              {chipCount !== null && (
                <span className="chip-count">💰 {chipCount} chips</span>
              )}
              <button onClick={handleLogout} className="btn-logout">
                Logout
              </button>
            </div>
          ) : (
            <button onClick={() => setShowLoginModal(true)} className="btn-login">
              Login / Sign Up
            </button>
          )}
          <button onClick={() => setShowCreateModal(true)} className="btn-create">
            + Create Table
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="tables-container">
        {loading && tables.length === 0 ? (
          <div className="loading">Loading tables...</div>
        ) : tables.length === 0 ? (
          <div className="empty-state">
            <p>No tables available</p>
            <p>Create one to get started!</p>
          </div>
        ) : (
          <div className="tables-grid">
            {tables.map(table => (
              <div key={table.table_id} className="table-card">
                <h3>{table.name}</h3>
                <div className="table-info">
                  <div className="info-row">
                    <span className="label">Blinds:</span>
                    <span className="value">${table.small_blind}/${table.big_blind}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Max Players:</span>
                    <span className="value">{table.max_players}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Turn Timeout:</span>
                    <span className="value">{table.turn_timeout_seconds}s</span>
                  </div>
                </div>
                <button
                  onClick={() => handleJoinTable(table.table_id)}
                  className="btn-join"
                >
                  Join Table
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {showCreateModal && (
        <CreateTableModal
          onClose={() => setShowCreateModal(false)}
          onCreated={(table) => {
            setShowCreateModal(false)
            handleJoinTable(table.table_id)
          }}
        />
      )}

      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onSuccess={(data) => {
            handleLoginSuccess(data.access_token, data.user.username, data.user.id, data.user.avatar_id)
          }}
        />
      )}
    </div>
  )
}
