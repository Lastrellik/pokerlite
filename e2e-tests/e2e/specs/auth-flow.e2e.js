import { expect, browser } from '@wdio/globals'

describe('Authentication Flow', () => {
  // Generate random test user data
  const timestamp = Date.now()
  const randomId = Math.random().toString(36).substring(7)
  const testUsername = `test_user_${timestamp}_${randomId}`
  const testEmail = `test_${timestamp}_${randomId}@example.com`
  const testPassword = 'TestPassword123!'

  it('should complete full auth flow: register, logout, login', async () => {
    // Navigate to lobby
    await browser.url('http://localhost:5173/')
    await browser.pause(1000)

    console.log(`Creating test account: ${testUsername}`)

    // Look for Login/Sign Up button
    let loginBtn = await $('button=Login / Sign Up')
    if (!(await loginBtn.isExisting())) {
      // Might already be logged in - logout first
      const logoutBtn = await $('button=Logout')
      if (await logoutBtn.isExisting()) {
        await logoutBtn.click()
        await browser.pause(500)
      }
      // Try finding login button again
      loginBtn = await $('button=Login / Sign Up')
    }

    // Click login button to open modal
    await loginBtn.waitForExist({ timeout: 5000 })
    await loginBtn.click()
    await browser.pause(500)

    // ===== STEP 1: REGISTER NEW ACCOUNT =====
    const loginModal = await $('.login-modal')
    await expect(loginModal).toBeDisplayed()

    // Switch to register tab
    const registerTab = await $('button=Sign Up')
    await registerTab.click()
    await browser.pause(300)

    // Fill in registration form
    const usernameInput = await $('input[placeholder="Username"]')
    await usernameInput.setValue(testUsername)

    const emailInput = await $('input[type="email"]')
    await emailInput.setValue(testEmail)

    const passwordInputs = await $$('input[type="password"]')
    await passwordInputs[0].setValue(testPassword)
    await passwordInputs[1].setValue(testPassword)

    // Submit registration
    const registerButton = await $('button=Sign Up')
    await registerButton.click()

    // Wait for successful registration (modal should close)
    await browser.waitUntil(
      async () => !(await loginModal.isDisplayed()),
      {
        timeout: 5000,
        timeoutMsg: 'Registration did not complete - modal still visible'
      }
    )

    // Verify we're logged in
    await browser.pause(500)
    const authUsername = await $(`.auth-username*=${testUsername}`)
    await authUsername.waitForExist({ timeout: 3000 })
    await expect(authUsername).toBeDisplayed()
    console.log('✓ Registration successful')

    // Should see chip count
    const chipCount = await $('.chip-count')
    await expect(chipCount).toBeDisplayed()
    console.log('✓ Chip count displayed')

    // ===== STEP 2: LOGOUT =====
    console.log('Logging out...')
    const logoutBtn = await $('button=Logout')
    await logoutBtn.click()
    await browser.pause(500)

    // Verify we're logged out
    await browser.waitUntil(
      async () => !(await authUsername.isExisting()),
      {
        timeout: 3000,
        timeoutMsg: 'Logout did not work - username still visible'
      }
    )

    // Should see login button again
    const loginBtnAfterLogout = await $('button=Login / Sign Up')
    await expect(loginBtnAfterLogout).toBeDisplayed()
    console.log('✓ Logged out successfully')

    // ===== STEP 3: LOGIN AGAIN =====
    console.log('Logging back in...')
    await loginBtnAfterLogout.click()
    await browser.pause(300)

    // Should see login modal
    await expect(loginModal).toBeDisplayed()

    // Make sure we're on Login tab (not Sign Up)
    const loginTab = await $('button=Log In')
    if (await loginTab.isExisting()) {
      await loginTab.click()
      await browser.pause(200)
    }

    // Fill in login form
    const loginUsernameInput = await $('input[placeholder="Username"]')
    await loginUsernameInput.setValue(testUsername)

    const loginPasswordInput = await $('input[type="password"]')
    await loginPasswordInput.setValue(testPassword)

    // Submit login
    const loginSubmitBtn = await $('button=Log In')
    await loginSubmitBtn.click()

    // Wait for successful login
    await browser.waitUntil(
      async () => !(await loginModal.isDisplayed()),
      {
        timeout: 5000,
        timeoutMsg: 'Login did not complete - modal still visible'
      }
    )

    // Verify we're logged in again
    await browser.pause(500)
    const authUsernameAfterLogin = await $(`.auth-username*=${testUsername}`)
    await authUsernameAfterLogin.waitForExist({ timeout: 3000 })
    await expect(authUsernameAfterLogin).toBeDisplayed()
    console.log('✓ Logged in successfully')

    // Verify chip count is still visible
    await expect(chipCount).toBeDisplayed()
    console.log('✓ Chip count restored')

    console.log(`\n✅ Full auth flow completed successfully for ${testUsername}`)
  })

  it('should handle login with wrong password', async () => {
    await browser.url('http://localhost:5173/')
    await browser.pause(1000)

    // Click login button
    const loginBtn = await $('button=Login / Sign Up')
    if (await loginBtn.isExisting()) {
      await loginBtn.click()
      await browser.pause(300)

      const loginModal = await $('.login-modal')
      await expect(loginModal).toBeDisplayed()

      // Make sure we're on Login tab
      const loginTab = await $('button=Log In')
      if (await loginTab.isExisting()) {
        await loginTab.click()
        await browser.pause(200)
      }

      // Try to login with wrong password
      const usernameInput = await $('input[placeholder="Username"]')
      await usernameInput.setValue(testUsername)

      const passwordInput = await $('input[type="password"]')
      await passwordInput.setValue('WrongPassword123!')

      const loginSubmitBtn = await $('button=Log In')
      await loginSubmitBtn.click()

      // Should show error (modal stays open or shows error message)
      await browser.pause(1000)

      // Modal should still be visible (login failed)
      await expect(loginModal).toBeDisplayed()
      console.log('✓ Login correctly rejected with wrong password')
    }
  })

  it('should handle registration with duplicate username', async () => {
    await browser.url('http://localhost:5173/')
    await browser.pause(1000)

    // Open login modal
    const loginBtn = await $('button=Login / Sign Up')
    await loginBtn.click()
    await browser.pause(300)

    const loginModal = await $('.login-modal')

    // Switch to register tab
    const registerTab = await $('button=Sign Up')
    if (await registerTab.isExisting()) {
      await registerTab.click()
      await browser.pause(200)

      // Try to register with existing username
      const usernameInput = await $('input[placeholder="Username"]')
      await usernameInput.setValue(testUsername) // Same as first test

      const emailInput = await $('input[type="email"]')
      await emailInput.setValue(`different_${testEmail}`)

      const passwordInputs = await $$('input[type="password"]')
      await passwordInputs[0].setValue(testPassword)
      await passwordInputs[1].setValue(testPassword)

      const registerButton = await $('button=Sign Up')
      await registerButton.click()

      // Should show error (modal stays open)
      await browser.pause(1000)
      await expect(loginModal).toBeDisplayed()
      console.log('✓ Registration correctly rejected duplicate username')
    }
  })
})
