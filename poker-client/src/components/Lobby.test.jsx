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

describe('Lobby Component', () => {
  const mockFetchTables = vi.fn()
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
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
