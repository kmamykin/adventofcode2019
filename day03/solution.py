from dataclasses import dataclass
from functools import reduce

@dataclass
class Point:
    x: int
    y: int


@dataclass
class Segment:
    start: Point
    end: Point

    def is_horizontal(self):
        return self.start.y == self.end.y

    def is_vertical(self):
        return self.start.x == self.end.x

    def normalized(self):
        if self.is_horizontal() and self.start.x > self.end.x:
            return Segment(self.end, self.start)
        elif self.is_vertical() and self.start.y > self.end.y:
            return Segment(self.end, self.start)
        else:
            return self # Should never be the case, only horizontal or vertical segments exist because of directions are R, L, U, D

    def overlap_points(self, another_segment) -> [Point]:
        s1 = self.normalized()
        s2 = another_segment.normalized()
        if s1.is_vertical() and s2.is_vertical() and s1.start.x == s2.start.x:
            return [Point(s1.start.x,i) for i in range(max(s1.start.y, s2.start.y), min(s1.end.y, s2.end.y)+1)]
        if s1.is_horizontal() and s2.is_horizontal() and s1.start.y == s2.start.y:
            return [Point(i, s1.start.y) for i in range(max(s1.start.x, s2.start.x), min(s1.end.x, s2.end.x)+1)]
        # one is vertical another is horizontal, only one intersection possible
        if s1.is_horizontal() and s2.is_vertical() and (s1.start.x <= s2.start.x <= s1.end.x) and (s2.start.y <= s1.start.y <= s2.end.y):
            return [Point(s2.start.x, s1.start.y)]
        if s1.is_vertical() and s2.is_horizontal() and (s2.start.x <= s1.start.x <= s2.end.x) and (s1.start.y <= s2.start.y <= s1.end.y):
            return [Point(s1.start.x, s2.start.y)]
        return []

    def contains(self, p: Point) -> bool:
        norm_self = self.normalized()
        return (
            ((norm_self.start.x <= p.x <= norm_self.end.x) and (norm_self.start.y == norm_self.end.y == p.y)) or
            ((norm_self.start.y <= p.y <= norm_self.end.y) and (norm_self.start.x == norm_self.end.x == p.x))
        )

    def steps(self) -> int:
        return manhattan_distance(self.start, self.end)

    def steps_to_point(self, p: Point) -> int:
        if self.contains(p):
            return manhattan_distance(self.start, p)
        else:
            return None


class Path:
    def __init__(self, segments, starting_point = Point(0,0)):
        self.segments = segments
        self.start = starting_point

    @classmethod
    def from_instructions(cls, wire: str, starting_point: Point):
        moving_instructions = [(i[0], int(i[1:])) for i in [e.strip() for e in wire.split(',')]]
        instruction_to_points = {
            'R': lambda i: Point(i, 0),
            'L': lambda i: Point(-i, 0),
            'U': lambda i: Point(0, i),
            'D': lambda i: Point(0, -i)
        }
        points = [instruction_to_points[direction](num) for direction, num in moving_instructions]

        def to_segment_combiner(acc, p):
            segment_end = Point(acc[1].x + p.x, acc[1].y + p.y)
            return acc[0] + [Segment(acc[1], segment_end)], segment_end

        segments = reduce(to_segment_combiner, points, ([], starting_point))[0]
        return Path(segments, starting_point)

    def steps_to_point(self, p: Point):
        steps = 0
        for segment in self.segments:
            if segment.contains(p):
                return steps + segment.steps_to_point(p)
            else:
                steps += segment.steps()
        return None

def segment_intersection(s1, s2):
    return s1.overlap_points(s2)


def find_intersections(path1: Path, path2: Path) -> [Point]:
    intersections = []
    for s1 in path1.segments:
        for s2 in path2.segments:
            intersections += segment_intersection(s1, s2)
    return intersections


def manhattan_distance(p1: Point, p2: Point) -> int:
    return abs(p2.x - p1.x) + abs(p2.y - p1.y)


def find_intersection_with_min_distance(wire1: str, wire2: str) -> int:
    path1 = Path.from_instructions(wire1, Point(0, 0))
    path2 = Path.from_instructions(wire2, Point(0, 0))
    intersections = find_intersections(path1, path2)
    intersections = [p for p in intersections if not p == Point(0,0)]
    return min([manhattan_distance(Point(0,0), point) for point in intersections])


def find_intersection_with_min_number_of_steps(wire1: str, wire2: str) -> (Point, int):
    path1 = Path.from_instructions(wire1, Point(0, 0))
    path2 = Path.from_instructions(wire2, Point(0, 0))
    intersections = find_intersections(path1, path2)
    intersections = [p for p in intersections if not p == Point(0,0)]
    steps_to_intersections1 = [path1.steps_to_point(i) for i in intersections]
    steps_to_intersections2 = [path2.steps_to_point(i) for i in intersections]
    steps_to_intersections = [d1 + d2 for d1, d2 in zip(steps_to_intersections1, steps_to_intersections2)]
    min_steps_index = steps_to_intersections.index(min(steps_to_intersections))
    return intersections[min_steps_index], steps_to_intersections[min_steps_index]


test1 = {
    "1": "R75,D30,R83,U83,L12,D49,R71,U7,L72",
    "2": "U62,R66,U55,R34,D71,R55,D58,R83",
    "distance": 159
}
test2 = {
    "1": "R98,U47,R26,D63,R33,U87,L62,D20,R33,U53,R51",
    "2": "U98,R91,D20,R16,D67,R40,U7,R15,U6,R7",
    "distance": 135
}

assert Path.from_instructions("R8", Point(0,0)).segments == [Segment(Point(0,0), Point(8,0))]
assert Path.from_instructions("R8,U5", Point(0,0)).segments == [Segment(Point(0,0), Point(8,0)), Segment(Point(8,0), Point(8,5))]
assert Path.from_instructions("R8,U5,L5,D3", Point(0,0)).segments == [Segment(Point(0,0), Point(8,0)), Segment(Point(8,0), Point(8,5)), Segment(Point(8,5), Point(3,5)), Segment(Point(3,5), Point(3,2))]
assert manhattan_distance(Point(0,0), Point(2,3)) == 5
assert manhattan_distance(Point(-1,-1), Point(2,3)) == 7
assert segment_intersection(Segment(Point(0,0), Point(0,2)), Segment(Point(1,0), Point(1,2))) == []
assert segment_intersection(Segment(Point(0,0), Point(0,2)), Segment(Point(-1,1), Point(1,1))) == [Point(0,1)]
assert find_intersection_with_min_distance(test1["1"], test1["2"]) == test1["distance"]
assert find_intersection_with_min_distance(test2["1"], test2["2"]) == test2["distance"]

print(segment_intersection(Segment(Point(0,0), Point(0,5)), Segment(Point(0,7), Point(0,5))))
lines = open("./day03/input.txt").readlines()
print(find_intersection_with_min_distance(lines[0], lines[1]))

assert find_intersection_with_min_number_of_steps("R75,D30,R83,U83,L12,D49,R71,U7,L72", "U62,R66,U55,R34,D71,R55,D58,R83")[1] == 610
assert find_intersection_with_min_number_of_steps("R98,U47,R26,D63,R33,U87,L62,D20,R33,U53,R51", "U98,R91,D20,R16,D67,R40,U7,R15,U6,R7")[1] == 410
print(find_intersection_with_min_number_of_steps(lines[0], lines[1]))