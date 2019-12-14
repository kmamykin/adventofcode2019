from dataclasses import dataclass
import math

def diff(p1, p2):
    return p2[0] - p1[0], p2[1] - p1[1]

def distance(p1, p2):
    d = diff(p1, p2)
    return pow(pow(d[0], 2) + pow(d[1], 2), 0.5)

def is_inline(p, p1, p2):
    if (p[0] == p1[0] == p2[0]) or (p[1] == p1[1] == p2[1]):
        return True
    return math.isclose(distance(p1, p2) + distance(p2, p), distance(p1, p))

def is_between(p, p1, p2):
    return (min(p1[0], p2[0]) <= p[0] <= max(p1[0], p2[0])) and (min(p1[1], p2[1]) <= p[1] <= max(p1[1], p2[1]))

def is_blocked(p, p1, p2):
    return is_inline(p, p1, p2) and is_between(p2, p1, p) and distance(p1, p) > distance(p1, p2)

@dataclass
class Map:
    width: int
    height: int
    positions: [[]]

    def __getitem__(self, position: (int, int)):
        return self.positions[position[1]][position[0]]

    def __setitem__(self, position: (int, int), value):
        self.positions[position[1]][position[0]] = value

    def each_cell(self):
        for w in range(self.width):
            for h in range(self.height):
                yield (w, h)

    def each_asteroid(self):
        for c in self.each_cell():
            if self[c]:
                yield c

    def expanding_from(self, position):
        already_visited = self.empty(default=False)
        for distance in range(1, max(self.width, self.height)):
            if self.within_boundaries((position[0], position[1] - distance)): # top
                for i in range(position[0]-distance, position[0]+distance+1):
                    p = (i, position[1] - distance)
                    if self.within_boundaries(p) and not already_visited[p]:
                        already_visited[p] = True
                        yield p
            if self.within_boundaries((position[0] - distance, position[1])): # left
                for i in range(position[1]-distance, position[1]+distance+1):
                    p = (position[0] - distance, i)
                    if self.within_boundaries(p) and not already_visited[p]:
                        already_visited[p] = True
                        yield p
            if self.within_boundaries((position[0] + distance, position[1])): # right
                for i in range(position[1]-distance, position[1]+distance+1):
                    p = (position[0] + distance, i)
                    if self.within_boundaries(p) and not already_visited[p]:
                        already_visited[p] = True
                        yield p
            if self.within_boundaries((position[0], position[1] + distance)): # bottom
                for i in range(position[0]-distance, position[0]+distance+1):
                    p = (i, position[1] + distance)
                    if self.within_boundaries(p) and not already_visited[p]:
                        already_visited[p] = True
                        yield p

    def blocked(self, from_p, to_p):
        for p in self.expanding_from(from_p):
            if is_blocked(p, from_p, to_p):
                yield p

    def contains_asteroid(self, position):
        return self[position] # it contains bools for now

    def within_boundaries(self, position):
        return (0 <= position[0] < self.width) and (0 <= position[1] < self.height)

    def visibility_at(self, position):
        visibility_map = self.copy()
        visibility_count = 0 # self is visible
        for p in visibility_map.expanding_from(position):
            if visibility_map.contains_asteroid(p):
                visibility_count +=1
                for b in visibility_map.blocked(position, p):
                    visibility_map[b] = False
                #print(f"from {position} visible {p}")
                #print(visibility_map.encode(sep="", printer=lambda c: "#" if c else "."))
        return visibility_count, visibility_map

    def copy(self):
        return Map(self.width, self.height, [l.copy() for l in self.positions])

    def empty(self, default=None):
        return Map(self.width, self.height, [[default]*self.width for h in range(self.height)])

    def visibility(self):
        visibility_map = self.empty(default=0)
        for position in self.each_asteroid():
            visibility, _ = self.visibility_at(position)
            visibility_map[position] = visibility
        return visibility_map

    def encode(self, sep = ",", printer = lambda c: f"{c}"):
        return "\n".join([sep.join([printer(self[w,h]) for w in range(self.width)]) for h in range(self.height)])

    def best_location(self) -> ((int, int), int):
        visibility_map = self.visibility()
        max_visibility = -1
        max_visibility_position = None
        for position in visibility_map.each_cell():
            visibility = visibility_map[position]
            if visibility >= max_visibility:
                max_visibility = visibility
                max_visibility_position = position
        return max_visibility_position, max_visibility

    @classmethod
    def parse(cls, multiline_map_encoding):
        lines = [line.strip() for line in multiline_map_encoding.splitlines() if len(line.strip())]
        assert all([len(l1) == len(l2) for l1, l2 in zip(lines[1:], lines[:-1])])
        width = len(lines[0])
        height = len(lines)
        positions = [[c == '#' for c in line] for line in lines]
        return Map(width, height, positions)



