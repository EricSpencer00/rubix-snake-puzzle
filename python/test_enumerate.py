#!/usr/bin/env python3
"""Cross-validation test vectors for the Rubik's Snake enumerator."""

from pathlib import Path
import subprocess
import sys

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


def test_prefix_partition():
    """One-joint shards must reconstruct the root search exactly."""
    whole = enumerate_snakes(9)
    shards = [enumerate_snakes(9, prefix=(rotation,)) for rotation in range(4)]

    assert all(shard['prefix'] == [rotation] for rotation, shard in enumerate(shards))
    assert all(shard['unconstrained'] == whole['unconstrained'] // 4 for shard in shards)
    assert sum(shard['unconstrained'] for shard in shards) == whole['unconstrained']
    assert sum(shard['valid'] for shard in shards) == whole['valid']
    assert sum(shard['closed_loops'] for shard in shards) == whole['closed_loops']


def test_prefix_validation():
    for invalid_prefix in ((4,), (-1,), (0, 1, 2, 3, 0, 1, 2, 3, 0)):
        try:
            enumerate_snakes(9, prefix=invalid_prefix)
        except ValueError:
            pass
        else:
            raise AssertionError(f'expected invalid prefix to fail: {invalid_prefix}')


def test_colliding_prefix_has_no_valid_suffix():
    result = enumerate_snakes(9, prefix=(0,) * 8)

    assert result['unconstrained'] == 1
    assert result['valid'] == 0
    assert result['closed_loops'] == 0
    assert result['invalid_pct'] == '100.00%'


def test_cli_rejects_prefix_longer_than_snake():
    script = Path(__file__).with_name('enumerate.py')
    completed = subprocess.run(
        [sys.executable, str(script), '--wedges', '1', '--prefix', '0'],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert 'prefix cannot contain more rotations' in completed.stderr

if __name__ == '__main__':
    print("Running cross-validation tests...")
    test_small_instances()
    test_prefix_partition()
    test_prefix_validation()
    test_colliding_prefix_has_no_valid_suffix()
    test_cli_rejects_prefix_longer_than_snake()
    print("All tests passed.")
