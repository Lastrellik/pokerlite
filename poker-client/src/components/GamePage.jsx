/**
 * GamePage - wrapper for the poker table that gets tableId from route params.
 */
import { useParams } from 'react-router-dom'
import { PokerGameProvider } from '../hooks/usePokerGame.jsx'
import PokerTable from './PokerTable'
import ConnectionPanel from './ConnectionPanel'
import './GamePage.css'

export default function GamePage() {
  const { tableId } = useParams()

  return (
    <PokerGameProvider>
      <div className="game-page">
        <header className="game-header">
          <h1>♠️ PokerLite ♥️</h1>
          <div className="table-id">Table: {tableId}</div>
          <ConnectionPanel />
        </header>
        <main className="game-main">
          <PokerTable tableId={tableId} />
        </main>
      </div>
    </PokerGameProvider>
  )
}
