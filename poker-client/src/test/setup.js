import '@testing-library/jest-dom'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock WebSocket as a class
global.WebSocket = class WebSocket {
  static OPEN = 1
  static CONNECTING = 0
  static CLOSING = 2
  static CLOSED = 3

  constructor(url) {
    this.url = url
    this.send = vi.fn((data) => { this.lastSentData = data })
    this.close = vi.fn()
    this.addEventListener = vi.fn()
    this.removeEventListener = vi.fn()
    this.readyState = WebSocket.OPEN

    // Trigger onopen asynchronously for tests
    setTimeout(() => {
      if (this.onopen) this.onopen()
    }, 0)
  }

  // Helper to simulate receiving messages
  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) })
    }
  }
}

// Mock localStorage with actual storage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
  }
})()
global.localStorage = localStorageMock
