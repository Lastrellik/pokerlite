import { useEffect, useState } from 'react'
import './HandResultModal.css'

function HandResultModal({ result, onClose, myPlayerName }) {
  const [show, setShow] = useState(false)

  useEffect(() => {
    if (result) {
      setShow(true)
    }
  }, [result])

  if (!result || !show) return null

  const handleClose = () => {
    setShow(false)
    setTimeout(() => onClose(), 300)
  }

  // Parse the result message to determine if current player won
  const isSplit = result.toLowerCase().includes('split pot')
  const isWinner = myPlayerName && result.toLowerCase().startsWith(myPlayerName.toLowerCase() + ' wins')
  const isInSplit = isSplit && myPlayerName && result.toLowerCase().includes(myPlayerName.toLowerCase())

  const didIWin = isWinner || isInSplit

  return (
    <div className={`modal-overlay ${show ? 'show' : ''}`} onClick={handleClose}>
      <div className={`result-modal ${show ? 'show' : ''}`} onClick={(e) => e.stopPropagation()}>
        <div className={`result-icon ${didIWin ? (isInSplit ? 'split' : 'winner') : 'loser'}`}>
          {didIWin ? (isInSplit ? '🤝' : '🏆') : '😔'}
        </div>

        <div className="result-title">
          {didIWin ? (isInSplit ? 'SPLIT POT!' : 'YOU WIN!') : 'HAND OVER'}
        </div>

        <div className="result-message">
          {result}
        </div>

        <button className="close-btn" onClick={handleClose}>
          Continue
        </button>
      </div>
    </div>
  )
}

export default HandResultModal
