/**
 * Known poker hands with deterministic seeds
 * These seeds produce specific, reproducible card deals
 */

export const KNOWN_HANDS = {
    // Seed 12345 - Simple high card showdown
    SEED_12345: {
        seed: 12345,
        description: 'Basic hand for testing showdown logic',
        // Note: Exact cards determined by shuffle algorithm
        // Run test with this seed to discover actual dealt cards
    },

    // Seed 99999 - For testing different scenarios
    SEED_99999: {
        seed: 99999,
        description: 'Alternative seed for variety in testing',
    },

    // Seed 42 - Classic test seed
    SEED_42: {
        seed: 42,
        description: 'The answer to life, universe, and poker',
    },

    // Seed 777 - Lucky sevens
    SEED_777: {
        seed: 777,
        description: 'Lucky seed for positive test cases',
    },

    // Seed 13 - Unlucky thirteen
    SEED_13: {
        seed: 13,
        description: 'For testing edge cases',
    },
}

/**
 * Test scenarios for common poker situations
 */
export const TEST_SCENARIOS = {
    /**
     * Two player heads-up game
     */
    HEADS_UP: {
        players: 2,
        smallBlind: 5,
        bigBlind: 10,
        startingStack: 1000,
    },

    /**
     * Four player game
     */
    FOUR_HANDED: {
        players: 4,
        smallBlind: 5,
        bigBlind: 10,
        startingStack: 1000,
    },

    /**
     * Short stack scenario for all-in testing
     */
    SHORT_STACK: {
        players: 2,
        smallBlind: 50,
        bigBlind: 100,
        startingStack: 200,
    },

    /**
     * Deep stack scenario
     */
    DEEP_STACK: {
        players: 2,
        smallBlind: 1,
        bigBlind: 2,
        startingStack: 10000,
    },

    /**
     * Fast game with short timeouts
     */
    SPEED_POKER: {
        players: 2,
        smallBlind: 5,
        bigBlind: 10,
        startingStack: 1000,
        turnTimeout: 5,
    },
}

/**
 * Expected action sequences for testing game flow
 */
export const ACTION_SEQUENCES = {
    /**
     * Both players check through all streets
     */
    CHECK_TO_SHOWDOWN: [
        { player: 'p1', action: 'call' },   // Call BB preflop
        { player: 'p2', action: 'check' },  // BB checks
        { player: 'p1', action: 'check' },  // Flop
        { player: 'p2', action: 'check' },
        { player: 'p1', action: 'check' },  // Turn
        { player: 'p2', action: 'check' },
        { player: 'p1', action: 'check' },  // River
        { player: 'p2', action: 'check' },
    ],

    /**
     * Player 1 folds preflop
     */
    FOLD_PREFLOP: [
        { player: 'p1', action: 'fold' },
    ],

    /**
     * Player 2 folds to bet on flop
     */
    FOLD_ON_FLOP: [
        { player: 'p1', action: 'call' },
        { player: 'p2', action: 'check' },
        { player: 'p1', action: 'raise', amount: 20 },
        { player: 'p2', action: 'fold' },
    ],

    /**
     * Both players go all-in
     */
    DOUBLE_ALL_IN: [
        { player: 'p1', action: 'allin' },
        { player: 'p2', action: 'call' },
    ],
}

export default {
    KNOWN_HANDS,
    TEST_SCENARIOS,
    ACTION_SEQUENCES,
}
