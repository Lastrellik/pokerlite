/**
 * Base Page Object with common utilities
 */
export default class BasePage {
    /**
     * Open a path and wait for page load
     */
    async open(path) {
        await browser.url(path)
        await browser.waitUntil(
            async () => (await browser.execute(() => document.readyState)) === 'complete',
            {
                timeout: 5000,
                timeoutMsg: 'Page did not finish loading'
            }
        )
    }

    /**
     * Wait for an element to contain specific text
     */
    async waitForText(selector, text, timeout = 5000) {
        await browser.waitUntil(
            async () => {
                try {
                    const elem = await $(selector)
                    const elemText = await elem.getText()
                    return elemText.includes(text)
                } catch (e) {
                    return false
                }
            },
            {
                timeout,
                timeoutMsg: `Text "${text}" not found in ${selector} within ${timeout}ms`
            }
        )
    }

    /**
     * Wait for an element to be clickable
     */
    async waitAndClick(selector, timeout = 5000) {
        const elem = await $(selector)
        await elem.waitForClickable({ timeout })
        await elem.click()
    }

    /**
     * Type text into an input
     */
    async typeText(selector, text) {
        const elem = await $(selector)
        await elem.waitForDisplayed()
        await elem.setValue(text)
    }

    /**
     * Get text content from element
     */
    async getText(selector) {
        const elem = await $(selector)
        await elem.waitForDisplayed()
        return await elem.getText()
    }

    /**
     * Check if element is displayed
     */
    async isDisplayed(selector) {
        try {
            const elem = await $(selector)
            return await elem.isDisplayed()
        } catch (e) {
            return false
        }
    }

    /**
     * Pause execution
     */
    async pause(ms) {
        await browser.pause(ms)
    }
}
