import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Card from './Card'

describe('Card', () => {
  describe('rendering', () => {
    it('renders empty card when no card prop', () => {
      const { container } = render(<Card />)
      expect(container.querySelector('.card.empty')).toBeInTheDocument()
    })

    it('renders face-down card', () => {
      const { container } = render(<Card card="Ah" faceDown />)
      expect(container.querySelector('.card.back')).toBeInTheDocument()
      expect(container.querySelector('.card-pattern')).toBeInTheDocument()
    })

    it('renders ace of hearts correctly', () => {
      render(<Card card="Ah" />)
      expect(screen.getAllByText('A')).toHaveLength(2) // Top and bottom corners
      expect(screen.getAllByText('♥')).toHaveLength(3) // Corners + center
    })

    it('renders king of spades correctly', () => {
      render(<Card card="Ks" />)
      expect(screen.getAllByText('K')).toHaveLength(2)
      expect(screen.getAllByText('♠')).toHaveLength(3)
    })

    it('renders ten correctly (T -> 10)', () => {
      render(<Card card="Td" />)
      expect(screen.getAllByText('10')).toHaveLength(2)
    })
  })

  describe('suits and colors', () => {
    it('renders hearts as red', () => {
      const { container } = render(<Card card="Ah" />)
      expect(container.querySelector('.card.red')).toBeInTheDocument()
    })

    it('renders diamonds as red', () => {
      const { container } = render(<Card card="Ad" />)
      expect(container.querySelector('.card.red')).toBeInTheDocument()
    })

    it('renders spades as black', () => {
      const { container } = render(<Card card="As" />)
      expect(container.querySelector('.card.black')).toBeInTheDocument()
    })

    it('renders clubs as black', () => {
      const { container } = render(<Card card="Ac" />)
      expect(container.querySelector('.card.black')).toBeInTheDocument()
    })
  })

  describe('sizes', () => {
    it('renders small card', () => {
      const { container } = render(<Card card="Ah" small />)
      expect(container.querySelector('.card.small')).toBeInTheDocument()
    })

    it('renders normal size by default', () => {
      const { container } = render(<Card card="Ah" />)
      expect(container.querySelector('.card.small')).not.toBeInTheDocument()
    })
  })

  describe('highlighting', () => {
    it('renders highlighted card', () => {
      const { container } = render(<Card card="Ah" highlighted />)
      expect(container.querySelector('.card.highlighted')).toBeInTheDocument()
    })

    it('does not highlight by default', () => {
      const { container } = render(<Card card="Ah" />)
      expect(container.querySelector('.card.highlighted')).not.toBeInTheDocument()
    })
  })

  describe('flip animation', () => {
    it('renders flip container when revealing', () => {
      const { container } = render(<Card card="Ah" revealing revealDelay={0} />)
      expect(container.querySelector('.card-flip-container')).toBeInTheDocument()
      expect(container.querySelector('.card-flip-inner.flipping')).toBeInTheDocument()
    })

    it('shows both card faces when revealing', () => {
      const { container } = render(<Card card="Ah" revealing revealDelay={0} />)
      expect(container.querySelector('.card-back')).toBeInTheDocument()
      expect(container.querySelector('.card-front')).toBeInTheDocument()
    })

    it('applies reveal delay style', () => {
      const { container } = render(<Card card="Ah" revealing revealDelay={500} />)
      const flipInner = container.querySelector('.card-flip-inner')
      expect(flipInner.style.animationDelay).toBe('500ms')
    })
  })
})
