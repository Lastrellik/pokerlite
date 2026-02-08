import { expect } from 'expect-webdriverio'
import LobbyPage from '../pageobjects/lobby.page.js'
import { ApiHelper } from '../helpers/api.helper.js'

describe('Lobby', () => {
    beforeEach(async () => {
        // Clean up all existing tables before each test for a clean slate
        await ApiHelper.cleanupAllTables()
        await LobbyPage.open()
    })

    it('should display the lobby page', async () => {
        await expect(browser).toHaveTitle('poker-client')
        await expect(LobbyPage.createTableBtn).toBeDisplayed()
    })

    it('should create a new table with default settings', async () => {
        const initialCount = await LobbyPage.getTableCount()

        // Create table via API so we don't navigate away
        await ApiHelper.createTable()

        // Wait for table to appear in lobby
        await browser.waitUntil(async () => {
            const newCount = await LobbyPage.getTableCount()
            return newCount > initialCount
        }, { timeout: 10000, timeoutMsg: 'New table should appear in lobby' })

        const newCount = await LobbyPage.getTableCount()
        expect(newCount).toBeGreaterThan(initialCount)
    })

    it('should create a table with custom settings', async () => {
        const initialCount = await LobbyPage.getTableCount()

        // Create table via API with custom settings
        await ApiHelper.createTable({
            smallBlind: 10,
            bigBlind: 20,
            maxPlayers: 6,
            turnTimeout: 15,
        })

        // Wait for table to appear
        await browser.waitUntil(async () => {
            const newCount = await LobbyPage.getTableCount()
            return newCount > initialCount
        }, { timeout: 10000, timeoutMsg: 'Table should be created' })

        // Verify table was created with correct settings
        const info = await LobbyPage.getTableInfo(0)
        expect(info).toContain('$10/$20')  // Should show blinds
    })

    it('should navigate to game page when joining a table', async () => {
        // Create a table via API
        await ApiHelper.createTable()

        // Wait for it to appear
        await browser.waitUntil(async () => {
            return (await LobbyPage.getTableCount()) > 0
        }, { timeout: 10000 })

        // Join it - this will trigger navigation
        await LobbyPage.joinFirstTable()

        // Verify navigation
        const url = await browser.getUrl()
        expect(url).toContain('/table/')
    })

    it('should show multiple tables in the lobby', async () => {
        const initialCount = await LobbyPage.getTableCount()

        // Create first table via API
        await ApiHelper.createTable({ smallBlind: 5, bigBlind: 10 })
        await browser.waitUntil(async () => {
            return (await LobbyPage.getTableCount()) === initialCount + 1
        }, { timeout: 10000 })

        // Create second table via API
        await ApiHelper.createTable({ smallBlind: 25, bigBlind: 50 })
        await browser.waitUntil(async () => {
            return (await LobbyPage.getTableCount()) === initialCount + 2
        }, { timeout: 10000 })

        const count = await LobbyPage.getTableCount()
        expect(count).toBeGreaterThanOrEqual(initialCount + 2)
    })
})
