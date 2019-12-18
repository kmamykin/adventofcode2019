from dataclasses import dataclass
from enum import Enum
import math
import random


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

    def execute_until(self):
        while True:
            instruction = self.next_instruction()
            if isinstance(instruction, InputInstruction) and not self.state.io.inputs: # exit before input instractuon to ask for input
                return ExecutionInterrupt.NEED_INPUT
            self.state = instruction.execute(self.state)
            if isinstance(instruction, OutputInstruction):
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


class TileType(Enum):
    EMPTY = 0
    WALL = 1
    BLOCK = 2
    H_PADDLE = 3
    BALL = 4


class GameBoard:
    def __init__(self):
        self.size = P(5, 5)
        self.tiles = {}
        self.default = TileType.EMPTY

    def _update_boundaty(self, point: Point):
        self.size = P(max(abs(self.size.x), abs(point.x) + 1), max(abs(self.size.y), abs(point.y) + 1))

    def _set_panel_value(self, point: Point, value):
        if not point.x in self.tiles:
            self.tiles[point.x] = {}
        self.tiles[point.x][point.y] = value

    def _panel_exists(self, point: Point):
        return (point.x in self.tiles) and (point.y in self.tiles[point.x])

    def __getitem__(self, point: Point):
        self._update_boundaty(point)
        return self.tiles[point.x][point.y] if self._panel_exists(point) else self.default

    def __setitem__(self, point: Point, value):
        self._update_boundaty(point)
        self._set_panel_value(point, value)

    def number_of_tiles(self, type: TileType):
        return sum(len([t for t in yvals.values() if t == type]) for x, yvals in self.tiles.items())


class Robot:

    def __init__(self, program, board):
        self.board = board
        self.inputs = [1] # start with neutral joystick
        self.outputs = []
        program[0] = 2 # initialize with coins
        self.program = IntcodeProgram(program, self.inputs, self.outputs)
        self.score = 0
        self.scores = [0]
        self.ball_position = P(0,0)
        self.paddle_position = P(0,0)
        self.game_started = False
        self.paddle_controller = PaddleController(board)

    def move(self, pre_decision = None, post_decision = None):
        result = self.program.execute_until()
        if result == ExecutionInterrupt.HALT:
            return
        if result == ExecutionInterrupt.HAS_OUTPUT:
            if len(self.outputs) < 3:
                return
            # handle output
            x = self.outputs.pop(0)
            y = self.outputs.pop(0)
            val = self.outputs.pop(0)
            if x == -1 and y == 0:
                self.score = val
                self.scores.append(val - self.scores[-1])
                self.game_started = True
            else:
                tile = TileType(val)
                if tile == TileType.BALL:
                    self.ball_position = P(x, y)
                    # print(f"set ball {self.ball_position}")
                elif tile == TileType.H_PADDLE:
                    self.paddle_position = P(x, y)
                    # print(f"set paddle {self.paddle_position}")
                self.board[P(x, y)] = tile
        if result == ExecutionInterrupt.NEED_INPUT:
            # handle input
            if pre_decision:
                pre_decision()
            self.paddle_controller.push(self.ball_position, self.paddle_position)
            j, msg = self.paddle_controller.optimal_joystick_state()
            self.inputs.append(j)
            if post_decision:
                post_decision()

    def run(self):
        while not self.program.halted:
            self.move(pre_decision= lambda: self.print(), post_decision=lambda: self.print_action())

    def print(self):
        tile_chars = {
            TileType.EMPTY: ".",
            TileType.WALL: u'\u2588',
            TileType.BLOCK: "#",
            TileType.H_PADDLE: "-",
            TileType.BALL: "O"
        }
        if self.board.number_of_tiles(TileType.BLOCK) == 1:
            return
        for h in range(0, self.board.size.y):
            line = []
            for w in range(0, self.board.size.x):
                p = P(w, h)
                c = tile_chars[self.board[p]]
                line.append(c)
            print("".join(line))

    def print_action(self):
        if self.board.number_of_tiles(TileType.BLOCK) == 1:
            return
        p = self.paddle_controller.optimal_paddle_position()
        j, msg = self.paddle_controller.optimal_joystick_state()
        print(f"{ ' ' * p.x }^")
        print(f"B:{self.ball_position} dir:{self.paddle_controller.ball_direction()}")
        print(f"P:{self.paddle_position} dir:{self.paddle_controller.paddle_direction()} {joystick_char(j)} {msg}")
        print(f"Score: {self.score}, step: {self.paddle_controller.step}")
        print("\n")


