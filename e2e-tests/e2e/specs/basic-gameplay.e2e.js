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

            console.log('=== PREFLOP ===')
            // Preflop: Alice calls, Bob checks
            await GamePage.performAction('call')
            console.log('Alice called')

            await browser.switchToWindow(handles[1])
            await GamePage.waitForMyTurn(15000)
            await GamePage.performAction('check')
            console.log('Bob checked - preflop complete')

            // FLOP - In heads-up, BB (Bob) acts first post-flop
            console.log('=== FLOP ===')
            await browser.switchToWindow(handles[1])

            // Wait for flop
            await browser.waitUntil(async () => {
                const cards = await GamePage.getBoardCards()
                console.log('Waiting for flop, board has', cards.length, 'cards')
                return cards.length === 3
            }, { timeout: 10000, timeoutMsg: 'Flop should be dealt' })

            await GamePage.waitForMyTurn(15000)
            await GamePage.performAction('check')
            console.log('Bob checked on flop')

            await browser.switchToWindow(handles[0])
            await GamePage.waitForMyTurn(15000)
            await GamePage.performAction('check')
            console.log('Alice checked on flop - flop complete')

            // TURN - Bob acts first
            console.log('=== TURN ===')
            await browser.switchToWindow(handles[1])

            // Wait for turn
            await browser.waitUntil(async () => {
                const cards = await GamePage.getBoardCards()
                console.log('Waiting for turn, board has', cards.length, 'cards')
                return cards.length === 4
            }, { timeout: 10000, timeoutMsg: 'Turn should be dealt' })

            await GamePage.waitForMyTurn(15000)
            await GamePage.performAction('check')
            console.log('Bob checked on turn')

            await browser.switchToWindow(handles[0])
            await GamePage.waitForMyTurn(15000)
            await GamePage.performAction('check')
            console.log('Alice checked on turn - turn complete')

            // RIVER - Bob acts first
            console.log('=== RIVER ===')
            await browser.switchToWindow(handles[1])

            // Wait for river
            await browser.waitUntil(async () => {
                const cards = await GamePage.getBoardCards()
                console.log('Waiting for river, board has', cards.length, 'cards')
                return cards.length === 5
            }, { timeout: 10000, timeoutMsg: 'River should be dealt' })

            await GamePage.waitForMyTurn(15000)
            await GamePage.performAction('check')
            console.log('Bob checked on river')

            await browser.switchToWindow(handles[0])
            await GamePage.waitForMyTurn(15000)
            await GamePage.performAction('check')
            console.log('Alice checked on river - river complete')

            // SHOWDOWN
            console.log('=== SHOWDOWN ===')
            // Wait for showdown - hand should end and Start Hand button reappears
            await browser.switchToWindow(handles[0])
            await GamePage.startHandBtn.waitForDisplayed({
                timeout: 10000,
                timeoutMsg: 'Start Hand button should reappear after showdown'
            })
            console.log('✓ Showdown complete - Start Hand button reappeared')
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
