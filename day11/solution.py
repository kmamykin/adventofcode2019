from dataclasses import dataclass
from enum import Enum
import math

class Memory:
    def __init__(self, initial_memory):
        self.memory = initial_memory.copy()

    def _extend_to(self, address: int):
        if address >= len(self.memory):
            additional_storage = [0] * (address - len(self.memory) + 1)
            self.memory.extend(additional_storage)

    def __getitem__(self, address: int):
        self._extend_to(address)
        return self.memory[address]

    def __setitem__(self, address: int, value: int):
        self._extend_to(address)
        self.memory[address] = value


class IO:
    def __init__(self, inputs, outputs = []):
        self.inputs = inputs
        self.outputs = outputs

    def read(self):
        if not self.inputs:
            raise Exception("IO input buffer is empty when trying to read")
        return self.inputs.pop(0)

    def write(self, value: int):
        self.outputs.append(value)


@dataclass
class ProgramState:
    memory: Memory
    address: int
    relative_base: int
    io: IO

    def advance(self, offset: int):
        return ProgramState(self.memory, self.address + offset, self.relative_base, self.io)

    def advance_relative_base(self, offset: int):
        return ProgramState(self.memory, self.address, self.relative_base + offset, self.io)

    def with_address(self, address: int):
        return ProgramState(self.memory, address, self.relative_base, self.io)

    def address_offset(self, offset: int = 0) -> int:
        return self.memory[self.address + offset]


class ParameterMode(Enum):
    POSITION = 0
    IMMEDIATE = 1
    RELATIVE = 2


@dataclass
class Parameter:
    value: int
    mode: ParameterMode

    def read(self, state: ProgramState):
        if self.mode == ParameterMode.POSITION:
            return state.memory[self.value]
        elif self.mode == ParameterMode.IMMEDIATE:
            return self.value
        elif self.mode == ParameterMode.RELATIVE:
            return state.memory[state.relative_base + self.value]
        else:
            raise Exception(f"Unknown parameter mode {self.mode}")

    def write(self, state: ProgramState, value):
        if self.mode == ParameterMode.POSITION:
            state.memory[self.value] = value
        elif self.mode == ParameterMode.IMMEDIATE:
            raise Exception("Can not write to memory at the position of immediate parameter")
        elif self.mode == ParameterMode.RELATIVE:
            state.memory[state.relative_base + self.value] = value
        else:
            raise Exception(f"Unknown parameter mode {self.mode}")


@dataclass
class InstructionDescriptor:
    value: int

    def opcode(self):
        return self.value % 100

    def parameter_mode(self, parameter_order: int) -> ParameterMode:
        digit_position = parameter_order + 1
        mode = ((self.value % pow(10, digit_position + 1)) - (self.value % pow(10, digit_position)))//pow(10, digit_position)
        return ParameterMode(mode)



@dataclass
class HaltInstruction:

    @staticmethod
    def from_memory(state: ProgramState):
        descriptor = InstructionDescriptor(state.address_offset())
        return HaltInstruction() if descriptor.opcode() == 99 else None

    def execute(self, state: ProgramState):
        # NOOP
        return state


@dataclass
class AddInstruction:
    parameter1: Parameter
    parameter2: Parameter
    parameter3: Parameter

    @classmethod
    def from_memory(cls, state: ProgramState):
        descriptor = InstructionDescriptor(state.address_offset())
        return cls(
            Parameter(state.address_offset(1), descriptor.parameter_mode(1)),
            Parameter(state.address_offset(2), descriptor.parameter_mode(2)),
            Parameter(state.address_offset(3), descriptor.parameter_mode(3))
        ) if descriptor.opcode() == 1 else None

    def execute(self, state: ProgramState):
        result = self.parameter1.read(state) + self.parameter2.read(state)
        self.parameter3.write(state, result)
        return state.advance(4)


@dataclass
class MultiplyInstruction:
    parameter1: Parameter
    parameter2: Parameter
    parameter3: Parameter

    @classmethod
    def from_memory(cls, state: ProgramState):
        descriptor = InstructionDescriptor(state.address_offset())
        return cls(
            Parameter(state.address_offset(1), descriptor.parameter_mode(1)),
            Parameter(state.address_offset(2), descriptor.parameter_mode(2)),
            Parameter(state.address_offset(3), descriptor.parameter_mode(3))
        ) if descriptor.opcode() == 2 else None

    def execute(self, state: ProgramState):
        result = self.parameter1.read(state) * self.parameter2.read(state)
        self.parameter3.write(state, result)
        return state.advance(4)


