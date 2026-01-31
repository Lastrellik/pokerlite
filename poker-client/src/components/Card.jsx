import './Card.css'

const SUIT_SYMBOLS = {
  's': '♠',
  'h': '♥',
  'd': '♦',
  'c': '♣'
}

const SUIT_COLORS = {
  's': 'black',
  'h': 'red',
  'd': 'red',
  'c': 'black'
}

const RANK_DISPLAY = {
  'T': '10',
  'J': 'J',
  'Q': 'Q',
  'K': 'K',
  'A': 'A'
}

function Card({ card, faceDown = false, small = false }) {
  if (!card) {
    return <div className={`card empty ${small ? 'small' : ''}`}></div>
  }

  if (faceDown) {
    return (
      <div className={`card back ${small ? 'small' : ''}`}>
        <div className="card-pattern"></div>
      </div>
    )
  }

  const rank = card[0]
  const suit = card[1]
  const suitSymbol = SUIT_SYMBOLS[suit] || suit
  const color = SUIT_COLORS[suit] || 'black'
  const displayRank = RANK_DISPLAY[rank] || rank

  return (
    <div className={`card ${color} ${small ? 'small' : ''}`}>
      <div className="card-corner top-left">
        <div className="rank">{displayRank}</div>
        <div className="suit">{suitSymbol}</div>
      </div>
      <div className="card-center">
        <div className="suit-large">{suitSymbol}</div>
      </div>
      <div className="card-corner bottom-right">
        <div className="rank">{displayRank}</div>
        <div className="suit">{suitSymbol}</div>
      </div>
    </div>
  )
}

export default Card
