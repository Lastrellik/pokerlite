import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { PokerGameProvider, usePokerGame } from './usePokerGame'

// Helper to render hook with provider
const renderPokerHook = () => {
  return renderHook(() => usePokerGame(), {
    wrapper: ({ children }) => <PokerGameProvider>{children}</PokerGameProvider>,
  })
}

describe('usePokerGame', () => {
  let mockWebSocket

  beforeEach(() => {
    mockWebSocket = null
    // Clear localStorage before each test
    localStorage.clear()
    // Capture the WebSocket instance when created
    const OriginalWebSocket = global.WebSocket
    global.WebSocket = class extends OriginalWebSocket {
      constructor(url) {
        super(url)
        mockWebSocket = this
      }
    }
  })

  describe('initial state', () => {
    it('starts disconnected', () => {
      const { result } = renderPokerHook()

      expect(result.current.connected).toBe(false)
      expect(result.current.myPid).toBeNull()
      expect(result.current.gameState).toBeNull()
    })

    it('has empty logs', () => {
      const { result } = renderPokerHook()

      expect(result.current.logs).toEqual([])
    })
  })

  describe('connect', () => {
    it('creates WebSocket connection', async () => {
      const { result } = renderPokerHook()

      act(() => {
        result.current.connect('Alice', 'table-1')
      })

      await waitFor(() => {
        expect(result.current.connected).toBe(true)
      })
    })

    it('sends join message on connect with null pid for new player', async () => {
      const { result } = renderPokerHook()

      act(() => {
        result.current.connect('Alice', 'table-1')
      })

      await waitFor(() => {
        expect(mockWebSocket.lastSentData).toBeDefined()
        const sent = JSON.parse(mockWebSocket.lastSentData)
        expect(sent.type).toBe('join')
        expect(sent.name).toBe('Alice')
        expect(sent.pid).toBeNull()
      })
    })

    it('reuses pid from localStorage on reconnect', async () => {
      // Simulate previously saved pid
      localStorage.setItem('pid_table-1', 'saved-pid-123')

      const { result } = renderPokerHook()

      act(() => {
        result.current.connect('Alice', 'table-1')
      })

      await waitFor(() => {
        expect(mockWebSocket.lastSentData).toBeDefined()
        const sent = JSON.parse(mockWebSocket.lastSentData)
        expect(sent.type).toBe('join')
        expect(sent.pid).toBe('saved-pid-123')
      })
    })

    it('adds connection log', async () => {
      const { result } = renderPokerHook()

      act(() => {
        result.current.connect('Alice', 'table-1')
      })

      await waitFor(() => {
        expect(result.current.logs.length).toBeGreaterThan(0)
        expect(result.current.logs.some(l => l.message.includes('table-1'))).toBe(true)
      })
    })
  })

  describe('message handling', () => {
    it('sets myPid on welcome message and saves to localStorage', async () => {
      const { result } = renderPokerHook()

      act(() => {
        result.current.connect('Alice', 'table-1')
      })

      await waitFor(() => expect(result.current.connected).toBe(true))

      act(() => {
        mockWebSocket.simulateMessage({ type: 'welcome', pid: 'player-123' })
      })

      expect(result.current.myPid).toBe('player-123')
      expect(localStorage.getItem('pid_table-1')).toBe('player-123')
    })

    it('updates gameState on state message', async () => {
      const { result } = renderPokerHook()

      act(() => {
        result.current.connect('Alice', 'table-1')
      })

      await waitFor(() => expect(result.current.connected).toBe(true))

      const mockState = {
        table_id: 'table-1',
        players: [{ pid: 'p1', name: 'Alice' }],
        pot: 100,
      }

      act(() => {
        mockWebSocket.simulateMessage({ type: 'state', state: mockState })
      })

      expect(result.current.gameState).toEqual(mockState)
    })

    it('sets handResult on win message', async () => {
      const { result } = renderPokerHook()

      act(() => {
        result.current.connect('Alice', 'table-1')
      })

      await waitFor(() => expect(result.current.connected).toBe(true))

      act(() => {
        mockWebSocket.simulateMessage({ type: 'info', message: 'Alice wins 100 chips' })
      })

      expect(result.current.handResult).toBe('Alice wins 100 chips')
    })
  })

  describe('sendAction', () => {
    it('sends action message', async () => {
      const { result } = renderPokerHook()

      act(() => {
        result.current.connect('Alice', 'table-1')
      })

      await waitFor(() => expect(result.current.connected).toBe(true))

      act(() => {
        result.current.sendAction('fold')
      })

      const sent = JSON.parse(mockWebSocket.lastSentData)
      expect(sent.type).toBe('action')
      expect(sent.action).toBe('fold')
    })

    it('includes amount for raise', async () => {
      const { result } = renderPokerHook()

      act(() => {
        result.current.connect('Alice', 'table-1')
      })

      await waitFor(() => expect(result.current.connected).toBe(true))

      act(() => {
        result.current.sendAction('raise', 50)
      })

      const sent = JSON.parse(mockWebSocket.lastSentData)
      expect(sent.type).toBe('action')
      expect(sent.action).toBe('raise')
      expect(sent.amount).toBe(50)
    })
  })

  describe('startHand', () => {
    it('sends start message', async () => {
      const { result } = renderPokerHook()

      act(() => {
        result.current.connect('Alice', 'table-1')
      })

      await waitFor(() => expect(result.current.connected).toBe(true))

      act(() => {
        result.current.startHand()
      })

      const sent = JSON.parse(mockWebSocket.lastSentData)
      expect(sent.type).toBe('start')
    })
  })

  describe('disconnect', () => {
    it('closes connection and clears localStorage', async () => {
      const { result } = renderPokerHook()

      act(() => {
        result.current.connect('Alice', 'table-1')
      })

      await waitFor(() => expect(result.current.connected).toBe(true))

      // Simulate receiving welcome to save pid
      act(() => {
        mockWebSocket.simulateMessage({ type: 'welcome', pid: 'player-123' })
      })

      expect(localStorage.getItem('pid_table-1')).toBe('player-123')

      act(() => {
        result.current.disconnect('table-1')
      })

      expect(result.current.connected).toBe(false)
      expect(localStorage.getItem('pid_table-1')).toBeNull()
    })
  })

  describe('clearHandResult', () => {
    it('clears hand result', async () => {
      const { result } = renderPokerHook()

      act(() => {
        result.current.connect('Alice', 'table-1')
      })

      await waitFor(() => expect(result.current.connected).toBe(true))

      act(() => {
        mockWebSocket.simulateMessage({ type: 'info', message: 'Alice wins' })
      })

      expect(result.current.handResult).toBe('Alice wins')

      act(() => {
        result.current.clearHandResult()
      })

      expect(result.current.handResult).toBeNull()
    })
  })
})
