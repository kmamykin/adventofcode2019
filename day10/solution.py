import math
from dataclasses import dataclass



@dataclass(eq=True)
class Point:
    x: int
    y: int

    def __getitem__(self, item):
        return self.x if item == 0 else self.y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, other: int):
        return Point(self.x * other, self.y * other)

    def distance(self, other):
        d = self - other
        return pow(pow(d.x, 2) + pow(d.y, 2), 0.5)

    def is_inline(self, p1, p2):
        if (self.x == p1.x == p2.x) or (self.y == p1.y == p2.y):
            return True
        return math.isclose(p1.distance(p2) + p2.distance(self), p1.distance(self))

    def is_between(self, p1, p2):
        return (min(p1.x, p2.x) <= self.x <= max(p1.x, p2.x)) and (min(p1.y, p2.y) <= self.y <= max(p1.y, p2.y))

    def is_blocked(self, p1, p2):
        return self.is_inline(p1, p2) and p2.is_between(p1, self) and p1.distance(self) > p1.distance(p2)


def P(x, y) -> Point:
    return Point(x, y)


@dataclass
class Map:
    width: int
    height: int
    positions: [[]]

    def __post_init__(self):
        self.lines_of_sight = LineOfSight.generate_all_line_of_sites(self.width, self.height)

    def __getitem__(self, position: Point):
        return self.positions[position[1]][position[0]]

    def __setitem__(self, position: Point, value):
        self.positions[position[1]][position[0]] = value

    def each_position(self):
        for w in range(self.width):
            for h in range(self.height):
                yield P(w, h)

    def each_asteroid(self):
        for c in self.each_position():
            if self[c]:
                yield c

    def contains_asteroid(self, position):
        return self[position]  # it contains bools for now

    def within_boundaries(self, position):
        return (0 <= position[0] < self.width) and (0 <= position[1] < self.height)

    def visibility_at(self, position):
        visibility_map = self.copy()
        visible_nodes = self.empty(default=False)
        visibility_count = 0  # self is visible
        for ls in self.lines_of_sight:
            lst = ls.transpose(position)
            first_found = False
            for p in lst.points:
                if visibility_map.within_boundaries(p):
                    if visibility_map[p] and not first_found:
                        visibility_count += 1
                        first_found = True
                        visible_nodes[p] = True
                    elif visibility_map[p] and first_found:
                        visibility_map[p] = False
        # print(visible_nodes.encode(sep="", printer=lambda c: "#" if c else "."))
        # print("\n")
        return visibility_count, visibility_map

    def copy(self):
        return Map(self.width, self.height, [l.copy() for l in self.positions])

    def empty(self, default=None):
        return Map(self.width, self.height, [[default] * self.width for h in range(self.height)])

    def visibility(self):
        visibility_map = self.empty(default=0)
        for position in self.each_asteroid():
            visibility, _ = self.visibility_at(position)
            visibility_map[position] = visibility
        return visibility_map

    def encode(self, sep=",", printer=lambda c: f"{c}"):
        return "\n".join([sep.join([printer(self[P(w, h)]) for w in range(self.width)]) for h in range(self.height)])

    def best_location(self) -> ((int, int), int):
        visibility_map = self.visibility()
        max_visibility = -1
        max_visibility_position = None
        for position in self.each_asteroid():
            visibility = visibility_map[position]
            if visibility >= max_visibility:
                max_visibility = visibility
                max_visibility_position = position
        return max_visibility_position, max_visibility

    def shoot_asteroids(self, from_position, number):
        map = self.copy()
        lost = [los.transpose(from_position) for los in self.lines_of_sight]
        asteroids = []
        while True:
            for los in lost:
                for p in los.points:
                    if map.within_boundaries(p) and map[p]:
                        asteroids.append(p)
                        map[p] = False
                        break
                    if len(asteroids) >= number:
                        return asteroids


    @classmethod
    def parse(cls, multiline_map_encoding):
        lines = [line.strip() for line in multiline_map_encoding.splitlines() if len(line.strip())]
        assert all([len(l1) == len(l2) for l1, l2 in zip(lines[1:], lines[:-1])])
        width = len(lines[0])
        height = len(lines)
        positions = [[c == '#' for c in line] for line in lines]
        return Map(width, height, positions)


