import { useState, useEffect } from 'react'
import Card from './Card'
import './Player.css'

function Player({ player, isDealer, isCurrentTurn, playerBet, small, isMe, showdownCards, isWinner, isSB, isBB, revealDelay = 0, folded, justFolded, justWon, lastAction, turnDeadline }) {
  // Countdown timer for current turn
  const [timeLeft, setTimeLeft] = useState(null)

  useEffect(() => {
    if (!isCurrentTurn || !turnDeadline) {
      setTimeLeft(null)
      return
    }

    const updateTimer = () => {
      const now = Date.now() / 1000
      const remaining = Math.max(0, Math.ceil(turnDeadline - now))
      setTimeLeft(remaining)
    }

    updateTimer()
    const interval = setInterval(updateTimer, 1000)

    return () => clearInterval(interval)
  }, [isCurrentTurn, turnDeadline])
  return (
    <div className={`player ${isCurrentTurn ? 'current-turn' : ''} ${isMe ? 'is-me' : ''} ${small ? 'small' : ''} ${isWinner ? 'winner' : ''} ${folded ? 'folded' : ''}`}>
      {justFolded && (
        <div className="action-overlay fold-overlay">
          <span className="action-text fold-text">FOLD</span>
        </div>
      )}
      {justWon && (
        <div className="action-overlay winner-overlay">
          <span className="action-text winner-text">WINNER</span>
        </div>
      )}
      {lastAction === 'raise' && (
        <div className="action-overlay raise-overlay">
          <span className="action-text raise-text">RAISE</span>
        </div>
      )}
      {lastAction === 'call' && (
        <div className="action-overlay call-overlay">
          <span className="action-text call-text">CALL</span>
        </div>
      )}
      {lastAction === 'all_in' && (
        <div className="action-overlay allin-overlay">
          <span className="action-text allin-text">ALL IN</span>
        </div>
      )}
      {lastAction === 'check' && (
        <div className="action-overlay check-overlay">
          <span className="action-text check-text">CHECK</span>
        </div>
      )}
      <div className="player-info-box">
        <div className="player-name">
          {player.name}
          <div className="player-badges">
            {isDealer && (
              <span className="badge-wrapper">
                <span className="dealer-button">D</span>
                <span className="badge-tooltip">Dealer - Position rotates each hand</span>
              </span>
            )}
            {isSB && (
              <span className="badge-wrapper">
                <span className="blind-chip sb">SB</span>
                <span className="badge-tooltip">Small Blind - Forced bet, half the big blind</span>
              </span>
            )}
            {isBB && (
              <span className="badge-wrapper">
                <span className="blind-chip bb">BB</span>
                <span className="badge-tooltip">Big Blind - Forced bet posted before cards are dealt</span>
              </span>
            )}
          </div>
        </div>
        <div className="player-stack">${player.stack}</div>
        {playerBet > 0 && (
          <div className="player-bet">Bet: ${playerBet}</div>
        )}
        {!player.connected && (
          <div className="player-status">Disconnected</div>
        )}
      </div>

      {isCurrentTurn && timeLeft !== null && (
        <div className="turn-timer-bar">
          <div
            className="turn-timer-fill"
            style={{
              width: `${(timeLeft / 30) * 100}%`,
              backgroundColor: timeLeft > 15 ? '#00f5ff' : timeLeft > 5 ? '#ffaa00' : '#ff4444'
            }}
          />
        </div>
      )}

      {showdownCards && (
        <div className="player-showdown-cards">
          {showdownCards.holeCards.map((card, idx) => (
            <Card
              key={idx}
              card={card}
              small
              highlighted={isWinner && showdownCards.highlightCards?.includes(card)}
              revealing={revealDelay > 0}
              revealDelay={idx * 800}
            />
          ))}
          {isWinner && showdownCards.handName && (
            <div className="hand-name">{showdownCards.handName}</div>
          )}
        </div>
      )}
    </div>
  )
}

export default Player
