import { expect } from 'expect-webdriverio'
import GamePage from '../pageobjects/game.page.js'
import { ApiHelper } from '../helpers/api.helper.js'

describe('Debug State', () => {
    let tableId

    beforeEach(async () => {
        tableId = await ApiHelper.createTable({
            smallBlind: 5,
            bigBlind: 10,
            turnTimeout: 30,
        })
    })

    afterEach(async () => {
        if (tableId) {
            await ApiHelper.deleteTable(tableId)
        }
    })

    it('should show what state looks like with 2 players', async () => {
        // Player 1 joins
        await GamePage.open(tableId)
        await GamePage.joinAsPlayer('Alice')
        await browser.pause(1000)

        console.log('=== After Alice joined ===')
        let state = await ApiHelper.getTableState(tableId)
        console.log('Players in table:', Object.keys(state.players || {}))
        console.log('Player details:', JSON.stringify(state.players, null, 2))
        console.log('Hand in progress:', state.hand_in_progress)

        // Check what the frontend sees
        const pageSource = await browser.execute(() => {
            // Get the game state from window if exposed, or from DOM
            const buttons = Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.textContent,
                classes: b.className,
                disabled: b.disabled
            }))
            return { buttons }
        })
        console.log('Buttons on page:', JSON.stringify(pageSource.buttons, null, 2))

        // Player 2 joins in new window
        await GamePage.openInNewWindow(tableId)
        await GamePage.joinAsPlayer('Bob')
        await browser.pause(1000)

        console.log('\n=== After Bob joined ===')
        state = await ApiHelper.getTableState(tableId)
        console.log('Players in table:', Object.keys(state.players || {}))
        console.log('Player details:', JSON.stringify(state.players, null, 2))
        console.log('Hand in progress:', state.hand_in_progress)

        // Switch back to Alice
        const handles = await browser.getWindowHandles()
        await browser.switchToWindow(handles[0])
        await browser.pause(1000)

        // Check buttons again
        const pageSource2 = await browser.execute(() => {
            const buttons = Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.textContent.trim(),
                classes: b.className,
                disabled: b.disabled,
                visible: b.offsetParent !== null
            }))

            // Try to get game state from React
            const actionButtons = document.querySelector('.action-buttons')
            const turnIndicator = document.querySelector('.turn-indicator')

            return {
                buttons,
                actionButtonsHTML: actionButtons ? actionButtons.innerHTML : null,
                turnIndicatorText: turnIndicator ? turnIndicator.textContent : null
            }
        })
        console.log('\nButtons after Bob joined:', JSON.stringify(pageSource2.buttons, null, 2))
        console.log('Action buttons HTML:', pageSource2.actionButtonsHTML)
        console.log('Turn indicator:', pageSource2.turnIndicatorText)

        // Try to find the start hand button
        const startBtn = await GamePage.startHandBtn
        const exists = await startBtn.isExisting()
        const displayed = exists ? await startBtn.isDisplayed() : false
        const clickable = displayed ? await startBtn.isClickable() : false

        console.log('\nStart Hand Button:')
        console.log('  Exists:', exists)
        console.log('  Displayed:', displayed)
        console.log('  Clickable:', clickable)

        if (exists) {
            const btnInfo = await browser.execute((selector) => {
                const btn = document.querySelector(selector)
                if (!btn) return null
                return {
                    text: btn.textContent,
                    disabled: btn.disabled,
                    offsetParent: btn.offsetParent !== null,
                    computedDisplay: window.getComputedStyle(btn).display
                }
            }, 'button.btn-start')
            console.log('  Button details:', JSON.stringify(btnInfo, null, 2))
        }

        // Close extra window
        await browser.closeWindow()
        await browser.switchToWindow(handles[0])
    })
})
