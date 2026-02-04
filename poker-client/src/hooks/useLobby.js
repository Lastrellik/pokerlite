/**
 * Hook for interacting with the lobby service API.
 */
import { useState, useCallback } from 'react'

const LOBBY_API_BASE = import.meta.env.VITE_LOBBY_URL || 'http://localhost:8000'

export function useLobby() {
  const [tables, setTables] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchTables = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${LOBBY_API_BASE}/api/tables`)
      if (!response.ok) throw new Error('Failed to fetch tables')
      const data = await response.json()
      setTables(data)
    } catch (err) {
      setError(err.message)
      console.error('Error fetching tables:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const createTable = useCallback(async (tableData) => {
    setError(null)
    try {
      const response = await fetch(`${LOBBY_API_BASE}/api/tables`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tableData),
      })
      if (!response.ok) throw new Error('Failed to create table')
      const table = await response.json()
      await fetchTables() // Refresh list
      return table
    } catch (err) {
      setError(err.message)
      console.error('Error creating table:', err)
      return null
    }
  }, [fetchTables])

  const deleteTable = useCallback(async (tableId) => {
    setError(null)
    try {
      const response = await fetch(`${LOBBY_API_BASE}/api/tables/${tableId}`, {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('Failed to delete table')
      await fetchTables() // Refresh list
      return true
    } catch (err) {
      setError(err.message)
      console.error('Error deleting table:', err)
      return false
    }
  }, [fetchTables])

  return { tables, loading, error, fetchTables, createTable, deleteTable }
}
