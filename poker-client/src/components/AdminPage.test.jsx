import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import AdminPage from './AdminPage'

// Mock react-router-dom navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const SAMPLE_USERS = [
  { id: 1, username: 'alice', email: 'alice@example.com', is_admin: false, stack: 1000 },
  { id: 2, username: 'bob', email: null, is_admin: false, stack: 5000 },
  { id: 3, username: 'admin', email: 'admin@example.com', is_admin: true, stack: 2500 },
]

function pagedResponse(users = SAMPLE_USERS, { page = 1, pages = 1 } = {}) {
  return { users, total: users.length, page, page_size: 20, pages }
}

function renderAdmin() {
  return render(
    <BrowserRouter>
      <AdminPage />
    </BrowserRouter>
  )
}

describe('AdminPage — access control', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    global.fetch = vi.fn()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('redirects to / when is_admin is not set', () => {
    renderAdmin()
    expect(mockNavigate).toHaveBeenCalledWith('/')
  })

  it('redirects to / when is_admin is "false"', () => {
    localStorage.setItem('is_admin', 'false')
    renderAdmin()
    expect(mockNavigate).toHaveBeenCalledWith('/')
  })

  it('does not redirect when is_admin is "true"', async () => {
    localStorage.setItem('is_admin', 'true')
    localStorage.setItem('auth_token', 'tok')

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => pagedResponse(),
    })

    renderAdmin()
    expect(mockNavigate).not.toHaveBeenCalledWith('/')
  })
})

describe('AdminPage — user table rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    localStorage.setItem('is_admin', 'true')
    localStorage.setItem('auth_token', 'admin-token')
    global.fetch = vi.fn()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('renders the page title and back link', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => pagedResponse([]),
    })

    renderAdmin()
    expect(screen.getByText('Admin Console')).toBeInTheDocument()
    expect(screen.getByText('Back to Lobby')).toBeInTheDocument()
  })

  it('shows loading state initially', () => {
    global.fetch.mockReturnValueOnce(new Promise(() => {})) // never resolves
    renderAdmin()
    expect(screen.getByText('Loading users...')).toBeInTheDocument()
  })

  it('renders user rows after fetch succeeds', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => pagedResponse(),
    })

    renderAdmin()

    await waitFor(() => {
      expect(screen.getByText('alice')).toBeInTheDocument()
      expect(screen.getByText('bob')).toBeInTheDocument()
      expect(screen.getByText('admin')).toBeInTheDocument()
    })
  })

  it('renders email addresses when present', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => pagedResponse(),
    })

    renderAdmin()

    await waitFor(() => {
      expect(screen.getByText('alice@example.com')).toBeInTheDocument()
      expect(screen.getByText('admin@example.com')).toBeInTheDocument()
    })
  })

  it('renders em-dash for null email', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => pagedResponse(),
    })

    renderAdmin()

    await waitFor(() => {
      // bob has no email — displayed as —
      const dashes = screen.getAllByText('—')
      expect(dashes.length).toBeGreaterThan(0)
    })
  })

  it('renders correct stack values in inputs', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => pagedResponse(),
    })

    renderAdmin()

    await waitFor(() => {
      const inputs = screen.getAllByRole('spinbutton')
      const values = inputs.map(i => i.value)
      expect(values).toContain('1000')
      expect(values).toContain('5000')
      expect(values).toContain('2500')
    })
  })

  it('calls GET /api/admin/users with auth token', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => pagedResponse([]),
    })

    renderAdmin()

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/users'),
        expect.objectContaining({
          headers: expect.objectContaining({ Authorization: 'Bearer admin-token' }),
        })
      )
    })
  })
})

describe('AdminPage — stack editing', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    localStorage.setItem('is_admin', 'true')
    localStorage.setItem('auth_token', 'admin-token')
    global.fetch = vi.fn()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('Save button is hidden when stack is unchanged', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => pagedResponse(),
    })

    renderAdmin()

    await waitFor(() => {
      expect(screen.getByText('alice')).toBeInTheDocument()
    })

    expect(screen.queryByText('Save')).not.toBeInTheDocument()
  })

  it('Save button appears when stack input is changed', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => pagedResponse(),
    })

    renderAdmin()

    await waitFor(() => {
      expect(screen.getByText('alice')).toBeInTheDocument()
    })

    const inputs = screen.getAllByRole('spinbutton')
    // Change alice's stack (first input, value 1000)
    await user.clear(inputs[0])
    await user.type(inputs[0], '9999')

    expect(screen.getByText('Save')).toBeInTheDocument()
  })

  it('Save button calls PATCH stack endpoint', async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => pagedResponse() })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ user_id: 1, stack: 9999 }) })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => pagedResponse() }) // refetch

    renderAdmin()

    await waitFor(() => {
      expect(screen.getByText('alice')).toBeInTheDocument()
    })

    const inputs = screen.getAllByRole('spinbutton')
    await user.clear(inputs[0])
    await user.type(inputs[0], '9999')

    const saveButton = screen.getByText('Save')
    await user.click(saveButton)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/users/1/stack'),
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ stack: 9999 }),
        })
      )
    })
  })

  it('refetches user list after saving stack', async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => pagedResponse() })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ user_id: 1, stack: 9999 }) })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => pagedResponse() }) // refetch

    renderAdmin()

    await waitFor(() => {
      expect(screen.getByText('alice')).toBeInTheDocument()
    })

    const inputs = screen.getAllByRole('spinbutton')
    await user.clear(inputs[0])
    await user.type(inputs[0], '9999')
    await user.click(screen.getByText('Save'))

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(3)
    })
  })
})

