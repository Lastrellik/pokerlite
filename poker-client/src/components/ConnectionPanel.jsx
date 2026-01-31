import { useState } from 'react'
import { usePokerGame } from '../hooks/usePokerGame.jsx'
import './ConnectionPanel.css'

function ConnectionPanel() {
  const { connected, myPid, connect, disconnect } = usePokerGame()
  const [playerName, setPlayerName] = useState('Player')
  const [tableId, setTableId] = useState('default')

  const handleConnect = () => {
    if (playerName && tableId) {
      connect(playerName, tableId)
    }
  }

  return (
    <div className="connection-panel">
      <div className="connection-inputs">
        <input
          type="text"
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
          placeholder="Your name"
          disabled={connected}
        />
        <input
          type="text"
          value={tableId}
          onChange={(e) => setTableId(e.target.value)}
          placeholder="Table ID"
          disabled={connected}
        />
        {!connected ? (
          <button onClick={handleConnect} className="btn-connect">
            Connect
          </button>
        ) : (
          <button onClick={disconnect} className="btn-disconnect">
            Disconnect
          </button>
        )}
      </div>
      <div className="connection-status">
        <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '🟢' : '🔴'}
        </span>
        <span className="status-text">
          {connected ? `Connected ${myPid ? `(${myPid.substring(0, 8)})` : ''}` : 'Disconnected'}
        </span>
      </div>
    </div>
  )
}

export default ConnectionPanel