@dataclass
class InputInstruction:
    parameter: Parameter

    @classmethod
    def from_memory(cls, state: ProgramState):
        descriptor = InstructionDescriptor(state.address_offset())
        return cls(
            Parameter(state.address_offset(1), descriptor.parameter_mode(1)),
        ) if descriptor.opcode() == 3 else None

    def execute(self, state: ProgramState):
        self.parameter.write(state, state.io.read())
        return state.advance(2)


@dataclass
class OutputInstruction:
    parameter: Parameter

    @classmethod
    def from_memory(cls, state: ProgramState):
        descriptor = InstructionDescriptor(state.address_offset())
        return cls(
            Parameter(state.address_offset(1), descriptor.parameter_mode(1)),
        ) if descriptor.opcode() == 4 else None

    def execute(self, state: ProgramState):
        state.io.write(self.parameter.read(state))
        return state.advance(2)


@dataclass
class JumpIfTrueInstruction:
    parameter1: Parameter
    parameter2: Parameter

    @classmethod
    def from_memory(cls, state: ProgramState):
        descriptor = InstructionDescriptor(state.address_offset())
        return cls(
            Parameter(state.address_offset(1), descriptor.parameter_mode(1)),
            Parameter(state.address_offset(2), descriptor.parameter_mode(2))
        ) if descriptor.opcode() == 5 else None

    def execute(self, state: ProgramState):
        if self.parameter1.read(state) > 0:
            return state.with_address(self.parameter2.read(state))
        else:
            return state.advance(3)


@dataclass
class JumpIfFalseInstruction:
    parameter1: Parameter
    parameter2: Parameter

    @classmethod
    def from_memory(cls, state: ProgramState):
        descriptor = InstructionDescriptor(state.address_offset())
        return cls(
            Parameter(state.address_offset(1), descriptor.parameter_mode(1)),
            Parameter(state.address_offset(2), descriptor.parameter_mode(2))
        ) if descriptor.opcode() == 6 else None

    def execute(self, state: ProgramState):
        if self.parameter1.read(state) == 0:
            return state.with_address(self.parameter2.read(state))
        else:
            return state.advance(3)


@dataclass
class LessThenInstruction:
    parameter1: Parameter
    parameter2: Parameter
    parameter3: Parameter

    @classmethod
    def from_memory(cls, state: ProgramState):
        descriptor = InstructionDescriptor(state.address_offset())
        return cls(
            Parameter(state.address_offset(1), descriptor.parameter_mode(1)),
            Parameter(state.address_offset(2), descriptor.parameter_mode(2)),
            Parameter(state.address_offset(3), descriptor.parameter_mode(3))
        ) if descriptor.opcode() == 7 else None

    def execute(self, state: ProgramState):
        if self.parameter1.read(state) < self.parameter2.read(state):
            self.parameter3.write(state, 1)
        else:
            self.parameter3.write(state, 0)
        return state.advance(4)


@dataclass
class EqualsInstruction:
    parameter1: Parameter
    parameter2: Parameter
    parameter3: Parameter

    @classmethod
    def from_memory(cls, state: ProgramState):
        descriptor = InstructionDescriptor(state.address_offset())
        return cls(
            Parameter(state.address_offset(1), descriptor.parameter_mode(1)),
            Parameter(state.address_offset(2), descriptor.parameter_mode(2)),
            Parameter(state.address_offset(3), descriptor.parameter_mode(3))
        ) if descriptor.opcode() == 8 else None

    def execute(self, state: ProgramState):
        if self.parameter1.read(state) == self.parameter2.read(state):
            self.parameter3.write(state, 1)
        else:
            self.parameter3.write(state, 0)
        return state.advance(4)


@dataclass
class RelativeBaseOffsetInstruction:
    parameter: Parameter

    @classmethod
    def from_memory(cls, state: ProgramState):
        descriptor = InstructionDescriptor(state.address_offset())
        return cls(
            Parameter(state.address_offset(1), descriptor.parameter_mode(1))
        ) if descriptor.opcode() == 9 else None

    def execute(self, state: ProgramState):
        # TODO: do something with relative_base
        offset = self.parameter.read(state)

        return state.advance(2).advance_relative_base(offset)


