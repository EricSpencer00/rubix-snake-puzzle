# Rubik's Snake State Space Explorer

An interactive 3D model of the Rubik's Snake, alongside small formal-methods experiments about its state space.

## The puzzle and its state space

The physical puzzle has 24 connected right-triangular prisms. This project models the 23 joints as four quarter-turn positions each, giving an upper bound of `4^23 = 70,368,744,177,664` turn sequences before checking for overlaps.

Peter Aylett's exhaustive search reports **13,446,591,920,995** non-overlapping sequences when mirror duplicates are included, **6,721,828,475,867** after its reversal-based symmetry reduction, and **63,970,851** closed-loop sequences. Aylett corrected the published totals in 2022. These are results from that external search, not a theorem proved by this repository. See [Aylett's write-up](https://blog.ylett.com/2011/09/rubiks-snake-combinations.html).

## What is in this repository

- `docs/` contains the interactive page. Its builder renders 24 half-cube triangular prisms and checks whether pieces sharing a cube occupy complementary halves or overlap.
- `python/` contains a backtracking enumerator. It rejects repeated lattice cells. Its check is not the same as the builder's half-cube overlap check, and its stored small-case counts do not prove the published full-size result.
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
```

The search grows quickly with the number of wedges. Its repeated-cell rule is a separate model from the browser builder's solid-prism check.

## Coq and TLA+

The files under `coq/` can be built with Coq/Rocq. The TLA+ specification can be opened in the TLA+ Toolbox for small-state exploration. Neither project currently establishes Aylett's full-size count.

## License

MIT
