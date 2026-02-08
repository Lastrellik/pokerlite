import { useState } from 'react'
import { usePokerGame } from '../hooks/usePokerGame.jsx'
import TurnTimer from './TurnTimer'
import './ActionButtons.css'

function ActionButtons({ isMyTurn, toCall, currentBet, handInProgress, playerCount, turnDeadline, turnTimeoutSeconds, myStack }) {
  const { sendAction, startHand } = usePokerGame()
  const [raiseAmount, setRaiseAmount] = useState(20)

  const handleFold = () => sendAction('fold')
  const handleCheck = () => sendAction('check')
  const handleCall = () => sendAction('call')
  const handleRaise = () => {
    const amount = parseInt(raiseAmount)
    // Validate: must be positive and greater than current bet
    if (amount > 0 && amount > currentBet) {
      sendAction('raise', amount)
    }
  }
  const handleAllIn = () => sendAction('all_in')

  const handleRaiseAmountChange = (e) => {
    const value = e.target.value
    // Only allow positive numbers
    if (value === '' || parseInt(value) >= 0) {
      setRaiseAmount(value)
    }
  }

  const canCheck = isMyTurn && toCall === 0
  const canCall = isMyTurn && toCall > 0
  const canStartHand = playerCount >= 2

  // Check if calling will be an all-in
  const callIsAllIn = myStack > 0 && toCall >= myStack
  const actualCallAmount = callIsAllIn ? myStack : toCall

  return (
    <div className={`action-buttons ${handInProgress ? 'with-cards' : ''}`}>
      {!handInProgress && canStartHand && (
        <button onClick={startHand} className="btn-action btn-start">
          🎲 Start Hand
        </button>
      )}

      {!handInProgress && !canStartHand && (
        <div className="turn-indicator">
          Waiting for players to join... ({playerCount}/2 minimum)
        </div>
      )}

      {handInProgress && (
        <>
          <button
            onClick={handleFold}
            disabled={!isMyTurn}
            className="btn-action btn-fold"
          >
            ❌ Fold
          </button>

          <button
            onClick={handleCheck}
            disabled={!canCheck}
            className="btn-action btn-check"
          >
            ✓ Check
          </button>

          <button
            onClick={handleCall}
            disabled={!canCall}
            className={`btn-action btn-call ${callIsAllIn ? 'all-in-call' : ''}`}
          >
            💰 Call ${actualCallAmount}{callIsAllIn ? ' (All-in)' : ''}
          </button>

          <div className="raise-group">
            <input
              type="number"
              value={raiseAmount}
              onChange={handleRaiseAmountChange}
              min={currentBet * 2 || 10}
              step="1"
              disabled={!isMyTurn}
              className="raise-input"
            />
            <button
              onClick={handleRaise}
              disabled={!isMyTurn || raiseAmount <= 0 || raiseAmount <= currentBet}
              className="btn-action btn-raise"
            >
              🚀 Raise
            </button>
          </div>

          <button
            onClick={handleAllIn}
            disabled={!isMyTurn}
            className="btn-action btn-all-in"
          >
            💎 All In
          </button>
        </>
      )}

      {!isMyTurn && handInProgress && (
        <div className="turn-indicator">Waiting for other players...</div>
      )}

      {isMyTurn && handInProgress && (
        <TurnTimer deadline={turnDeadline} isMyTurn={isMyTurn} turnTimeoutSeconds={turnTimeoutSeconds} />
      )}
    </div>
  )
}

export default ActionButtons
