import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Lobby from './Lobby'

// Mock the hooks
vi.mock('../hooks/useLobby', () => ({
  useLobby: vi.fn(),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  }
})

// Mock CreateTableModal
vi.mock('./CreateTableModal', () => ({
  default: ({ onClose, onCreated }) => (
    <div data-testid="create-modal">
      <button onClick={() => onCreated({ table_id: 'new-table-123' })}>
        Create
      </button>
      <button onClick={onClose}>Cancel</button>
    </div>
  ),
}))

import { useLobby } from '../hooks/useLobby'

// Helper to create a JWT token for testing
function createTestToken(expiresInSeconds) {
  const now = Math.floor(Date.now() / 1000)
  const payload = {
    sub: 'testuser',
    exp: now + expiresInSeconds
  }
  const encodedPayload = btoa(JSON.stringify(payload))
  return `header.${encodedPayload}.signature`
}

describe('Lobby Component', () => {
  const mockFetchTables = vi.fn()
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    localStorage.clear()
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.useRealTimers()
    localStorage.clear()
  })

  const renderLobby = () => {
    return render(
      <BrowserRouter>
        <Lobby />
      </BrowserRouter>
    )
  }

  it('renders lobby header', () => {
    useLobby.mockReturnValue({
      tables: [],
      loading: false,
      error: null,
      fetchTables: mockFetchTables,
    })

    renderLobby()
    expect(screen.getByText('🃏 PokerLite Lobby')).toBeInTheDocument()
    expect(screen.getByText('+ Create Table')).toBeInTheDocument()
  })

  it('shows loading state when tables are being fetched', () => {
    useLobby.mockReturnValue({
      tables: [],
      loading: true,
      error: null,
      fetchTables: mockFetchTables,
    })

    renderLobby()
    expect(screen.getByText('Loading tables...')).toBeInTheDocument()
  })

  it('shows error message when fetch fails', () => {
    useLobby.mockReturnValue({
      tables: [],
      loading: false,
      error: 'Failed to fetch tables',
      fetchTables: mockFetchTables,
    })

    renderLobby()
    expect(screen.getByText('Failed to fetch tables')).toBeInTheDocument()
  })

  it('shows empty state when no tables exist', () => {
    useLobby.mockReturnValue({
      tables: [],
      loading: false,
      error: null,
      fetchTables: mockFetchTables,
    })

    renderLobby()
    expect(screen.getByText('No tables available')).toBeInTheDocument()
    expect(screen.getByText('Create one to get started!')).toBeInTheDocument()
  })

  it('displays list of tables', () => {
    const mockTables = [
      {
        table_id: 'table-1',
        name: 'High Stakes',
        small_blind: 5,
        big_blind: 10,
        max_players: 8,
        turn_timeout_seconds: 30,
      },
      {
        table_id: 'table-2',
        name: 'Casual Game',
        small_blind: 1,
        big_blind: 2,
        max_players: 6,
        turn_timeout_seconds: 45,
      },
    ]

    useLobby.mockReturnValue({
      tables: mockTables,
      loading: false,
      error: null,
      fetchTables: mockFetchTables,
    })

    renderLobby()
    expect(screen.getByText('High Stakes')).toBeInTheDocument()
    expect(screen.getByText('Casual Game')).toBeInTheDocument()
    expect(screen.getByText('$5/$10')).toBeInTheDocument()
    expect(screen.getByText('$1/$2')).toBeInTheDocument()
  })

  it('fetches tables on mount and sets up auto-refresh', async () => {
    useLobby.mockReturnValue({
      tables: [],
      loading: false,
      error: null,
      fetchTables: mockFetchTables,
    })

    renderLobby()
    
    expect(mockFetchTables).toHaveBeenCalledTimes(1)

    // Fast-forward 5 seconds
    vi.advanceTimersByTime(5000)
    expect(mockFetchTables).toHaveBeenCalledTimes(2)

    // Fast-forward another 5 seconds
    vi.advanceTimersByTime(5000)
    expect(mockFetchTables).toHaveBeenCalledTimes(3)
  })

  it('opens create table modal when create button is clicked', async () => {
    // Use real timers for this test
    vi.useRealTimers()

    useLobby.mockReturnValue({
      tables: [],
      loading: false,
      error: null,
      fetchTables: mockFetchTables,
    })

    renderLobby()

    const createButton = screen.getByText('+ Create Table')
    await user.click(createButton)

    expect(screen.getByTestId('create-modal')).toBeInTheDocument()

    // Restore fake timers
    vi.useFakeTimers()
  })

  it('closes modal when cancel is clicked', async () => {
    // Use real timers for this test
    vi.useRealTimers()

    useLobby.mockReturnValue({
      tables: [],
      loading: false,
      error: null,
      fetchTables: mockFetchTables,
    })

    renderLobby()

    const createButton = screen.getByText('+ Create Table')
    await user.click(createButton)

    const cancelButton = screen.getByText('Cancel')
    await user.click(cancelButton)

    await waitFor(() => {
      expect(screen.queryByTestId('create-modal')).not.toBeInTheDocument()
    })

    // Restore fake timers
    vi.useFakeTimers()
  })
})

