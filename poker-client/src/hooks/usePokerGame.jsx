import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'

const PokerGameContext = createContext()

export function PokerGameProvider({ children }) {
  const [connected, setConnected] = useState(false)
  const [myPid, setMyPid] = useState(localStorage.getItem('pokerlite_pid') || null)
  const [gameState, setGameState] = useState(null)
  const [logs, setLogs] = useState([])
  const [handResult, setHandResult] = useState(null)
  const wsRef = useRef(null)

  const addLog = useCallback((message) => {
    setLogs(prev => [...prev.slice(-50), { time: new Date().toLocaleTimeString(), message }])
  }, [])

  const connect = useCallback((playerName, tableId) => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    const ws = new WebSocket(`ws://localhost:8000/ws/${tableId}`)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')
      ws.send(JSON.stringify({
        type: 'join',
        name: playerName,
        pid: myPid
      }))
      setConnected(true)
      addLog(`Connected to table: ${tableId}`)
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)

        if (msg.type === 'welcome') {
          setMyPid(msg.pid)
          localStorage.setItem('pokerlite_pid', msg.pid)
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
  }, [myPid, addLog])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setConnected(false)
  }, [])

  const clearPlayerId = useCallback(() => {
    setMyPid(null)
    localStorage.removeItem('pokerlite_pid')
    addLog('Player ID cleared - you will get a new ID on reconnect')
  }, [addLog])

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
    clearPlayerId,
    sendAction,
    startHand,
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