class IntcodeProgram:
    state: ProgramState

    def __init__(self, program, inputs, outputs=None):
        self.state = ProgramState(Memory(program), 0, 0, IO(inputs, [] if outputs is None else outputs))
        self.halted = False
        self.instruction_types = [
            HaltInstruction,
            AddInstruction, MultiplyInstruction, InputInstruction, OutputInstruction,
            JumpIfTrueInstruction, JumpIfFalseInstruction, LessThenInstruction, EqualsInstruction,
            RelativeBaseOffsetInstruction
        ]

    def next_instruction(self):
        for type in self.instruction_types:
            instruction = type.from_memory(self.state)
            if instruction:
                return instruction
        raise Exception(f"Unkown instruction descriptor {self.state.memory[self.state.address]} at position {self.state.address}")

    def execute(self):
        while not self.halted:
            instruction = self.next_instruction()
            self.state = instruction.execute(self.state)
            self.halted = isinstance(instruction, HaltInstruction)
        return self.state

    def execute_until(self, predicate = lambda state: False):
        while True:
            instruction = self.next_instruction()
            self.state = instruction.execute(self.state)
            if isinstance(instruction, HaltInstruction):
                self.halted = True
                break
            if predicate(self.state):
                break
        return self.state

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

def P(x, y) -> Point:
    return Point(x, y)


class PanelColor(Enum):
    BLACK = 0
    WHITE = 1


def turn(direction, turn_direction):
    theta = math.radians(-90 if turn_direction == 0 else 90)
    c, s = math.cos(theta), math.sin(theta)
    return P(round(c*direction.x - s*direction.y), round(s*direction.x + c*direction.y))

class Robot:

    def __init__(self, program, map):
        self.position = P(0, 0)
        self.direction = P(0, -1)
        self.map = map
        self.inputs = []
        self.outputs = []
        self.program = IntcodeProgram(program, self.inputs, self.outputs)

    def move(self):
        panel_color = self.map[self.position]
        self.inputs.append(panel_color.value)
        self.program.execute_until(lambda state: len(state.io.outputs) == 2)
        if self.program.halted:
            return
        new_color = self.outputs.pop(0)
        self.map[self.position] = PanelColor(new_color)
        turn_direction = self.outputs.pop(0) # 0 - turn left, 1 - turn right
        self.direction = turn(self.direction, turn_direction)
        self.position = self.position + self.direction

    def run(self, print = False):
        if print:
            self.print()
        while not self.program.halted:
            self.move()
            if print:
                self.print()

    def print(self):
        dir_chars = {
            P(0,-1): "^",
            P(1, 0): ">",
            P(0, 1): "v",
            P(-1, 0): "<"
        }
        for h in range(-self.map.boundary.y+1, self.map.boundary.y):
            line = []
            for w in range(-self.map.boundary.x+1, self.map.boundary.x):
                p = P(w, h)
                c = "." if self.map[p] == PanelColor.BLACK else "#"
                c = dir_chars[self.direction] if p == self.position else c
                line.append(c)
            print("".join(line))
        print("\n")

class PanelMap:
    def __init__(self):
        self.boundary = P(5, 5)
        self.panels = {}
        self.default = PanelColor.BLACK

    def _update_boundaty(self, point: Point):
        max_coord = max(abs(self.boundary.x), abs(self.boundary.y), abs(point.x), abs(point.y))
        self.boundary = P(max_coord, max_coord)

    def _set_panel_value(self, point: Point, value):
        if not point.x in self.panels:
            self.panels[point.x] = {}
        self.panels[point.x][point.y] = value

    def _panel_exists(self, point: Point):
        return (point.x in self.panels) and (point.y in self.panels[point.x])

    def __getitem__(self, point: Point):
        self._update_boundaty(point)
        return self.panels[point.x][point.y] if self._panel_exists(point) else self.default

    def __setitem__(self, point: Point, value):
        self._update_boundaty(point)
        self._set_panel_value(point, value)

    def painted_panels(self):
        return sum(len(yvals.values()) for x, yvals in self.panels.items())


assert turn(P(0, -1), 0) == P(-1, 0)
assert turn(P(-1, 0), 0) == P(0, 1)
assert turn(P(0, 1), 0) == P(1, 0)
assert turn(P(1, 0), 0) == P(0, -1)
assert turn(P(0, -1), 1) == P(1, 0)
assert turn(P(1, 0), 1) == P(0, 1)
assert turn(P(0, 1), 1) == P(-1, 0)
assert turn(P(-1, 0), 1) == P(0, -1)

map = PanelMap()
assert map[P(0,0)] == PanelColor.BLACK
assert map.painted_panels() == 0

map[P(0,0)] = PanelColor.WHITE
assert map[P(0,0)] == PanelColor.WHITE
assert map.painted_panels() == 1

map[P(0,0)] = PanelColor.BLACK
assert map[P(0,0)] == PanelColor.BLACK
assert map.painted_panels() == 1

map[P(1,1)] = PanelColor.WHITE
assert map[P(1,1)] == PanelColor.WHITE
assert map.painted_panels() == 2


# program = [int(s) for s in open("day11/input1.txt").read().strip().split(',')]
# map = PanelMap()
# robot = Robot(program, map)
# robot.run()
# robot.print()
# print(map.painted_panels())

