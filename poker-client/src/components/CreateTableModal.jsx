/**
 * Modal for creating a new poker table.
 */
import { useState } from 'react'
import { useLobby } from '../hooks/useLobby'
import './CreateTableModal.css'

export default function CreateTableModal({ onClose, onCreated }) {
  const { createTable } = useLobby()
  const [formData, setFormData] = useState({
    name: '',
    small_blind: 5,
    big_blind: 10,
    max_players: 8,
    turn_timeout_seconds: 30,
  })
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)

    const table = await createTable(formData)
    if (table && onCreated) {
      onCreated(table)
    }

    setSubmitting(false)
  }

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>Create New Table</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Table Name</label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => updateField('name', e.target.value)}
              required
              maxLength={50}
              placeholder="High Stakes Table"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="small_blind">Small Blind</label>
              <input
                id="small_blind"
                type="number"
                value={formData.small_blind}
                onChange={(e) => updateField('small_blind', parseInt(e.target.value))}
                min={1}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="big_blind">Big Blind</label>
              <input
                id="big_blind"
                type="number"
                value={formData.big_blind}
                onChange={(e) => updateField('big_blind', parseInt(e.target.value))}
                min={2}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="max_players">Max Players</label>
              <select
                id="max_players"
                value={formData.max_players}
                onChange={(e) => updateField('max_players', parseInt(e.target.value))}
              >
                {[2, 3, 4, 5, 6, 7, 8].map(n => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="timeout">Turn Timeout (seconds)</label>
              <input
                id="timeout"
                type="number"
                value={formData.turn_timeout_seconds}
                onChange={(e) => updateField('turn_timeout_seconds', parseInt(e.target.value))}
                min={10}
                max={120}
                required
              />
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Creating...' : 'Create Table'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
