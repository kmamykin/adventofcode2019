from dataclasses import dataclass
import networkx as nx
from itertools import combinations, permutations, chain, groupby


@dataclass
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

    def __hash__(self):
        return self.x*100+self.y

    def __repr__(self):
        return f"(x={self.x}, y={self.y})"


def P(x, y) -> Point:
    return Point(x, y)


class Map:
    def __init__(self, init_size=P(1,1)):
        self.size = init_size
        self.tiles = {}
        self.default = " "

    def _update_boundary(self, point: Point):
        max_y = max(abs(self.size.y), abs(point.y)+1)
        max_x = max(abs(self.size.x), abs(point.x)+1)
        self.size = P(max_x, max_y)

    def _set_panel_value(self, point: Point, value):
        if not point.x in self.tiles:
            self.tiles[point.x] = {}
        self.tiles[point.x][point.y] = value

    def _panel_exists(self, point: Point):
        return (point.x in self.tiles) and (point.y in self.tiles[point.x])

    def __getitem__(self, point: Point):
        self._update_boundary(point)
        return self.tiles[point.x][point.y] if self._panel_exists(point) else self.default

    def __setitem__(self, point: Point, value):
        self._update_boundary(point)
        self._set_panel_value(point, value)


def node(level, point):
    return f"l{level}-{point}"


class Maze:
    def __init__(self, graph, portals, aa, zz):
        self.graph = graph
        self.portals = portals
        self.aa = aa
        self.zz = zz

    @classmethod
    def parse(cls, lines, size, hole_position, hole_size):

        def fill_map(size, lines):
            map = Map(init_size=size)
            for y, line in enumerate([l for l in lines.splitlines() if len(l)]):
                line = line.ljust(size.x)
                for x, c in enumerate(line):
                    p = P(x, y)
                    map[p] = c
            return map

        def detect_teleports(map, xit, yit, first_letter_offset, secont_letter_offset):
            for x in xit:
                for y in yit:
                    p = P(x, y)
                    c = map[p]
                    fl = map[p+first_letter_offset]
                    sl = map[p+secont_letter_offset]
                    if c == '.' and 'A' <= fl <= 'Z' and 'A' <= sl <= 'Z':
                        yield fl+sl, p

        def detect_portals(map, hole_position, hole_size):
            tl = hole_position + P(-1, -1)
            br = hole_position + hole_size
            tr = P(br.x, tl.y)
            bl = P(tl.x, br.y)
            outer_portals = list(chain(
                detect_teleports(map, range(2, size.x - 2), [2], P(0, -2), P(0, -1)),  # top
                detect_teleports(map, range(2, size.x - 2), [size.y - 3], P(0, 1), P(0, 2)),  # bottom
                detect_teleports(map, [2], range(2, size.y - 2), P(-2, 0), P(-1, 0)),  # left
                detect_teleports(map, [size.x - 3], range(2, size.y - 2), P(1, 0), P(2, 0)),  # right
            ))
            outer_portals = [(k, p, 'outer') for k, p in outer_portals]
            inner_portals = list(chain(
                detect_teleports(map, range(tl.x, tr.x), [tl.y], P(0, 1), P(0, 2)),  # top
                detect_teleports(map, range(bl.x, br.x), [br.y], P(0, -2), P(0, -1)),  # bottom
                detect_teleports(map, [tl.x], range(tl.y, bl.y), P(1, 0), P(2, 0)),  # left
                detect_teleports(map, [tr.x], range(tr.y, br.y), P(-2, 0), P(-1, 0)),  # right
            ))
            inner_portals = [(k, p, 'inner') for k, p in inner_portals]

            st = sorted(chain(outer_portals, inner_portals), key=lambda t: t[0])
            portals = {k: list(grp) for k, grp in groupby(st, key=lambda t: t[0])}
            aa = portals['AA'][0]
            zz = portals['ZZ'][0]
            portals.pop('AA')
            portals.pop('ZZ')
            return aa, zz, portals

        def build_level(g, map, level):
            for y in range(1, map.size.y - 1):
                for x in range(1, map.size.x - 1):
                    p = P(x, y)
                    c = map[p]
                    if c == '.':
                        for tp in [p + P(1, 0), p + P(-1, 0), p + P(0, -1), p + P(0, 1)]:
                            tc = map[tp]
                            if tc == '.':
                                g.add_edge(node(level, p), node(level, tp), weight=1)

        def add_portal_connections(g, portals, fl, tl):
            for k, (p1, p2) in portals.items():
                if p1[2] == 'outer' and p2[2] == 'outer':
                    g.add_edge(node(tl, p1[1]), node(tl, p2[1]), weight=1)
                if p1[2] == 'inner':
                    g.add_edge(node(fl, p1[1]), node(tl, p2[1]), weight=1)
                if p2[2] == 'inner':
                    g.add_edge(node(fl, p2[1]), node(tl, p1[1]), weight=1)

        map = fill_map(size, lines)
        aa, zz, portals = detect_portals(map, hole_position, hole_size)
        graph = nx.Graph()
        build_level(graph, map, 0)
        for level in range(1, 100):
            build_level(graph, map, level)
            add_portal_connections(graph, portals, level-1, level)
        return cls(graph, portals, aa, zz)

    def shortest_path(self):
        start_point = node(0, self.aa[1])
        end_point = node(0, self.zz[1])
        return nx.shortest_path_length(self.graph, start_point, end_point, weight='weight')

    def path(self, f, t):
        return nx.shortest_path(self.graph, f, t)

    # def __getitem__(self, item):
    #     points = self.teleports[item]
    #     if len(points) == 2:
    #         if points[0].y > points[1].y:
    #             return points[1], points[0]
    #         elif points[0].y < points[1].y:
    #             return points[0], points[1]
    #         else:
    #             return points[0], points[1]
    #     else:
    #         return points

