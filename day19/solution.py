from dataclasses import dataclass
from enum import Enum
import math
import curses
from curses import wrapper
import time
import networkx as nx

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


class ExecutionInterrupt(Enum):
    HALT = 0
    NEED_INPUT = 1
    HAS_OUTPUT = 2


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

    def execute_until_interrupt(self, interrupts = {ExecutionInterrupt.NEED_INPUT, ExecutionInterrupt.HAS_OUTPUT}):
        while True:
            instruction = self.next_instruction()
            if ExecutionInterrupt.NEED_INPUT in interrupts and isinstance(instruction, InputInstruction) and not self.state.io.inputs: # exit before input instractuon to ask for input
                return ExecutionInterrupt.NEED_INPUT
            self.state = instruction.execute(self.state)
            if ExecutionInterrupt.HAS_OUTPUT in interrupts and isinstance(instruction, OutputInstruction):
                return ExecutionInterrupt.HAS_OUTPUT
            if isinstance(instruction, HaltInstruction):
                self.halted = True
                return ExecutionInterrupt.HALT


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
    STATIONARY = 0
    PULLED = 1


class Map:
    def __init__(self, starting_size=P(5, 5)):
        self.size = starting_size
        self.tiles = {}
        self.default = '.'

    def _update_boundary(self, point: Point):
        max_coord = max(abs(self.size.x), abs(self.size.y), abs(point.x)+1, abs(point.y)+1)
        self.size = P(max_coord, max_coord)

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

    def each_coordinate(self):
        for h in range(self.size.y):
            for w in range(self.size.x):
                p = P(w, h)
                yield p

    def count(self, tile_value):
        c = 0
        for p in self.each_coordinate():
            if self[p] == tile_value:
                c += 1
        return c

    def print(self):
        lines = []
        for h in range(self.size.y):
            line = []
            for w in range(self.size.x):
                p = P(w, h)
                ch = self[p]
                line.append(ch)
            lines.append(''.join(line))
        print("\n".join(lines))

    @classmethod
    def parse(cls, lines):
        map = cls()
        for y, line in enumerate([l for l in lines.splitlines() if len(l)]):
            for x, ch in enumerate(line):
                p = P(x, y)
                map[p] = ch
        return map

def create_program_computer(program_code):

    def execution_step(p):
        outputs = []
        inputs = [p.x, p.y]
        program = IntcodeProgram(program_code, inputs, outputs)
        result = program.execute_until_interrupt(interrupts={ExecutionInterrupt.HAS_OUTPUT})
        if result == ExecutionInterrupt.HALT:
            return None
        if result == ExecutionInterrupt.HAS_OUTPUT:
            val = outputs[0]
            return '.' if val == 0 else '#'
    return execution_step


def find_bottom_beam_cover(map):
    end_point = None
    start_point = None
    for x in range(map.size.x-1, 0, -1):
        p = P(x, 49)
        ch = map[p]
        if end_point is None and ch == '#':
            end_point = p
        if end_point is not None and ch == '.':
            start_point = p + P(1, 0)
        if start_point is not None and end_point is not None:
            return start_point, end_point

class Robot:

    def __init__(self, program, map):
        self.map = map
        self.program = create_program_computer(program)

    def fill(self):
        for p in self.map.each_coordinate():
            out = self.program(p)
            if out is None:
                return
            self.map[p] = out

    def min_distance_to_fit_square(self, size):
        # looking at the map we know the beam is going to hit bottom border, so look just there
        start_50, end_50 = find_bottom_beam_cover(self.map)
        width_each_50 = end_50.x - start_50.x + 1
        width_each_100 = 2*width_each_50
        drift_each_100 = 2*end_50.x
        i = 1
        while width_each_100*i < size+drift_each_100:
            i += 1

        y = (i-2)*100
        x = (i-2)*end_50.x*2
        p = P(x, y)
        val = self.program(p)
        if val == '.':
            step = P(-1, 0)
            while val == '.':
                p += step
                val = self.program(p)
        else:
            step = P(1, 0)
            while val == '#':
                p += step
                val = self.program(p)
            p -= step  # prev step!

        tr = p
        trv = self.program(tr)
        assert trv == '#'
        bl = tr + P(-size, size) + P(1, -1)
        blv = self.program(bl)
        assert blv == '.'
        while blv == '.':
            if self.program(tr + P(1, 1)) == '#':
                tr = tr + P(1, 1)
            else:
                tr = tr + P(0, 1)
            bl = tr + P(-size, size) + P(1, -1)
            blv = self.program(bl)
        return P(bl.x, tr.y)


map = Map.parse(open("day19/map.txt").read())
map.print()
robot = Robot([int(s) for s in open("day19/input1.txt").read().strip().split(',')], map)
print(robot.min_distance_to_fit_square(100))
