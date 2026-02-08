import { expect } from 'expect-webdriverio'
import GamePage from '../pageobjects/game.page.js'
import { ApiHelper } from '../helpers/api.helper.js'
import { KNOWN_HANDS } from '../fixtures/hands.js'

describe('Deterministic Hands', () => {
    let tableId

    beforeEach(async () => {
        tableId = await ApiHelper.createTable({
            smallBlind: 5,
            bigBlind: 10,
            turnTimeout: 30,
        })
    })

    afterEach(async () => {
        // Clean up table
        if (tableId) {
            await ApiHelper.deleteTable(tableId)
        }
    })

    it('should deal deterministic cards with seed', async () => {
        const seed = KNOWN_HANDS.SEED_12345.seed

        // Set the seed
        await ApiHelper.setDeckSeed(tableId, seed)

        // Join players
        await GamePage.open(tableId)
        await GamePage.joinAsPlayer('Alice')

        await GamePage.openInNewWindow(tableId)
        await GamePage.joinAsPlayer('Bob')

        const handles = await browser.getWindowHandles()
        await browser.switchToWindow(handles[0])

        // Start hand
        await GamePage.startHand()

        // Get the table state from API to verify determinism
        const state1 = await ApiHelper.getTableState(tableId)

        // Verify we have a deck
        expect(state1.deck).toBeDefined()
        expect(state1.remaining_cards).toBeGreaterThan(0)

        // Store the initial state for comparison
        console.log('Seed:', seed)
        console.log('First deal - Board:', state1.board)
        console.log('First deal - Hole cards:', state1.hole_cards)

        // Fold to end hand quickly
        await GamePage.performAction('fold')
    })

    it('should produce consistent results across multiple runs with same seed', async () => {
        const seed = KNOWN_HANDS.SEED_42.seed
        const runs = []

        // Run the same scenario 3 times with the same seed
        for (let run = 0; run < 3; run++) {
            const testTableId = await ApiHelper.createTable()
            await ApiHelper.setDeckSeed(testTableId, seed)

            // Quick game setup via API and automation
            await GamePage.open(testTableId)
            await GamePage.joinAsPlayer('Alice')

            await GamePage.openInNewWindow(testTableId)
            await GamePage.joinAsPlayer('Bob')

            const handles = await browser.getWindowHandles()
            await browser.switchToWindow(handles[0])

            await GamePage.startHand()

            // Check-check through one street to get flop
            await GamePage.performAction('call')

            await browser.switchToWindow(handles[1])
            await GamePage.waitForMyTurn()
            await GamePage.performAction('check')

            // Wait for flop to be dealt
            await browser.waitUntil(async () => {
                const state = await ApiHelper.getTableState(testTableId)
                return state.board && state.board.length === 3
            }, { timeout: 5000, timeoutMsg: 'Flop should be dealt' })

            // Get the state
            const state = await ApiHelper.getTableState(testTableId)

            // Store cards only, normalize by sorting player IDs
            const holeCardsArray = Object.values(state.hole_cards).sort()
            runs.push({
                board: state.board,
                holeCards: holeCardsArray,
            })

            // Cleanup
            await browser.switchToWindow(handles[0])
            const foldBtn = await GamePage.foldBtn
            if (await foldBtn.isClickable()) {
                await GamePage.performAction('fold')
            }

            // Close extra window
            await GamePage.closeExtraWindows()
        }

        // All runs should have identical boards and hole cards
        console.log('Run 1:', runs[0])
        console.log('Run 2:', runs[1])
        console.log('Run 3:', runs[2])

        expect(JSON.stringify(runs[0])).toBe(JSON.stringify(runs[1]))
        expect(JSON.stringify(runs[1])).toBe(JSON.stringify(runs[2]))
    })

    it('should produce different results with different seeds', async () => {
        const results = []

        const seeds = [KNOWN_HANDS.SEED_12345.seed, KNOWN_HANDS.SEED_99999.seed]

        for (const seed of seeds) {
            const testTableId = await ApiHelper.createTable()
            await ApiHelper.setDeckSeed(testTableId, seed)

            await GamePage.open(testTableId)
            await GamePage.joinAsPlayer('Alice')

            await GamePage.openInNewWindow(testTableId)
            await GamePage.joinAsPlayer('Bob')

            const handles = await browser.getWindowHandles()
            await browser.switchToWindow(handles[0])

            await GamePage.startHand()

            const state = await ApiHelper.getTableState(testTableId)
            results.push(state.deck)

            // Cleanup
            await GamePage.performAction('fold')
            await GamePage.closeExtraWindows()
        }

        // Different seeds should produce different decks
        expect(JSON.stringify(results[0])).not.toBe(JSON.stringify(results[1]))
    })

    it('should allow verification of specific hand outcomes', async () => {
        const seed = KNOWN_HANDS.SEED_777.seed

        await ApiHelper.setDeckSeed(tableId, seed)

        await GamePage.open(tableId)
        await GamePage.joinAsPlayer('Alice')

        await GamePage.openInNewWindow(tableId)
        await GamePage.joinAsPlayer('Bob')

        const handles = await browser.getWindowHandles()
        await browser.switchToWindow(handles[0])

        await GamePage.startHand()

        // Preflop: Alice calls, Bob checks
        await GamePage.performAction('call')

        await browser.switchToWindow(handles[1])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        // Flop - Bob acts first in heads-up
        await browser.switchToWindow(handles[1])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        await browser.switchToWindow(handles[0])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        // Turn - Bob acts first
        await browser.switchToWindow(handles[1])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        await browser.switchToWindow(handles[0])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        // River - Bob acts first
        await browser.switchToWindow(handles[1])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        await browser.switchToWindow(handles[0])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        // Wait for river to be fully dealt (5 cards on board)
        await browser.waitUntil(async () => {
            const cards = await GamePage.getBoardCards()
            return cards.length === 5
        }, { timeout: 5000, timeoutMsg: 'River should be dealt with 5 cards' })

        // Wait for showdown to complete - Start Hand button should reappear
        await GamePage.startHandBtn.waitForDisplayed({
            timeout: 10000,
            timeoutMsg: 'Start Hand button should reappear after showdown'
        })

        console.log('✓ Showdown completed successfully with seed 777')
    })

    afterEach(async () => {
        await GamePage.closeExtraWindows()
    })
})