@dataclass
class LineOfSight:
    origin: Point
    dest: Point
    points: [Point]

    def transpose(self, point):
        return LineOfSight(self.origin + point, self.dest + point, [p + point for p in self.points])

    @property
    def angle(self):
        deg = math.degrees(math.atan2(self.dest.x, -self.dest.y))
        return 360 + deg if deg < 0 else deg

    def __eq__(self, other):
        return self.angle == other.angle

    def __hash__(self):
        return hash(self.angle)

    @classmethod
    def to(cls, dest):
        origin = P(0,0)
        n = math.gcd(dest.x, dest.y)
        increment = P(dest.x//n, dest.y//n)
        return cls(origin, dest, [increment*(i+1) for i in range(n)])

    @classmethod
    def walk_border_clockwise(cls, width, height):
        # assume origin at (0,0) on the board of size (2*width-1, 2*height-1)
        st = P(0,-height+1)
        tr = P(width-1, -height+1)
        br = P(width-1, height-1)
        bl = P(-width+1, height-1)
        tl = P(-width+1, -height+1)

        for i in range(st.x, tr.x):
            yield P(i, tr.y)
        for i in range(tr.y, br.y):
            yield P(tr.x, i)
        for i in range(br.x, bl.x, -1):
            yield P(i, br.y)
        for i in range(bl.y, tl.y, -1):
            yield P(bl.x, i)
        for i in range(tl.x, st.x):
            yield P(i, -height+1)

    @classmethod
    def generate_all_line_of_sites(cls, width, height):
        # for p in cls.walk_border_clockwise(width, height):
        #     yield cls.to(p)
        loss = []
        p1 = None
        for x in range(-width+1, width):
            for y in range(-height+1, height):
                if x == 0 and y == 0:
                    continue
                p = P(x, y)
                for i in range(2, 1000):
                    p1 = p * i
                    if abs(p1.x) >= width or abs(p1.y) >= height:
                        break
                loss.append(LineOfSight.to(p1))
        uniq = list(set(loss))
        return list(sorted(uniq, key= lambda los: los.angle))

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
assert m[P(0, 0)] == False
assert m[P(1, 0)] == True
assert m[P(0, 1)] == False
assert m[P(4, 4)] == True

assert m.contains_asteroid(P(1, 0))
assert m.contains_asteroid(P(4, 0))
assert not m.contains_asteroid(P(1, 1))

assert m.within_boundaries(P(0, 0))
assert not m.within_boundaries(P(-1, 0))
assert not m.within_boundaries(P(0, -1))
assert m.within_boundaries(P(4, 4))
assert not m.within_boundaries(P(5, 4))
assert not m.within_boundaries(P(4, 5))

# assert is_between(P(1, 2), P(0, 2), P(2, 2))
# assert is_between(P(1, 2), P(2, 2), P(0, 2))
# assert is_blocked(P(0, 2), P(2, 2), P(1, 2))

# """
# .7..7
# .....
# 67775
# ....7
# ...87
# """
# print(m.visibility_at(P(1,0))[1].encode(sep="", printer=lambda c: "#" if c else "."))
assert m.visibility_at(P(1, 0))[0] == 7
assert m.visibility_at(P(4, 0))[0] == 7
assert m.visibility_at(P(0, 2))[0] == 6
assert m.visibility_at(P(1, 2))[0] == 7
assert m.visibility_at(P(2, 2))[0] == 7
assert m.visibility_at(P(3, 2))[0] == 7
# print(m.visibility_at((4,2))[1].encode(sep="", printer=lambda c: "#" if c else "."))
assert m.visibility_at(P(4, 3))[0] == 7
assert m.visibility_at(P(3, 4))[0] == 8
assert m.visibility_at(P(4, 4))[0] == 7

assert m.best_location() == (P(3, 4), 8)

assert list(LineOfSight.walk_border_clockwise(2, 2)) == [P(0,-1), P(1,-1), P(1,0), P(1,1), P(0,1), P(-1,1), P(-1,0), P(-1,-1)]

assert LineOfSight.to(P(16,4)).points == [Point(x=4, y=1), Point(x=8, y=2), Point(x=12, y=3), Point(x=16, y=4)]
assert LineOfSight.to(P(-16,-4)).points == [Point(x=-4, y=-1), Point(x=-8, y=-2), Point(x=-12, y=-3), Point(x=-16, y=-4)]

assert LineOfSight.to(P(0, -1)).angle == 0
assert LineOfSight.to(P(1, -1)).angle == 45
assert LineOfSight.to(P(1, 0)).angle == 90
assert LineOfSight.to(P(1, 1)).angle == 135
assert LineOfSight.to(P(0, 1)).angle == 180
assert LineOfSight.to(P(-1, 1)).angle == 225
assert LineOfSight.to(P(-1, 0)).angle == 270
assert LineOfSight.to(P(-1, -1)).angle == 315

# print([los.angle for los in LineOfSight.generate_all_line_of_sites(3, 3)])
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

# assert Map.parse("""
# ......#.#.
# #..#.#....
# ..#######.
# .#.#.###..
# .#..#.....
# ..#....#.#
# #..#....#.
# .##.#..###
# ##...#..#.
# .#....####
# """).best_location() == (P(5, 8), 33)
#
#
# assert Map.parse("""
# #.#...#.#.
# .###....#.
# .#....#...
# ##.#.#.#.#
# ....#.#.#.
# .##..###.#
# ..#...##..
# ..##....##
# ......#...
# .####.###.
# """).best_location() == (P(1, 2), 35)
#
# assert Map.parse("""
# .#..#..###
# ####.###.#
# ....###.#.
# ..###.##.#
# ##.##.#.#.
# ....###..#
# ..#.#..#.#
# #..#.#.###
# .##...##.#
# .....#.#..
# """).best_location() == (P(6, 3), 41)

m1 = Map.parse("""
.#..##.###...#######
##.############..##.
.#.######.########.#
.###.#######.####.#.
#####.##.#.##.###.##
..#####..#.#########
####################
#.####....###.#.#.##
##.#################
#####.##.###..####..
..######..##.#######
####.##.####...##..#
.#####..#.######.###
##...#.##########...
#.##########.#######
.####.#.###.###.#.##
....##.##.###..#####
.#.#.###########.###
#.#.#.#####.####.###
###.##.####.##.#..##
""")
# assert m2.best_location() == (P(11, 13), 210)
# # 11,13 with 210

def pretty_print_asteroids(asteroids):
    for i, p in enumerate(asteroids):
        print(f"The {i+1} asteroid to be vaporized is at {p.x},{p.y}.")

# pretty_print_asteroids(m1.shoot_asteroids(P(11, 13), 200))

input1 = open("day10/input1.txt").read()
m2 = Map.parse(input1)
best_loc2 = m2.best_location()
print(best_loc2)
pretty_print_asteroids(m2.shoot_asteroids(best_loc2[0], 200))
