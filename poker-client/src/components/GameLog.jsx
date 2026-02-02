import { useState, useEffect, useRef } from 'react'
import { usePokerGame } from '../hooks/usePokerGame.jsx'
import './GameLog.css'

function GameLog() {
  const { logs } = usePokerGame()
  const [isOpen, setIsOpen] = useState(false)
  const logEndRef = useRef(null)

  useEffect(() => {
    if (isOpen && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, isOpen])

  return (
    <div className={`game-log ${isOpen ? 'open' : ''}`}>
      <button
        className="log-toggle"
        onClick={() => setIsOpen(!isOpen)}
      >
        📜 Game Log {logs.length > 0 && `(${logs.length})`}
      </button>

      {isOpen && (
        <div className="log-content">
          {logs.length === 0 ? (
            <div className="log-empty">No events yet...</div>
          ) : (
            logs.map((log, idx) => (
              <div key={idx} className="log-entry">
                <span className="log-time">{log.time}</span>
                <span className="log-message" style={{ whiteSpace: 'pre-wrap' }}>{log.message}</span>
              </div>
            ))
          )}
          <div ref={logEndRef} />
        </div>
      )}
    </div>
  )
}

export default GameLog