describe('Lobby Component - Authentication', () => {
  const mockFetchTables = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    global.fetch = vi.fn()
    useLobby.mockReturnValue({
      tables: [],
      loading: false,
      error: null,
      fetchTables: mockFetchTables,
    })
  })

  afterEach(() => {
    localStorage.clear()
  })

  const renderLobby = () => {
    return render(
      <BrowserRouter>
        <Lobby />
      </BrowserRouter>
    )
  }

  it('clears expired token on mount', () => {
    // Set up expired token in localStorage
    const expiredToken = createTestToken(-3600) // Expired 1 hour ago
    localStorage.setItem('auth_token', expiredToken)
    localStorage.setItem('username', 'testuser')
    localStorage.setItem('user_id', '123')
    localStorage.setItem('avatar_id', 'avatar1')

    renderLobby()

    // Should clear all auth data
    expect(localStorage.getItem('auth_token')).toBeNull()
    expect(localStorage.getItem('username')).toBeNull()
    expect(localStorage.getItem('user_id')).toBeNull()
    expect(localStorage.getItem('avatar_id')).toBeNull()

    // Should show login button
    expect(screen.getByText('Login / Sign Up')).toBeInTheDocument()
  })

  it('keeps valid token on mount and fetches chip count', async () => {
    // Set up valid token
    const validToken = createTestToken(3600) // Expires in 1 hour
    localStorage.setItem('auth_token', validToken)
    localStorage.setItem('username', 'testuser')

    // Mock successful chip count fetch
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ stack: 5000, user_id: 123, username: 'testuser' })
    })

    renderLobby()

    // Should keep auth data
    expect(localStorage.getItem('auth_token')).toBe(validToken)
    expect(localStorage.getItem('username')).toBe('testuser')

    // Should fetch chip count
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/auth/stack',
        expect.objectContaining({
          headers: {
            'Authorization': `Bearer ${validToken}`
          }
        })
      )
    })

    // Should display username and chip count
    await waitFor(() => {
      expect(screen.getByText('testuser')).toBeInTheDocument()
      expect(screen.getByText('💰 5000 chips')).toBeInTheDocument()
    })
  })

  it('shows login button when no token present', () => {
    renderLobby()

    expect(screen.getByText('Login / Sign Up')).toBeInTheDocument()
    expect(screen.queryByText('Logout')).not.toBeInTheDocument()
  })

  it('clears auth on 401 response when fetching chips', async () => {
    // Set up valid token
    const validToken = createTestToken(3600)
    localStorage.setItem('auth_token', validToken)
    localStorage.setItem('username', 'testuser')
    localStorage.setItem('user_id', '123')

    // Mock 401 response
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Invalid token' })
    })

    renderLobby()

    // Should attempt to fetch chip count
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
    })

    // Should clear auth data after 401
    await waitFor(() => {
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('username')).toBeNull()
      expect(localStorage.getItem('user_id')).toBeNull()
    })

    // Should show login button
    await waitFor(() => {
      expect(screen.getByText('Login / Sign Up')).toBeInTheDocument()
    })
  })

  it('clears auth on 403 response when fetching chips', async () => {
    // Set up valid token
    const validToken = createTestToken(3600)
    localStorage.setItem('auth_token', validToken)
    localStorage.setItem('username', 'testuser')

    // Mock 403 response
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'Forbidden' })
    })

    renderLobby()

    // Should clear auth data after 403
    await waitFor(() => {
      expect(localStorage.getItem('auth_token')).toBeNull()
    })
  })

  it('handles malformed token on mount', () => {
    // Set up malformed token
    localStorage.setItem('auth_token', 'not.a.valid.token')
    localStorage.setItem('username', 'testuser')

    renderLobby()

    // Should clear all auth data
    expect(localStorage.getItem('auth_token')).toBeNull()
    expect(localStorage.getItem('username')).toBeNull()

    // Should show login button
    expect(screen.getByText('Login / Sign Up')).toBeInTheDocument()
  })

  it('handles token without expiration claim', () => {
    // Create token without exp field
    const payload = { sub: 'testuser' } // No exp field
    const encodedPayload = btoa(JSON.stringify(payload))
    const tokenNoExp = `header.${encodedPayload}.signature`

    localStorage.setItem('auth_token', tokenNoExp)
    localStorage.setItem('username', 'testuser')

    // Mock successful chip count fetch
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ stack: 1000 })
    })

    renderLobby()

    // Should accept token without exp (doesn't expire)
    expect(localStorage.getItem('auth_token')).toBe(tokenNoExp)
  })
})
