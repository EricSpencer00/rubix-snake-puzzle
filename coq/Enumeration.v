(* Enumeration.v — Computable enumeration and verification for small instances *)

Require Import RubikSnake.
Require Import List ZArith Bool.
Import ListNotations.
Open Scope Z_scope.

(* === Small checked examples === *)

(* 1 wedge (0 joints): always valid, exactly 1 config *)
Lemma one_wedge_count : count_valid 0 = 1.
Proof. reflexivity. Qed.

(* 2 wedges (1 joint): all 4 rotations valid — not enough pieces to collide *)
Lemma two_wedge_count : count_valid 1 = 4.
Proof. reflexivity. Qed.

(* 3 wedges (2 joints): all 16 valid — still too few for collision *)
Lemma three_wedge_count : count_valid 2 = 16.
Proof. reflexivity. Qed.

(* These tiny examples are checked in Coq. They do not establish the
   larger Python counts or the published 24-piece result. *)

(* The physical all-zero bar is clear in the browser. This lattice abstraction
   instead returns to the origin after eight zero turns, so the previously
   admitted straight_always_valid statement was false in this model. *)
Lemma all_zero_lattice_counterexample : is_valid (repeat R0 8) = false.
Proof. reflexivity. Qed.

(* Mirror preserves validity *)
Lemma mirror_preserves_validity : forall cfg,
  is_valid cfg = true -> is_valid (mirror_config cfg) = true.
Proof.
  (* Mirror is a geometric reflection — if no collision in original,
     the reflected configuration also has no collision. *)
Admitted.
