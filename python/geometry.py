"""Exact half-cube model shared with the browser by regression fixtures.

Coordinates are doubled integers. Closure joins the two free square leg faces
with opposite outward normals; wedge centers are never identified to close a
loop. This is executable geometry, not a proof of the full puzzle count.
"""

from dataclasses import dataclass


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(a, k):
    return tuple(x * k for x in a)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def rotate(value, axis, turns):
    turns %= 4
    parallel = scale(axis, dot(axis, value))
    if turns == 0:
        return value
    if turns == 1:
        return add(cross(axis, value), parallel)
    if turns == 2:
        return add(scale(value, -1), scale(parallel, 2))
    return add(scale(cross(axis, value), -1), parallel)


@dataclass(frozen=True)
class Piece:
    origin2: tuple
    a: tuple
    b: tuple
    c: tuple

    def vertices2(self):
        o, a, b, c = self.origin2, scale(self.a, 2), scale(self.b, 2), scale(self.c, 2)
        return (o, add(o, a), add(o, b), add(o, c), add(add(o, a), c), add(add(o, b), c))

    def occupancy(self):
        vertices = self.vertices2()
        cell2 = tuple(min(p[i] for p in vertices) for i in range(3))
        corners = {sum(((p[i]-cell2[i])//2) << i for i in range(3)) for p in vertices}
        missing = sorted(set(range(8)) - corners)
        edge_axis = {1: 0, 2: 1, 4: 2}[missing[0] ^ missing[1]]
        other = [i for i in range(3) if i != edge_axis]
        bits = ((missing[0] >> other[0]) & 1) | (((missing[0] >> other[1]) & 1) << 1)
        return cell2, edge_axis * 4 + bits

    def face(self, span):
        o, s, c = self.origin2, scale(span, 2), scale(self.c, 2)
        return frozenset((o, add(o, s), add(o, c), add(add(o, s), c)))


INITIAL = Piece((0, 0, 0), (1, 0, 0), (0, -1, 0), (0, 0, 1))


def advance(piece, index, turn):
    even = index % 2 == 0
    span = piece.a if even else piece.b
    axis = scale(piece.b if even else piece.a, -1)
    pivot2 = add(piece.origin2, add(span, piece.c))
    offset = add(span, scale(piece.c, -1))
    return Piece(add(pivot2, rotate(offset, axis, -turn)),
                 rotate(scale(piece.a, -1), axis, -turn),
                 rotate(scale(piece.b, -1), axis, -turn),
                 rotate(piece.c, axis, -turn))


def pieces(config):
    result = [INITIAL]
    for index, turn in enumerate(config):
        result.append(advance(result[-1], index, turn))
    return result


def complementary(kind):
    return (kind // 4) * 4 + ((kind % 4) ^ 3)


def collides(piece, occupied):
    cell, kind = piece.occupancy()
    return any(kind != complementary(other) for other in occupied.get(cell, ()))


def has_collision(placed):
    occupied = {}
    for piece in placed:
        if collides(piece, occupied):
            return True
        cell, kind = piece.occupancy()
        occupied.setdefault(cell, []).append(kind)
    return False


def endpoints_match(first, last, last_index):
    span = last.a if last_index % 2 == 0 else last.b
    normal = scale(last.b if last_index % 2 == 0 else last.a, -1)
    first_normal = scale(first.a, -1)
    return last_index > 0 and first.face(first.b) == last.face(span) and dot(first_normal, normal) == -1


def is_closed(config):
    placed = pieces(config)
    return endpoints_match(placed[0], placed[-1], len(config)) and not has_collision(placed)


def count_half_cubes(num_wedges, prefix):
    placed = pieces(prefix)
    suffix_space = 4 ** (num_wedges - 1 - len(prefix))
    if has_collision(placed):
        return 0, 0, suffix_space
    occupied = {}
    for piece in placed:
        cell, kind = piece.occupancy()
        occupied.setdefault(cell, []).append(kind)
    valid = closed = 0

    def visit(piece, index):
        nonlocal valid, closed
        if index == num_wedges - 1:
            valid += 1
            closed += endpoints_match(INITIAL, piece, index)
            return
        for turn in range(4):
            candidate = advance(piece, index, turn)
            if collides(candidate, occupied):
                continue
            cell, kind = candidate.occupancy()
            occupied.setdefault(cell, []).append(kind)
            visit(candidate, index + 1)
            occupied[cell].pop()

    visit(placed[-1], len(prefix))
    return valid, closed, suffix_space
