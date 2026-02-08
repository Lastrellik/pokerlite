import axios from 'axios'

const LOBBY_URL = 'http://localhost:8000'
const GAME_URL = 'http://localhost:8001'

/**
 * API Helper for backend interactions during tests
 */
export class ApiHelper {
    /**
     * Create a new table via API
     */
    static async createTable(config = {}) {
        try {
            const response = await axios.post(`${LOBBY_URL}/api/tables`, {
                name: config.name || 'Test Table',
                small_blind: config.smallBlind || 5,
                big_blind: config.bigBlind || 10,
                max_players: config.maxPlayers || 8,
                turn_timeout_seconds: config.turnTimeout || 30,
            })
            return response.data.table_id
        } catch (error) {
            console.error('Failed to create table:', error.message)
            throw error
        }
    }

    /**
     * Set deterministic deck seed for a table
     */
    static async setDeckSeed(tableId, seed) {
        try {
            const response = await axios.post(
                `${GAME_URL}/api/test/tables/${tableId}/config`,
                {
                    deck_seed: seed,
                    use_deterministic_deck: true,
                }
            )
            return response.data
        } catch (error) {
            console.error('Failed to set deck seed:', error.message)
            throw error
        }
    }

    /**
     * Get internal table state for verification
     */
    static async getTableState(tableId) {
        try {
            const response = await axios.get(
                `${GAME_URL}/api/test/tables/${tableId}/state`
            )
            return response.data
        } catch (error) {
            console.error('Failed to get table state:', error.message)
            throw error
        }
    }

    /**
     * Wait for service to be healthy
     */
    static async waitForServiceHealth(maxRetries = 30, retryDelay = 1000) {
        for (let i = 0; i < maxRetries; i++) {
            try {
                await axios.get(`${LOBBY_URL}/api/health`, { timeout: 2000 })
                await axios.get(`${GAME_URL}/api/health`, { timeout: 2000 })
                return true
            } catch (e) {
                if (i === maxRetries - 1) {
                    throw new Error('Services not healthy after max retries')
                }
                await new Promise(r => setTimeout(r, retryDelay))
            }
        }
    }

    /**
     * Get all tables from lobby
     */
    static async getAllTables() {
        try {
            const response = await axios.get(`${LOBBY_URL}/api/tables`)
            return response.data
        } catch (error) {
            console.error('Failed to get tables:', error.message)
            throw error
        }
    }

    /**
     * Delete a table
     */
    static async deleteTable(tableId) {
        try {
            await axios.delete(`${LOBBY_URL}/api/tables/${tableId}`)
            return true
        } catch (error) {
            console.error('Failed to delete table:', error.message)
            return false
        }
    }

    /**
     * Clean up all test tables (useful for test cleanup)
     */
    static async cleanupAllTables() {
        try {
            const tables = await this.getAllTables()
            await Promise.all(tables.map(t => this.deleteTable(t.table_id)))
            console.log(`Cleaned up ${tables.length} tables`)
        } catch (error) {
            console.error('Failed to cleanup tables:', error.message)
        }
    }
}

export default ApiHelper