def joystick_char(x):
    joystick_chars = {
        0: "|", -1: "<", 1: ">"
    }
    return joystick_chars[x]


def sign(x):
    return 0 if x == 0 else int(math.copysign(1, x))


def is_moving_towards_paddle(curr_ball, prev_ball):
    return curr_ball.y > prev_ball.y


def side_bounce(direction):
    return P(-direction.x, direction.y)


def vertical_bounce(directon):
    return P(directon.x, -directon.y)

def reverse_bounce(directon):
    return P(-directon.x, -directon.y)


def simulate_ball_trajectory(curr_paddle, curr_ball, prev_ball, board):
    if prev_ball is None:
        return curr_paddle
    else:
        direction = curr_ball - prev_ball  # possible values (-1, -1), (-1, 1), (1, -11), (1, 1)
        position = curr_ball
        counter = 0
        while position.y < curr_paddle.y:
            counter += 1
            if counter > 200 or position.x == 0 or position.x+1 >= board.size.x or position.y+1 >= board.size.y or position.y == 0:
                return None
            # its possible to change directon twice in one iteration
            # first we check for side bounce
            # then we chack for directional bounce
            if direction.x > 0 and board[position + P(1,0)] in (TileType.BLOCK, TileType.WALL):
                direction = side_bounce(direction)
            elif direction.x < 0 and board[position + P(-1,0)] in (TileType.BLOCK, TileType.WALL):
                direction = side_bounce(direction)

            if direction.y < 0 and board[position + P(0,-1)] == TileType.BLOCK: # moving up and block above
                direction = vertical_bounce(direction)
            elif direction.y > 0 and board[position + P(0,1)] == TileType.BLOCK: # moving down and block below
                direction = P(direction.x, -direction.y)
            elif direction.x > 0 and direction.y < 0 and board[position + P(1,-1)] == TileType.BLOCK: # moving top right and block ahead
                direction = reverse_bounce(direction)
            elif direction.x < 0 and direction.y < 0 and board[position + P(-1,-1)] == TileType.BLOCK: # moving top left and block ahead
                direction = reverse_bounce(direction)
            position += direction
        return position


