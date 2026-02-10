import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePokerGame } from '../hooks/usePokerGame.jsx'
import LoginModal from './LoginModal'
import './ConnectionPanel.css'

function ConnectionPanel() {
  const { tableId } = useParams()
  const navigate = useNavigate()
  const { connected, myPid, connect, disconnect } = usePokerGame()

  const [showLoginModal, setShowLoginModal] = useState(false)
  const [chipCount, setChipCount] = useState(null)
  const [loadingChips, setLoadingChips] = useState(false)
  const [chipAmount, setChipAmount] = useState('1000')

  // Check if user is authenticated
  const authToken = localStorage.getItem('auth_token')
  const authUsername = localStorage.getItem('username')

  const LOBBY_URL = import.meta.env.VITE_LOBBY_URL || 'http://localhost:8000'

  // Use sessionStorage for guest name (per-tab), or auth username
  const [playerName, setPlayerName] = useState(
    authUsername || sessionStorage.getItem('playerName') || ''
  )

  // Update player name when auth changes
  useEffect(() => {
    if (authUsername) {
      setPlayerName(authUsername)
    }
  }, [authUsername])

  // Fetch chip count when authenticated
  useEffect(() => {
    if (authToken && !connected) {
      fetchChipCount()
    }
  }, [authToken, connected])

  const fetchChipCount = async () => {
    if (!authToken) return

    try {
      const response = await fetch(`${LOBBY_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        // Get user ID and fetch stack
        const stackResponse = await fetch(`${LOBBY_URL}/api/auth/stack`, {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        })
        if (stackResponse.ok) {
          const stackData = await stackResponse.json()
          setChipCount(stackData.stack)
        }
      }
    } catch (error) {
      console.error('Error fetching chip count:', error)
    }
  }

  const handleAddChips = async () => {
    if (!authToken) return

    const amount = parseInt(chipAmount)
    if (isNaN(amount) || amount < 1 || amount > 100000) {
      alert('Please enter a valid amount between 1 and 100,000')
      return
    }

    setLoadingChips(true)
    try {
      const response = await fetch(`${LOBBY_URL}/api/auth/add-chips`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ amount })
      })

      if (response.ok) {
        const data = await response.json()
        setChipCount(data.new_stack)
        alert(`Added ${data.added} chips! New balance: ${data.new_stack}`)
      } else {
        const error = await response.json()
        alert(`Failed to add chips: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error adding chips:', error)
      alert('Error adding chips')
    } finally {
      setLoadingChips(false)
    }
  }

  const handleConnect = () => {
    if (playerName && tableId) {
      const token = localStorage.getItem('auth_token')
      connect(playerName, tableId, token) // Pass token to connect
      // Save to sessionStorage for guest mode
      if (!authUsername) {
        sessionStorage.setItem('playerName', playerName)
      }
    }
  }

  const handleDisconnect = () => {
    disconnect(tableId)
    navigate('/')
  }

  const handleLoginSuccess = (data) => {
    setShowLoginModal(false)
    setPlayerName(data.user.username)
    // Auto-connect after login
    if (tableId) {
      connect(data.user.username, tableId, data.access_token)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('username')
    localStorage.removeItem('user_id')
    localStorage.removeItem('avatar_id')
    setPlayerName('')
    if (connected) {
      disconnect(tableId)
    }
  }

  if (!connected) {
    return (
      <div className="connection-panel">
        {showLoginModal && (
          <LoginModal
            onClose={() => setShowLoginModal(false)}
            onSuccess={handleLoginSuccess}
          />
        )}

        <div className="connection-inputs">
          {authToken ? (
            // Authenticated user
            <>
              <span className="auth-username">👤 {playerName}</span>
              {chipCount !== null && (
                <span className="chip-count">💰 {chipCount} chips</span>
              )}
              <button onClick={handleConnect} className="btn-connect">
                Join Table
              </button>
              {chipCount !== null && (
                <div className="chip-controls">
                  <input
                    type="number"
                    value={chipAmount}
                    onChange={(e) => setChipAmount(e.target.value)}
                    placeholder="Amount"
                    min="1"
                    max="100000"
                    className="chip-amount-input"
                  />
                  <button
                    onClick={handleAddChips}
                    className="btn-add-chips"
                    disabled={loadingChips}
                  >
                    {loadingChips ? 'Adding...' : 'Add Chips'}
                  </button>
                </div>
              )}
              <button onClick={handleLogout} className="btn-logout">
                Logout
              </button>
            </>
          ) : (
            // Guest or not logged in
            <>
              <input
                type="text"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                placeholder="Enter your name"
                onKeyPress={(e) => e.key === 'Enter' && handleConnect()}
                autoFocus
              />
              <button onClick={handleConnect} className="btn-connect" disabled={!playerName}>
                Join as Guest
              </button>
              <button onClick={() => setShowLoginModal(true)} className="btn-login">
                Login / Sign Up
              </button>
            </>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="connection-panel">
      <div className="connection-status">
        <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '🟢' : '🔴'}
        </span>
        <span className="status-text">
          {connected ? myPid ? `${authToken ? '👤 ' : ''}${playerName} (${myPid.substring(0, 8)})` : 'Connecting...' : 'Disconnected'}
        </span>
        <button onClick={handleDisconnect} className="btn-disconnect">
          Leave Table
        </button>
        {authToken && (
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        )}
      </div>
    </div>
  )
}

export default ConnectionPanel
