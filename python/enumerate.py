#!/usr/bin/env python3
"""
Reference enumerator for Rubik's Snake valid configurations.

Uses backtracking with collision pruning to count all non-self-intersecting
configurations. Results for small N cross-validate the Coq proofs and TLA+ model.

Usage:
    python3 enumerate.py --wedges 8
    python3 enumerate.py --wedges 24 --prefix 0,1,3
    python3 enumerate.py --wedges 24 --parallel  # full puzzle, needs hours
"""

import argparse
from typing import NamedTuple, Optional, Sequence, Tuple
from collections import defaultdict

# Direction vectors
DIRS = {
    'PosX': (1,0,0),  'NegX': (-1,0,0),
    'PosY': (0,1,0),  'NegY': (0,-1,0),
    'PosZ': (0,0,1),  'NegZ': (0,0,-1),
}

NEG = {
    'PosX':'NegX', 'NegX':'PosX',
    'PosY':'NegY', 'NegY':'PosY',
    'PosZ':'NegZ', 'NegZ':'PosZ',
}

# Cross product lookup for axis-aligned directions
CROSS = {}
_basis = [('PosX',(1,0,0)),('PosY',(0,1,0)),('PosZ',(0,0,1)),
          ('NegX',(-1,0,0)),('NegY',(0,-1,0)),('NegZ',(0,0,-1))]
for na, va in _basis:
    for nb, vb in _basis:
        cx = va[1]*vb[2] - va[2]*vb[1]
        cy = va[2]*vb[0] - va[0]*vb[2]
        cz = va[0]*vb[1] - va[1]*vb[0]
        for nc, vc in _basis:
            if vc == (cx, cy, cz):
                CROSS[(na, nb)] = nc
                break


class Orientation(NamedTuple):
    fwd: str
    up: str


def apply_rotation(o: Orientation, rot: int) -> str:
    """Apply rotation to get new up direction."""
    right = CROSS.get((o.fwd, o.up), 'PosX')
    if rot == 0: return o.up
    if rot == 1: return right
    if rot == 2: return NEG[o.up]
    if rot == 3: return NEG[right]


def vec_add(a, b):
    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])


def parse_prefix(value: str) -> Tuple[int, ...]:
    """Parse a comma-separated rotation prefix for the command-line interface."""
    if not value.strip():
        return ()

    try:
        prefix = tuple(int(part.strip()) for part in value.split(','))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            'prefix must be comma-separated rotation numbers in the range 0..3'
        ) from exc

    if any(rotation not in range(4) for rotation in prefix):
        raise argparse.ArgumentTypeError(
            'prefix must be comma-separated rotation numbers in the range 0..3'
        )
    return prefix


def _advance_state(pos, fwd: str, up: str, parity: bool, rot: int):
    """Advance one joint and return the next position/orientation state."""
    new_up = apply_rotation(Orientation(fwd, up), rot)
    step_dir = new_up if parity else fwd
    new_pos = vec_add(pos, DIRS[step_dir])

    if parity:
        next_fwd = new_up
        next_up = NEG[fwd]
    else:
        next_fwd = fwd
        next_up = new_up

    return new_pos, next_fwd, next_up, not parity


def enumerate_snakes(
    num_wedges: int,
    prefix: Optional[Sequence[int]] = None,
) -> dict:
    """Count valid configurations via backtracking.

    ``prefix`` fixes the rotations at the first joints and enumerates only the
    remaining suffix. This makes a large search reproducibly shardable: the
    four one-rotation prefixes are disjoint and cover the root search space.
    """
    if not isinstance(num_wedges, int) or isinstance(num_wedges, bool) or num_wedges < 1:
        raise ValueError('num_wedges must be a positive integer')

    num_joints = num_wedges - 1
    prefix = tuple(prefix or ())
    if len(prefix) > num_joints:
        raise ValueError('prefix cannot contain more rotations than the snake has joints')
    if any(
        not isinstance(rotation, int)
        or isinstance(rotation, bool)
        or rotation not in range(4)
        for rotation in prefix
    ):
        raise ValueError('prefix rotations must be integers in the range 0..3')

    valid_count = 0
    closed_count = 0
    start = (0, 0, 0)
    pos = start
    fwd = 'PosX'
    up = 'PosY'
    parity = False
    occupied = {start}

    # Materialize the requested prefix before entering the recursive search.
    # An invalid prefix owns an empty valid subspace, but still reports the
    # suffix size so shard totals remain auditable.
    for rot in prefix:
        pos, fwd, up, parity = _advance_state(pos, fwd, up, parity, rot)
        if pos in occupied:
            return {
                'wedges': num_wedges,
                'joints': num_joints,
                'prefix': list(prefix),
                'unconstrained': 4 ** (num_joints - len(prefix)),
                'valid': 0,
                'closed_loops': 0,
                'invalid_pct': '100.00%',
            }
        occupied.add(pos)

    def backtrack(depth, pos, fwd, up, parity, occupied):
        nonlocal valid_count, closed_count

        if depth == num_joints:
            valid_count += 1
            if pos == start:
                closed_count += 1
            return

        for rot in range(4):
            new_pos, next_fwd, next_up, next_parity = _advance_state(
                pos, fwd, up, parity, rot
            )

            if new_pos in occupied:
                continue

            occupied.add(new_pos)
            backtrack(depth + 1, new_pos, next_fwd, next_up, next_parity, occupied)
            occupied.remove(new_pos)

    backtrack(len(prefix), pos, fwd, up, parity, occupied)

    unconstrained = 4 ** (num_joints - len(prefix))

    return {
        'wedges': num_wedges,
        'joints': num_joints,
        'prefix': list(prefix),
        'unconstrained': unconstrained,
        'valid': valid_count,
        'closed_loops': closed_count,
        'invalid_pct': f"{(1 - valid_count / unconstrained) * 100:.2f}%",
    }


def main():
    parser = argparse.ArgumentParser(description='Rubik\'s Snake enumerator')
    parser.add_argument('--wedges', type=int, default=8,
                        help='Number of wedges (default: 8, standard: 24)')
    parser.add_argument(
        '--prefix',
        type=parse_prefix,
        default=(),
        metavar='R0,R1,...',
        help='Fixed joint rotations for a reproducible search shard (values 0..3)',
    )
    args = parser.parse_args()
    if args.wedges < 1:
        parser.error('--wedges must be a positive integer')
    if len(args.prefix) > args.wedges - 1:
        parser.error('prefix cannot contain more rotations than the snake has joints')

    print(f"Enumerating {args.wedges}-wedge Rubik's Snake...")
    remaining_joints = args.wedges - 1 - len(args.prefix)
    if args.prefix:
        prefix_text = ','.join(str(rotation) for rotation in args.prefix)
        print(f"Fixed prefix: {prefix_text}")
    print(f"Unconstrained state space: 4^{remaining_joints} = {4**remaining_joints:,}")
    print()

    results = enumerate_snakes(args.wedges, args.prefix)

    print(f"Results for {results['wedges']} wedges ({results['joints']} joints):")
    print(f"  Unconstrained configs: {results['unconstrained']:>20,}")
    print(f"  Valid (no collision):  {results['valid']:>20,}")
    print(f"  Closed loops:         {results['closed_loops']:>20,}")
    print(f"  Invalid percentage:   {results['invalid_pct']:>20}")


if __name__ == '__main__':
    main()
