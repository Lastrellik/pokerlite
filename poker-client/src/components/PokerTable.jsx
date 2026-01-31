import { useMemo } from 'react'
import { usePokerGame } from '../hooks/usePokerGame.jsx'
import Card from './Card'
import Player from './Player'
import ActionButtons from './ActionButtons'
import GameLog from './GameLog'
import HandResultModal from './HandResultModal'
import './PokerTable.css'

function PokerTable() {
  const { gameState, myPid, handResult, clearHandResult } = usePokerGame()

  const myPlayer = useMemo(() => {
    if (!gameState || !myPid) return null
    return gameState.players?.find(p => p.pid === myPid)
  }, [gameState, myPid])

  const otherPlayers = useMemo(() => {
    if (!gameState || !myPid) return []
    return gameState.players?.filter(p => p.pid !== myPid) || []
  }, [gameState, myPid])

  const myBet = gameState?.player_bets?.[myPid] || 0
  const toCall = Math.max(0, (gameState?.current_bet || 0) - myBet)

  // Count eligible players (connected with chips)
  const eligiblePlayerCount = useMemo(() => {
    if (!gameState?.players) return 0
    return gameState.players.filter(p => p.connected && p.stack > 0).length
  }, [gameState?.players])

  return (
    <div className="poker-table-container">
      <div className="poker-table">
        {/* Center area with community cards and pot */}
        <div className="table-center">
          <div className="pot-display">
            <div className="pot-label">POT</div>
            <div className="pot-amount">${gameState?.pot || 0}</div>
          </div>

          <div className="community-cards">
            {gameState?.board?.map((card, idx) => (
              <Card key={idx} card={card} />
            )) || []}
            {(!gameState?.board || gameState.board.length === 0) && (
              <div className="no-cards">No community cards</div>
            )}
          </div>

          <div className="street-indicator">
            {gameState?.hand_in_progress
              ? `${gameState.street?.toUpperCase() || 'WAITING'}`
              : 'Waiting for hand...'}
          </div>
        </div>

        {/* Other players around the table */}
        <div className="other-players">
          {otherPlayers.map((player, idx) => (
            <div
              key={player.pid}
              className={`player-seat seat-${idx}`}
              style={{
                transform: `rotate(${(360 / Math.max(otherPlayers.length, 1)) * idx}deg) translateY(-200px) rotate(-${(360 / Math.max(otherPlayers.length, 1)) * idx}deg)`
              }}
            >
              <Player
                player={player}
                isDealer={player.seat === gameState?.dealer_seat}
                isCurrentTurn={player.pid === gameState?.current_turn_pid}
                playerBet={gameState?.player_bets?.[player.pid] || 0}
                small
              />
            </div>
          ))}
        </div>

        {/* Your hand at the bottom */}
        {myPlayer && (
          <div className="my-hand">
            <Player
              player={myPlayer}
              isDealer={myPlayer.seat === gameState?.dealer_seat}
              isCurrentTurn={myPlayer.pid === gameState?.current_turn_pid}
              playerBet={myBet}
              isMe
            />
            <div className="my-cards">
              {gameState?.hole_cards?.map((card, idx) => (
                <Card key={idx} card={card} />
              )) || [<Card key="1" faceDown />, <Card key="2" faceDown />]}
            </div>
            <div className="my-info">
              <div className="info-item">
                <span className="label">Stack:</span>
                <span className="value">${myPlayer.stack}</span>
              </div>
              <div className="info-item">
                <span className="label">To Call:</span>
                <span className="value">${toCall}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Action buttons */}
      <ActionButtons
        isMyTurn={gameState?.current_turn_pid === myPid}
        toCall={toCall}
        currentBet={gameState?.current_bet || 0}
        handInProgress={gameState?.hand_in_progress || false}
        playerCount={eligiblePlayerCount}
        turnDeadline={gameState?.turn_deadline}
      />

      {/* Game log */}
      <GameLog />

      {/* Hand result modal */}
      <HandResultModal result={handResult} onClose={clearHandResult} myPlayerName={myPlayer?.name} />
    </div>
  )
}

export default PokerTable
