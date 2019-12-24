from dataclasses import dataclass
from enum import Enum
import math
import curses
from curses import wrapper
import time
import networkx as nx
from itertools import combinations, permutations

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


class MapTile(Enum):
    EMPTY = 0
    WALL = 1


class Map:
    def __init__(self):
        self.size = P(1, 1)
        self.tiles = {}
        self.default = "#"

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


def turn(direction, turn_direction):
    theta = math.radians(-90 if turn_direction == 0 else 90)
    c, s = math.cos(theta), math.sin(theta)
    return P(round(c*direction.x - s*direction.y), round(s*direction.x + c*direction.y))


def parse_map(lines):
    map = Map()
    for y, line in enumerate([l for l in lines.splitlines() if len(l)]):
        for x, c in enumerate(line):
            p = P(x, y)
            map[p] = c
    return map


def print_map(map):
    lines = []
    for y in range(map.size.y):
        line = []
        for x in range(map.size.x):
            p = P(x, y)
            c = map[p]
            line.append(c)
        lines.append("".join(line))
    return "\n".join(lines)


class VaultState:
    def __init__(self, graph, paths, size, position, keys, doors, key_history):
        self.graph = graph
        self.paths = paths
        self.size = size
        self.position = position
        self.keys = keys
        self.doors = doors
        self.key_history = key_history

    @property
    def id(self):
        return f"id-({self.position.x},{self.position.y})-" + "".join([k for k in self.keys.values()])

    @classmethod
    def from_map(cls, map):
        graph = nx.Graph()
        size = map.size
        position = None
        keys = {}
        doors = {}
        for y in range(1, map.size.y-1):
            for x in range(1, map.size.x-1):
                p = P(x, y)
                c = map[p]
                if c != '#':
                    if c == '@':
                        position = p
                    elif 'a' <= c <= 'z':
                        keys[p] = c
                    elif 'A' <= c <= 'Z':
                        doors[p] = c
                    for tp in [p+P(1, 0), p+P(-1,0), p+P(0,-1), p+P(0,1)]:
                        tc = map[tp]
                        if tc != '#':
                            graph.add_node(p)
                            graph.add_node(tp)
                            graph.add_edge(p, tp, weight = 1)
                else:
                    pass
        paths = []
        for fp, tp in combinations(keys.keys(), 2):
            for path in nx.all_shortest_paths(graph, fp, tp):
                paths.append((fp, tp, path))
                paths.append((tp, fp, path)) # nothing relies on the path pointing one way or another
        for tp in keys.keys():
            for path in nx.all_shortest_paths(graph, position, tp):
                paths.append((position, tp, path))

        return cls(graph, paths, size, position, keys, doors, [])

    def as_map(self):
        map = Map()
        map[P(0,0)] = '#'
        map[self.size+P(-1,-1)] = '#'
        for node in self.graph.nodes():
            map[node] = '.'
        map[self.position] = '@'
        for p, c in self.keys.items():
            map[p] = c
        for p, c in self.doors.items():
            map[p] = c
        return map

    def possible_moves(self):
        # find @ as the position
        paths = []
        for fp, tp, path in self.paths:
            if fp == self.position and tp in self.keys:
                blocked = False
                for u in path:
                    if u in self.doors.keys():
                        blocked = True
                if not blocked:
                    paths.append((tp, len(path)-1))
        return paths

    def move_to(self, key_position):
        key = self.keys[key_position]
        door = key.upper()
        new_keys = {p:c for p, c in self.keys.items() if p!= key_position}
        new_doors = {p:c for p, c in self.doors.items() if c!= door}
        new_key_history = self.key_history.copy()
        new_key_history.append(key)
        return VaultState(self.graph, self.paths, self.size, key_position, new_keys, new_doors, new_key_history)


def explore_moves(state, distances):
    if state.id in distances:
        return distances[state.id]
    if not state.keys:
        distances[state.id] = 0
        return 0
    min_dist = None
    for end_point, dist_to_point in state.possible_moves():
        next_state = state.move_to(end_point)
        dist_from_point_to_end = explore_moves(next_state, distances)
        if min_dist is None or (dist_to_point + dist_from_point_to_end) < min_dist:
            min_dist = dist_to_point + dist_from_point_to_end
    distances[state.id] = min_dist
    # print(f"{state.id} - {min_dist}")
    return distances[state.id]


def shortest_path_to_collect_all_keys(state):
    distances = {}
    return explore_moves(state, distances)


# s = VaultState.from_map(parse_map("""
# #########
# #b.A.@.a#
# #########
# """))
# assert shortest_path_to_collect_all_keys(s) == 8

# s = VaultState.from_map(parse_map("""
# ########################
# #f.D.E.e.C.b.A.@.a.B.c.#
# ######################.#
# #d.....................#
# ########################
# """))
# assert shortest_path_to_collect_all_keys(s) == 86

# s = VaultState.from_map(parse_map("""
# #################
# #i.G..c...e..H.p#
# ########.########
# #j.A..b...f..D.o#
# ########@########
# #k.E..a...g..B.n#
# ########.########
# #l.F..d...h..C.m#
# #################
# """))
# assert shortest_path_to_collect_all_keys(s) == 136
s = VaultState.from_map(parse_map(open("day18/input1.txt").read()))
print(shortest_path_to_collect_all_keys(s))