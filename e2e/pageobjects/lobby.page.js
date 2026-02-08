import BasePage from './base.page.js'

/**
 * Lobby Page Object
 */
class LobbyPage extends BasePage {
    // Selectors
    get createTableBtn() { return $('button*=Create Table') }
    get tablesList() { return $('.tables-list') }

    // Modal selectors
    get modalSmallBlind() { return $('input[id="smallBlind"]') }
    get modalBigBlind() { return $('input[id="bigBlind"]') }
    get modalMaxPlayers() { return $('select[id="maxPlayers"]') }
    get modalTurnTimeout() { return $('input[id="turnTimeoutSeconds"]') }
    get modalSubmit() { return $('.modal button[type="submit"]') }
    get modalCancel() { return $('.modal button*=Cancel') }

    /**
     * Open lobby page
     */
    async open() {
        await super.open('/')
        await this.createTableBtn.waitForDisplayed({ timeout: 5000 })
    }

    /**
     * Create a new table with optional configuration
     */
    async createTable(config = {}) {
        await this.createTableBtn.click()
        await this.modalSmallBlind.waitForDisplayed()

        if (config.smallBlind !== undefined) {
            await this.modalSmallBlind.clearValue()
            await this.modalSmallBlind.setValue(config.smallBlind)
        }

        if (config.bigBlind !== undefined) {
            await this.modalBigBlind.clearValue()
            await this.modalBigBlind.setValue(config.bigBlind)
        }

        if (config.maxPlayers !== undefined) {
            await this.modalMaxPlayers.selectByAttribute('value', config.maxPlayers.toString())
        }

        if (config.turnTimeout !== undefined) {
            await this.modalTurnTimeout.clearValue()
            await this.modalTurnTimeout.setValue(config.turnTimeout)
        }

        await this.modalSubmit.click()

        // Wait for modal to close
        await browser.pause(500)
    }

    /**
     * Join the first available table
     */
    async joinFirstTable() {
        const tableLink = await $('.table-item a')
        await tableLink.waitForClickable()
        await tableLink.click()

        // Wait for navigation
        await browser.waitUntil(
            async () => (await browser.getUrl()).includes('/table/'),
            { timeout: 5000, timeoutMsg: 'Did not navigate to table page' }
        )
    }

    /**
     * Get the number of tables in the lobby
     */
    async getTableCount() {
        const tables = await $$('.table-item')
        return tables.length
    }

    /**
     * Get table information
     */
    async getTableInfo(index = 0) {
        const tables = await $$('.table-item')
        if (tables.length === 0) return null

        const table = tables[index]
        const text = await table.getText()
        return text
    }
}

export default new LobbyPage()
