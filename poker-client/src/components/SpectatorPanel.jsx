import './SpectatorPanel.css'

function SpectatorPanel({ role, waitlistPosition, onJoinWaitlist, onLeaveWaitlist }) {
  const isOnWaitlist = role === 'waitlist'

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
        ) : (
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
