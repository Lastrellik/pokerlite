import { useMemo, useCallback, useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePokerGame } from '../hooks/usePokerGame.jsx'
import Card from './Card'
import Player from './Player'
import ActionButtons from './ActionButtons'
import GameLog from './GameLog'
import SpectatorPanel from './SpectatorPanel'
import SidePots from './SidePots'
import './PokerTable.css'

// Ellipse dimensions for player positioning (table is 800x500)
const ELLIPSE_RX = 410  // horizontal radius
const ELLIPSE_RY = 230  // vertical radius

// Calculate position on ellipse by seat number (1-8)
// Seats arranged like a clock: 1=top, 3=right, 5=bottom, 7=left
const getPositionBySeat = (seat) => {
  // Wrap seat to 1-8 range
  const wrappedSeat = ((seat - 1) % 8) + 1

  // Each seat is 45° apart, starting from top (seat 1 = -90°)
  // Seat 1 = -90° (top), Seat 3 = 0° (right), Seat 5 = 90° (bottom), Seat 7 = 180° (left)
  const angleDeg = -90 + (wrappedSeat - 1) * 45
  const angleRad = angleDeg * (Math.PI / 180)

  return {
    x: Math.round(ELLIPSE_RX * Math.cos(angleRad)) - 75,
    y: Math.round(ELLIPSE_RY * Math.sin(angleRad)) - 60,
  }
}

