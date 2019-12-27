from dataclasses import dataclass

@dataclass
class State:
    area: []
    height: int
    width : int

    def __repr__(self):
        return "\n".join([''.join(self.area[y]) for y in range(self.height)])

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def get(self, x, y):
        if 0 <= x < 5 and 0 <= y < 5:
            return self.area[y][x]
        else:
            return '.'

    def ajacency(self, x, y):
        return sum([1 if self.get(x, y) == '#' else 0 for x, y in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]])

    def mutate(self):
        def new_state(x, y):
            tile = self.get(x, y)
            adj = self.ajacency(x, y)
            if tile == '#' and adj != 1:
                return '.'
            elif tile == '.' and (adj == 1 or adj == 2):
                return '#'
            else:
                return tile

        area = [[new_state(x, y) for x in range(self.width)] for y in range(self.height)]
        return State(area, self.height, self.width)

    def biodiversity_rating(self):
        multipliers = [[pow(2, (y*5)+x) for x in range(self.width)] for y in range(self.height)]
        rating = 0
        for y in range(self.height):
            for x in range(self.width):
                rating += multipliers[y][x] if self.get(x, y) == '#' else 0
        return rating


    @classmethod
    def parse(cls, lines):
        lines = [line.strip() for line in lines.splitlines() if len(line.strip())]
        height, width = 5, 5
        area = [[lines[y][x] for x in range(width)] for y in range(height)]
        return cls(area, height, width)


def mutate_until_duplicate(s):
    history = set()
    state = s
    while state not in history:
        history.add(state)
        state = state.mutate()
        print(state)
        print()
    return state


s = State.parse("""
###..
.##..
#....
##..#
.###.
""")

s = mutate_until_duplicate(s)
print(s.biodiversity_rating())