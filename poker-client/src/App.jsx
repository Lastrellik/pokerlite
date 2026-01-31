import { useState } from 'react'
import PokerTable from './components/PokerTable'
import ConnectionPanel from './components/ConnectionPanel'
import { PokerGameProvider } from './hooks/usePokerGame.jsx'
import './App.css'

function App() {
  return (
    <PokerGameProvider>
      <div className="app">
        <header className="app-header">
          <h1>♠️ PokerLite ♥️</h1>
          <ConnectionPanel />
        </header>
        <main className="app-main">
          <PokerTable />
        </main>
      </div>
    </PokerGameProvider>
  )
}

export default App
