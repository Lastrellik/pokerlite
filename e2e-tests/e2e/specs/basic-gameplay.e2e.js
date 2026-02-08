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

            // Start the hand
            await GamePage.startHand()

            // Verify pot has blinds (5 + 10 = 15)
            await browser.pause(500)
            const pot = await GamePage.getPotAmount()
            expect(pot).toBe(15)

            // Verify log shows hand started
            await GamePage.waitForLogMessage('New hand started')
        })

        it('should handle fold scenario', async () => {
            // Setup two players
            await GamePage.open(tableId)
            await GamePage.joinAsPlayer('Alice')

            await GamePage.openInNewWindow(tableId)
            await GamePage.joinAsPlayer('Bob')

            const handles = await browser.getWindowHandles()
            await browser.switchToWindow(handles[0])

            await GamePage.startHand()
            await browser.pause(500)

            // Alice folds
            await GamePage.performAction('fold')

            // Bob should win
            await GamePage.waitForLogMessage('Bob wins', 5000)
        })

        it('should handle check-check to showdown', async () => {
            // Setup two players
            await GamePage.open(tableId)
            await GamePage.joinAsPlayer('Alice')

            await GamePage.openInNewWindow(tableId)
            await GamePage.joinAsPlayer('Bob')

            const handles = await browser.getWindowHandles()
            await browser.switchToWindow(handles[0])

            await GamePage.startHand()
            await browser.pause(500)

            // Play through all streets with checks
            // Preflop: Alice calls, Bob checks
            await GamePage.performAction('call')

            await browser.switchToWindow(handles[1])
            await GamePage.waitForMyTurn()
            await GamePage.performAction('check')

            // Flop: check-check
            await browser.switchToWindow(handles[0])
            await GamePage.waitForMyTurn()
            const flopCards = await GamePage.getBoardCards()
            expect(flopCards.length).toBe(3)

            await GamePage.performAction('check')

            await browser.switchToWindow(handles[1])
            await GamePage.waitForMyTurn()
            await GamePage.performAction('check')

            // Turn: check-check
            await browser.switchToWindow(handles[0])
            await GamePage.waitForMyTurn()
            const turnCards = await GamePage.getBoardCards()
            expect(turnCards.length).toBe(4)

            await GamePage.performAction('check')

            await browser.switchToWindow(handles[1])
            await GamePage.waitForMyTurn()
            await GamePage.performAction('check')

            // River: check-check
            await browser.switchToWindow(handles[0])
            await GamePage.waitForMyTurn()
            const riverCards = await GamePage.getBoardCards()
            expect(riverCards.length).toBe(5)

            await GamePage.performAction('check')

            await browser.switchToWindow(handles[1])
            await GamePage.waitForMyTurn()
            await GamePage.performAction('check')

            // Should see showdown result
            await browser.pause(1000)
            const messages = await GamePage.getLogMessages(10)
            const hasWinner = messages.some(m =>
                m.includes('wins') || m.includes('split pot')
            )
            expect(hasWinner).toBe(true)
        })

        afterEach(async () => {
            // Close extra windows
            const handles = await browser.getWindowHandles()
            for (let i = handles.length - 1; i > 0; i--) {
                await browser.switchToWindow(handles[i])
                await browser.closeWindow()
            }
            await browser.switchToWindow(handles[0])
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

            await GamePage.startHand()
            await browser.pause(500)

            const initialPot = await GamePage.getPotAmount()
            expect(initialPot).toBe(15)  // SB 5 + BB 10

            // Alice raises to 20
            await GamePage.performAction('raise')
            await browser.pause(500)

            // Pot should now be 5 + 20 = 25 (Bob's BB is already in)
            const potAfterRaise = await GamePage.getPotAmount()
            expect(potAfterRaise).toBeGreaterThan(initialPot)
        })

        afterEach(async () => {
            const handles = await browser.getWindowHandles()
            for (let i = handles.length - 1; i > 0; i--) {
                await browser.switchToWindow(handles[i])
                await browser.closeWindow()
            }
            await browser.switchToWindow(handles[0])
        })
    })
})
