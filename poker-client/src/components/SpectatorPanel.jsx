import './SpectatorPanel.css'

function SpectatorPanel({ role, waitlistPosition, onJoinWaitlist, onLeaveWaitlist, myStack }) {
  const isOnWaitlist = role === 'waitlist'
  const hasNoChips = myStack === 0

  return (
    <div className="spectator-panel">
      <div className="spectator-header">
        {isOnWaitlist ? 'On Waitlist' : 'Watching as Spectator'}
      </div>

      {isOnWaitlist && waitlistPosition > 0 && (
        <div className="waitlist-position">
          Position: <span className="position-number">#{waitlistPosition}</span>
        </div>
      )}

      <div className="spectator-message">
        {isOnWaitlist
          ? 'You will be seated when a spot opens up'
          : hasNoChips
            ? 'You need chips to join the waitlist. Add chips in the lobby to play.'
            : 'Join the waitlist to play when a seat opens'}
      </div>

      <div className="spectator-actions">
        {isOnWaitlist ? (
          <button
            className="waitlist-button leave"
            onClick={onLeaveWaitlist}
          >
            Leave Waitlist
          </button>
        ) : hasNoChips ? null : (
          <button
            className="waitlist-button join"
            onClick={onJoinWaitlist}
          >
            Join Waitlist
          </button>
        )}
      </div>
    </div>
  )
}

export default SpectatorPanel
