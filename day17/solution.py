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


class MovementCommand(Enum):
    NORTH = 1
    SOUTH = 2
    WEST = 3
    EAST = 4


class MapTile(Enum):
    EMPTY = 0
    SCAFFOLD = 1


class Map:
    def __init__(self):
        self.size = P(5, 5)
        self.tiles = {}
        self.default = MapTile.EMPTY

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


def turn(direction, turn_direction):
    theta = math.radians(-90 if turn_direction == 0 else 90)
    c, s = math.cos(theta), math.sin(theta)
    return P(round(c*direction.x - s*direction.y), round(s*direction.x + c*direction.y))


class Robot:

    def __init__(self, program, map, instructions):
        self.map = map
        self.inputs = []
        self.outputs = []
        program[0] = 2
        self.program = IntcodeProgram(program, self.inputs, self.outputs)
        self.start_position = P(0,0)
        self.position = self.start_position
        self.direction = P(0, -1)
        self.map[self.position] = MapTile.SCAFFOLD
        self.graph = nx.Graph()
        self.completed = False
        self.reading_position = P(0,0)
        self.instructions = instructions
        for line in instructions:
            for c in line:
                self.inputs.append(ord(c))
            self.inputs.append(10) # end of line

    def move(self):
        robot_chars = {
            '^': P(0,-1),
            '>': P(1, 0),
            '<': P(-1, 0),
            'v': P(0, 1)
        }
        # self.inputs.append(movements[self.direction].value)
        result = self.program.execute_until_interrupt(interrupts={ExecutionInterrupt.HAS_OUTPUT})
        if result == ExecutionInterrupt.HAS_OUTPUT:
            output = self.outputs.pop(0)
            if output > 255:
                # we have the amount of dust
                self.amount_of_dust = output
            if chr(output) == '.':
                self.map[self.reading_position] = MapTile.EMPTY
                self.reading_position += P(1, 0)
            elif chr(output) == '#':
                self.map[self.reading_position] = MapTile.SCAFFOLD
                self.reading_position += P(1, 0)
            elif chr(output) in ('^', 'v', '<', '>'):
                self.map[self.reading_position] = MapTile.EMPTY
                self.position = self.reading_position
                self.direction = robot_chars[chr(output)]
                self.reading_position += P(1, 0)
            elif chr(output) == 'X':
                raise Exception('X')
            elif output == 10:
                self.reading_position = P(0, self.reading_position.y + 1)

    def run(self, update_fn = None):
        while not self.program.halted and not self.completed:
            self.move()
            update_fn()


class CursesDisplay:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.screen_size = P(0,0)

    def update(self, robot, map):
        if self.screen_size != map.size:
            self.screen_size = map.size
            self.stdscr.clear()
        tile_chars = {
            MapTile.EMPTY: ".",
            MapTile.SCAFFOLD: "#"
        }
        robot_chars = {
            P(0,-1): '^',
            P(1, 0): '>',
            P(-1, 0): '<',
            P(0, 1): 'v'
        }
        for h in range(map.size.y):
            for w in range(map.size.x):
                p = P(w, h)
                screen_coords = P(w, h) + P(1,1)
                ch = robot_chars[robot.direction] if p == robot.position else tile_chars[map[p]]

                try:
                    self.stdscr.addch(screen_coords.y, screen_coords.x, ch)
                except:
                    pass

        self.stdscr.refresh()

def main(stdscr):
    display = CursesDisplay(stdscr)
    map = Map()
    robot = Robot([int(s) for s in open("day17/input1.txt").read().strip().split(',')], map, instructions=[
        "A,C,A,B,C,A,B,C,A,B",
        "L,12,L,12,L,6,L,6",
        "L,12,L,6,R,12,R,8",
        "R,8,R,4,L,12",
        "n"
    ])
    robot.run(lambda: 1)
    display.update(robot, map)
    # time.sleep(600)

wrapper(main)