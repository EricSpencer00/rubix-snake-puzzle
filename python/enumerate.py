#!/usr/bin/env python3
"""
Reference enumerator for Rubik's Snake valid configurations.

Uses backtracking with collision pruning to count all non-self-intersecting
configurations. Results for small N cross-validate the Coq proofs and TLA+ model.

Usage:
    python3 enumerate.py --wedges 8
    python3 enumerate.py --wedges 24 --parallel  # full puzzle, needs hours
"""

import argparse
from typing import NamedTuple
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


def enumerate_snakes(num_wedges: int) -> dict:
    """Count valid configurations via backtracking."""
    num_joints = num_wedges - 1
    valid_count = 0
    closed_count = 0

    def backtrack(depth, pos, fwd, up, parity, occupied):
        nonlocal valid_count, closed_count

        if depth == num_joints:
            valid_count += 1
            if pos == (0, 0, 0):
                closed_count += 1
            return

        for rot in range(4):
            new_up = apply_rotation(Orientation(fwd, up), rot)
            step_dir = new_up if parity else fwd
            new_pos = vec_add(pos, DIRS[step_dir])

            if new_pos in occupied:
                continue

            # Compute next orientation
            if parity:
                next_fwd = new_up
                next_up = NEG[fwd]
            else:
                next_fwd = fwd
                next_up = new_up

            occupied.add(new_pos)
            backtrack(depth + 1, new_pos, next_fwd, next_up, not parity, occupied)
            occupied.remove(new_pos)

    start = (0, 0, 0)
    occupied = {start}
    backtrack(0, start, 'PosX', 'PosY', False, occupied)

    return {
        'wedges': num_wedges,
        'joints': num_joints,
        'unconstrained': 4 ** num_joints,
        'valid': valid_count,
        'closed_loops': closed_count,
        'invalid_pct': f"{(1 - valid_count / 4**num_joints) * 100:.2f}%",
    }


def main():
    parser = argparse.ArgumentParser(description='Rubik\'s Snake enumerator')
    parser.add_argument('--wedges', type=int, default=8,
                        help='Number of wedges (default: 8, standard: 24)')
    args = parser.parse_args()

    print(f"Enumerating {args.wedges}-wedge Rubik's Snake...")
    print(f"Unconstrained state space: 4^{args.wedges-1} = {4**(args.wedges-1):,}")
    print()

    results = enumerate_snakes(args.wedges)

    print(f"Results for {results['wedges']} wedges ({results['joints']} joints):")
    print(f"  Unconstrained configs: {results['unconstrained']:>20,}")
    print(f"  Valid (no collision):  {results['valid']:>20,}")
    print(f"  Closed loops:         {results['closed_loops']:>20,}")
    print(f"  Invalid percentage:   {results['invalid_pct']:>20}")


if __name__ == '__main__':
    main()
