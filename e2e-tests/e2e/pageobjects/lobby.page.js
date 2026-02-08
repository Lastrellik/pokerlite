import BasePage from './base.page.js'

/**
 * Lobby Page Object
 */
class LobbyPage extends BasePage {
    // Selectors
    get createTableBtn() { return $('.btn-create') }
    get tablesGrid() { return $('.tables-grid') }

    // Modal selectors
    get modalName() { return $('input[id="name"]') }
    get modalSmallBlind() { return $('input[id="small_blind"]') }
    get modalBigBlind() { return $('input[id="big_blind"]') }
    get modalMaxPlayers() { return $('select[id="max_players"]') }
    get modalTurnTimeout() { return $('input[id="timeout"]') }
    get modalSubmit() { return $('.modal-content button[type="submit"]') }
    get modalCancel() { return $('.modal-content button[type="button"]') }

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
        await this.modalName.waitForDisplayed()

        // Always set the name (required field)
        const name = config.name || 'Test Table'
        await this.modalName.setValue(name)

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
        await browser.waitUntil(async () => {
            return !(await this.modalSubmit.isDisplayed().catch(() => false))
        }, { timeout: 5000, timeoutMsg: 'Modal should close after creating table' })
    }

    /**
     * Join the first available table
     */
    async joinFirstTable() {
        const joinBtn = await $('.table-card .btn-join')
        await joinBtn.waitForClickable()
        await joinBtn.click()

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
        const tables = await $$('.table-card')
        return tables.length
    }

    /**
     * Get table information
     */
    async getTableInfo(index = 0) {
        const tables = await $$('.table-card')
        if (tables.length === 0) return null

        const table = tables[index]
        const text = await table.getText()
        return text
    }
}

export default new LobbyPage()
