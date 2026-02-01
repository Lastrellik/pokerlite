import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Player from './Player'

const mockPlayer = {
  pid: 'p1',
  name: 'Alice',
  stack: 1000,
  seat: 1,
  connected: true,
}

describe('Player', () => {
  describe('basic rendering', () => {
    it('renders player name', () => {
      render(<Player player={mockPlayer} />)
      expect(screen.getByText('Alice')).toBeInTheDocument()
    })

    it('renders player stack', () => {
      render(<Player player={mockPlayer} />)
      expect(screen.getByText('$1000')).toBeInTheDocument()
    })

    it('shows disconnected status', () => {
      const disconnectedPlayer = { ...mockPlayer, connected: false }
      render(<Player player={disconnectedPlayer} />)
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })
  })

  describe('betting', () => {
    it('shows bet amount when player has bet', () => {
      render(<Player player={mockPlayer} playerBet={50} />)
      expect(screen.getByText('Bet: $50')).toBeInTheDocument()
    })

    it('does not show bet when zero', () => {
      render(<Player player={mockPlayer} playerBet={0} />)
      expect(screen.queryByText(/Bet:/)).not.toBeInTheDocument()
    })
  })

  describe('position badges', () => {
    it('shows dealer button', () => {
      render(<Player player={mockPlayer} isDealer />)
      expect(screen.getByText('D')).toBeInTheDocument()
    })

    it('shows small blind badge', () => {
      render(<Player player={mockPlayer} isSB />)
      expect(screen.getByText('SB')).toBeInTheDocument()
    })

    it('shows big blind badge', () => {
      render(<Player player={mockPlayer} isBB />)
      expect(screen.getByText('BB')).toBeInTheDocument()
    })

    it('shows multiple badges', () => {
      render(<Player player={mockPlayer} isDealer isSB />)
      expect(screen.getByText('D')).toBeInTheDocument()
      expect(screen.getByText('SB')).toBeInTheDocument()
    })
  })

  describe('turn indicator', () => {
    it('applies current-turn class', () => {
      const { container } = render(<Player player={mockPlayer} isCurrentTurn />)
      expect(container.querySelector('.player.current-turn')).toBeInTheDocument()
    })
  })

  describe('styling', () => {
    it('applies is-me class', () => {
      const { container } = render(<Player player={mockPlayer} isMe />)
      expect(container.querySelector('.player.is-me')).toBeInTheDocument()
    })

    it('applies small class', () => {
      const { container } = render(<Player player={mockPlayer} small />)
      expect(container.querySelector('.player.small')).toBeInTheDocument()
    })

    it('applies winner class', () => {
      const { container } = render(<Player player={mockPlayer} isWinner />)
      expect(container.querySelector('.player.winner')).toBeInTheDocument()
    })
  })

  describe('showdown cards', () => {
    const showdownCards = {
      holeCards: ['Ah', 'Kh'],
      highlightCards: ['Ah'],
      handName: 'Pair',
    }

    it('renders showdown cards', () => {
      const { container } = render(
        <Player player={mockPlayer} showdownCards={showdownCards} />
      )
      expect(container.querySelector('.player-showdown-cards')).toBeInTheDocument()
    })

    it('shows hand name for winner', () => {
      render(
        <Player player={mockPlayer} showdownCards={showdownCards} isWinner />
      )
      expect(screen.getByText('Pair')).toBeInTheDocument()
    })

    it('does not show hand name for loser', () => {
      render(
        <Player player={mockPlayer} showdownCards={showdownCards} isWinner={false} />
      )
      expect(screen.queryByText('Pair')).not.toBeInTheDocument()
    })
  })
})