# ................................................####.....................#.###.................
# ..................................................##.....................##.#.#................
# .............................................####..#.#.................##.###..#...............
# ..............................................##.....##.................#.###.##...............
# .............................................##.####.##................##.###..#...............
# ............................................##...#....#.................##.#.#.................
# ............................................##.##.###.#...##......#####.#..##.#<...............
# .............................................###..#.#.#..####..###...#.#.#.###.#...............
# .............................................#..##.###...##.###.....##....#..##................
# .............................................#.##.#.#..#....#.#.#.#..#####..#..................
# ...........................................#####..#.#.##.......#...#.#..#####..#...............
# .........................................##..##..##......#.#####...#..#...#####.#..............
# .........................................#.#..#...##.##.#...####....##.####..####..............
# ...........................................#..#.#...#..#..##..##.#....##.......................
# ..........................................#.###.#..#.#..#.###..#.##............................
# ...........................................#......####.###...####.#.#..........................
# ..............................................#.#..#.##.#......#.#.##..........................
# .............................................#.#...####..##..##....#.#.........................
# .............................................#......#.##..#..######.#..........................
# .......................................####...###....#....###...##.#...........................
# .......................................#...#...#.##.##...#....#..#.............................
# .......................................######....##..####..##....#####.#.......................
# .......................................##....####.#....###.#.......#.##........................
# ........................................######....###.#..##..#....##.##.#......................
# ......................................##....#.##...##.##..###.#..#.##.#..###...................
# .....................................#.#...####...#.##.#..#.#.#.###..#.#.#..#..................
# .....................................#####.##..#####..#.#.........#.##.#...##..................
# .........................................#..####..#..#..#.#......####.###.#.#..................
# .......................................#####..###.##.#..#..##.#.....#....#..#..................
# ...........................................##.#.##.####.####.#######.....##....................
# ...........................................##......#.####.#.#.#####.##...##....................
# ...........................................####.........#...#....###.#..##.....................
# ...........................................#..#........#.#.####.....##..##.....................
# ...........................................#..#....#.##.#..#.......#.....##....................
# ..........................................#.###...#..###....####.#.######.#....................
# ..........................................##.#.#..#..#...........###.#...####...##.............
# ............................................#.#..#.#..#.#.###...###..#.####..#...##............
# ............................................#....####.###.....#...#..###..##...##.#............
# ..........................................###..#.###..#####...#.#.###...#.##.#.#####...........
# ..........................................#..########.##...##....####...###.##...#..#..........
# ............................................##.##..##.#..####..########....###..#.##.#.........
# .........................................#.#.##.#.#.#.###.##.##.#..#.#.....#..##.##.#.#........
# .........................................###.##..#####.##..#.#.#..#.#.#...##.##......##........
# .......................................##.#.#.#..##...##.#..#.#.#.#####.....#.####.#...........
# .......................................##.#.######..##..###.##..##.#.#.#...#####...............
# ..........................................##......#...#.#.##.###..###.##....####.#.............
# .......................................#.#...#####......##.###.##.....#####.###.####...........
# .........................................#..#.#..####....#.#.##.#..#...#.#.##.####..#..........
# .......................................##...##.#..#####....##.##..####..#.#.#.#.###.#..........
# ...............................................#..##.##..########..#.#..##.#.#####.#.###.#.....
# ...........................................###.#.....##.#########...##..#.#.###..#...#..##.....
# .......................................#.#.##..#.##.##..##..#..#...#.#.#..###.#.####.#.###.....
# ......................................#.##.##...###...##..##.##..##..##.....#.#..#.##.#..#.#...
# .....................................#.##...#.#...####....###...#..#.........######.##.....##..
# .....................................#.##.#.##..####....##.##...##...........#....###.....##...
# ......................................#..###...##...##...#...#.##.............#..#..#.#..####..
# ......................................#.##..####..###.##.#..#.#.#..............##.....##.......
# .....................................####...#..#..###..#......##......................####.....
# .....................................####...##......###.##..#.........................#.#......
# ......................................#.#######.........####...................................
# .......................................######.....##.#.###.##..................................
# .......................................#.###.##..#..#####.##...................................
# .......................................#.##.###..###.##.##.#...................................
# .....................................####.##.####...#.##.###...................................
# .....................................##..##.#...#.....#.###....................................
# ......................................###.#...##...............................................
# ......................................#.###....................................................
# ...............................................................................................


program = [int(s) for s in open("day11/input2.txt").read().strip().split(',')]
map = PanelMap()
map[P(0,0)] = PanelColor.WHITE
robot = Robot(program, map)
robot.run()
robot.print()

