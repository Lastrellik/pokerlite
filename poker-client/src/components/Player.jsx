import './Player.css'

function Player({ player, isDealer, isCurrentTurn, playerBet, small, isMe }) {
  return (
    <div className={`player ${isCurrentTurn ? 'current-turn' : ''} ${isMe ? 'is-me' : ''} ${small ? 'small' : ''}`}>
      <div className="player-info-box">
        <div className="player-name">
          {player.name}
          {isDealer && <span className="dealer-button">D</span>}
        </div>
        <div className="player-stack">${player.stack}</div>
        {playerBet > 0 && (
          <div className="player-bet">Bet: ${playerBet}</div>
        )}
        {!player.connected && (
          <div className="player-status">Disconnected</div>
        )}
      </div>
    </div>
  )
}

export default Player
