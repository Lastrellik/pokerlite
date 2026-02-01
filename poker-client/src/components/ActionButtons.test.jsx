import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ActionButtons from './ActionButtons'

// Mock the usePokerGame hook
vi.mock('../hooks/usePokerGame.jsx', () => ({
  usePokerGame: () => ({
    sendAction: vi.fn(),
    startHand: vi.fn(),
  }),
}))

describe('ActionButtons', () => {
  describe('when hand not in progress', () => {
    it('shows start button when enough players', () => {
      render(
        <ActionButtons
          handInProgress={false}
          playerCount={2}
          isMyTurn={false}
          toCall={0}
          currentBet={0}
        />
      )
      expect(screen.getByText(/Start Hand/)).toBeInTheDocument()
    })

    it('shows waiting message when not enough players', () => {
      render(
        <ActionButtons
          handInProgress={false}
          playerCount={1}
          isMyTurn={false}
          toCall={0}
          currentBet={0}
        />
      )
      expect(screen.getByText(/Waiting for players/)).toBeInTheDocument()
    })
  })

  describe('when hand in progress', () => {
    it('shows all action buttons', () => {
      render(
        <ActionButtons
          handInProgress={true}
          playerCount={2}
          isMyTurn={true}
          toCall={10}
          currentBet={20}
        />
      )

      expect(screen.getByText(/Fold/)).toBeInTheDocument()
      expect(screen.getByText(/Check/)).toBeInTheDocument()
      expect(screen.getByText(/Call/)).toBeInTheDocument()
      expect(screen.getByText(/Raise/)).toBeInTheDocument()
      expect(screen.getByText(/All In/)).toBeInTheDocument()
    })

    it('shows call amount', () => {
      render(
        <ActionButtons
          handInProgress={true}
          playerCount={2}
          isMyTurn={true}
          toCall={50}
          currentBet={50}
        />
      )

      expect(screen.getByText(/Call \$50/)).toBeInTheDocument()
    })

    it('disables buttons when not my turn', () => {
      render(
        <ActionButtons
          handInProgress={true}
          playerCount={2}
          isMyTurn={false}
          toCall={10}
          currentBet={20}
        />
      )

      expect(screen.getByText(/Fold/).closest('button')).toBeDisabled()
      expect(screen.getByText(/Raise/).closest('button')).toBeDisabled()
    })

    it('disables check when there is amount to call', () => {
      render(
        <ActionButtons
          handInProgress={true}
          playerCount={2}
          isMyTurn={true}
          toCall={10}
          currentBet={20}
        />
      )

      expect(screen.getByText(/Check/).closest('button')).toBeDisabled()
    })

    it('enables check when no amount to call', () => {
      render(
        <ActionButtons
          handInProgress={true}
          playerCount={2}
          isMyTurn={true}
          toCall={0}
          currentBet={0}
        />
      )

      expect(screen.getByText(/Check/).closest('button')).not.toBeDisabled()
    })

    it('disables call when no amount to call', () => {
      render(
        <ActionButtons
          handInProgress={true}
          playerCount={2}
          isMyTurn={true}
          toCall={0}
          currentBet={0}
        />
      )

      expect(screen.getByText(/Call/).closest('button')).toBeDisabled()
    })
  })

  describe('raise input', () => {
    it('has raise amount input', () => {
      render(
        <ActionButtons
          handInProgress={true}
          playerCount={2}
          isMyTurn={true}
          toCall={0}
          currentBet={10}
        />
      )

      const input = screen.getByRole('spinbutton')
      expect(input).toBeInTheDocument()
    })

    it('allows changing raise amount', () => {
      render(
        <ActionButtons
          handInProgress={true}
          playerCount={2}
          isMyTurn={true}
          toCall={0}
          currentBet={10}
        />
      )

      const input = screen.getByRole('spinbutton')
      fireEvent.change(input, { target: { value: '50' } })
      expect(input.value).toBe('50')
    })
  })
})
