import { useState, useEffect, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import './AdminPage.css'

const LOBBY_URL = import.meta.env.VITE_LOBBY_URL || 'http://localhost:8000'

export default function AdminPage() {
  const navigate = useNavigate()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editStacks, setEditStacks] = useState({})
  const [saving, setSaving] = useState({})
  const [pendingDelete, setPendingDelete] = useState(new Set())

  const authToken = localStorage.getItem('auth_token')

  const handleAuthError = useCallback(() => {
    navigate('/')
  }, [navigate])

  const fetchUsers = useCallback(async () => {
    try {
      const res = await fetch(`${LOBBY_URL}/api/admin/users`, {
        headers: { Authorization: `Bearer ${authToken}` },
      })
      if (res.status === 401 || res.status === 403) {
        handleAuthError()
        return
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setUsers(data)
      setEditStacks({})
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [authToken, handleAuthError])

  useEffect(() => {
    if (localStorage.getItem('is_admin') !== 'true') {
      navigate('/')
      return
    }
    fetchUsers()
  }, [navigate, fetchUsers])

  const handleStackChange = (userId, value) => {
    setEditStacks(prev => ({ ...prev, [userId]: value }))
  }

  const handleSaveStack = async (userId, originalStack) => {
    const newStack = parseInt(editStacks[userId], 10)
    if (isNaN(newStack) || newStack < 0 || newStack > 10_000_000) return

    setSaving(prev => ({ ...prev, [userId]: true }))
    try {
      const res = await fetch(`${LOBBY_URL}/api/admin/users/${userId}/stack`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ stack: newStack }),
      })
      if (res.status === 401 || res.status === 403) {
        handleAuthError()
        return
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await fetchUsers()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(prev => ({ ...prev, [userId]: false }))
    }
  }

  const handleDeleteClick = (userId) => {
    setPendingDelete(prev => new Set([...prev, userId]))
  }

  const handleDeleteCancel = (userId) => {
    setPendingDelete(prev => {
      const next = new Set(prev)
      next.delete(userId)
      return next
    })
  }

  const handleDeleteConfirm = async (userId) => {
    try {
      const res = await fetch(`${LOBBY_URL}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${authToken}` },
      })
      if (res.status === 401 || res.status === 403) {
        handleAuthError()
        return
      }
      if (!res.ok) {
        const data = await res.json()
        setError(data.detail || `HTTP ${res.status}`)
        handleDeleteCancel(userId)
        return
      }
      await fetchUsers()
    } catch (err) {
      setError(err.message)
      handleDeleteCancel(userId)
    }
  }

  const handleToggleAdmin = async (userId, currentIsAdmin) => {
    const endpoint = currentIsAdmin ? 'demote' : 'promote'
    try {
      const res = await fetch(`${LOBBY_URL}/api/admin/users/${userId}/${endpoint}`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${authToken}` },
      })
      if (res.status === 401 || res.status === 403) {
        handleAuthError()
        return
      }
      if (!res.ok) {
        const data = await res.json()
        setError(data.detail || `HTTP ${res.status}`)
        return
      }
      await fetchUsers()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Admin Console</h1>
        <Link to="/" className="admin-back">Back to Lobby</Link>
      </div>

      {error && (
        <div className="admin-error">
          {error}
          <button onClick={() => setError('')} className="admin-error-dismiss">×</button>
        </div>
      )}

      {loading ? (
        <div className="admin-loading">Loading users...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Stack</th>
                <th>Admin</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => {
                const editedStack = editStacks[user.id]
                const originalStack = user.stack ?? 0
                const stackValue = editedStack !== undefined ? editedStack : originalStack
                const isDirty = editedStack !== undefined && parseInt(editedStack, 10) !== originalStack

                return (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td>{user.username}</td>
                    <td>{user.email || <span className="admin-none">—</span>}</td>
                    <td className="stack-cell">
                      <input
                        type="number"
                        className="stack-input"
                        value={stackValue}
                        min={0}
                        max={10000000}
                        onChange={e => handleStackChange(user.id, e.target.value)}
                      />
                      {isDirty && (
                        <button
                          className="btn-save"
                          disabled={saving[user.id]}
                          onClick={() => handleSaveStack(user.id, originalStack)}
                        >
                          {saving[user.id] ? '...' : 'Save'}
                        </button>
                      )}
                    </td>
                    <td>
                      <button
                        className={`btn-toggle-admin ${user.is_admin ? 'is-admin' : ''}`}
                        onClick={() => handleToggleAdmin(user.id, user.is_admin)}
                      >
                        {user.is_admin ? 'Admin' : 'User'}
                      </button>
                    </td>
                    <td className="delete-cell">
                      {pendingDelete.has(user.id) ? (
                        <>
                          <button className="btn-confirm-delete" onClick={() => handleDeleteConfirm(user.id)}>Confirm</button>
                          <button className="btn-cancel-delete" onClick={() => handleDeleteCancel(user.id)}>Cancel</button>
                        </>
                      ) : (
                        <button className="btn-delete" onClick={() => handleDeleteClick(user.id)}>Delete</button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
