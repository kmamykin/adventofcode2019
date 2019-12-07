from dataclasses import dataclass
# from enum import Enum
# # NOT USED
# class ParameterMode(Enum):
#     POSITION = 0
#     IMMEDIATE = 1
#

@dataclass
class Parameter:
    value: int
    immediate: bool

    def read(self, memory):
        return self.value if self.immediate else memory[self.value]

    def write(self, memory, value):
        if self.immediate:
            raise Exception("Can not write to memory at the position of immediate parameter")
        else:
            memory[self.value] = value


class IO:
    def __init__(self, inputs):
        self.inputs = inputs
        self.outputs = []

    def read(self):
        return self.inputs.pop(0)

    def write(self, value: int):
        self.outputs.append(value)


@dataclass
class HaltInstruction:

    @staticmethod
    def from_memory(memory, address):
        return HaltInstruction()

    def execute(self, memory, address, io=None):
        # NOOP
        return address


@dataclass
class AddInstruction:
    parameter1: Parameter
    parameter2: Parameter
    parameter3: Parameter

    @classmethod
    def from_memory(cls, memory, address):
        instruction_cell = memory[address]
        return cls(
            Parameter(memory[address + 1], decode_parameter_mode(instruction_cell, 2)),
            Parameter(memory[address + 2], decode_parameter_mode(instruction_cell, 3)),
            Parameter(memory[address + 3], decode_parameter_mode(instruction_cell, 4))
        )

    def execute(self, memory, address, io=None):
        result = self.parameter1.read(memory) + self.parameter2.read(memory)
        self.parameter3.write(memory, result)
        return address + 4


@dataclass
class MultiplyInstruction:
    parameter1: Parameter
    parameter2: Parameter
    parameter3: Parameter

    @classmethod
    def from_memory(cls, memory, address):
        instruction_cell = memory[address]
        return cls(
            Parameter(memory[address + 1], decode_parameter_mode(instruction_cell, 2)),
            Parameter(memory[address + 2], decode_parameter_mode(instruction_cell, 3)),
            Parameter(memory[address + 3], decode_parameter_mode(instruction_cell, 4))
        )

    def execute(self, memory, address, io=None):
        result = self.parameter1.read(memory) * self.parameter2.read(memory)
        self.parameter3.write(memory, result)
        return address + 4


@dataclass
class InputInstruction:
    parameter: Parameter

    @classmethod
    def from_memory(cls, memory, address):
        instruction_cell = memory[address]
        return cls(
            Parameter(memory[address + 1], decode_parameter_mode(instruction_cell, 2)),
        )

    def execute(self, memory, address, io):
        self.parameter.write(memory, io.read())
        return address + 2


@dataclass
class OutputInstruction:
    parameter: Parameter

    @classmethod
    def from_memory(cls, memory, address):
        instruction_cell = memory[address]
        return cls(
            Parameter(memory[address + 1], decode_parameter_mode(instruction_cell, 2)),
        )

    def execute(self, memory, address, io):
        io.write(self.parameter.read(memory))
        return address + 2


@dataclass
class JumpIfTrueInstruction:
    parameter1: Parameter
    parameter2: Parameter

    @classmethod
    def from_memory(cls, memory, address):
        instruction_cell = memory[address]
        return cls(
            Parameter(memory[address + 1], decode_parameter_mode(instruction_cell, 2)),
            Parameter(memory[address + 2], decode_parameter_mode(instruction_cell, 3))
        )

    def execute(self, memory, address, io=None):
        if self.parameter1.read(memory) > 0:
            return self.parameter2.read(memory)
        else:
            return address + 3


@dataclass
class JumpIfFalseInstruction:
    parameter1: Parameter
    parameter2: Parameter

    @classmethod
    def from_memory(cls, memory, address):
        instruction_cell = memory[address]
        return cls(
            Parameter(memory[address + 1], decode_parameter_mode(instruction_cell, 2)),
            Parameter(memory[address + 2], decode_parameter_mode(instruction_cell, 3))
        )

    def execute(self, memory, address, io=None):
        if self.parameter1.read(memory) == 0:
            return self.parameter2.read(memory)
        else:
            return address + 3


@dataclass
class LessThenInstruction:
    parameter1: Parameter
    parameter2: Parameter
    parameter3: Parameter

    @classmethod
    def from_memory(cls, memory, address):
        instruction_cell = memory[address]
        return cls(
            Parameter(memory[address + 1], decode_parameter_mode(instruction_cell, 2)),
            Parameter(memory[address + 2], decode_parameter_mode(instruction_cell, 3)),
            Parameter(memory[address + 3], decode_parameter_mode(instruction_cell, 4))
        )

    def execute(self, memory, address, io=None):
        if self.parameter1.read(memory) < self.parameter2.read(memory):
            self.parameter3.write(memory, 1)
        else:
            self.parameter3.write(memory, 0)
        return address + 4


