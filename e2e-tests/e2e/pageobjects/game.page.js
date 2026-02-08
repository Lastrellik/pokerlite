import BasePage from './base.page.js'

/**
 * Game Page Object
 */
class GamePage extends BasePage {
    // Connection selectors
    get playerNameInput() { return $('input[placeholder*="name"]') }
    get joinBtn() { return $('button.btn-connect') }
    get leaveBtn() { return $('button.btn-disconnect') }

    // Game action selectors
    get startHandBtn() { return $('button.btn-start') }
    get foldBtn() { return $('button.btn-fold') }
    get checkBtn() { return $('button*=Check') }
    get callBtn() { return $('button*=Call') }
    get raiseBtn() { return $('button*=Raise') }
    get allInBtn() { return $('button*=All') }

    // Game info selectors
    get pot() { return $('.pot-amount') }
    get board() { return $('.board') }
    get gameLog() { return $('.game-log') }

    /**
     * Open a specific table
     */
    async open(tableId) {
        await super.open(`/table/${tableId}`)
    }

    /**
     * Open table in new window as a new player (with cleared storage)
     * This ensures each window gets a separate player ID instead of reusing
     * the PID from localStorage.
     */
    async openInNewWindow(tableId) {
        await browser.newWindow(`http://localhost:5173/table/${tableId}`)
        // Clear storage so this window gets a fresh player ID
        await browser.execute(() => {
            localStorage.clear()
            sessionStorage.clear()
        })
    }

    /**
     * Close all extra windows and switch back to the first window
     * Handles window cleanup safely to avoid "no such window" errors
     */
    async closeExtraWindows() {
        const handles = await browser.getWindowHandles()
        // Close all windows except the first one
        for (let i = handles.length - 1; i > 0; i--) {
            await browser.switchToWindow(handles[i])
            await browser.closeWindow()
        }
        // Switch back to the first window if it exists
        if (handles.length > 0) {
            await browser.switchToWindow(handles[0])
        }
    }

    /**
     * Join the game as a player
     */
    async joinAsPlayer(playerName) {
        await this.playerNameInput.waitForDisplayed({ timeout: 5000 })
        await this.playerNameInput.setValue(playerName)
        await this.joinBtn.click()

        // Wait for connection by waiting for Leave button to appear
        await this.leaveBtn.waitForDisplayed({ timeout: 5000 })
    }

    /**
     * Start a new hand
     */
    async startHand() {
        await this.startHandBtn.waitForClickable({ timeout: 10000 })
        await this.startHandBtn.click()

        // Wait for hand to actually start by waiting for pot to appear
        await this.pot.waitForDisplayed({ timeout: 5000 })
    }

    /**
     * Wait for Start Hand button to be available
     * This means enough players have joined
     */
    async waitForStartHandButton() {
        await this.startHandBtn.waitForClickable({ timeout: 10000 })
    }

    /**
     * Perform a game action
     */
    async performAction(action) {
        let button
        switch (action.toLowerCase()) {
            case 'fold':
                button = this.foldBtn
                break
            case 'check':
                button = this.checkBtn
                break
            case 'call':
                button = this.callBtn
                break
            case 'raise':
                button = this.raiseBtn
                break
            case 'allin':
            case 'all-in':
                button = this.allInBtn
                break
            default:
                throw new Error(`Unknown action: ${action}`)
        }

        await button.waitForClickable({ timeout: 5000 })
        await button.click()
        await browser.pause(300)
    }

    /**
     * Get the pot amount
     */
    async getPotAmount() {
        const potElement = await this.pot
        const text = await potElement.getText()
        const match = text.match(/\$?(\d+)/)
        return match ? parseInt(match[1]) : 0
    }

    /**
     * Get board cards as array
     */
    async getBoardCards() {
        try {
            const boardElement = await this.board
            const cards = await boardElement.$$('.card')
            return await Promise.all(cards.map(card => card.getText()))
        } catch (e) {
            return []
        }
    }

    /**
     * Get recent log messages
     */
    async getLogMessages(count = 10) {
        const logItems = await this.gameLog.$$('.log-item')
        const messages = []

        const itemsToRead = Math.min(count, logItems.length)
        for (let i = 0; i < itemsToRead; i++) {
            const msg = await logItems[i].$('.message')
            const text = await msg.getText()
            messages.push(text)
        }

        return messages
    }

    /**
     * Wait for specific log message
     */
    async waitForLogMessage(textToFind, timeout = 5000) {
        await browser.waitUntil(
            async () => {
                const messages = await this.getLogMessages(20)
                return messages.some(msg => msg.includes(textToFind))
            },
            {
                timeout,
                timeoutMsg: `Log message containing "${textToFind}" not found`
            }
        )
    }

    /**
     * Check if it's my turn (action buttons enabled)
     */
    async isMyTurn() {
        try {
            await this.foldBtn.waitForClickable({ timeout: 1000 })
            return true
        } catch (e) {
            return false
        }
    }

    /**
     * Wait for my turn
     */
    async waitForMyTurn(timeout = 10000) {
        await browser.waitUntil(
            async () => await this.isMyTurn(),
            {
                timeout,
                timeoutMsg: 'Turn did not arrive within timeout'
            }
        )
    }

    /**
     * Get player seat information
     */
    async getPlayerAtSeat(seatNumber) {
        const playerElem = await $(`.player-seat-${seatNumber}`)
        if (!(await playerElem.isDisplayed())) {
            return null
        }

        const nameElem = await playerElem.$('.player-name')
        const stackElem = await playerElem.$('.player-stack')

        return {
            name: await nameElem.getText(),
            stack: await stackElem.getText()
        }
    }

    /**
     * Check if player has folded
     */
    async hasPlayerFolded(playerName) {
        const messages = await this.getLogMessages(20)
        return messages.some(msg => msg.includes(`${playerName} folds`))
    }

    /**
     * Get hole cards (if visible)
     */
    async getMyHoleCards() {
        try {
            const holeCards = await $$('.my-cards .card')
            return await Promise.all(holeCards.map(card => card.getText()))
        } catch (e) {
            return []
        }
    }
}

export default new GamePage()
