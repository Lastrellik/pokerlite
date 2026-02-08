# PokerLite E2E Tests

Comprehensive end-to-end testing suite for PokerLite using WebdriverIO (WDIO).

## Features

- **Deterministic Deck Shuffling**: Seed-based card dealing for reproducible test scenarios
- **Multi-Player Testing**: Simulate multiple players using separate browser windows
- **Page Object Model**: Maintainable test structure with reusable page objects
- **API Helpers**: Direct backend manipulation for faster test setup

## Quick Start

### Run All Tests

```bash
./run-e2e-tests.sh
```

This script will:
1. Check if services are running (start them if needed)
2. Wait for all services to be healthy
3. Run the e2e test suite
4. Stop services if it started them

### Run with Visible Browser

```bash
HEADLESS=false ./run-e2e-tests.sh
```

### Run Specific Test Suite

```bash
npm run test:e2e -- --spec ./e2e/specs/lobby.e2e.js
```

## Test Suites

### Lobby Tests (`lobby.e2e.js`)
- Display lobby page
- Create tables with custom settings
- Navigate to game from lobby
- Multiple tables management

### Basic Gameplay Tests (`basic-gameplay.e2e.js`)
- Two-player game flow
- Fold scenarios
- Check-check to showdown
- Pot calculations
- Raise mechanics

### Deterministic Hands Tests (`deterministic-hands.e2e.js`)
- Verify seed-based card dealing
- Test reproducibility across runs
- Different seeds produce different results
- Hand outcome verification

## Deterministic Testing

### How It Works

The game service supports deterministic deck shuffling for testing:

1. **Set a seed** via API before starting a hand
2. **Same seed = same cards** every time
3. **Different seeds = different deals**

### Example

```javascript
import { ApiHelper } from '../helpers/api.helper.js'

// Create a table
const tableId = await ApiHelper.createTable()

// Set deterministic seed
await ApiHelper.setDeckSeed(tableId, 12345)

// Now every hand will deal the same cards!
```

### Known Seeds

See `fixtures/hands.js` for predefined seeds with known outcomes:

- `SEED_12345`: Basic testing seed
- `SEED_42`: The answer to everything
- `SEED_777`: Lucky sevens
- `SEED_99999`: Alternative scenario

## Page Objects

### LobbyPage

```javascript
import LobbyPage from '../pageobjects/lobby.page.js'

await LobbyPage.open()
await LobbyPage.createTable({ smallBlind: 10, bigBlind: 20 })
await LobbyPage.joinFirstTable()
```

### GamePage

```javascript
import GamePage from '../pageobjects/game.page.js'

await GamePage.open(tableId)
await GamePage.joinAsPlayer('Alice')
await GamePage.startHand()
await GamePage.performAction('call')
await GamePage.waitForMyTurn()
const pot = await GamePage.getPotAmount()
const board = await GamePage.getBoardCards()
```

## API Helpers

### Create Tables

```javascript
const tableId = await ApiHelper.createTable({
    smallBlind: 5,
    bigBlind: 10,
    maxPlayers: 8,
    turnTimeout: 30
})
```

### Set Deck Seed

```javascript
await ApiHelper.setDeckSeed(tableId, 12345)
```

### Get Table State

```javascript
const state = await ApiHelper.getTableState(tableId)
console.log(state.board)      // Board cards
console.log(state.hole_cards)  // All players' hole cards
console.log(state.deck)        // Remaining deck
```

## Writing New Tests

### 1. Create Test File

```javascript
// e2e/specs/my-feature.e2e.js
import { expect } from 'expect-webdriverio'
import GamePage from '../pageobjects/game.page.js'
import { ApiHelper } from '../helpers/api.helper.js'

describe('My Feature', () => {
    let tableId

    beforeEach(async () => {
        tableId = await ApiHelper.createTable()
    })

    it('should do something cool', async () => {
        await GamePage.open(tableId)
        // ... your test
    })
})
```

### 2. Use Page Objects

