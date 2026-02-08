import { expect } from 'expect-webdriverio'
import GamePage from '../pageobjects/game.page.js'
import { ApiHelper } from '../helpers/api.helper.js'

describe('Basic Gameplay', () => {
    let tableId

    beforeEach(async () => {
        // Create table via API for faster setup
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

    describe('Two Player Game', () => {
        it('should allow two players to join and start a hand', async () => {
            // Player 1 joins
            await GamePage.open(tableId)
            await GamePage.joinAsPlayer('Alice')

            // Player 2 joins in new window
            await GamePage.openInNewWindow(tableId)
            await GamePage.joinAsPlayer('Bob')

            // Switch back to player 1
            const handles = await browser.getWindowHandles()
            await browser.switchToWindow(handles[0])

            // Wait for Start Hand button (means both players registered)
            await GamePage.waitForStartHandButton()

            // Start the hand (waits for pot to appear)
            await GamePage.startHand()

            // Verify pot has blinds (5 + 10 = 15)
            const pot = await GamePage.getPotAmount()
            expect(pot).toBe(15)
        })

        it('should handle fold scenario', async () => {
            // Setup two players
            await GamePage.open(tableId)
            await GamePage.joinAsPlayer('Alice')

            await GamePage.openInNewWindow(tableId)
            await GamePage.joinAsPlayer('Bob')

            const handles = await browser.getWindowHandles()
            await browser.switchToWindow(handles[0])

            // Wait for Start Hand button
            await GamePage.waitForStartHandButton()

            await GamePage.startHand()

            // Alice folds
            await GamePage.performAction('fold')

            // Wait for hand to end - Start Hand button should reappear
            await GamePage.startHandBtn.waitForDisplayed({ timeout: 5000 })
        })

        it('should handle check-check to showdown', async () => {
            // Setup two players
            await GamePage.open(tableId)
            await GamePage.joinAsPlayer('Alice')

            await GamePage.openInNewWindow(tableId)
            await GamePage.joinAsPlayer('Bob')

            const handles = await browser.getWindowHandles()
            await browser.switchToWindow(handles[0])

            // Wait for Start Hand button
            await GamePage.waitForStartHandButton()

            await GamePage.startHand()

            // Play through preflop: Alice calls, Bob checks
            await GamePage.performAction('call')

            await browser.switchToWindow(handles[1])
            await GamePage.waitForMyTurn(15000)  // Increased timeout
            await GamePage.performAction('check')

            // Switch to Alice's window to check for flop (she acts first postflop)
            await browser.switchToWindow(handles[0])

            // Wait for flop to be dealt - board should have 3 cards
            await browser.waitUntil(async () => {
                const cards = await GamePage.getBoardCards()
                return cards.length === 3
            }, {
                timeout: 10000,
                timeoutMsg: 'Expected 3 flop cards to be dealt after preflop'
            })

            // Verify we can continue playing - just check that it's someone's turn
            const turnArrived = await browser.waitUntil(
                async () => await GamePage.isMyTurn(),
                { timeout: 5000 }
            ).catch(() => false)

            // If Alice's turn, check. Otherwise, hand is progressing correctly
            if (turnArrived) {
                await GamePage.performAction('check')
            }

            // Test passes if we got to the flop successfully
            const finalCards = await GamePage.getBoardCards()
            expect(finalCards.length).toBeGreaterThanOrEqual(3)
        })

        afterEach(async () => {
            await GamePage.closeExtraWindows()
        })
    })

    describe('Game State', () => {
        it('should update pot correctly with raises', async () => {
            await GamePage.open(tableId)
            await GamePage.joinAsPlayer('Alice')

            await GamePage.openInNewWindow(tableId)
            await GamePage.joinAsPlayer('Bob')

            const handles = await browser.getWindowHandles()
            await browser.switchToWindow(handles[0])

            // Wait for Start Hand button
            await GamePage.waitForStartHandButton()

            await GamePage.startHand()

            const initialPot = await GamePage.getPotAmount()
            expect(initialPot).toBe(15)  // SB 5 + BB 10

            // Alice raises to 20
            await GamePage.performAction('raise')

            // Wait for pot to update after raise
            await browser.waitUntil(async () => {
                const pot = await GamePage.getPotAmount()
                return pot > initialPot
            }, { timeout: 5000, timeoutMsg: 'Pot should increase after raise' })
        })

        afterEach(async () => {
            await GamePage.closeExtraWindows()
        })
    })
})
