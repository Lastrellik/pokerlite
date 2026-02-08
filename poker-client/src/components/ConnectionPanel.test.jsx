import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import ConnectionPanel from './ConnectionPanel'

// Mock the hooks
const mockConnect = vi.fn()
const mockDisconnect = vi.fn()
const mockNavigate = vi.fn()

vi.mock('../hooks/usePokerGame.jsx', () => ({
  usePokerGame: () => ({
    connected: false,
    myPid: null,
    connect: mockConnect,
    disconnect: mockDisconnect,
  }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ tableId: 'test-table-123' }),
    useNavigate: () => mockNavigate,
  }
})

describe('ConnectionPanel Component', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
  })

  const renderPanel = () => {
    return render(
      <BrowserRouter>
        <ConnectionPanel />
      </BrowserRouter>
    )
  }

  it('shows name input when no name is saved', () => {
    renderPanel()
    
    expect(screen.getByPlaceholderText('Enter your name')).toBeInTheDocument()
    expect(screen.getByText('Join')).toBeInTheDocument()
  })

  it('disables join button when name is empty', () => {
    renderPanel()
    
    const joinButton = screen.getByText('Join')
    expect(joinButton).toBeDisabled()
  })

  it('enables join button when name is entered', async () => {
    renderPanel()
    
    const input = screen.getByPlaceholderText('Enter your name')
    await user.type(input, 'TestPlayer')

    const joinButton = screen.getByText('Join')
    expect(joinButton).not.toBeDisabled()
  })

  it('calls connect with player name when join is clicked', async () => {
    renderPanel()
    
    const input = screen.getByPlaceholderText('Enter your name')
    await user.type(input, 'TestPlayer')

    const joinButton = screen.getByText('Join')
    await user.click(joinButton)

    await waitFor(() => {
      expect(mockConnect).toHaveBeenCalledWith('TestPlayer', 'test-table-123')
    })
  })

  it('saves player name to sessionStorage on connect', async () => {
    renderPanel()
    
    const input = screen.getByPlaceholderText('Enter your name')
    await user.type(input, 'TestPlayer')

    const joinButton = screen.getByText('Join')
    await user.click(joinButton)

    await waitFor(() => {
      expect(sessionStorage.setItem).toHaveBeenCalledWith('playerName', 'TestPlayer')
    })
  })

  it('calls connect on Enter key press', async () => {
    renderPanel()

    const input = screen.getByPlaceholderText('Enter your name')
    await user.type(input, 'TestPlayer{Enter}')

    await waitFor(() => {
      expect(mockConnect).toHaveBeenCalledWith('TestPlayer', 'test-table-123')
    })
  })

  it('pre-fills name from sessionStorage but allows editing', async () => {
    sessionStorage.setItem('playerName', 'SavedName')

    renderPanel()

    const input = screen.getByPlaceholderText('Enter your name')
    expect(input).toHaveValue('SavedName')

    // Can still edit it
    await user.clear(input)
    await user.type(input, 'NewName')
    expect(input).toHaveValue('NewName')
  })
})

describe('ConnectionPanel - Connected State', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.setItem('playerName', 'SavedPlayer')
  })

  it('shows connected status when connected', () => {
    vi.doMock('../hooks/usePokerGame.jsx', () => ({
      usePokerGame: () => ({
        connected: true,
        myPid: 'player-123',
        connect: mockConnect,
        disconnect: mockDisconnect,
      }),
    }))

    render(
      <BrowserRouter>
        <ConnectionPanel />
      </BrowserRouter>
    )
    
    expect(screen.getByText('🟢')).toBeInTheDocument()
    expect(screen.getByText(/SavedPlayer/)).toBeInTheDocument()
  })

  it('calls disconnect and navigates to lobby when leave is clicked', async () => {
    vi.doMock('../hooks/usePokerGame.jsx', () => ({
      usePokerGame: () => ({
        connected: true,
        myPid: 'player-123',
        connect: mockConnect,
        disconnect: mockDisconnect,
      }),
    }))

    render(
      <BrowserRouter>
        <ConnectionPanel />
      </BrowserRouter>
    )
    
    const leaveButton = screen.getByText('Leave Table')
    await user.click(leaveButton)

    expect(mockDisconnect).toHaveBeenCalledWith('test-table-123')
    expect(mockNavigate).toHaveBeenCalledWith('/')
  })
})
