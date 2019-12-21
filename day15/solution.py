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


class ReplyCode(Enum):
    WALL = 0
    MOVED = 1
    OXYGEN = 2


class MapTile(Enum):
    EMPTY = 0
    WALL = 1
    OXYGEN = 2


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

    def __init__(self, program, map):
        self.map = map
        self.inputs = []
        self.outputs = []
        self.program = IntcodeProgram(program, self.inputs, self.outputs)
        self.score = 0
        self.start_position = P(0,0)
        self.target_position = None
        self.position =self.start_position
        self.direction = P(0, -1)
        self.map[self.position] = MapTile.EMPTY
        self.graph = nx.Graph()
        self.completed = False

    def move(self):
        movements = {
            P(0,-1): MovementCommand.NORTH,
            P(1, 0): MovementCommand.EAST,
            P(-1, 0): MovementCommand.WEST,
            P(0, 1): MovementCommand.SOUTH
        }
        self.inputs.append(movements[self.direction].value)
        result = self.program.execute_until_interrupt(interrupts={ExecutionInterrupt.HAS_OUTPUT})
        if result == ExecutionInterrupt.HAS_OUTPUT:
            reply_code = ReplyCode(self.outputs.pop(0))
            if reply_code == ReplyCode.WALL:
                self.map[self.position + self.direction] = MapTile.WALL
                self.direction = turn(self.direction, 0)
            elif reply_code == ReplyCode.MOVED:
                self.graph.add_edge(self.position, self.position + self.direction)
                self.position += self.direction
                self.map[self.position] = MapTile.EMPTY
                self.direction = turn(self.direction, 1)
            elif reply_code == ReplyCode.OXYGEN:
                self.graph.add_edge(self.position, self.position + self.direction)
                self.position += self.direction
                self.target_position = self.position
                self.map[self.position] = MapTile.OXYGEN

    def run(self, update_fn = None):
        while not self.program.halted and not self.completed:
            self.move()
            update_fn()

    def shortest_distance(self):
        path = nx.shortest_path(self.graph, source=self.start_position, target=self.target_position)
        return len(path) - 1

class CursesDisplay:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.screen_size = P(0,0)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)

    def update(self, robot, map):
        if self.screen_size != map.size:
            self.screen_size = map.size
            self.stdscr.clear()
        tile_chars = {
            MapTile.EMPTY: ".",
            MapTile.WALL: "#",
            MapTile.OXYGEN: 'O'
        }
        for h in range(-map.size.y+1, map.size.y):
            for w in range(-map.size.x+1, map.size.x):
                p = P(w, h)
                screen_coords = P(w, h) + map.size + P(1,1)
                ch = '*' if p == robot.position else tile_chars[map[p]]

                try:
                    self.stdscr.addch(screen_coords.y, screen_coords.x, ch, curses.color_pair(1))
                except:
                    pass

        if robot.target_position:
            path = nx.shortest_path(robot.graph, source=robot.start_position, target=robot.target_position)
            for c in path:
                screen_coords = c + map.size + P(1,1)
                try:
                    self.stdscr.addch(screen_coords.y, screen_coords.x, '+', curses.color_pair(1))
                except:
                    pass
            screen_coords = map.size + map.size + P(3,0)
            self.stdscr.addstr(screen_coords.y, screen_coords.x, f"Distance: {len(path) - 1}", curses.color_pair(1))
        self.stdscr.refresh()
        # time.sleep(0.01)

def main(stdscr):
    display = CursesDisplay(stdscr)
    map = Map()
    robot = Robot([int(s) for s in open("day15/input1.txt").read().strip().split(',')], map)
    robot.run(lambda: display.update(robot, map))
    print(robot.shortest_distance())

wrapper(main)