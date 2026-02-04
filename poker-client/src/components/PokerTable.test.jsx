import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import PokerTable from './PokerTable'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../hooks/usePokerGame.jsx', () => ({
  usePokerGame: vi.fn(),
}))

// Mock child components
vi.mock('./Card', () => ({
  default: ({ card, faceDown }) => (
    <div data-testid="card">{faceDown ? 'Face Down' : card}</div>
  ),
}))

vi.mock('./Player', () => ({
  default: ({ player }) => <div data-testid="player">{player.name}</div>,
}))

vi.mock('./ActionButtons', () => ({
  default: () => <div data-testid="action-buttons">Actions</div>,
}))

vi.mock('./GameLog', () => ({
  default: () => <div data-testid="game-log">Log</div>,
}))

vi.mock('./SpectatorPanel', () => ({
  default: ({ role }) => <div data-testid="spectator-panel">{role}</div>,
}))

import { usePokerGame } from '../hooks/usePokerGame.jsx'

describe('PokerTable Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  const renderTable = () => {
    return render(
      <BrowserRouter>
        <PokerTable tableId="test-table" />
      </BrowserRouter>
    )
  }

  it('renders table with basic elements', () => {
    usePokerGame.mockReturnValue({
      gameState: {
        pot: 100,
        board: [],
        players: [],
        hand_in_progress: false,
      },
      myPid: null,
      handResult: null,
      joinWaitlist: vi.fn(),
      leaveWaitlist: vi.fn(),
    })

    renderTable()
    
    expect(screen.getByText('POT')).toBeInTheDocument()
    expect(screen.getByText('$100')).toBeInTheDocument()
    expect(screen.getByText('Waiting for hand...')).toBeInTheDocument()
  })

  it('displays community cards when present', () => {
    usePokerGame.mockReturnValue({
      gameState: {
        pot: 100,
        board: ['Ah', 'Kd', 'Qs'],
        players: [],
        hand_in_progress: true,
        street: 'flop',
      },
      myPid: null,
      handResult: null,
      joinWaitlist: vi.fn(),
      leaveWaitlist: vi.fn(),
    })

    renderTable()
    
    const cards = screen.getAllByTestId('card')
    expect(cards).toHaveLength(3)
    expect(screen.getByText('FLOP')).toBeInTheDocument()
  })

  it('renders players around the table', () => {
    const players = [
      { pid: 'p1', name: 'Alice', seat: 1, stack: 1000, connected: true },
      { pid: 'p2', name: 'Bob', seat: 3, stack: 500, connected: true },
    ]

    usePokerGame.mockReturnValue({
      gameState: {
        pot: 0,
        board: [],
        players,
        hand_in_progress: false,
      },
      myPid: 'p1',
      handResult: null,
      joinWaitlist: vi.fn(),
      leaveWaitlist: vi.fn(),
    })

    renderTable()
    
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
  })

  it('shows action buttons for seated player', () => {
    const players = [
      { pid: 'p1', name: 'Alice', seat: 1, stack: 1000, connected: true },
    ]

    usePokerGame.mockReturnValue({
      gameState: {
        pot: 0,
        board: [],
        players,
        hand_in_progress: true,
        my_role: 'seated',
        hole_cards: ['Ah', 'Kd'],
        current_bet: 10,
        player_bets: {},
      },
      myPid: 'p1',
      handResult: null,
      joinWaitlist: vi.fn(),
      leaveWaitlist: vi.fn(),
    })

    renderTable()
    
    expect(screen.getByTestId('action-buttons')).toBeInTheDocument()
    expect(screen.getByText('Stack:')).toBeInTheDocument()
    expect(screen.getByText('$1000')).toBeInTheDocument()
  })

  it('shows spectator panel for non-seated player', () => {
    usePokerGame.mockReturnValue({
      gameState: {
        pot: 0,
        board: [],
        players: [],
        hand_in_progress: false,
        my_role: 'spectator',
      },
      myPid: 'p1',
      handResult: null,
      joinWaitlist: vi.fn(),
      leaveWaitlist: vi.fn(),
    })

    renderTable()
    
    expect(screen.getByTestId('spectator-panel')).toBeInTheDocument()
    expect(screen.getByText('spectator')).toBeInTheDocument()
  })

  it('redirects to lobby after 3 seconds when player busts out', () => {
    const players = [
      { pid: 'p1', name: 'Alice', seat: 1, stack: 0, connected: true },
    ]

    usePokerGame.mockReturnValue({
      gameState: {
        pot: 0,
        board: [],
        players,
        hand_in_progress: false,
      },
      myPid: 'p1',
      handResult: null,
      joinWaitlist: vi.fn(),
      leaveWaitlist: vi.fn(),
    })

    renderTable()
    
    expect(mockNavigate).not.toHaveBeenCalled()

    // Fast forward 3 seconds
    vi.advanceTimersByTime(3000)

    expect(mockNavigate).toHaveBeenCalledWith('/')
  })

  it('does not redirect if player has chips', () => {
    const players = [
      { pid: 'p1', name: 'Alice', seat: 1, stack: 100, connected: true },
    ]

    usePokerGame.mockReturnValue({
      gameState: {
        pot: 0,
        board: [],
        players,
        hand_in_progress: false,
      },
      myPid: 'p1',
      handResult: null,
      joinWaitlist: vi.fn(),
      leaveWaitlist: vi.fn(),
    })

    renderTable()
    
    vi.advanceTimersByTime(5000)

    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('shows hole cards for seated player', () => {
    const players = [
      { pid: 'p1', name: 'Alice', seat: 1, stack: 1000, connected: true },
    ]

    usePokerGame.mockReturnValue({
      gameState: {
        pot: 0,
        board: [],
        players,
        hand_in_progress: true,
        my_role: 'seated',
        hole_cards: ['Ah', 'Kd'],
        current_bet: 0,
        player_bets: {},
      },
      myPid: 'p1',
      handResult: null,
      joinWaitlist: vi.fn(),
      leaveWaitlist: vi.fn(),
    })

    renderTable()
    
    // Should show 2 hole cards
    const myCards = screen.getAllByTestId('card')
    expect(myCards.filter(c => c.textContent !== 'Face Down').length).toBeGreaterThan(0)
  })
})
