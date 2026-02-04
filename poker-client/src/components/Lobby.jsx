/**
 * Lobby component - displays list of tables and allows creation/joining.
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLobby } from '../hooks/useLobby'
import CreateTableModal from './CreateTableModal'
import './Lobby.css'

export default function Lobby() {
  const navigate = useNavigate()
  const { tables, loading, error, fetchTables } = useLobby()
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    fetchTables()
    // Refresh table list every 5 seconds
    const interval = setInterval(fetchTables, 5000)
    return () => clearInterval(interval)
  }, [fetchTables])

  const handleJoinTable = (tableId) => {
    navigate(`/table/${tableId}`)
  }

  return (
    <div className="lobby">
      <div className="lobby-header">
        <h1>🎰 PokerLite Lobby</h1>
        <button onClick={() => setShowCreateModal(true)} className="btn-create">
          + Create Table
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="tables-container">
        {loading && tables.length === 0 ? (
          <div className="loading">Loading tables...</div>
        ) : tables.length === 0 ? (
          <div className="empty-state">
            <p>No tables available</p>
            <p>Create one to get started!</p>
          </div>
        ) : (
          <div className="tables-grid">
            {tables.map(table => (
              <div key={table.table_id} className="table-card">
                <h3>{table.name}</h3>
                <div className="table-info">
                  <div className="info-row">
                    <span className="label">Blinds:</span>
                    <span className="value">${table.small_blind}/${table.big_blind}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Max Players:</span>
                    <span className="value">{table.max_players}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Turn Timeout:</span>
                    <span className="value">{table.turn_timeout_seconds}s</span>
                  </div>
                </div>
                <button
                  onClick={() => handleJoinTable(table.table_id)}
                  className="btn-join"
                >
                  Join Table
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {showCreateModal && (
        <CreateTableModal
          onClose={() => setShowCreateModal(false)}
          onCreated={(table) => {
            setShowCreateModal(false)
            handleJoinTable(table.table_id)
          }}
        />
      )}
    </div>
  )
}
