import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePokerGame } from '../hooks/usePokerGame.jsx'
import './ConnectionPanel.css'

function ConnectionPanel() {
  const { tableId } = useParams()
  const navigate = useNavigate()
  const { connected, myPid, connect, disconnect } = usePokerGame()

  // Load name from localStorage or use default
  const [playerName, setPlayerName] = useState(
    localStorage.getItem('playerName') || ''
  )
  const [showNameInput, setShowNameInput] = useState(!connected && !playerName)

  // Auto-connect if we have a name
  useEffect(() => {
    if (playerName && tableId && !connected) {
      connect(playerName, tableId)
      localStorage.setItem('playerName', playerName)
    }
  }, []) // Only on mount

  const handleConnect = () => {
    if (playerName && tableId) {
      connect(playerName, tableId)
      localStorage.setItem('playerName', playerName)
      setShowNameInput(false)
    }
  }

  const handleDisconnect = () => {
    disconnect()
    navigate('/')
  }

  if (showNameInput && !connected) {
    return (
      <div className="connection-panel">
        <div className="connection-inputs">
          <input
            type="text"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            placeholder="Enter your name"
            onKeyPress={(e) => e.key === 'Enter' && handleConnect()}
            autoFocus
          />
          <button onClick={handleConnect} className="btn-connect" disabled={!playerName}>
            Join
          </button>
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
          {connected ? myPid ? `${playerName} (${myPid.substring(0, 8)})` : 'Connecting...' : 'Disconnected'}
        </span>
        <button onClick={handleDisconnect} className="btn-disconnect">
          Leave Table
        </button>
      </div>
    </div>
  )
}

export default ConnectionPanel