function PokerTable({ tableId }) {
  const navigate = useNavigate()
  const { gameState, myPid, handResult, joinWaitlist, leaveWaitlist } = usePokerGame(tableId)

  const myPlayer = useMemo(() => {
    if (!gameState || !myPid) return null
    return gameState.players?.find(p => p.pid === myPid)
  }, [gameState, myPid])

  // Redirect to lobby if player busts out (loses all money)
  useEffect(() => {
    if (myPlayer && myPlayer.stack === 0 && myPlayer.connected) {
      // Give 3 seconds to see the final result before redirecting
      const redirectTimer = setTimeout(() => {
        navigate('/')
      }, 3000)
      return () => clearTimeout(redirectTimer)
    }
  }, [myPlayer, navigate])

  const otherPlayers = useMemo(() => {
    if (!gameState || !myPid) return []
    return gameState.players?.filter(p => p.pid !== myPid) || []
  }, [gameState, myPid])

  // All players for table positioning (including me)
  const allPlayers = useMemo(() => {
    if (!gameState?.players) return []
    return gameState.players
  }, [gameState?.players])

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
  const [showdownPhase, setShowdownPhase] = useState(null) // null | 'flipping' | 'revealing' | 'runout' | 'showModal'
  const prevShowdownRef = useRef(null)
  const wasRunoutRef = useRef(false)

  useEffect(() => {
    const hasShowdown = !!gameState?.showdown
    const hadShowdown = prevShowdownRef.current
    const isRunout = gameState?.showdown?.runout

    if (hasShowdown && !hadShowdown) {
      // New showdown started
      prevShowdownRef.current = true

      if (isRunout) {
        // Runout - show cards immediately, no winner phase yet
        wasRunoutRef.current = true
        setShowdownPhase('runout')
      } else {
        // Normal showdown with winners
        if (wasRunoutRef.current) {
          // Transitioning from runout to final showdown - go straight to revealing
          wasRunoutRef.current = false
          setShowdownPhase('revealing')

          const modalTimer = setTimeout(() => {
            setShowdownPhase('showModal')
          }, 3000)

          return () => clearTimeout(modalTimer)
        } else {
          // Fresh showdown - do the flip animation
          setShowdownPhase('flipping')

          const revealTimer = setTimeout(() => {
            setShowdownPhase('revealing')
          }, 3000)

          const modalTimer = setTimeout(() => {
            setShowdownPhase('showModal')
          }, 6000)

          return () => {
            clearTimeout(revealTimer)
            clearTimeout(modalTimer)
          }
        }
      }
    } else if (hasShowdown && hadShowdown && !isRunout && wasRunoutRef.current) {
      // Runout just finished, now we have the real showdown with winners
      wasRunoutRef.current = false
      setShowdownPhase('revealing')

      const modalTimer = setTimeout(() => {
        setShowdownPhase('showModal')
      }, 3000)

      return () => clearTimeout(modalTimer)
    } else if (!hasShowdown && hadShowdown) {
      // Showdown ended
      prevShowdownRef.current = false
      wasRunoutRef.current = false
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

  // Track who just folded for animation
  const [justFoldedPids, setJustFoldedPids] = useState(new Set())
  const prevFoldedPidsRef = useRef(new Set())
  const shownFoldAnimationRef = useRef(new Set()) // Track who we've already shown fold animation for this hand

  useEffect(() => {
    const currentFolded = new Set(
      gameState?.players?.filter(p => p.folded).map(p => p.pid) || []
    )
    const prevFolded = prevFoldedPidsRef.current

    // Find newly folded players that haven't had animation shown yet
    const newlyFolded = new Set()
    currentFolded.forEach(pid => {
      if (!prevFolded.has(pid) && !shownFoldAnimationRef.current.has(pid)) {
        newlyFolded.add(pid)
        shownFoldAnimationRef.current.add(pid)
      }
    })

    if (newlyFolded.size > 0) {
      setJustFoldedPids(newlyFolded)
      // Clear after animation completes
      const timer = setTimeout(() => {
        setJustFoldedPids(new Set())
      }, 2000)
      return () => clearTimeout(timer)
    }

    // Reset when hand ends (no one is folded anymore)
    if (currentFolded.size === 0) {
      setJustFoldedPids(new Set())
      shownFoldAnimationRef.current = new Set()
    }

    prevFoldedPidsRef.current = currentFolded
  }, [gameState?.players])

  // Track who just won for animation
  const [justWonPids, setJustWonPids] = useState(new Set())
  const prevShowdownRef2 = useRef(null)

  useEffect(() => {
    const showdown = gameState?.showdown
    const hadShowdown = prevShowdownRef2.current

    // Fold win - show immediately
    if (showdown?.fold_win && !hadShowdown) {
      const winnerPids = new Set(showdown.winner_pids || [])
      setJustWonPids(winnerPids)
      const clearTimer = setTimeout(() => {
        setJustWonPids(new Set())
      }, 2000)
      prevShowdownRef2.current = showdown
      return () => clearTimeout(clearTimer)
    }

    // Card showdown - delay until after highlights appear
    if (showdownPhase === 'revealing' && showdown && !showdown.fold_win) {
      const winnerPids = new Set(showdown.winner_pids || [])
      if (winnerPids.size > 0) {
        // Wait 1.5 seconds after highlights appear
        const showTimer = setTimeout(() => {
          setJustWonPids(winnerPids)
        }, 1500)
        const clearTimer = setTimeout(() => {
          setJustWonPids(new Set())
        }, 3500)
        return () => {
          clearTimeout(showTimer)
          clearTimeout(clearTimer)
        }
      }
    }

    // Reset when showdown clears
    if (!showdown) {
      setJustWonPids(new Set())
      prevShowdownRef2.current = null
    }
  }, [showdownPhase, gameState?.showdown])

  // Track last action for animation
  const [displayedAction, setDisplayedAction] = useState(null) // {pid, action}
  const prevActionRef = useRef(null)

  useEffect(() => {
    const currentAction = gameState?.last_action
    const prevAction = prevActionRef.current

    // Check if this is a new action (different from previous)
    const isNewAction = currentAction && (
      !prevAction ||
      currentAction.pid !== prevAction.pid ||
      currentAction.action !== prevAction.action
    )

    if (isNewAction && currentAction.action !== 'fold') {
      // Don't show fold here - it has its own tracking
      setDisplayedAction({ pid: currentAction.pid, action: currentAction.action })
      // Clear after animation
      const timer = setTimeout(() => {
        setDisplayedAction(null)
      }, 1500)
      prevActionRef.current = currentAction
      return () => clearTimeout(timer)
    }

    // Reset when hand ends
    if (!gameState?.hand_in_progress) {
      setDisplayedAction(null)
      prevActionRef.current = null
    }

    prevActionRef.current = currentAction
  }, [gameState?.last_action, gameState?.hand_in_progress])

  // Base delay for showdown card reveal - always reveal if showdown exists
  const getRevealDelay = useCallback(() => {
    if (!gameState?.showdown) return 0
    return 200  // Small initial delay
  }, [gameState?.showdown])

  // Show highlights during revealing phase
  const shouldHighlight = showdownPhase === 'revealing' || showdownPhase === 'showModal'

  return (
    <div className="poker-table-container">
      <div className="table-area">
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

        {/* Show side pots breakdown during showdown */}
        {shouldHighlight && gameState?.showdown?.side_pots && (
          <SidePots sidePots={gameState.showdown.side_pots} />
        )}

        {/* All players around the table (including current player) */}
        <div className="other-players">
          {allPlayers.map((player, idx) => {
            const seat = player.seat || (idx + 1)
            const pos = getPositionBySeat(seat)
            const isMe = player.pid === myPid
            return (
            <div
              key={player.pid}
              className={`player-seat seat-${seat}${isMe ? ' is-me' : ''}`}
              style={{
                transform: `translate(${pos.x}px, ${pos.y}px)`
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
                folded={player.folded}
                justFolded={justFoldedPids.has(player.pid)}
                justWon={justWonPids.has(player.pid)}
                lastAction={displayedAction?.pid === player.pid ? displayedAction.action : null}
                isMe={isMe}
                turnDeadline={gameState?.turn_deadline}
              />
            </div>
          )})}
        </div>
      </div>
      </div>

      {/* Your cards and actions at the bottom - only for seated players */}
      {myPlayer && gameState?.my_role === 'seated' && (
        <div className="my-hand">
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
            turnTimeoutSeconds={gameState?.turn_timeout_seconds || 30}
            myStack={myPlayer?.stack || 0}
          />
        </div>
      )}

      {/* Spectator/Waitlist panel for non-seated players */}
      {gameState?.my_role && gameState.my_role !== 'seated' && (
        <SpectatorPanel
          role={gameState.my_role}
          waitlistPosition={gameState.waitlist_position}
          onJoinWaitlist={joinWaitlist}
          onLeaveWaitlist={leaveWaitlist}
        />
      )}

      {/* Game log */}
      <GameLog />

    </div>
  )
}

export default PokerTable
