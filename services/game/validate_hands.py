#!/usr/bin/env python3
"""
Validate poker hand evaluation with detailed test cases.
"""
from app.core.game import _evaluate_hand, _compare_hands, HAND_RANKS


def test_hand_scenarios():
    """Test complete hand scenarios with 7 cards."""

    print("="*60)
    print("TESTING 7-CARD HAND EVALUATION")
    print("="*60)

    test_cases = [
        {
            "name": "Royal Flush vs Straight Flush",
            "hand1": ["As", "Ks", "Qs", "Js", "Ts", "2h", "3d"],
            "hand2": ["9h", "Th", "Jh", "Qh", "Kh", "2c", "3c"],
            "winner": 1,
            "description": "Royal flush beats straight flush"
        },
        {
            "name": "Four of a Kind vs Full House",
            "hand1": ["Ah", "Ac", "Ad", "As", "Kh", "Kc", "2d"],
            "hand2": ["Qh", "Qc", "Qd", "Jh", "Jc", "9s", "8s"],
            "winner": 1,
            "description": "Quad aces beats queens full"
        },
        {
            "name": "Full House vs Flush",
            "hand1": ["Kh", "Kc", "Kd", "9h", "9c", "2s", "3s"],
            "hand2": ["Ah", "Kh", "Qh", "Jh", "9h", "2c", "3d"],
            "winner": 1,
            "description": "Full house beats flush"
        },
        {
            "name": "Flush vs Straight",
            "hand1": ["2s", "4s", "6s", "8s", "Ts", "Ah", "Kd"],
            "hand2": ["5h", "6d", "7c", "8h", "9s", "Ac", "Kc"],
            "winner": 1,
            "description": "Flush beats straight"
        },
        {
            "name": "Straight vs Three of a Kind",
            "hand1": ["5h", "6d", "7c", "8s", "9h", "Ac", "Kd"],
            "hand2": ["Qh", "Qc", "Qd", "Jh", "Ts", "2c", "3d"],
            "winner": 1,
            "description": "Straight beats trips"
        },
        {
            "name": "Two Pair vs Pair (Kickers)",
            "hand1": ["Ah", "Ac", "Kd", "Kh", "Qc", "2s", "3s"],
            "hand2": ["Ah", "Ac", "Qd", "Jh", "9c", "7s", "5s"],
            "winner": 1,
            "description": "Two pair beats one pair"
        },
        {
            "name": "Pair vs Pair (Higher Pair)",
            "hand1": ["Ah", "Ac", "Kd", "Qh", "Jc", "9s", "7s"],
            "hand2": ["Kh", "Kc", "Qd", "Jh", "9c", "7c", "5c"],
            "winner": 1,
            "description": "Pair of aces beats pair of kings"
        },
        {
            "name": "Pair vs Pair (Same Pair, Kicker)",
            "hand1": ["Ah", "Ac", "Kd", "Qh", "Jc", "9s", "7s"],
            "hand2": ["Ah", "Ac", "Td", "Qh", "Jc", "9s", "7s"],
            "winner": 1,
            "description": "King kicker beats ten kicker"
        },
        {
            "name": "High Card vs High Card",
            "hand1": ["Ah", "Kc", "Qd", "Jh", "9c", "7s", "5s"],
            "hand2": ["Ah", "Kc", "Qd", "Jh", "8c", "7s", "6s"],
            "winner": 1,
            "description": "9 high beats 8 high"
        },
        {
            "name": "Wheel Straight vs Two Pair",
            "hand1": ["Ah", "2c", "3d", "4h", "5c", "Ks", "Qs"],
            "hand2": ["9h", "9c", "8d", "8h", "Kc", "Qs", "Js"],
            "winner": 1,
            "description": "A-2-3-4-5 straight (wheel) beats two pair"
        },
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        eval1 = _evaluate_hand(test["hand1"])
        eval2 = _evaluate_hand(test["hand2"])

        result = _compare_hands(eval1, eval2)

        # Get hand names
        rank_names = {v: k for k, v in HAND_RANKS.items()}
        name1 = rank_names.get(eval1[0], "unknown").replace("_", " ").title()
        name2 = rank_names.get(eval2[0], "unknown").replace("_", " ").title()

        expected_winner = test["winner"]
        actual_winner = 1 if result == -1 else (2 if result == 1 else 0)

        if actual_winner == expected_winner:
            print(f"✓ {test['name']}")
            print(f"  Hand 1: {name1} {eval1[1]}")
            print(f"  Hand 2: {name2} {eval2[1]}")
            print(f"  Result: Hand {actual_winner} wins - {test['description']}")
            passed += 1
        else:
            print(f"✗ {test['name']}")
            print(f"  Hand 1: {name1} {eval1[1]}")
            print(f"  Hand 2: {name2} {eval2[1]}")
            print(f"  Expected: Hand {expected_winner}, Got: Hand {actual_winner}")
            print(f"  {test['description']}")
            failed += 1
        print()

    print("="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)

    return failed == 0


def test_edge_cases():
    """Test edge cases in hand evaluation."""

    print("\n" + "="*60)
    print("TESTING EDGE CASES")
    print("="*60)

    tests = []

    # Test 1: Ensure best 5 cards are used from 7
    hand1 = ["Ah", "Ac", "Ad", "As", "Kh", "Kc", "Kd"]  # 4 aces + 3 kings
    eval1 = _evaluate_hand(hand1)
    rank_names = {v: k for k, v in HAND_RANKS.items()}
    name1 = rank_names.get(eval1[0], "unknown").replace("_", " ").title()

    if name1 == "Four Of A Kind":
        print("✓ Best 5 cards selected: Four aces (not full house)")
        tests.append(True)
    else:
        print(f"✗ Expected Four of a Kind, got {name1}")
        tests.append(False)

    # Test 2: Flush with more than 5 cards of same suit
    hand2 = ["2s", "4s", "6s", "8s", "Ts", "Qs", "Ks"]  # 7 spades
    eval2 = _evaluate_hand(hand2)
    name2 = rank_names.get(eval2[0], "unknown").replace("_", " ").title()

    if name2 == "Flush":
        print("✓ Flush detected with 7 cards of same suit")
        tests.append(True)
    else:
        print(f"✗ Expected Flush, got {name2}")
        tests.append(False)

    # Test 3: Straight with extra cards
    hand3 = ["2h", "3c", "4d", "5s", "6h", "7c", "8d"]  # Multiple straights possible
    eval3 = _evaluate_hand(hand3)
    name3 = rank_names.get(eval3[0], "unknown").replace("_", " ").title()

    if name3 == "Straight":
        print(f"✓ Straight detected: high card {eval3[1][0]}")
        tests.append(True)
    else:
        print(f"✗ Expected Straight, got {name3}")
        tests.append(False)

    # Test 4: Two pair vs two pair (higher pairs win)
    hand4a = ["Ah", "Ac", "Kd", "Kh", "2c", "3s", "4s"]  # A-A-K-K
    hand4b = ["Kh", "Kc", "Qd", "Qh", "Ac", "2s", "3s"]  # K-K-Q-Q
    eval4a = _evaluate_hand(hand4a)
    eval4b = _evaluate_hand(hand4b)
    result4 = _compare_hands(eval4a, eval4b)

    if result4 == -1:  # hand4a wins
        print("✓ A-A-K-K beats K-K-Q-Q")
        tests.append(True)
    else:
        print("✗ A-A-K-K should beat K-K-Q-Q")
        tests.append(False)

    print()
    print("="*60)
    print(f"Edge Cases: {sum(tests)}/{len(tests)} passed")
    print("="*60)

    return all(tests)


if __name__ == "__main__":
    scenarios_ok = test_hand_scenarios()
    edge_cases_ok = test_edge_cases()

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Hand Scenarios: {'✓ PASS' if scenarios_ok else '✗ FAIL'}")
    print(f"Edge Cases: {'✓ PASS' if edge_cases_ok else '✗ FAIL'}")

    if scenarios_ok and edge_cases_ok:
        print("\n🎉 ALL TESTS PASSED! POKER ENGINE IS SOLID! 🎉")
    else:
        print("\n⚠️  SOME TESTS FAILED - NEEDS FIXES")
