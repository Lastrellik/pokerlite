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

function Card({ card, faceDown = false, small = false, highlighted = false, revealing = false, revealDelay = 0 }) {
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

  // If revealing, wrap in flip container
  if (revealing) {
    return (
      <div
        className={`card-flip-container ${small ? 'small' : ''}`}
      >
        <div
          className={`card-flip-inner flipping`}
          style={{
            animationDelay: `${revealDelay}ms`,
            transform: 'rotateY(0deg)',
            transformStyle: 'preserve-3d'
          }}
        >
          {/* Back face - visible initially */}
          <div
            className={`card back card-face card-back ${small ? 'small' : ''}`}
            style={{ transform: 'rotateY(0deg)', backfaceVisibility: 'hidden' }}
          >
            <div className="card-pattern"></div>
          </div>
          {/* Front face - hidden initially */}
          <div
            className={`card ${color} card-face card-front ${small ? 'small' : ''} ${highlighted ? 'highlighted' : ''}`}
            style={{ transform: 'rotateY(180deg)', backfaceVisibility: 'hidden' }}
          >
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
        </div>
      </div>
    )
  }

  return (
    <div className={`card ${color} ${small ? 'small' : ''} ${highlighted ? 'highlighted' : ''}`}>
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
