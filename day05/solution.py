from dataclasses import dataclass
from enum import Enum


class ParameterMode(Enum):
    POSITION = 0
    IMMEDIATE = 1


@dataclass
class Parameter:
    value: int
    mode: ParameterMode

    def read(self, memory):
        return self.value if self.mode == ParameterMode.IMMEDIATE else memory[self.value]

    def write(self, memory, value):
        if self.mode == ParameterMode.IMMEDIATE:
            raise Exception("Can not write to memory at the position of immediate parameter")
        else:
            memory[self.value] = value



@dataclass
class InstructionDescriptor:
    value: int

    def opcode(self):
        return self.value % 100

    def parameter_mode(self, parameter_order: int) -> ParameterMode:
        digit_position = parameter_order + 1
        mode = ((self.value % pow(10, digit_position + 1)) - (self.value % pow(10, digit_position)))//pow(10, digit_position)
        return ParameterMode(mode)


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
        descriptor = InstructionDescriptor(memory[address])
        return cls(
            Parameter(memory[address + 1], descriptor.parameter_mode(1)),
            Parameter(memory[address + 2], descriptor.parameter_mode(2)),
            Parameter(memory[address + 3], descriptor.parameter_mode(3))
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
        descriptor = InstructionDescriptor(memory[address])
        return cls(
            Parameter(memory[address + 1], descriptor.parameter_mode(1)),
            Parameter(memory[address + 2], descriptor.parameter_mode(2)),
            Parameter(memory[address + 3], descriptor.parameter_mode(3))
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
        descriptor = InstructionDescriptor(memory[address])
        return cls(
            Parameter(memory[address + 1], descriptor.parameter_mode(1)),
        )

    def execute(self, memory, address, io):
        self.parameter.write(memory, io.read())
        return address + 2


@dataclass
class OutputInstruction:
    parameter: Parameter

    @classmethod
    def from_memory(cls, memory, address):
        descriptor = InstructionDescriptor(memory[address])
        return cls(
            Parameter(memory[address + 1], descriptor.parameter_mode(1)),
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
        descriptor = InstructionDescriptor(memory[address])
        return cls(
            Parameter(memory[address + 1], descriptor.parameter_mode(1)),
            Parameter(memory[address + 2], descriptor.parameter_mode(2))
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
        descriptor = InstructionDescriptor(memory[address])
        return cls(
            Parameter(memory[address + 1], descriptor.parameter_mode(1)),
            Parameter(memory[address + 2], descriptor.parameter_mode(2))
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
        descriptor = InstructionDescriptor(memory[address])
        return cls(
            Parameter(memory[address + 1], descriptor.parameter_mode(1)),
            Parameter(memory[address + 2], descriptor.parameter_mode(2)),
            Parameter(memory[address + 3], descriptor.parameter_mode(3))
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
        descriptor = InstructionDescriptor(memory[address])
        return cls(
            Parameter(memory[address + 1], descriptor.parameter_mode(1)),
            Parameter(memory[address + 2], descriptor.parameter_mode(2)),
            Parameter(memory[address + 3], descriptor.parameter_mode(3))
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
        descriptor = InstructionDescriptor(self.memory[self.address])
        if descriptor.opcode() == 1:
            return AddInstruction.from_memory(self.memory, self.address)
        elif descriptor.opcode() == 2:
            return MultiplyInstruction.from_memory(self.memory, self.address)
        elif descriptor.opcode() == 3:
            return InputInstruction.from_memory(self.memory, self.address)
        elif descriptor.opcode() == 4:
            return OutputInstruction.from_memory(self.memory, self.address)
        elif descriptor.opcode() == 5:
            return JumpIfTrueInstruction.from_memory(self.memory, self.address)
        elif descriptor.opcode() == 6:
            return JumpIfFalseInstruction.from_memory(self.memory, self.address)
        elif descriptor.opcode() == 7:
            return LessThenInstruction.from_memory(self.memory, self.address)
        elif descriptor.opcode() == 8:
            return EqualsInstruction.from_memory(self.memory, self.address)
        elif descriptor.opcode() == 99:
            return HaltInstruction()
        else:
            raise Exception(f"Unkown opcode {descriptor.opcode()} at position {self.address}")

    def execute(self, inputs):
        io = IO(inputs)
        halt = False
        while not halt:
            instruction = self.peek_instruction()
            self.address = instruction.execute(self.memory, self.address, io)
            halt = isinstance(instruction, HaltInstruction)
        return io.outputs


print(HaltInstruction())
assert InstructionDescriptor(1002).opcode() == 2
assert InstructionDescriptor(1002).parameter_mode(1) == ParameterMode.POSITION
assert InstructionDescriptor(1002).parameter_mode(2) == ParameterMode.IMMEDIATE
assert InstructionDescriptor(1002).parameter_mode(3) == ParameterMode.POSITION
assert IntcodeProgram([99]).peek_instruction() == HaltInstruction()
mult = MultiplyInstruction(Parameter(4, ParameterMode(0)), Parameter(3, ParameterMode(1)), Parameter(4, ParameterMode(0)))
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
