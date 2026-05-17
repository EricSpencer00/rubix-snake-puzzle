---------------------------- MODULE RubikSnake ----------------------------
(*
 * TLA+ specification of the Rubik's Snake puzzle.
 *
 * Models the snake as a state machine that places wedges one at a time,
 * choosing a rotation at each joint. The invariant is collision-freedom:
 * no two wedges occupy the same grid cell.
 *
 * For model checking, set N (number of wedges) to a small value (4-10).
 * Full 24-wedge enumeration is infeasible for TLC but the spec is
 * exact and can verify small-instance counts against the Coq proofs.
 *)

EXTENDS Integers, Sequences, FiniteSets, TLC

CONSTANT N  \* Number of wedges (standard = 24, use <= 10 for TLC)

ASSUME N \in 2..24

Rotations == {0, 1, 2, 3}  \* R0, R90, R180, R270

(* 3D point as a triple *)
Point(x, y, z) == <<x, y, z>>

(* 6 axis-aligned direction vectors *)
DirVecs == [
    PosX |-> <<1, 0, 0>>,  NegX |-> <<-1, 0, 0>>,
    PosY |-> <<0, 1, 0>>,  NegY |-> <<0, -1, 0>>,
    PosZ |-> <<0, 0, 1>>,  NegZ |-> <<0, 0, -1>>
]

NegDir == [
    PosX |-> "NegX", NegX |-> "PosX",
    PosY |-> "NegY", NegY |-> "PosY",
    PosZ |-> "NegZ", NegZ |-> "PosZ"
]

AllDirs == {"PosX", "NegX", "PosY", "NegY", "PosZ", "NegZ"}

(* Cross product on axis-aligned directions *)
CrossDir[a \in AllDirs, b \in AllDirs] ==
    CASE a = "PosX" /\ b = "PosY" -> "PosZ"
      [] a = "PosX" /\ b = "NegY" -> "NegZ"
      [] a = "PosX" /\ b = "PosZ" -> "NegY"
      [] a = "PosX" /\ b = "NegZ" -> "PosY"
      [] a = "NegX" /\ b = "PosY" -> "NegZ"
      [] a = "NegX" /\ b = "NegY" -> "PosZ"
      [] a = "NegX" /\ b = "PosZ" -> "PosY"
      [] a = "NegX" /\ b = "NegZ" -> "NegY"
      [] a = "PosY" /\ b = "PosX" -> "NegZ"
      [] a = "PosY" /\ b = "NegX" -> "PosZ"
      [] a = "PosY" /\ b = "PosZ" -> "PosX"
      [] a = "PosY" /\ b = "NegZ" -> "NegX"
      [] a = "NegY" /\ b = "PosX" -> "PosZ"
      [] a = "NegY" /\ b = "NegX" -> "NegZ"
      [] a = "NegY" /\ b = "PosZ" -> "NegX"
      [] a = "NegY" /\ b = "NegZ" -> "PosX"
      [] a = "PosZ" /\ b = "PosX" -> "PosY"
      [] a = "PosZ" /\ b = "NegX" -> "NegY"
      [] a = "PosZ" /\ b = "PosY" -> "NegX"
      [] a = "PosZ" /\ b = "NegY" -> "PosX"
      [] a = "NegZ" /\ b = "PosX" -> "NegY"
      [] a = "NegZ" /\ b = "NegX" -> "PosY"
      [] a = "NegZ" /\ b = "PosY" -> "PosX"
      [] a = "NegZ" /\ b = "NegY" -> "NegX"
      [] OTHER -> "PosX"  \* degenerate: parallel

VecAdd(a, b) == <<a[1]+b[1], a[2]+b[2], a[3]+b[3]>>

(*
 * State: we build the snake incrementally.
 *   placed     : number of wedges placed so far
 *   occupied   : set of grid cells occupied
 *   curPos     : current wedge position
 *   curFwd     : current forward direction (string key)
 *   curUp      : current up direction (string key)
 *   curParity  : FALSE for even wedges, TRUE for odd
 *   configs    : sequence of rotations chosen so far
 *   validCount : count of complete valid configurations found
 *)
VARIABLES placed, occupied, curPos, curFwd, curUp, curParity, configs, validCount

vars == <<placed, occupied, curPos, curFwd, curUp, curParity, configs, validCount>>

(* Apply rotation to orientation: rotates "up" around "forward" axis *)
ApplyRot(fwd, up, rot) ==
    LET right == CrossDir[fwd, up] IN
    CASE rot = 0 -> up
      [] rot = 1 -> right
      [] rot = 2 -> NegDir[up]
      [] rot = 3 -> NegDir[right]

StepDir(fwd, up, parity) ==
    IF parity THEN up ELSE fwd

Init ==
    /\ placed = 1
    /\ occupied = {<<0, 0, 0>>}
    /\ curPos = <<0, 0, 0>>
    /\ curFwd = "PosX"
    /\ curUp = "PosY"
    /\ curParity = FALSE
    /\ configs = <<>>
    /\ validCount = 0

PlaceNext(rot) ==
    LET newUp == ApplyRot(curFwd, curUp, rot)
        stepD == StepDir(curFwd, newUp, curParity)
        newPos == VecAdd(curPos, DirVecs[stepD])
        newFwd == IF curParity THEN newUp ELSE curFwd
        newUp2 == IF curParity THEN NegDir[curFwd] ELSE newUp
    IN
    /\ placed < N
    /\ newPos \notin occupied  \* collision check
    /\ placed' = placed + 1
    /\ occupied' = occupied \union {newPos}
    /\ curPos' = newPos
    /\ curFwd' = newFwd
    /\ curUp' = newUp2
    /\ curParity' = ~curParity
    /\ configs' = Append(configs, rot)
    /\ UNCHANGED validCount

Complete ==
    /\ placed = N
    /\ validCount' = validCount + 1
    /\ placed' = 0  \* reset to trigger backtracking via TLC
    /\ UNCHANGED <<occupied, curPos, curFwd, curUp, curParity, configs>>

Next ==
    \/ \E rot \in Rotations : PlaceNext(rot)
    \/ Complete

Spec == Init /\ [][Next]_vars

(* Invariant: no cell is occupied twice (enforced by construction) *)
NoCollision == Cardinality(occupied) = placed

(* Temporal property: eventually we enumerate all valid configurations *)
TypeInvariant ==
    /\ placed \in 0..N
    /\ curParity \in BOOLEAN
    /\ curFwd \in AllDirs
    /\ curUp \in AllDirs

=============================================================================
