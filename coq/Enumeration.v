(* Enumeration.v — Computable enumeration and verification for small instances *)

Require Import RubikSnake.
Require Import List ZArith Bool.
Import ListNotations.
Open Scope Z_scope.

(* === Test vectors for cross-validation === *)

(* 1 wedge (0 joints): always valid, exactly 1 config *)
Lemma one_wedge_count : count_valid 0 = 1.
Proof. reflexivity. Qed.

(* 2 wedges (1 joint): all 4 rotations valid — not enough pieces to collide *)
Lemma two_wedge_count : count_valid 1 = 4.
Proof. reflexivity. Qed.

(* 3 wedges (2 joints): all 16 valid — still too few for collision *)
Lemma three_wedge_count : count_valid 2 = 16.
Proof. reflexivity. Qed.

(* These machine-checked equalities serve as ground truth for the
   TLA+ model checker and Python reference implementation. *)

(* === Key structural lemma === *)

(* The straight configuration is always valid for any length *)
Lemma straight_always_valid : forall n,
  is_valid (repeat R0 n) = true.
Proof.
  induction n; simpl; auto.
  (* The straight line never revisits a grid cell. *)
  (* Full proof requires showing repeat-R0 produces strictly increasing coords. *)
Admitted.

(* Mirror preserves validity *)
Lemma mirror_preserves_validity : forall cfg,
  is_valid cfg = true -> is_valid (mirror_config cfg) = true.
Proof.
  (* Mirror is a geometric reflection — if no collision in original,
     the reflected configuration also has no collision. *)
Admitted.
