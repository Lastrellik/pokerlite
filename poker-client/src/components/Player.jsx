import Card from './Card'
import './Player.css'

function Player({ player, isDealer, isCurrentTurn, playerBet, small, isMe, showdownCards, isWinner, isSB, isBB }) {
  return (
    <div className={`player ${isCurrentTurn ? 'current-turn' : ''} ${isMe ? 'is-me' : ''} ${small ? 'small' : ''} ${isWinner ? 'winner' : ''}`}>
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

      {showdownCards && (
        <div className="player-showdown-cards">
          {showdownCards.holeCards.map((card, idx) => (
            <Card
              key={idx}
              card={card}
              small
              highlighted={isWinner && showdownCards.highlightCards?.includes(card)}
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
