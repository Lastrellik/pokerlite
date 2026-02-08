import { expect } from 'expect-webdriverio'
import LobbyPage from '../pageobjects/lobby.page.js'

describe('Lobby', () => {
    beforeEach(async () => {
        await LobbyPage.open()
    })

    it('should display the lobby page', async () => {
        await expect(browser).toHaveTitle('PokerLite')
        await expect(LobbyPage.createTableBtn).toBeDisplayed()
    })

    it('should create a new table with default settings', async () => {
        const initialCount = await LobbyPage.getTableCount()

        await LobbyPage.createTable()

        // Wait a moment for table to appear
        await browser.pause(1000)

        const newCount = await LobbyPage.getTableCount()
        expect(newCount).toBeGreaterThan(initialCount)
    })

    it('should create a table with custom settings', async () => {
        await LobbyPage.createTable({
            smallBlind: 10,
            bigBlind: 20,
            maxPlayers: 6,
            turnTimeout: 15,
        })

        // Verify table was created
        await browser.pause(1000)
        const info = await LobbyPage.getTableInfo(0)
        expect(info).toContain('10/20')  // Should show blinds
    })

    it('should navigate to game page when joining a table', async () => {
        // Create a table first
        await LobbyPage.createTable()
        await browser.pause(500)

        // Join it
        await LobbyPage.joinFirstTable()

        // Verify navigation
        const url = await browser.getUrl()
        expect(url).toContain('/table/')
    })

    it('should show multiple tables in the lobby', async () => {
        // Create multiple tables
        await LobbyPage.createTable({ smallBlind: 5, bigBlind: 10 })
        await browser.pause(500)

        await LobbyPage.createTable({ smallBlind: 25, bigBlind: 50 })
        await browser.pause(500)

        const count = await LobbyPage.getTableCount()
        expect(count).toBeGreaterThanOrEqual(2)
    })
})
