# Rubik's Snake Puzzle — Formal Verification

Formal methods approach to enumerating all valid (non-self-intersecting) configurations of the [Rubik's Snake](https://en.wikipedia.org/wiki/Rubik%27s_Snake) puzzle.

## The Puzzle

The Rubik's Snake consists of **24 right-triangular prisms** (wedges) connected in a chain. Each joint between consecutive wedges allows **4 discrete rotations** (0°, 90°, 180°, 270°). With 23 joints, the unconstrained state space is **4^23 = 70,368,744,177,664** configurations.

The constraint: **no two wedges may occupy the same space** (no self-intersection).

## Known Results

Peter Aylett's exhaustive backtracking search (2011, corrected 2022) established:

| Metric | Count |
|--------|-------|
| Unconstrained states (4^23) | 70,368,744,177,664 |
| Valid non-self-intersecting | **13,446,591,920,995** |
| After symmetry deduction (mirror + cyclic) | **6,721,828,475,867** |
| Closed-loop configurations | 63,970,851 |

~19.1% of the state space is invalid due to collision.

## This Repository

We formalize the state space and collision constraints using formal methods:

- **`coq/`** — Coq (Rocq) formalization: defines wedge geometry, rotation semantics, collision predicate, and valid configuration space. Proves structural properties.
- **`tla/`** — TLA+ specification: models the snake as a state machine for model checking small instances.
- **`python/`** — Reference enumerator for validation against formal specs.

## Prior Work

- **Aylett (2011/2022)** — Exhaustive C enumeration. [Blog post](https://blog.ylett.com/2011/09/rubiks-snake-combinations.html)
- **Li, Hou, Bishop (2020)** — "Computational Design and Analysis of a Magic Snake," *J. Mechanisms and Robotics* 12(5). 1D-to-3D conversion methods.
- **Hou, Chen, Li (2021)** — "Some Mathematical Problems Related to the Rubik's Snake," *J. Mechanisms and Robotics* 13(1).
- **Grotto, Perucca, Van Steenbergen Bergeron (2021)** — "Rubik's Snakes on a Plane," Univ. Luxembourg. Eulerian path characterization of planar configurations.
- **scholtes/snek** — Python enumerator with OpenSCAD visualization. [GitHub](https://github.com/scholtes/snek)

No prior formal verification (Coq, Lean, Isabelle, TLA+, Alloy) of this puzzle exists. This is the first.

## Building

### Coq
```bash
cd coq && make
```
Requires Coq 8.18+ / Rocq.

### TLA+
Open `tla/RubikSnake.tla` in the [TLA+ Toolbox](https://github.com/tlaplus/tlaplus) or run with `tlc`.

### Python
```bash
cd python && python3 enumerate.py --wedges 8
```

## License

MIT