@dataclass
class EqualsInstruction:
    parameter1: Parameter
    parameter2: Parameter
    parameter3: Parameter

    @classmethod
    def from_memory(cls, memory, address):
        instruction_cell = memory[address]
        return cls(
            Parameter(memory[address + 1], decode_parameter_mode(instruction_cell, 2)),
            Parameter(memory[address + 2], decode_parameter_mode(instruction_cell, 3)),
            Parameter(memory[address + 3], decode_parameter_mode(instruction_cell, 4))
        )

    def execute(self, memory, address, io=None):
        if self.parameter1.read(memory) == self.parameter2.read(memory):
            self.parameter3.write(memory, 1)
        else:
            self.parameter3.write(memory, 0)
        return address + 4


class IntcodeProgram:
    memory: [int]
    address: int

    def __init__(self, program):
        self.memory = program.copy()
        self.address = 0

    def peek_instruction(self):
        instruction_signature = self.memory[self.address]
        if decode_opcode(self.memory[self.address]) == 1:
            return AddInstruction.from_memory(self.memory, self.address)
        elif decode_opcode(instruction_signature) == 2:
            return MultiplyInstruction.from_memory(self.memory, self.address)
        elif decode_opcode(instruction_signature) == 3:
            return InputInstruction.from_memory(self.memory, self.address)
        elif decode_opcode(instruction_signature) == 4:
            return OutputInstruction.from_memory(self.memory, self.address)
        elif decode_opcode(instruction_signature) == 5:
            return JumpIfTrueInstruction.from_memory(self.memory, self.address)
        elif decode_opcode(instruction_signature) == 6:
            return JumpIfFalseInstruction.from_memory(self.memory, self.address)
        elif decode_opcode(instruction_signature) == 7:
            return LessThenInstruction.from_memory(self.memory, self.address)
        elif decode_opcode(instruction_signature) == 8:
            return EqualsInstruction.from_memory(self.memory, self.address)
        elif decode_opcode(instruction_signature) == 99:
            return HaltInstruction()
        else:
            raise Exception(f"Unkown opcode {decode_opcode(instruction_signature)} at position {self.address}")

    def execute(self, inputs):
        io = IO(inputs)
        halt = False
        while not halt:
            instruction = self.peek_instruction()
            self.address = instruction.execute(self.memory, self.address, io)
            halt = isinstance(instruction, HaltInstruction)
        return io.outputs


def decode_opcode(value):
    return value % 100


def decode_parameter_mode(value, digit_position):
    return bool((value % pow(10, digit_position+1)) - (value % pow(10, digit_position)))


print(HaltInstruction())
assert decode_opcode(1002) == 2
assert decode_parameter_mode(1002, 2) == False
assert decode_parameter_mode(1002, 3) == True
assert decode_parameter_mode(1002, 4) == False
assert IntcodeProgram([99]).peek_instruction() == HaltInstruction()
mult = MultiplyInstruction(Parameter(4, False), Parameter(3, True), Parameter(4, False))
assert IntcodeProgram([1002,4,3,4,33]).peek_instruction() == mult
assert mult.execute([1002,4,3,4,33], 0) == 4
prog = [int(s) for s in open("./day05/input.txt").read().strip().split(',')]
print(prog)
print(IntcodeProgram(prog).execute([1]))

# input equals to 8 program
assert IntcodeProgram([3,9,8,9,10,9,4,9,99,-1,8]).execute([8]) == [1]
assert IntcodeProgram([3,9,8,9,10,9,4,9,99,-1,8]).execute([7]) == [0]

# input less then 8
assert IntcodeProgram([3,9,7,9,10,9,4,9,99,-1,8]).execute([8]) == [0]
assert IntcodeProgram([3,9,7,9,10,9,4,9,99,-1,8]).execute([7]) == [1]

# input equal to 8
assert IntcodeProgram([3,3,1108,-1,8,3,4,3,99]).execute([8]) == [1]
assert IntcodeProgram([3,3,1108,-1,8,3,4,3,99]).execute([7]) == [0]

# input less then 8
assert IntcodeProgram([3,3,1107,-1,8,3,4,3,99]).execute([8]) == [0]
assert IntcodeProgram([3,3,1107,-1,8,3,4,3,99]).execute([7]) == [1]

# jump tests
assert IntcodeProgram([3,12,6,12,15,1,13,14,13,4,13,99,-1,0,1,9]).execute([0]) == [0]
assert IntcodeProgram([3,12,6,12,15,1,13,14,13,4,13,99,-1,0,1,9]).execute([10]) == [1]
assert IntcodeProgram([3,3,1105,-1,9,1101,0,0,12,4,12,99,1]).execute([0]) == [0]
assert IntcodeProgram([3,3,1105,-1,9,1101,0,0,12,4,12,99,1]).execute([10]) == [1]

largerExample = [
    3,21,1008,21,8,20,1005,20,22,107,8,21,20,1006,20,31,
    1106,0,36,98,0,0,1002,21,125,20,4,20,1105,1,46,104,
    999,1105,1,46,1101,1000,1,20,4,20,1105,1,46,98,99
]

assert IntcodeProgram(largerExample).execute([7]) == [999]
assert IntcodeProgram(largerExample).execute([8]) == [1000]
assert IntcodeProgram(largerExample).execute([9]) == [1001]


prog = [int(s) for s in open("./day05/input2.txt").read().strip().split(',')]
print(prog)
print(IntcodeProgram(prog).execute([5]))
