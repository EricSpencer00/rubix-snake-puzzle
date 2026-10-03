# Rubik's Snake State Space Explorer

An interactive 3D model of the Rubik's Snake, alongside small formal-methods experiments about its state space.

## The puzzle and its state space

The physical puzzle has 24 connected right-triangular prisms. This project models the 23 joints as four quarter-turn positions each, giving an upper bound of `4^23 = 70,368,744,177,664` turn sequences before checking for overlaps.

Peter Aylett's exhaustive search reports **13,446,591,920,995** non-overlapping sequences when mirror duplicates are included, **6,721,828,475,867** after its reversal-based symmetry reduction, and **63,970,851** closed-loop sequences. Aylett corrected the published totals in 2022. These are results from that external search, not a theorem proved by this repository. See [Aylett's write-up](https://blog.ylett.com/2011/09/rubiks-snake-combinations.html).

## What is in this repository

- `docs/` contains the interactive page. Its builder renders 24 half-cube triangular prisms and checks whether pieces sharing a cube occupy complementary halves or overlap.
- `python/` contains prefix-shardable backtracking searches. The default `lattice` model rejects repeated cells and preserves the historical small-case counts. The optional `half-cube` model uses the browser's prism geometry and measures physical end-face closure. Neither search proves the published full-size result.
- `coq/` defines an integer-grid rotation and repeated-position model. It has a few checked examples, but some structural lemmas are admitted and it does not prove the 24-piece count.
- `tla/` contains an incremental state-machine specification for small cases. This repository does not claim a checked 24-piece TLC run.

## Running the page

Serve the `docs/` directory with any static web server and open `index.html`. The Three.js renderer is bundled locally under `docs/vendor/`.

GitHub Pages publishes `docs/` from `dev`, the branch used for page fixes. A push to a different branch does not update the live site.

## Checking the page

```sh
npm ci
npm test
npx playwright install chromium
npm run test:browser
```

The browser check starts a temporary local preview, tests the 24-piece model and overlap switch, checks animation and keyboard controls, and saves screenshots at desktop, tablet, and phone widths. To check the deployed page, run `npm run test:browser -- https://ericspencer.us/rubix-snake-puzzle/`.

## Running the Python reference search

```sh
cd python
python3 enumerate.py --wedges 8
python3 enumerate.py --wedges 6 --model half-cube
python3 enumerate.py --wedges 6 --model half-cube --prefix 2,2
```

The search grows quickly with the number of wedges. Fix a prefix to count only that suffix space. Prefixes of the same length partition the root search; sum their `unconstrained`, `valid`, and (for the half-cube model) `closed_loops` values. An overlapping prefix owns an empty valid shard. This command runs a single shard; it does not provision compute or launch parallel jobs.

Physical closure requires the first and last exposed square leg faces to coincide with opposite outward normals, with no prism overlap anywhere. Matching face centers alone or placing the final wedge at the first wedge's center is insufficient. The Python `half-cube` model and browser `isClosedSnake` implement this contact criterion. A single wedge is not closed. Square end faces permit quarter-turn alignment; material orientation does not require the entire final frame to equal the initial frame.

The old lattice closure check compared the last occupied position to the occupied origin, which every valid multi-piece path was forbidden to revisit. `closed_loops` is now `null` (`None` in Python) in lattice results; physical closure is unavailable in that abstraction. Consumers that previously expected an integer must select `--model half-cube` or handle the unavailable value. The page's historical chart remains explicitly scoped to lattice counts.

## Bounded regression checks

```sh
python3 python/test_enumerate.py
python3 -m unittest discover -s python -v
python3 python/generate_coq_fixtures.py --check
npm test
```

The default Python count regression runs 2–10 wedges; historical 11–14 values remain recorded without running their larger searches. Half-cube root and two-joint shard tests run 1–6 wedges, including one closed four-piece sequence `[2,2,2]` and eight closed six-piece sequences. These are rooted, oriented turn-sequence counts without mirror or reversal reduction.

Shared fixtures in `tests/fixtures/collision-models.json` cover straight, overlapping, open, and closed examples. Browser and Python half-cube tests compare exact occupancies and closure against them. `[0,2,2,1]` passes the lattice check but overlaps in the physical model; eight zero turns fail the lattice check but form a clear physical bar. Generated Coq examples check the lattice positions and validity from these same fixtures. Agreement on fixtures is regression evidence, not general equivalence or a completed physical proof.

## Coq and TLA+

Run `make -C coq` with Coq/Rocq installed to compile the lattice definitions and fixture examples. The lattice diagnostic is named `revisits_first_cell`; it does not model physical closure. The old admitted `straight_always_valid` statement is refuted by the eight-zero-turn fixture and has been replaced by that counterexample. The TLA+ specification can be opened in the TLA+ Toolbox for small-state exploration. Neither project currently establishes Aylett's full-size count, and other admitted structural lemmas remain unfinished.

## License

MIT
