from dataclasses import dataclass
from enum import Enum

@dataclass
class Instruction:
    opcode: int
    length: int
    is_halt: bool = False


class ParameterMode(Enum):
    POSITION = 0
    IMMEDIATE = 1


@dataclass
class Parameter:
    value: int
    immediate: bool

    def value_from(self, memory):
        return self.value if self.immediate else memory[self.value]

    def write_to(self, memory, value):
        if self.immediate:
            raise Exception("Can not write to memory at the position of immediate parameter")
        else:
            memory[self.value] = value

@dataclass
class HaltInstruction:

    @staticmethod
    def length():
        return 1

    @staticmethod
    def from_memory(memory, pointer):
        return HaltInstruction()

    def execute(self, memory):
        # NOOP
        return memory


@dataclass
class AddInstruction:
    parameter1: Parameter
    parameter2: Parameter
    parameter3: Parameter

    @staticmethod
    def length():
        return 4

    @staticmethod
    def from_memory(memory, pointer):
        instruction_cell = memory[pointer]
        return AddInstruction(
            Parameter(memory[pointer+1], decode_parameter_mode(instruction_cell, 2)),
            Parameter(memory[pointer+2], decode_parameter_mode(instruction_cell, 3)),
            Parameter(memory[pointer+3], decode_parameter_mode(instruction_cell, 4))
        )

    def execute(self, memory):
        result = self.parameter1.value_from(memory) + self.parameter2.value_from(memory)
        self.parameter3.write_to(memory, result)
        return memory


@dataclass
class MultiplyInstruction:
    parameter1: Parameter
    parameter2: Parameter
    parameter3: Parameter

    @staticmethod
    def length():
        return 4

    @staticmethod
    def from_memory(memory, pointer):
        instruction_cell = memory[pointer]
        return MultiplyInstruction(
            Parameter(memory[pointer+1], decode_parameter_mode(instruction_cell, 2)),
            Parameter(memory[pointer+2], decode_parameter_mode(instruction_cell, 3)),
            Parameter(memory[pointer+3], decode_parameter_mode(instruction_cell, 4))
        )

    def execute(self, memory):
        result = self.parameter1.value_from(memory) * self.parameter2.value_from(memory)
        self.parameter3.write_to(memory, result)
        return memory

@dataclass
class InputInstruction:
    parameter: Parameter
    input: int = 1

    @staticmethod
    def length():
        return 2

    @staticmethod
    def from_memory(memory, pointer):
        instruction_cell = memory[pointer]
        return InputInstruction(
            Parameter(memory[pointer+1], decode_parameter_mode(instruction_cell, 2)),
        )

    def execute(self, memory):
        self.parameter.write_to(memory, self.input)
        return memory

@dataclass
class OutputInstruction:
    parameter: Parameter
    output: int = 0

    @staticmethod
    def length():
        return 2

    @staticmethod
    def from_memory(memory, pointer):
        instruction_cell = memory[pointer]
        return OutputInstruction(
            Parameter(memory[pointer+1], decode_parameter_mode(instruction_cell, 2)),
        )

    def execute(self, memory):
        print(self.parameter.value_from(memory))
        return memory


class IntcodeProgram:
    memory: [int]
    instruction_pointer: int

    def __init__(self, program):
        self.memory = program.copy()
        self.instruction_pointer = 0

    def execute(self, inputs):
        outputs = []
        instruction = read_instruction(self.memory, self.instruction_pointer)
        while not isinstance(instruction, HaltInstruction):
            _ = instruction.execute(self.memory)
            self.instruction_pointer += instruction.length()
            instruction = read_instruction(self.memory, self.instruction_pointer)
        return outputs


def decode_opcode(value):
    return value % 100


def decode_parameter_mode(value, digit_position):
    return bool((value % pow(10, digit_position+1)) - (value % pow(10, digit_position)))


def read_instruction(memory, pointer):
    instruction_signature = memory[pointer]
    if decode_opcode(memory[pointer]) == 1:
        return AddInstruction.from_memory(memory, pointer)
    elif decode_opcode(instruction_signature) == 2:
        return MultiplyInstruction.from_memory(memory, pointer)
    elif decode_opcode(instruction_signature) == 3:
        return InputInstruction.from_memory(memory, pointer)
    elif decode_opcode(instruction_signature) == 4:
        return OutputInstruction.from_memory(memory, pointer)
    elif decode_opcode(instruction_signature) == 99:
        return HaltInstruction()
    else:
        raise Exception(f"Unkown opcode {decode_opcode(instruction_signature)} at position {pointer}")


print(HaltInstruction())
assert decode_opcode(1002) == 2
assert decode_parameter_mode(1002, 2) == False
assert decode_parameter_mode(1002, 3) == True
assert decode_parameter_mode(1002, 4) == False
assert read_instruction([99], 0) == HaltInstruction()
mult = MultiplyInstruction(Parameter(4, False), Parameter(3, True), Parameter(4, False))
assert read_instruction([1002,4,3,4,33], 0) == mult
assert mult.execute([1002,4,3,4,33]) == [1002,4,3,4,99]
prog = [int(s) for s in open("./day05/input.txt").read().strip().split(',')]
print(prog)
print(IntcodeProgram(prog).execute([1]))

