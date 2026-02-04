import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CreateTableModal from './CreateTableModal'

const mockCreateTable = vi.fn()

vi.mock('../hooks/useLobby', () => ({
  useLobby: () => ({
    createTable: mockCreateTable,
  }),
}))

describe('CreateTableModal Component', () => {
  const mockOnClose = vi.fn()
  const mockOnCreated = vi.fn()
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderModal = () => {
    return render(
      <CreateTableModal onClose={mockOnClose} onCreated={mockOnCreated} />
    )
  }

  it('renders create table form', () => {
    renderModal()
    
    expect(screen.getByText('Create New Table')).toBeInTheDocument()
    expect(screen.getByLabelText('Table Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Small Blind')).toBeInTheDocument()
    expect(screen.getByLabelText('Big Blind')).toBeInTheDocument()
    expect(screen.getByLabelText('Max Players')).toBeInTheDocument()
    expect(screen.getByLabelText('Turn Timeout (seconds)')).toBeInTheDocument()
  })

  it('has default values', () => {
    renderModal()
    
    expect(screen.getByLabelText('Small Blind')).toHaveValue(5)
    expect(screen.getByLabelText('Big Blind')).toHaveValue(10)
    expect(screen.getByLabelText('Max Players')).toHaveValue(8)
    expect(screen.getByLabelText('Turn Timeout (seconds)')).toHaveValue(30)
  })

  it('closes modal when cancel is clicked', async () => {
    renderModal()
    
    const cancelButton = screen.getByText('Cancel')
    await user.click(cancelButton)

    expect(mockOnClose).toHaveBeenCalled()
  })

  it('closes modal when overlay is clicked', async () => {
    const { container } = renderModal()
    
    const overlay = container.querySelector('.modal-overlay')
    await user.click(overlay)

    expect(mockOnClose).toHaveBeenCalled()
  })

  it('does not close when modal content is clicked', async () => {
    const { container } = renderModal()
    
    const content = container.querySelector('.modal-content')
    await user.click(content)

    expect(mockOnClose).not.toHaveBeenCalled()
  })

  it('updates form fields when user types', async () => {
    renderModal()
    
    const nameInput = screen.getByLabelText('Table Name')
    await user.type(nameInput, 'High Stakes')

    expect(nameInput).toHaveValue('High Stakes')
  })

  it('creates table with correct data on submit', async () => {
    const createdTable = { table_id: 'new-table', name: 'Test Table' }
    mockCreateTable.mockResolvedValue(createdTable)

    renderModal()
    
    const nameInput = screen.getByLabelText('Table Name')
    await user.type(nameInput, 'Test Table')

    const submitButton = screen.getByText('Create Table')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockCreateTable).toHaveBeenCalledWith({
        name: 'Test Table',
        small_blind: 5,
        big_blind: 10,
        max_players: 8,
        turn_timeout_seconds: 30,
      })
    })

    expect(mockOnCreated).toHaveBeenCalledWith(createdTable)
  })

  it('shows submitting state while creating table', async () => {
    mockCreateTable.mockImplementation(() => new Promise(() => {})) // Never resolves

    renderModal()
    
    const nameInput = screen.getByLabelText('Table Name')
    await user.type(nameInput, 'Test Table')

    const submitButton = screen.getByText('Create Table')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Creating...')).toBeInTheDocument()
    })

    expect(screen.getByText('Cancel')).toBeDisabled()
  })

  it('allows changing max players', async () => {
    renderModal()
    
    const maxPlayersSelect = screen.getByLabelText('Max Players')
    await user.selectOptions(maxPlayersSelect, '6')

    expect(maxPlayersSelect).toHaveValue(6)
  })

  it('does not call onCreated if table creation fails', async () => {
    mockCreateTable.mockResolvedValue(null) // Indicates failure

    renderModal()
    
    const nameInput = screen.getByLabelText('Table Name')
    await user.type(nameInput, 'Test Table')

    const submitButton = screen.getByText('Create Table')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockCreateTable).toHaveBeenCalled()
    })

    expect(mockOnCreated).not.toHaveBeenCalled()
  })
})
