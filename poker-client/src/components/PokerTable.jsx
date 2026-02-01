import { useMemo, useCallback, useState, useEffect, useRef } from 'react'
import { usePokerGame } from '../hooks/usePokerGame.jsx'
import Card from './Card'
import Player from './Player'
import ActionButtons from './ActionButtons'
import GameLog from './GameLog'
import './PokerTable.css'

function PokerTable() {
  const { gameState, myPid, handResult } = usePokerGame()

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

  // Helper to get showdown data for a player
  const getShowdownData = useCallback((pid) => {
    if (!gameState?.showdown?.players?.[pid]) return null
    const playerData = gameState.showdown.players[pid]
    return {
      holeCards: playerData.hole_cards,
      highlightCards: playerData.highlight_cards,
      handName: playerData.hand_name,
    }
  }, [gameState?.showdown])

  const isWinner = useCallback((pid) => {
    return gameState?.showdown?.winner_pids?.includes(pid) || false
  }, [gameState?.showdown])

  // Check if a community card is part of any winner's key cards
  const isWinningCard = useCallback((card) => {
    if (!gameState?.showdown?.winner_pids) return false
    return gameState.showdown.winner_pids.some(winnerPid =>
      gameState.showdown.players[winnerPid]?.highlight_cards?.includes(card)
    )
  }, [gameState?.showdown])

  // Track showdown phases: 'flipping' -> 'revealing' -> 'showModal'
  const [showdownPhase, setShowdownPhase] = useState(null) // null | 'flipping' | 'revealing' | 'showModal'
  const prevShowdownRef = useRef(null)

  useEffect(() => {
    const hasShowdown = !!gameState?.showdown
    const hadShowdown = prevShowdownRef.current

    if (hasShowdown && !hadShowdown) {
      // New showdown started
      prevShowdownRef.current = true
      setShowdownPhase('flipping')

      // After 3 seconds, highlight the winning cards
      const revealTimer = setTimeout(() => {
        setShowdownPhase('revealing')
      }, 3000)

      // After 6 seconds (3s more), show the modal
      const modalTimer = setTimeout(() => {
        setShowdownPhase('showModal')
      }, 6000)

      return () => {
        clearTimeout(revealTimer)
        clearTimeout(modalTimer)
      }
    } else if (!hasShowdown && hadShowdown) {
      // Showdown ended - but keep phase until modal dismissed
      prevShowdownRef.current = false
      if (!handResult) {
        setShowdownPhase(null)
      }
    }
  }, [gameState?.showdown, handResult])

  // Clear phase when handResult is dismissed
  useEffect(() => {
    if (!handResult && !gameState?.showdown) {
      setShowdownPhase(null)
    }
  }, [handResult, gameState?.showdown])

  // Track board cards for flip animation
  const prevBoardLengthRef = useRef(0)
  const [revealedIndices, setRevealedIndices] = useState(new Set())

  // Calculate which cards are new (need flip animation)
  const currentBoardLength = gameState?.board?.length || 0
  const newCardIndices = useMemo(() => {
    const indices = []
    for (let i = 0; i < currentBoardLength; i++) {
      if (!revealedIndices.has(i)) {
        indices.push(i)
      }
    }
    return indices
  }, [currentBoardLength, revealedIndices])

  // After animation completes, mark cards as revealed
  useEffect(() => {
    if (newCardIndices.length > 0) {
      const timer = setTimeout(() => {
        setRevealedIndices(prev => {
          const next = new Set(prev)
          newCardIndices.forEach(i => next.add(i))
          return next
        })
      }, 1500) // After flip animation completes
      return () => clearTimeout(timer)
    }
  }, [newCardIndices])

  // Reset revealed indices when board resets
  useEffect(() => {
    if (currentBoardLength < prevBoardLengthRef.current) {
      setRevealedIndices(new Set())
    }
    prevBoardLengthRef.current = currentBoardLength
  }, [currentBoardLength])

  // Base delay for showdown card reveal - always reveal if showdown exists
  const getRevealDelay = useCallback(() => {
    if (!gameState?.showdown) return 0
    return 200  // Small initial delay
  }, [gameState?.showdown])

  // Show highlights during revealing phase
  const shouldHighlight = showdownPhase === 'revealing' || showdownPhase === 'showModal'

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
            {(gameState?.showdown?.board || gameState?.board)?.map((card, idx) => (
              <Card
                key={idx}
                card={card}
                highlighted={shouldHighlight && isWinningCard(card)}
                revealing={newCardIndices.includes(idx)}
                revealDelay={newCardIndices.indexOf(idx) * 400}
              />
            )) || []}
            {(!gameState?.board || gameState.board.length === 0) && !gameState?.showdown?.board && (
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
                showdownCards={getShowdownData(player.pid)}
                isWinner={shouldHighlight && isWinner(player.pid)}
                isSB={player.pid === gameState?.sb_pid}
                isBB={player.pid === gameState?.bb_pid}
                revealDelay={getRevealDelay()}
              />
            </div>
          ))}
        </div>
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
            showdownCards={getShowdownData(myPid)}
            isWinner={shouldHighlight && isWinner(myPid)}
            isSB={myPid === gameState?.sb_pid}
            isBB={myPid === gameState?.bb_pid}
            revealDelay={getRevealDelay()}
          />
          <div className="my-cards">
            {gameState?.hole_cards?.map((card, idx) => {
              const amIWinner = shouldHighlight && isWinner(myPid)
              const myShowdown = gameState?.showdown?.players?.[myPid]
              const highlighted = amIWinner && myShowdown?.highlight_cards?.includes(card)
              return <Card key={idx} card={card} highlighted={highlighted} />
            }) || [<Card key="1" faceDown />, <Card key="2" faceDown />]}
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

          {/* Action buttons */}
          <ActionButtons
            isMyTurn={gameState?.current_turn_pid === myPid}
            toCall={toCall}
            currentBet={gameState?.current_bet || 0}
            handInProgress={gameState?.hand_in_progress || false}
            playerCount={eligiblePlayerCount}
            turnDeadline={gameState?.turn_deadline}
          />
        </div>
      )}

      {/* Game log */}
      <GameLog />

    </div>
  )
}

export default PokerTable
