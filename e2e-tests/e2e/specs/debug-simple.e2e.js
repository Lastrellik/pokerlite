import { expect } from 'expect-webdriverio'
import GamePage from '../pageobjects/game.page.js'
import { ApiHelper } from '../helpers/api.helper.js'

describe('Simple Debug', () => {
    let tableId

    beforeEach(async () => {
        tableId = await ApiHelper.createTable({
            smallBlind: 5,
            bigBlind: 10,
            turnTimeout: 30,
        })
        console.log('Created table:', tableId)
    })

    afterEach(async () => {
        if (tableId) {
            await ApiHelper.deleteTable(tableId)
        }
    })

    it('should have 2 players after Alice and Bob join', async () => {
        // Alice joins in first window
        await GamePage.open(tableId)
        await GamePage.joinAsPlayer('Alice')
        await browser.pause(2000)

        console.log('=== After Alice joined ===')
        let state = await ApiHelper.getTableState(tableId)
        console.log('Players:', Object.keys(state.players || {}))
        console.log('Player details:', JSON.stringify(state.players, null, 2))

        // Get Alice's window state
        const aliceState = await browser.execute(() => {
            return {
                localStorage: {...localStorage},
                sessionStorage: {...sessionStorage},
            }
        })
        console.log('Alice storage:', aliceState)

        // Bob joins in second window
        await GamePage.openInNewWindow(tableId)
        await GamePage.joinAsPlayer('Bob')
        await browser.pause(2000)

        console.log('\n=== After Bob joined ===')
        state = await ApiHelper.getTableState(tableId)
        console.log('Players:', Object.keys(state.players || {}))
        console.log('Player details:', JSON.stringify(state.players, null, 2))

        // Get Bob's window state
        const bobState = await browser.execute(() => {
            return {
                localStorage: {...localStorage},
                sessionStorage: {...sessionStorage},
            }
        })
        console.log('Bob storage:', bobState)

        // Switch back to Alice
        const handles = await browser.getWindowHandles()
        await browser.switchToWindow(handles[0])
        await browser.pause(1000)

        // Check for Start Hand button
        const startBtn = await GamePage.startHandBtn
        const exists = await startBtn.isExisting()
        console.log('\nStart Hand Button exists:', exists)

        if (exists) {
            const displayed = await startBtn.isDisplayed()
            const clickable = await startBtn.isClickable()
            console.log('Start Hand Button displayed:', displayed)
            console.log('Start Hand Button clickable:', clickable)

            // Try clicking it
            console.log('Clicking Start Hand button...')

            // Capture browser console logs
            const logs = await browser.execute(() => {
                const logs = []
                const originalLog = console.log
                console.log = (...args) => {
                    logs.push(args.join(' '))
                    originalLog.apply(console, args)
                }
                return logs
            })

            await startBtn.click()

            // Wait a bit to see what happens
            await browser.pause(2000)

            // Check if pot appeared
            const potEl = await GamePage.pot
            const potExists = await potEl.isExisting()
            const potDisplayed = potExists ? await potEl.isDisplayed() : false
            console.log('Pot exists:', potExists, 'displayed:', potDisplayed)

            // Get game state after clicking
            const postClickState = await ApiHelper.getTableState(tableId)
            console.log('Hand in progress after click:', postClickState.hand_in_progress)
            console.log('Pot after click:', postClickState.pot)
        }

        // Verify we have 2 different players
        expect(Object.keys(state.players).length).toBe(2)

        // Close extra windows
        await GamePage.closeExtraWindows()
    })
})
