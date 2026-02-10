import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'

const PokerGameContext = createContext()

export function PokerGameProvider({ children }) {
  const [connected, setConnected] = useState(false)
  const [myPid, setMyPid] = useState(null)
  const [gameState, setGameState] = useState(null)
  const [logs, setLogs] = useState([])
  const [handResult, setHandResult] = useState(null)
  const wsRef = useRef(null)

  const addLog = useCallback((message) => {
    setLogs(prev => [...prev.slice(-50), { time: new Date().toLocaleTimeString(), message }])
  }, [])

  const connect = useCallback((playerName, tableId, token = null) => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    // Use environment variable or fallback to window.location for production
    const wsBaseUrl = import.meta.env.VITE_WS_URL ||
                      `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`

    const ws = new WebSocket(`${wsBaseUrl}/ws/${tableId}`)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')

      const joinMessage = {
        type: 'join',
        name: playerName
      }

      // Add token if authenticated
      if (token) {
        joinMessage.token = token
        console.log('Connecting with authentication token')
      } else {
        // Guest mode - only reuse pid if the player name matches (for reconnections)
        const savedData = sessionStorage.getItem(`player_${tableId}`)
        let savedPid = null
        if (savedData) {
          try {
            const { name, pid } = JSON.parse(savedData)
            // Only reuse pid if same player name
            if (name === playerName) {
              savedPid = pid
            }
          } catch (e) {
            // Invalid saved data, ignore
          }
        }
        if (savedPid) {
          joinMessage.pid = savedPid
        }
      }

      ws.send(JSON.stringify(joinMessage))
      setConnected(true)
      addLog(`Connected to table: ${tableId}${token ? ' (authenticated)' : ' (guest)'}`)
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)

        if (msg.type === 'welcome') {
          setMyPid(msg.pid)
          // Save both name and pid so we only reuse pid if same player reconnects (guest mode only)
          if (!token) {
            sessionStorage.setItem(`player_${tableId}`, JSON.stringify({ name: playerName, pid: msg.pid }))
          }
          addLog(`Joined as ${playerName} (${msg.pid.substring(0, 8)})`)
        } else if (msg.type === 'state') {
          setGameState(msg.state)
        } else if (msg.type === 'info') {
          addLog(`📢 ${msg.message}`)
          // Check if this is a win/loss message
          if (msg.message.toLowerCase().includes('wins') || msg.message.toLowerCase().includes('split pot')) {
            setHandResult(msg.message)
          }
        }
      } catch (e) {
        console.error('Failed to parse message:', e)
      }
    }

    ws.onclose = () => {
      setConnected(false)
      addLog('Disconnected from server')
    }

    ws.onerror = () => {
      addLog('Connection error')
    }
  }, [addLog])

  const disconnect = useCallback((tableId) => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    // Clear saved player data when explicitly disconnecting
    if (tableId) {
      sessionStorage.removeItem(`player_${tableId}`)
    }
    setConnected(false)
  }, [])

  const sendAction = useCallback((action, amount = null) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      addLog('Not connected!')
      return
    }

    const message = { type: 'action', action }
    if (amount !== null) {
      message.amount = amount
    }

    wsRef.current.send(JSON.stringify(message))
    addLog(`Action: ${action}${amount ? ` $${amount}` : ''}`)
  }, [addLog])

  const startHand = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      addLog('Not connected!')
      return
    }

    wsRef.current.send(JSON.stringify({ type: 'start' }))
    addLog('Started new hand')
  }, [addLog])

  const joinWaitlist = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      addLog('Not connected!')
      return
    }

    wsRef.current.send(JSON.stringify({ type: 'join_waitlist' }))
    addLog('Joining waitlist...')
  }, [addLog])

  const leaveWaitlist = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      addLog('Not connected!')
      return
    }

    wsRef.current.send(JSON.stringify({ type: 'leave_waitlist' }))
    addLog('Leaving waitlist...')
  }, [addLog])

  const clearHandResult = useCallback(() => {
    setHandResult(null)
  }, [])

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const value = {
    connected,
    myPid,
    gameState,
    logs,
    handResult,
    connect,
    disconnect,
    sendAction,
    startHand,
    joinWaitlist,
    leaveWaitlist,
    clearHandResult
  }

  return (
    <PokerGameContext.Provider value={value}>
      {children}
    </PokerGameContext.Provider>
  )
}

export function usePokerGame() {
  const context = useContext(PokerGameContext)
  if (!context) {
    throw new Error('usePokerGame must be used within PokerGameProvider')
  }
  return context
}
