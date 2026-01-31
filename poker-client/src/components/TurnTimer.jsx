import { useState, useEffect } from 'react'
import './TurnTimer.css'

function TurnTimer({ deadline, isMyTurn }) {
  const [timeLeft, setTimeLeft] = useState(0)

  useEffect(() => {
    if (!deadline) {
      setTimeLeft(0)
      return
    }

    const updateTimer = () => {
      const now = Date.now() / 1000 // Convert to seconds
      const remaining = Math.max(0, deadline - now)
      setTimeLeft(remaining)
    }

    // Update immediately
    updateTimer()

    // Update every 100ms for smooth countdown
    const interval = setInterval(updateTimer, 100)

    return () => clearInterval(interval)
  }, [deadline])

  if (timeLeft === 0 || !isMyTurn) {
    return null
  }

  const percentage = (timeLeft / 20) * 100
  const isUrgent = timeLeft < 5

  return (
    <div className={`turn-timer ${isUrgent ? 'urgent' : ''}`}>
      <div className="timer-text">
        {Math.ceil(timeLeft)}s
      </div>
      <div className="timer-bar">
        <div
          className="timer-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

export default TurnTimer
