#!/usr/bin/env python3
"""Cross-validation test vectors for the Rubik's Snake enumerator."""

from enumerate import enumerate_snakes

EXPECTED = {
    2:  4,
    3:  16,
    4:  64,
    5:  256,
    6:  1024,
    7:  4096,
    8:  16384,
    9:  64512,
    10: 245760,
    11: 983040,
    12: 3735552,
    13: 14811136,
    14: 54525952,
}

def test_small_instances():
    for n, expected_valid in sorted(EXPECTED.items()):
        result = enumerate_snakes(n)
        assert result['valid'] == expected_valid, \
            f"n={n}: expected {expected_valid}, got {result['valid']}"
        pct = (1 - result['valid'] / result['unconstrained']) * 100
        print(f"  n={n:2d}: {result['valid']:>10,} / {result['unconstrained']:>10,} valid ({pct:5.2f}% invalid)")

if __name__ == '__main__':
    print("Running cross-validation tests...")
    test_small_instances()
    print("All tests passed.")
