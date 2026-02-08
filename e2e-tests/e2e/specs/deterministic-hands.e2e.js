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
        await browser.pause(500)

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
        await browser.pause(1000)
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
            await browser.pause(500)

            // Check-check through one street to get flop
            await GamePage.performAction('call')

            await browser.switchToWindow(handles[1])
            await GamePage.waitForMyTurn()
            await GamePage.performAction('check')

            await browser.pause(1000)

            // Get the state
            const state = await ApiHelper.getTableState(testTableId)
            runs.push({
                board: state.board,
                holeCards: state.hole_cards,
            })

            // Cleanup
            await browser.switchToWindow(handles[0])
            const foldBtn = await GamePage.foldBtn
            if (await foldBtn.isClickable()) {
                await GamePage.performAction('fold')
            }
            await browser.pause(500)

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
            await browser.pause(500)

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
        await browser.pause(500)

        // Play to showdown with checks
        await GamePage.performAction('call')

        await browser.switchToWindow(handles[1])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        // Flop
        await browser.switchToWindow(handles[0])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        await browser.switchToWindow(handles[1])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        // Turn
        await browser.switchToWindow(handles[0])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        await browser.switchToWindow(handles[1])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        // River
        await browser.switchToWindow(handles[0])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        await browser.switchToWindow(handles[1])
        await GamePage.waitForMyTurn()
        await GamePage.performAction('check')

        await browser.pause(1000)

        // Get final state
        const finalState = await ApiHelper.getTableState(tableId)

        // Verify we have complete board
        expect(finalState.board.length).toBe(5)

        // Log for reference in future test development
        console.log('Seed 777 final board:', finalState.board)
        console.log('Seed 777 hole cards:', finalState.hole_cards)

        // Verify showdown happened
        const messages = await GamePage.getLogMessages(10)
        const hasOutcome = messages.some(m => m.includes('wins') || m.includes('split'))
        expect(hasOutcome).toBe(true)
    })

    afterEach(async () => {
        await GamePage.closeExtraWindows()
    })
})