- Import page objects for interactions
- Use API helpers for setup
- Avoid direct selectors in tests

### 3. Test Patterns

**Multi-player games:**
```javascript
// Player 1
await GamePage.open(tableId)
await GamePage.joinAsPlayer('Alice')

// Player 2 in new window
await browser.newWindow(`http://localhost:5173/table/${tableId}`)
await GamePage.joinAsPlayer('Bob')

// Switch between windows
const handles = await browser.getWindowHandles()
await browser.switchToWindow(handles[0])  // Alice
await browser.switchToWindow(handles[1])  // Bob
```

**Deterministic scenarios:**
```javascript
await ApiHelper.setDeckSeed(tableId, 42)
await GamePage.startHand()
// Cards will always be the same with seed 42
```

**Verify outcomes:**
```javascript
await GamePage.waitForLogMessage('Alice wins')
const pot = await GamePage.getPotAmount()
expect(pot).toBe(200)
```

## Debugging

### View Browser

Run with `HEADLESS=false` to see the browser:

```bash
HEADLESS=false ./run-e2e-tests.sh
```

### Add Debug Pauses

```javascript
await browser.debug()  // Pauses and opens REPL
await browser.pause(5000)  // Pause for 5 seconds
```

### Console Logs

```javascript
console.log('Current pot:', await GamePage.getPotAmount())
console.log('Board cards:', await GamePage.getBoardCards())
```

### Check Test State

```javascript
const state = await ApiHelper.getTableState(tableId)
console.log(JSON.stringify(state, null, 2))
```

## Test Data

### Fixtures

Predefined test scenarios in `fixtures/hands.js`:

- **KNOWN_HANDS**: Seeds with descriptions
- **TEST_SCENARIOS**: Game configurations (heads-up, short stack, etc.)
- **ACTION_SEQUENCES**: Common action patterns

### Example

```javascript
import { TEST_SCENARIOS } from '../fixtures/hands.js'

const tableId = await ApiHelper.createTable(TEST_SCENARIOS.SHORT_STACK)
// Creates table with short stacks for all-in testing
```

## Best Practices

1. **Use API for setup** - Faster than clicking through UI
2. **Clean up windows** - Close extra browser windows in `afterEach`
3. **Wait for actions** - Use `waitForMyTurn()`, `waitForLogMessage()`
4. **Deterministic when possible** - Use seeds for reproducible tests
5. **Test isolation** - Each test should be independent
6. **Meaningful assertions** - Check both UI and backend state

## Troubleshooting

### Tests Timeout

- Increase timeout in test: `mochaOpts.timeout` in `wdio.conf.js`
- Check services are running: `curl http://localhost:8000/api/health`
- Add pauses after actions: `await browser.pause(500)`

### Flaky Tests

- Add explicit waits: `waitForMyTurn()`, `waitForLogMessage()`
- Avoid fixed `pause()` - use `waitUntil()` instead
- Check for race conditions in multi-window tests

### Services Not Ready

- Increase retry count in `wdio.conf.js` before hook
- Check `dev-start.sh` output for errors
- Verify ports 8000, 8001, 5173 are available

### Element Not Found

- Update selectors in page objects
- Check if element is in shadow DOM
- Wait for element: `elem.waitForDisplayed()`

## CI/CD Integration

The test suite is designed to run in CI environments:

1. Services start via `dev-start.sh`
2. Tests run headlessly by default
3. Exit code reflects test status
4. Auto-cleanup on completion

Example GitHub Actions:

```yaml
- name: Run E2E Tests
  run: ./run-e2e-tests.sh
```

## Performance

- Tests run sequentially (`maxInstances: 1`) for state isolation
- API helpers minimize UI interactions
- Background table creation speeds up setup
- Typical suite runtime: 2-5 minutes

## Future Enhancements

- [ ] Screenshot capture on failure
- [ ] Video recording of test runs
- [ ] Visual regression testing
- [ ] Load/stress testing
- [ ] Mobile viewport testing
- [ ] Multi-browser support (Firefox, Safari)
