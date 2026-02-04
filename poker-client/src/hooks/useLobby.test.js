import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useLobby } from './useLobby'

describe('useLobby Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    console.error.mockRestore()
  })

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useLobby())

    expect(result.current.tables).toEqual([])
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBe(null)
  })

  it('fetches tables successfully', async () => {
    const mockTables = [
      { table_id: 'table-1', name: 'Table 1' },
      { table_id: 'table-2', name: 'Table 2' },
    ]

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockTables,
    })

    const { result } = renderHook(() => useLobby())

    await act(async () => {
      await result.current.fetchTables()
    })

    expect(result.current.tables).toEqual(mockTables)
    expect(result.current.error).toBe(null)
    expect(result.current.loading).toBe(false)
  })

  it('handles fetch tables error', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
    })

    const { result } = renderHook(() => useLobby())

    await act(async () => {
      await result.current.fetchTables()
    })

    expect(result.current.tables).toEqual([])
    expect(result.current.error).toBe('Failed to fetch tables')
    expect(result.current.loading).toBe(false)
  })

  it('creates table successfully', async () => {
    const newTable = { table_id: 'new-table', name: 'New Table' }
    const tableData = { name: 'New Table', small_blind: 1, big_blind: 2 }

    // Mock create response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => newTable,
    })

    // Mock fetchTables call after create
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [newTable],
    })

    const { result } = renderHook(() => useLobby())

    let createdTable
    await act(async () => {
      createdTable = await result.current.createTable(tableData)
    })

    expect(createdTable).toEqual(newTable)
    expect(result.current.tables).toEqual([newTable])
  })

  it('handles create table error', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
    })

    const { result } = renderHook(() => useLobby())

    let createdTable
    await act(async () => {
      createdTable = await result.current.createTable({})
    })

    expect(createdTable).toBe(null)
    expect(result.current.error).toBe('Failed to create table')
  })

  it('deletes table successfully', async () => {
    // Mock delete response
    global.fetch.mockResolvedValueOnce({
      ok: true,
    })

    // Mock fetchTables call after delete
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })

    const { result } = renderHook(() => useLobby())

    let success
    await act(async () => {
      success = await result.current.deleteTable('table-1')
    })

    expect(success).toBe(true)
    expect(result.current.tables).toEqual([])
  })

  it('handles delete table error', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
    })

    const { result } = renderHook(() => useLobby())

    let success
    await act(async () => {
      success = await result.current.deleteTable('table-1')
    })

    expect(success).toBe(false)
    expect(result.current.error).toBe('Failed to delete table')
  })
})