class PaddleController:
    def __init__(self, board):
        self.board = board
        self.opt_paddle_position = None
        self.prev_state = (None, None)
        self.curr_state = (None, None)
        self.step = 0

    def push(self, ball_position: Point, paddle_position: Point):
        self.step += 1 #
        if self.step == 1:
            self.prev_state = (ball_position - P(1,1), paddle_position)
        else:
            self.prev_state = self.curr_state
        self.curr_state = (ball_position, paddle_position)

    def state(self):
        curr_ball, curr_paddle = self.curr_state
        prev_ball, prev_paddle = self.prev_state
        ball_direction = curr_ball - prev_ball
        paddle_direction = curr_paddle - prev_paddle
        return curr_ball, prev_ball, ball_direction, curr_paddle, prev_paddle, paddle_direction

    def ball_direction(self):
        curr_ball, prev_ball, ball_direction, curr_paddle, prev_paddle, paddle_direction = self.state()
        return ball_direction

    def paddle_direction(self):
        curr_ball, prev_ball, ball_direction, curr_paddle, prev_paddle, paddle_direction = self.state()
        return paddle_direction

    def optimal_paddle_position(self):
        curr_ball, prev_ball, ball_direction, curr_paddle, prev_paddle, paddle_direction = self.state()
        number_of_blocks = self.board.number_of_tiles(TileType.BLOCK)
        if self.step == 1:
            self.stats = [[0,0,0,0] for i in range(45)]
        if number_of_blocks == 1:
            if curr_ball.y == 20 and ball_direction.y > 0:
                self.saved_direction = ball_direction
                self.saved_ball_x = curr_ball.x
            if curr_ball.y == 19 and ball_direction.y < 0:
                case = -1
                if self.saved_direction == P(1, 1) and ball_direction == P(-1, -1):
                    case = 0
                elif self.saved_direction == P(1, 1) and ball_direction == P(1, -1):
                    case = 1
                elif self.saved_direction == P(-1, 1) and ball_direction == P(-1, -1):
                    case = 2
                elif self.saved_direction == P(-1, 1) and ball_direction == P(1, -1):
                    case = 3

                self.stats[self.saved_ball_x][case] = self.stats[self.saved_ball_x][case] + 1
            if self.step % 1000 == 0:
                print(self.stats)
        # When the ball bounces high up, track it's position and direction
        if ball_direction.y < 0 or (ball_direction.y > 0 and curr_ball.y < 17):
            return P(curr_ball.x, curr_paddle.y)
        if ball_direction.y > 0 and curr_ball.y >= 5 and number_of_blocks == 1: # moving down and can not change direction
            opt_paddle_position = simulate_ball_trajectory(curr_paddle, curr_ball, prev_ball, self.board)
            if curr_ball.y >= 15 and ball_direction == P(1, 1):
                return opt_paddle_position + P(-1, 0)# random.choice([opt_paddle_position, ])
            if  curr_ball.y >= 15 and ball_direction == P(-1, 1):
                return opt_paddle_position + P(1, 0)#random.choice([opt_paddle_position, curr_paddle + P(1, 0)])
            return opt_paddle_position
        if ball_direction.y > 0 and curr_ball.y >= 17: # moving down and can not change direction
            opt_paddle_position = simulate_ball_trajectory(curr_paddle, curr_ball, prev_ball, self.board)
            return opt_paddle_position

        # opt_paddle_position = simulate_ball_trajectory(curr_paddle, curr_ball, prev_ball, self.board)
        # return opt_paddle_position if opt_paddle_position else curr_paddle #P((curr_ball + ball_direction).x, curr_paddle.y)

    def optimal_joystick_state(self):
        if self.step == 1:
            return 0, "wait"
        if self.step == 2:
            return -1, "left"
        curr_ball, prev_ball, ball_direction, curr_paddle, prev_paddle, paddle_direction = self.state()
        return sign(self.optimal_paddle_position().x - curr_paddle.x), "moving to position"

        # if curr_ball.y == curr_paddle.y - 1: # ball on top of the paddle. Predictively start moving same direction of the ball
        #     ball_direction = curr_ball - prev_ball
        #     return sign(ball_direction.x), "ball bouncing, move with the ball"

        # if ball_direction.y < 0 or (ball_direction.y > 0 and curr_ball.y < 17): # can still change direction
        #     if curr_ball.x - curr_paddle.x: #
        #         return sign(ball_direction.x), "staying under the ball"
        #     else:
        #         return sign(curr_ball.x - curr_paddle.x), "moving under the ball"
        # if ball_direction.y > 0 and curr_ball.y >= 17: # moving down and can not change direction
        #     opt_paddle_position = simulate_ball_trajectory(curr_paddle, curr_ball, prev_ball, self.board)
        #     return sign(opt_paddle_position.x - curr_paddle.x), "Moving to optimal position"
        # return 0, "confused..."

b = GameBoard()
assert b[P(0,0)] == TileType.EMPTY
b[P(0,0)] = TileType.BALL
assert b[P(0,0)] == TileType.BALL


# pc = PaddleController()
# pc.push(Point(x=20, y=18), Point(x=22, y=21))
# assert pc.optimal_paddle_position() == Point(x=22, y=21)
# assert pc.optimal_joystick_state() == 0
# pc.push(Point(x=21, y=19), Point(x=23, y=21))
# assert pc.optimal_paddle_position() == Point(x=22, y=21)
# assert pc.optimal_joystick_state() == -1
# pc.push(Point(x=22, y=20), Point(x=22, y=21))
# assert pc.optimal_paddle_position() == Point(x=22, y=21)
# assert pc.optimal_joystick_state() == 0
# pc.push(Point(x=21, y=19), Point(x=23, y=21)) # moving away
# assert pc.optimal_paddle_position() == Point(x=21, y=21)
# assert pc.optimal_joystick_state() == -1
# pc.push(Point(x=20, y=18), Point(x=23, y=21)) # moving away
# assert pc.optimal_paddle_position() == Point(x=20, y=21)
# assert pc.optimal_joystick_state() == -1

# only one position recorded - stay neutral
# Moving closer - move towards intersection with the paddle plane
#   with wall bounce
#   without wall bounce
# Moving away - move to be under the ball. Shlould predict bounces off the blocks?

board = GameBoard()
robot = Robot([int(s) for s in open("day13/input1.txt").read().strip().split(',')], board)
robot.run()


# 15873 15964