import math
from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from functools import reduce
from datetime import datetime


@dataclass
class Point3D:
    x: int
    y: int
    z: int

    def __add__(self, other):
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Point3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other: int):
        return Point3D(self.x * other, self.y * other, self.z * other)

    def __repr__(self):
        return f"<x={self.x: >3}, y={self.y: >3}, z={self.z: >3}>"

    def __hash__(self):
        return hash((self.x, self.y, self.z))


def P(x, y, z) -> Point3D:
    return Point3D(x, y, z)


class Moons(Enum):
    Io = 0
    Europa = 1
    Ganymede = 2
    Callisto = 3


@dataclass
class MoonState:
    position: Point3D
    velocity: Point3D

    def __repr__(self):
        return f"pos={self.position}, vel={self.velocity}"

    def __hash__(self):
        return hash((self.position, self.velocity))

    def potential_energy(self):
        return abs(self.position.x) + abs(self.position.y) + abs(self.position.z)

    def kinetic_energy(self):
        return abs(self.velocity.x) + abs(self.velocity.y) + abs(self.velocity.z)

    def total_energy(self):
        return self.potential_energy() * self.kinetic_energy()

    def apply_forces(self, forces: [Point3D]):
        total_force = reduce(lambda s, e: s + e, forces, P(0, 0, 0))
        velocity = self.velocity + total_force
        position = self.position + velocity
        return MoonState(position, velocity)


@dataclass
class SystemState:
    moons: (MoonState, MoonState, MoonState, MoonState)

    @classmethod
    def from_positions(cls, positions: [Point3D]):
        return SystemState(tuple([MoonState(p, P(0,0,0)) for p in positions]))

    def __repr__(self):
        return " ".join([f"{m}" for m in self.moons])

    def __hash__(self):
        return hash(self.moons)

    def potential_energy(self):
        return sum([m.potential_energy() for m in self.moons])

    def kenetic_energy(self):
        return sum([m.kinetic_energy() for m in self.moons])

    def total_energy(self):
        return sum([m.total_energy() for m in self.moons])


def simulate_step(state: SystemState):
    forces = {m: [] for m in Moons}
    for m1, m2 in combinations(Moons, 2):
        g1, g2 = gravity(state.moons[m1.value].position, state.moons[m2.value].position)
        forces[m1].append(g1)
        forces[m2].append(g2)

    # debug here
    # force = lambda fs: reduce(lambda s, e: s + e, fs, P(0, 0, 0))
    # print([force(forces[m]) for m in Moons])
    return SystemState(tuple([state.moons[m.value].apply_forces(forces[m]) for m in Moons]))


def gravity(pos1: Point3D, pos2: Point3D) -> (Point3D, Point3D):
    def diff(v1, v2):
        if v1 < v2:
            return 1
        elif v1 > v2:
            return -1
        else:
            return 0
    return P(diff(pos1.x, pos2.x), diff(pos1.y, pos2.y), diff(pos1.z, pos2.z)), P(diff(pos2.x, pos1.x), diff(pos2.y, pos1.y), diff(pos2.z, pos1.z))


def simulate_steps(state: SystemState, number_of_stemps: int, debug = False):
    for i in range(number_of_stemps):
        if debug:
            print(f"After {i} stop")
            print(state)
        state = simulate_step(state)
    if debug:
        print(f"After {number_of_stemps} stop")
        print(state)
    return state


def system_period(state: SystemState, max_steps = None) -> int:
    step = 1
    starting_state = state
    print(f"pot={state.potential_energy()}, kin={state.kenetic_energy()}, total={state.total_energy()}")
    state = simulate_step(state)
    while (state != starting_state) and (max_steps is None or step <= max_steps):
        print(f"pot={state.potential_energy()}, kin={state.kenetic_energy()}, total={state.total_energy()}")
        state = simulate_step(state)
        step += 1
        if step % 1000000 == 0:
            print(f"Step {step} at {datetime.now()}")
    print(f"pot={state.potential_energy()}, kin={state.kenetic_energy()}, total={state.total_energy()}")
    return step


# EXAMPLE 1
# <x=-1, y=0, z=2>
# <x=2, y=-10, z=-7>
# <x=4, y=-8, z=8>
# <x=3, y=5, z=-1>
example1 = SystemState.from_positions([
    P(-1, 0, 2),
    P(2, -10, -7),
    P(4, -8, 8),
    P(3, 5, -1)
])
example1_copy = SystemState.from_positions([
    P(-1, 0, 2),
    P(2, -10, -7),
    P(4, -8, 8),
    P(3, 5, -1)
])
print(hash(example1))
assert hash(example1) == hash(example1_copy)
assert example1 == example1_copy
assert example1 in {example1_copy}
assert example1_copy in {example1}
assert example1 in {example1, example1_copy}
assert len({example1, example1_copy}) == 1
example1_2772 = simulate_steps(example1, 2772)
# print(example1)
# print(example1_2772)
assert example1 == example1_2772
assert hash(example1) == hash(example1_2772)
# assert simulate_steps(example1, 10, debug = False).total_energy() == 179
print(system_period(example1))
# assert system_period(example1) == 2772

# EXAMPLE 2
# <x=-8, y=-10, z=0>
# <x=5, y=5, z=10>
# <x=2, y=-7, z=3>
# <x=9, y=-8, z=-3>
example2 = SystemState.from_positions([
    P(-8, -10, 0),
    P(5, 5, 10),
    P(2, -7, 3),
    P(9, -8, -3)
])
# assert simulate_steps(example2, 100, debug = False).total_energy() == 1940
# assert system_period(example2) == 4686774924

# INPUT 1
# <x=-3, y=10, z=-1>
# <x=-12, y=-10, z=-5>
# <x=-9, y=0, z=10>
# <x=7, y=-5, z=-3>

problem1 = SystemState.from_positions([
    P(-3, 10, -1),
    P(-12, -10, -5),
    P(-9, 0, 10),
    P(7, -5, -3)
])

# print(simulate_steps(problem1, 1000, debug = False).total_energy())

# INPUT 2
# <x=-3, y=10, z=-1>
# <x=-12, y=-10, z=-5>
# <x=-9, y=0, z=10>
# <x=7, y=-5, z=-3>
problem2 = SystemState.from_positions([
    P(-3, 10, -1),
    P(-12, -10, -5),
    P(-9, 0, 10),
    P(7, -5, -3)
])
# print(system_period(problem2, max_steps=100))