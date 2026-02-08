import axios from 'axios'

import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

export const config = {
    runner: 'local',
    specs: [join(__dirname, 'specs', '**', '*.e2e.js')],
    exclude: [],
    maxInstances: 1,  // Run one test at a time for poker game state management
    capabilities: [{
        browserName: 'firefox',
        'moz:firefoxOptions': {
            args: [
                '-private',  // Use private browsing to isolate storage between windows
                ...(process.env.HEADLESS === 'true' ? ['-headless'] : [])
            ]
        }
    }],
    logLevel: 'info',
    bail: 0,
    baseUrl: 'http://localhost:5173',
    waitforTimeout: 10000,
    connectionRetryTimeout: 120000,
    connectionRetryCount: 3,
    services: ['geckodriver'],
    framework: 'mocha',
    reporters: ['spec'],
    mochaOpts: {
        ui: 'bdd',
        timeout: 60000
    },

    /**
     * Gets executed before test execution begins.
     * Wait for all services to be healthy before running tests.
     */
    before: async function () {
        const maxRetries = 30
        const retryDelay = 1000

        console.log('Waiting for services to be ready...')

        // Check lobby service
        for (let i = 0; i < maxRetries; i++) {
            try {
                await axios.get('http://localhost:8000/api/health', { timeout: 2000 })
                console.log('✓ Lobby service ready')
                break
            } catch (e) {
                if (i === maxRetries - 1) {
                    throw new Error('Lobby service not ready after 30 seconds')
                }
                await new Promise(r => setTimeout(r, retryDelay))
            }
        }

        // Check game service
        for (let i = 0; i < maxRetries; i++) {
            try {
                await axios.get('http://localhost:8001/api/health', { timeout: 2000 })
                console.log('✓ Game service ready')
                break
            } catch (e) {
                if (i === maxRetries - 1) {
                    throw new Error('Game service not ready after 30 seconds')
                }
                await new Promise(r => setTimeout(r, retryDelay))
            }
        }

        // Check frontend
        for (let i = 0; i < maxRetries; i++) {
            try {
                await axios.get('http://localhost:5173', { timeout: 2000 })
                console.log('✓ Frontend ready')
                break
            } catch (e) {
                if (i === maxRetries - 1) {
                    throw new Error('Frontend not ready after 30 seconds')
                }
                await new Promise(r => setTimeout(r, retryDelay))
            }
        }

        console.log('All services ready! Starting tests...\n')
    },

    /**
     * Gets executed after all tests are done.
     */
    after: function () {
        console.log('\nTests complete!')
    }
}