describe('AdminPage — admin toggle', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    localStorage.setItem('is_admin', 'true')
    localStorage.setItem('auth_token', 'admin-token')
    global.fetch = vi.fn()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('renders "Admin" button for admin users and "User" for non-admins', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => pagedResponse(),
    })

    renderAdmin()

    await waitFor(() => {
      // alice and bob are non-admins
      const userButtons = screen.getAllByRole('button', { name: 'User' })
      expect(userButtons.length).toBe(2)
      // admin user has Admin button (use role to avoid matching the <th> header)
      const adminButtons = screen.getAllByRole('button', { name: 'Admin' })
      expect(adminButtons.length).toBe(1)
    })
  })

  it('clicking "User" button calls promote endpoint', async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => pagedResponse() })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ user_id: 1, is_admin: true }) })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => pagedResponse() }) // refetch

    renderAdmin()

    await waitFor(() => {
      expect(screen.getAllByText('User').length).toBe(2)
    })

    const userButtons = screen.getAllByText('User')
    await user.click(userButtons[0]) // promote alice

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/promote'),
        expect.objectContaining({ method: 'PATCH' })
      )
    })
  })

  it('clicking "Admin" button calls demote endpoint', async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => pagedResponse() })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ user_id: 3, is_admin: false }) })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => pagedResponse() }) // refetch

    renderAdmin()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Admin' })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: 'Admin' }))

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/demote'),
        expect.objectContaining({ method: 'PATCH' })
      )
    })
  })

  it('refetches user list after admin toggle', async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => pagedResponse() })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ user_id: 1, is_admin: true }) })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => pagedResponse() })

    renderAdmin()

    await waitFor(() => {
      expect(screen.getAllByText('User').length).toBe(2)
    })

    await user.click(screen.getAllByText('User')[0])

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(3)
    })
  })

  it('shows error message on demote 400 (cannot demote self)', async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => pagedResponse() })
      .mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Cannot demote yourself' }),
      })

    renderAdmin()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Admin' })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: 'Admin' }))

    await waitFor(() => {
      expect(screen.getByText('Cannot demote yourself')).toBeInTheDocument()
    })
  })
})

describe('AdminPage — auth error handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    localStorage.setItem('is_admin', 'true')
    localStorage.setItem('auth_token', 'bad-token')
    global.fetch = vi.fn()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('redirects to / on 401 from user list fetch', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false, status: 401, json: async () => ({}) })

    renderAdmin()

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('redirects to / on 403 from user list fetch', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false, status: 403, json: async () => ({}) })

    renderAdmin()

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('shows error message on non-auth fetch failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({}) })

    renderAdmin()

    await waitFor(() => {
      expect(screen.getByText(/HTTP 500/i)).toBeInTheDocument()
    })
  })

  it('error message can be dismissed', async () => {
    const user = userEvent.setup()
    global.fetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({}) })

    renderAdmin()

    await waitFor(() => {
      expect(screen.getByText(/HTTP 500/i)).toBeInTheDocument()
    })

    await user.click(screen.getByText('×'))

    await waitFor(() => {
      expect(screen.queryByText(/HTTP 500/i)).not.toBeInTheDocument()
    })
  })
})

describe('AdminPage — Lobby admin link', () => {
  // Tests that the Admin link appears in Lobby when is_admin=true
  // are covered in the broader Lobby.test.jsx suite; this block ensures
  // the AdminPage link leads back to the lobby.

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    localStorage.setItem('is_admin', 'true')
    localStorage.setItem('auth_token', 'admin-token')
    global.fetch = vi.fn()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('renders a "Back to Lobby" link pointing to /', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, status: 200, json: async () => [] })

    renderAdmin()

    const link = screen.getByText('Back to Lobby')
    expect(link.closest('a')).toHaveAttribute('href', '/')
  })
})