# Map accessors
m = Map.parse("""
.#..#
.....
#####
....#
...##
""")
assert m.width == 5
assert m.height == 5
assert m[(0,0)] == False
assert m[(1,0)] == True
assert m[(0,1)] == False
assert m[(4,4)] == True

assert m.contains_asteroid((1, 0))
assert m.contains_asteroid((4, 0))
assert not m.contains_asteroid((1, 1))

assert m.within_boundaries((0,0))
assert not m.within_boundaries((-1,0))
assert not m.within_boundaries((0,-1))
assert m.within_boundaries((4,4))
assert not m.within_boundaries((5,4))
assert not m.within_boundaries((4,5))

assert list(m.expanding_from((2,2)))[:8] == [(1, 1), (2, 1), (3, 1), (1, 2), (1, 3), (3, 2), (3, 3), (2, 3)]
assert list(m.expanding_from((0,0)))[:8] == [(1, 0), (1, 1), (0, 1), (2, 0), (2, 1), (2, 2), (0, 2), (1, 2)]

assert is_between((1,2), (0,2), (2,2))
assert is_between((1,2), (2,2), (0,2))
assert is_blocked((0,2), (2,2), (1,2))
assert list(m.blocked((0,0), (1,0))) == [(2,0),(3,0),(4,0)]
assert list(m.blocked((0,0), (0,1))) == [(0,2),(0,3),(0,4)]
assert list(m.blocked((0,0), (1,1))) == [(2,2),(3,3),(4,4)]
assert list(m.blocked((0,0), (2,1))) == [(4,2)]
assert list(m.blocked((0,0), (3,0))) == [(4,0)]
assert list(m.blocked((0,0), (3,3))) == [(4,4)]

# """
# .7..7
# .....
# 67775
# ....7
# ...87
# """
# print(m.visibility().encode())
assert m.visibility_at((1,0))[0] == 7
assert m.visibility_at((4,0))[0] == 7
assert m.visibility_at((0,2))[0] == 6
assert m.visibility_at((1,2))[0] == 7
assert m.visibility_at((2,2))[0] == 7
assert m.visibility_at((3,2))[0] == 7
# print(m.visibility_at((4,2))[1].encode(sep="", printer=lambda c: "#" if c else "."))
assert m.visibility_at((4,3))[0] == 7
assert m.visibility_at((3,4))[0] == 8
assert m.visibility_at((4,4))[0] == 7

assert m.best_location() == ((3,4), 8)

# """
# #.........
# ...A......
# ...B..a...
# .EDCG....a
# ..F.c.b...
# .....c....
# ..efd.c.gb
# .......c..
# ....f...c.
# ...e..d..c
# """
#

assert Map.parse("""
......#.#.
#..#.#....
..#######.
.#.#.###..
.#..#.....
..#....#.#
#..#....#.
.##.#..###
##...#..#.
.#....####
""").best_location() == ((5, 8), 33)


assert Map.parse("""
#.#...#.#.
.###....#.
.#....#...
##.#.#.#.#
....#.#.#.
.##..###.#
..#...##..
..##....##
......#...
.####.###.
""").best_location() == ((1, 2), 35)

assert Map.parse("""
.#..#..###
####.###.#
....###.#.
..###.##.#
##.##.#.#.
....###..#
..#.#..#.#
#..#.#.###
.##...##.#
.....#.#..
""").best_location() == ((6, 3), 41)

# assert Map.parse("""
# .#..##.###...#######
# ##.############..##.
# .#.######.########.#
# .###.#######.####.#.
# #####.##.#.##.###.##
# ..#####..#.#########
# ####################
# #.####....###.#.#.##
# ##.#################
# #####.##.###..####..
# ..######..##.#######
# ####.##.####...##..#
# .#####..#.######.###
# ##...#.##########...
# #.##########.#######
# .####.#.###.###.#.##
# ....##.##.###..#####
# .#.#.###########.###
# #.#.#.#####.####.###
# ###.##.####.##.#..##
# """).best_location() == ((11, 13), 210)
# # # 11,13 with 210

input1 = open("day10/input1.txt").read()
print(Map.parse(input1).best_location())
