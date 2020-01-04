from dataclasses import dataclass

@dataclass
class State:
    levels: []
    depth: int
    height: int
    width : int

    def __repr__(self):
        s = ""
        for l in range(self.depth):
            s += "\n".join([''.join(self.levels[l][y]) for y in range(self.height)])
            s += "\n\n"
        return s

    # def __eq__(self, other):
    #     return str(self) == str(other)
    #
    # def __hash__(self):
    #     return hash(str(self))

    def get(self, l, x, y):
        if 0 <= x < 5 and 0 <= y < 5 and 0 <= l < self.depth:
            return self.levels[l][y][x]
        else:
            return '.'

    def adjacency(self, l, x, y):
        adjacency_rules = {
            1: [(1, 2, 1), (1, 1, 2), (0, 1, 0), (0, 0, 1)],
            2: [(1, 1, 1), (0, -1, 0), (0, 1, 0), (0, 0, 1)],
            3: [(1, 0, 1), (0, -1, 0), (0, 1, 0), (0, 0, 1)],
            4: [(1, -1, 1), (0, -1, 0), (0, 1, 0), (0, 0, 1)],
            5: [(1, -2, 1), (1, -1, 2), (0, -1, 0), (0, 0, 1)],

            6: [(1, 1, 1), (0, 0, -1), (0, 0, 1), (0, 1, 0)],
            7: [(0, -1, 0), (0, 0, -1), (0, 0, 1), (0, 1, 0)],
            8: [(0, -1, 0), (0, 0, -1), (0, 1, 0), (-1, -2, -1), (-1, -1, -1), (-1, 0, -1), (-1, 1, -1), (-1, 2, -1)],
            9: [(0, -1, 0), (0, 0, -1), (0, 0, 1), (0, 1, 0)],
            10: [(1, -1, 1), (0, 0, -1), (0, 0, 1), (0, -1, 0)],

            11: [(1, 1, 0), (0, 0, -1), (0, 0, 1), (0, 1, 0)],
            12: [(0, -1, 0), (0, 0, -1), (0, 0, 1), (-1, -1, -2), (-1, -1, -1), (-1, -1, 0), (-1, -1, 1), (-1, -1, 2)],
            # 13 is recursive level
            14: [(0, 1, 0), (0, 0, -1), (0, 0, 1), (-1, 1, -2), (-1, 1, -1), (-1, 1, 0), (-1, 1, 1), (-1, 1, 2)],
            15: [(1, -1, 0), (0, 0, -1), (0, 0, 1), (0, -1, 0)],

            16: [(1, 1, -1), (0, 0, -1), (0, 0, 1), (0, 1, 0)],
            17: [(0, -1, 0), (0, 0, -1), (0, 0, 1), (0, 1, 0)],
            18: [(0, -1, 0), (0, 0, 1), (0, 1, 0), (-1, -2, 1), (-1, -1, 1), (-1, 0, 1), (-1, 1, 1), (-1, 2, 1)],
            19: [(0, -1, 0), (0, 0, -1), (0, 0, 1), (0, 1, 0)],
            20: [(1, -1, -1), (0, 0, -1), (0, 0, 1), (0, -1, 0)],

            21: [(1, 1, -2), (1, 2, -1), (0, 1, 0), (0, 0, -1)],
            22: [(1, 1, -1), (0, -1, 0), (0, 1, 0), (0, 0, -1)],
            23: [(1, 0, -1), (0, -1, 0), (0, 1, 0), (0, 0, -1)],
            24: [(1, -1, -1), (0, -1, 0), (0, 1, 0), (0, 0, -1)],
            25: [(1, -2, -1), (1, -1, -2), (0, -1, 0), (0, 0, -1)],
        }
        rule_number = y*self.width + x + 1
        rule = adjacency_rules[rule_number]
        return sum([1 if self.get(l+dl, x+dx, y+dy) == '#' else 0 for dl, dx, dy in rule])

    def grow(self):
        l0 = [['.' for x in range(self.width)] for y in range(self.height)]
        ln = [['.' for x in range(self.width)] for y in range(self.height)]
        new_levels = [l0] + self.levels + [ln]
        return State(new_levels, self.depth+2, self.height, self.width)

    def mutate(self):
        def new_state(l, x, y):
            if x == 2 and y == 2:
                return '?'
            tile = self.get(l, x, y)
            adj = self.adjacency(l, x, y)
            if tile == '#' and adj != 1:
                return '.'
            elif tile == '.' and (adj == 1 or adj == 2):
                return '#'
            else:
                return tile

        area = [[[new_state(l, x, y) for x in range(self.width)] for y in range(self.height)] for l in range(self.depth)]
        return State(area, self.depth, self.height, self.width)

    # def biodiversity_rating(self):
    #     multipliers = [[pow(2, (y*5)+x) for x in range(self.width)] for y in range(self.height)]
    #     rating = 0
    #     for y in range(self.height):
    #         for x in range(self.width):
    #             rating += multipliers[y][x] if self.get(x, y) == '#' else 0
    #     return rating

    def bug_count(self):
        count = 0
        for l in range(self.depth):
            for y in range(self.height):
                for x in range(self.width):
                    if self.get(l, x, y) == '#':
                        count += 1
        return count

    @classmethod
    def parse(cls, lines):
        lines = [line.strip() for line in lines.splitlines() if len(line.strip())]
        height, width = 5, 5
        initial_level = [[lines[y][x] for x in range(width)] for y in range(height)]
        return cls([initial_level], 1, height, width)


def mutate_until_duplicate(s):
    history = set()
    state = s
    while state not in history:
        history.add(state)
        state = state.mutate()
        print(state)
        print()
    return state


# s = State.parse("""
# ....#
# #..#.
# #.?##
# ..#..
# #....
# """)
# s = s.grow().mutate()
# s = s.grow().mutate()
# s = s.grow().mutate()
# s = s.grow().mutate()
# s = s.grow().mutate()
# s = s.grow().mutate()
# s = s.grow().mutate()
# s = s.grow().mutate()
# s = s.grow().mutate()
# s = s.grow().mutate()
# print(s)
# print(s.bug_count())
#

s = State.parse("""
###..
.##..
#.?..
##..#
.###.
""")
for i in range(200):
    s = s.grow().mutate()
print(s.bug_count())
