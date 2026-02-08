import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePokerGame } from '../hooks/usePokerGame.jsx'
import './ConnectionPanel.css'

function ConnectionPanel() {
  const { tableId } = useParams()
  const navigate = useNavigate()
  const { connected, myPid, connect, disconnect } = usePokerGame()

  // Use sessionStorage instead of localStorage so each tab is a new player
  // Start with empty name so user must enter it for each new tab
  const [playerName, setPlayerName] = useState(
    sessionStorage.getItem('playerName') || ''
  )

  const handleConnect = () => {
    if (playerName && tableId) {
      connect(playerName, tableId)
      // Save to sessionStorage (per-tab) instead of localStorage (shared)
      sessionStorage.setItem('playerName', playerName)
    }
  }

  const handleDisconnect = () => {
    disconnect(tableId)
    navigate('/')
  }

  if (!connected) {
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
