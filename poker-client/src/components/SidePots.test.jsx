import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import SidePots from './SidePots'

describe('SidePots', () => {
  it('renders nothing when sidePots is null', () => {
    const { container } = render(<SidePots sidePots={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when sidePots is empty array', () => {
    const { container } = render(<SidePots sidePots={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders main pot and side pot breakdown', () => {
    const sidePots = [
      { type: 'Main Pot', amount: 100, winners: ['Alice'] },
      { type: 'Side Pot 1', amount: 50, winners: ['Bob', 'Charlie'] },
    ]

    render(<SidePots sidePots={sidePots} />)

    expect(screen.getByText('Pot Breakdown')).toBeInTheDocument()
    expect(screen.getByText('Main Pot')).toBeInTheDocument()
    expect(screen.getByText('$100')).toBeInTheDocument()
    expect(screen.getByText(/Winner: Alice/)).toBeInTheDocument()

    expect(screen.getByText('Side Pot 1')).toBeInTheDocument()
    expect(screen.getByText('$50')).toBeInTheDocument()
    expect(screen.getByText(/Winners: Bob, Charlie/)).toBeInTheDocument()
  })

  it('handles single winner vs multiple winners text', () => {
    const singleWinner = [
      { type: 'Main Pot', amount: 100, winners: ['Alice'] },
    ]

    const { rerender } = render(<SidePots sidePots={singleWinner} />)
    expect(screen.getByText(/Winner:/)).toBeInTheDocument()

    const multipleWinners = [
      { type: 'Main Pot', amount: 100, winners: ['Alice', 'Bob'] },
    ]

    rerender(<SidePots sidePots={multipleWinners} />)
    expect(screen.getByText(/Winners:/)).toBeInTheDocument()
  })
})