# s = Maze.parse("""
#          A
#          A
#   #######.#########
#   #######.........#
#   #######.#######.#
#   #######.#######.#
#   #######.#######.#
#   #####  B    ###.#
# BC...##  C    ###.#
#   ##.##       ###.#
#   ##...DE  F  ###.#
#   #####    G  ###.#
#   #########.#####.#
# DE..#######...###.#
#   #.#########.###.#
# FG..#########.....#
#   ###########.#####
#              Z
#              Z
# """, size=P(21, 19), hole_position=P(7,7), hole_size=P(7, 5))
# assert s.shortest_path() == 26

# s = Maze.parse("""
#                    A
#                    A
#   #################.#############
#   #.#...#...................#.#.#
#   #.#.#.###.###.###.#########.#.#
#   #.#.#.......#...#.....#.#.#...#
#   #.#########.###.#####.#.#.###.#
#   #.............#.#.....#.......#
#   ###.###########.###.#####.#.#.#
#   #.....#        A   C    #.#.#.#
#   #######        S   P    #####.#
#   #.#...#                 #......VT
#   #.#.#.#                 #.#####
#   #...#.#               YN....#.#
#   #.###.#                 #####.#
# DI....#.#                 #.....#
#   #####.#                 #.###.#
# ZZ......#               QG....#..AS
#   ###.###                 #######
# JO..#.#.#                 #.....#
#   #.#.#.#                 ###.#.#
#   #...#..DI             BU....#..LF
#   #####.#                 #.#####
# YN......#               VT..#....QG
#   #.###.#                 #.###.#
#   #.#...#                 #.....#
#   ###.###    J L     J    #.#.###
#   #.....#    O F     P    #.#...#
#   #.###.#####.#.#####.#####.###.#
#   #...#.#.#...#.....#.....#.#...#
#   #.#####.###.###.#.#.#########.#
#   #...#.#.....#...#.#.#.#.....#.#
#   #.###.#####.###.###.#.#.#######
#   #.#.........#...#.............#
#   #########.###.###.#############
#            B   J   C
#            U   P   P
# """, size=P(35, 37), hole_position=P(9,9), hole_size=P(17, 19))
# # print(list(s.graph.nodes()))
# # print(list(s.graph.edges()))
# # print(s.path(P(19,2), P(17, 8))) ## AA AS
# # print(s.path(P(19,2), P(32, 17))) ## AA AS
# assert s.shortest_path() == 58

# s = Maze.parse(open("day20/input1.txt").read(), size=P(121, 125), hole_position=P(33,33), hole_size=P(55, 59))
# print(s.shortest_path())

# s = Maze.parse("""
#              Z L X W       C
#              Z P Q B       K
#   ###########.#.#.#.#######.###############
#   #...#.......#.#.......#.#.......#.#.#...#
#   ###.#.#.#.#.#.#.#.###.#.#.#######.#.#.###
#   #.#...#.#.#...#.#.#...#...#...#.#.......#
#   #.###.#######.###.###.#.###.###.#.#######
#   #...#.......#.#...#...#.............#...#
#   #.#########.#######.#.#######.#######.###
#   #...#.#    F       R I       Z    #.#.#.#
#   #.###.#    D       E C       H    #.#.#.#
#   #.#...#                           #...#.#
#   #.###.#                           #.###.#
#   #.#....OA                       WB..#.#..ZH
#   #.###.#                           #.#.#.#
# CJ......#                           #.....#
#   #######                           #######
#   #.#....CK                         #......IC
#   #.###.#                           #.###.#
#   #.....#                           #...#.#
#   ###.###                           #.#.#.#
# XF....#.#                         RF..#.#.#
#   #####.#                           #######
#   #......CJ                       NM..#...#
#   ###.#.#                           #.###.#
# RE....#.#                           #......RF
#   ###.###        X   X       L      #.#.#.#
#   #.....#        F   Q       P      #.#.#.#
#   ###.###########.###.#######.#########.###
#   #.....#...#.....#.......#...#.....#.#...#
#   #####.#.###.#######.#######.###.###.#.#.#
#   #.......#.......#.#.#.#.#...#...#...#.#.#
#   #####.###.#####.#.#.#.#.###.###.#.###.###
#   #.......#.....#.#...#...............#...#
#   #############.#.#.###.###################
#                A O F   N
#                A A D   M
# """, size=P(45, 37), hole_position=P(9,9), hole_size=P(27, 19))
# assert s.shortest_path() == 396


s = Maze.parse(open("day20/input1.txt").read(), size=P(121, 125), hole_position=P(33,33), hole_size=P(55, 59))
print(s.shortest_path())
