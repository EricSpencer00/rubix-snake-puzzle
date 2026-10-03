"""Bounded physical-model, closure, and shared collision regressions."""
import itertools
import json
from pathlib import Path
import unittest
import subprocess
import sys

from enumerate import enumerate_snakes, _advance_state
from geometry import INITIAL, Piece, endpoints_match, has_collision, is_closed, pieces

FIXTURES = json.loads((Path(__file__).resolve().parents[1] / 'tests/fixtures/collision-models.json').read_text())


class GeometryTests(unittest.TestCase):
    def test_shared_fixtures(self):
        for case in FIXTURES:
            with self.subTest(case=case['id']):
                placed = pieces(case['turns'])
                self.assertEqual(not has_collision(placed), case['half_cube_valid'])
                self.assertEqual(is_closed(case['turns']), case['physical_closed'])
                self.assertEqual([dict(cell2=list(cell), kind=kind) for cell, kind in
                                  (p.occupancy() for p in placed)], case['half_cube_occupancy'])
                state = ((0, 0, 0), 'PosX', 'PosY', False)
                positions = [list(state[0])]
                for turn in case['turns']:
                    state = _advance_state(*state, turn)
                    positions.append(list(state[0]))
                self.assertEqual(positions, case['lattice_positions'])
                result = enumerate_snakes(len(case['turns']) + 1, case['turns'])
                self.assertEqual(result['valid'], int(case['lattice_valid']))
                self.assertIsNone(result['closed_loops'])
                physical = enumerate_snakes(len(case['turns']) + 1, case['turns'], 'half-cube')
                self.assertEqual(physical['valid'], int(case['half_cube_valid']))
                self.assertEqual(physical['closed_loops'], int(case['physical_closed']))

    def test_end_contact_requires_opposite_normals(self):
        # Same rectangular face, material on the same side: not a closure.
        self.assertFalse(endpoints_match(INITIAL, INITIAL, 1))
        opposing = Piece(INITIAL.origin2, (-1, 0, 0), INITIAL.b, INITIAL.c)
        self.assertTrue(endpoints_match(INITIAL, opposing, 1))
        # Face centers alone do not establish orientation or face equality.
        rotated = Piece(INITIAL.origin2, (-1, 0, 0), INITIAL.c, INITIAL.b)
        self.assertTrue(endpoints_match(INITIAL, rotated, 1))  # Square face permits quarter turns.

    def test_closed_wedges_have_distinct_centroids(self):
        for case in FIXTURES:
            if case['physical_closed']:
                placed = pieces(case['turns'])
                centroids6 = [tuple(sum(v[i] for v in p.vertices2()) for i in range(3)) for p in placed]
                self.assertEqual(len(set(centroids6)), len(placed))

    def test_end_contact_is_insufficient_when_interiors_overlap(self):
        placed = pieces([2] * 7)
        self.assertTrue(endpoints_match(placed[0], placed[-1], 7))
        self.assertTrue(has_collision(placed))
        self.assertFalse(is_closed([2] * 7))
        for i in range(4):
            self.assertEqual(placed[i], placed[i + 4])

    def test_small_root_counts_and_two_joint_shards(self):
        for wedges, valid, closed in ((1, 1, 0), (2, 4, 0), (3, 16, 0),
                                       (4, 64, 1), (5, 241, 0), (6, 920, 8)):
            whole = enumerate_snakes(wedges, model='half-cube')
            self.assertEqual((whole['valid'], whole['closed_loops']), (valid, closed))
            depth = min(2, wedges - 1)
            shards = [enumerate_snakes(wedges, prefix, 'half-cube')
                      for prefix in itertools.product(range(4), repeat=depth)]
            for key in ('unconstrained', 'valid', 'closed_loops'):
                self.assertEqual(sum(shard[key] for shard in shards), whole[key])

    def test_api_rejects_invalid_bounds(self):
        for wedges in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                enumerate_snakes(wedges, model='half-cube')
        for prefix in ((True,), (1.5,), (4,), (0, 0, 0)):
            with self.assertRaises(ValueError):
                enumerate_snakes(3, prefix, 'half-cube')

    def test_cli_known_closed_prefix_and_single_wedge(self):
        script = Path(__file__).with_name('enumerate.py')
        result = subprocess.run([sys.executable, str(script), '--wedges', '4',
                                 '--model', 'half-cube', '--prefix', '2,2,2'],
                                capture_output=True, text=True, check=True)
        self.assertRegex(result.stdout, r'Closed loops:\s+1')
        result = subprocess.run([sys.executable, str(script), '--wedges', '1'],
                                capture_output=True, text=True, check=True)
        self.assertIn('Physical closure: unavailable', result.stdout)


if __name__ == '__main__':
    unittest.main()
