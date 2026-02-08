/**
 * SidePots - displays breakdown of main pot and side pots during showdown
 */
import './SidePots.css'

export default function SidePots({ sidePots }) {
  if (!sidePots || sidePots.length === 0) return null

  return (
    <div className="side-pots-display">
      <div className="side-pots-title">Pot Breakdown</div>
      <div className="side-pots-list">
        {sidePots.map((pot, idx) => (
          <div key={idx} className="side-pot-item">
            <div className="side-pot-header">
              <span className="side-pot-type">{pot.type}</span>
              <span className="side-pot-amount">${pot.amount}</span>
            </div>
            <div className="side-pot-winners">
              Winner{pot.winners.length > 1 ? 's' : ''}: {pot.winners.join(', ')}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
