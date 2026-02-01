import '@testing-library/jest-dom'

// Mock WebSocket for tests
class MockWebSocket {
  constructor(url) {
    this.url = url
    this.readyState = WebSocket.CONNECTING
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      this.onopen?.()
    }, 0)
  }

  send(data) {
    this.lastSentData = data
  }

  close() {
    this.readyState = WebSocket.CLOSED
    this.onclose?.()
  }

  // Helper to simulate receiving a message
  simulateMessage(data) {
    this.onmessage?.({ data: JSON.stringify(data) })
  }
}

MockWebSocket.CONNECTING = 0
MockWebSocket.OPEN = 1
MockWebSocket.CLOSING = 2
MockWebSocket.CLOSED = 3

global.WebSocket = MockWebSocket
