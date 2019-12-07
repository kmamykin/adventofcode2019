from dataclasses import dataclass
from enum import Enum
import itertools

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
        descriptor = InstructionDescriptor(memory[address])
        return HaltInstruction() if descriptor.opcode() == 99 else None

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
        ) if descriptor.opcode() == 1 else None

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
        ) if descriptor.opcode() == 2 else None

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
        ) if descriptor.opcode() == 3 else None

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
        ) if descriptor.opcode() == 4 else None

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
        ) if descriptor.opcode() == 5 else None

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
        ) if descriptor.opcode() == 6 else None

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
        ) if descriptor.opcode() == 7 else None

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
        ) if descriptor.opcode() == 8 else None

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
        self.instruction_types = [
            AddInstruction, MultiplyInstruction, InputInstruction, OutputInstruction,
            JumpIfTrueInstruction, JumpIfFalseInstruction, LessThenInstruction, EqualsInstruction,
            HaltInstruction
        ]

    def next_instruction(self):
        for type in self.instruction_types:
            instruction = type.from_memory(self.memory, self.address)
            if instruction:
                return instruction
        raise Exception(f"Unkown instruction descriptor {self.memory[self.address]} at position {self.address}")

    def execute(self, inputs):
        io = IO(inputs)
        halt = False
        while not halt:
            instruction = self.next_instruction()
            self.address = instruction.execute(self.memory, self.address, io)
            halt = isinstance(instruction, HaltInstruction)
        return io.outputs


def generate_phase_settings():
    for p in itertools.permutations(list(range(5))):
        yield p
    #
    # for i1 in range(5):
    #     for i2 in range(5):
    #         for i3 in range(5):
    #             for i4 in range(5):
    #                 for i5 in range(5):
    #                     yield [i1, i2, i3, i4, i5]


def create_amplifier(prog):
    def amplify(phase, input):
        outputs = IntcodeProgram(prog).execute([phase, input])
        return outputs[0]
    return amplify

def thruster_signal(prog, phase_settings):
    a0 = create_amplifier(prog)(phase_settings[0], 0)
    a1 = create_amplifier(prog)(phase_settings[1], a0)
    a2 = create_amplifier(prog)(phase_settings[2], a1)
    a3 = create_amplifier(prog)(phase_settings[3], a2)
    a4 = create_amplifier(prog)(phase_settings[4], a3)
    return a4

def max_thruster_signal(program_string):
    prog = [int(s) for s in program_string.strip().split(',')]
    max_signal = -9999
    max_settings = None
    for phase_settings in generate_phase_settings():
        signal = thruster_signal(prog, phase_settings)
        if signal > max_signal:
            max_signal = signal
            max_settings = phase_settings

    return max_signal, max_settings

print(list(generate_phase_settings()))
assert max_thruster_signal("3,15,3,16,1002,16,10,16,1,16,15,15,4,15,99,0,0") == (43210, (4,3,2,1,0))
assert max_thruster_signal("3,23,3,24,1002,24,10,24,1002,23,-1,23,101,5,23,23,1,24,23,23,4,23,99,0,0") == (54321, (0,1,2,3,4))
assert max_thruster_signal("3,31,3,32,1002,32,10,32,1001,31,-2,31,1007,31,0,33,1002,33,7,33,1,33,31,31,1,32,31,31,4,31,99,0,0,0") == (65210, (1,0,4,3,2))
print(max_thruster_signal(open("day07/input.txt").read()))

# print(list(generate_phase_settings()))



# assert InstructionDescriptor(1002).opcode() == 2
# assert InstructionDescriptor(1002).parameter_mode(1) == ParameterMode.POSITION
# assert InstructionDescriptor(1002).parameter_mode(2) == ParameterMode.IMMEDIATE
# assert InstructionDescriptor(1002).parameter_mode(3) == ParameterMode.POSITION
# assert IntcodeProgram([99]).next_instruction() == HaltInstruction()
# mult = MultiplyInstruction(Parameter(4, ParameterMode(0)), Parameter(3, ParameterMode(1)), Parameter(4, ParameterMode(0)))
# assert IntcodeProgram([1002,4,3,4,33]).next_instruction() == mult
# assert mult.execute([1002,4,3,4,33], 0) == 4
# prog = [int(s) for s in open("./day05/input.txt").read().strip().split(',')]
# print(IntcodeProgram(prog).execute([1]))
#
# # input equals to 8 program
# assert IntcodeProgram([3,9,8,9,10,9,4,9,99,-1,8]).execute([8]) == [1]
# assert IntcodeProgram([3,9,8,9,10,9,4,9,99,-1,8]).execute([7]) == [0]
#
# # input less then 8
# assert IntcodeProgram([3,9,7,9,10,9,4,9,99,-1,8]).execute([8]) == [0]
# assert IntcodeProgram([3,9,7,9,10,9,4,9,99,-1,8]).execute([7]) == [1]
#
# # input equal to 8
# assert IntcodeProgram([3,3,1108,-1,8,3,4,3,99]).execute([8]) == [1]
# assert IntcodeProgram([3,3,1108,-1,8,3,4,3,99]).execute([7]) == [0]
#
# # input less then 8
# assert IntcodeProgram([3,3,1107,-1,8,3,4,3,99]).execute([8]) == [0]
# assert IntcodeProgram([3,3,1107,-1,8,3,4,3,99]).execute([7]) == [1]
#
# # jump tests
# assert IntcodeProgram([3,12,6,12,15,1,13,14,13,4,13,99,-1,0,1,9]).execute([0]) == [0]
# assert IntcodeProgram([3,12,6,12,15,1,13,14,13,4,13,99,-1,0,1,9]).execute([10]) == [1]
# assert IntcodeProgram([3,3,1105,-1,9,1101,0,0,12,4,12,99,1]).execute([0]) == [0]
# assert IntcodeProgram([3,3,1105,-1,9,1101,0,0,12,4,12,99,1]).execute([10]) == [1]
#
# largerExample = [
#     3,21,1008,21,8,20,1005,20,22,107,8,21,20,1006,20,31,
#     1106,0,36,98,0,0,1002,21,125,20,4,20,1105,1,46,104,
#     999,1105,1,46,1101,1000,1,20,4,20,1105,1,46,98,99
# ]
#
# assert IntcodeProgram(largerExample).execute([7]) == [999]
# assert IntcodeProgram(largerExample).execute([8]) == [1000]
# assert IntcodeProgram(largerExample).execute([9]) == [1001]
#
#
# prog = [int(s) for s in open("./day05/input2.txt").read().strip().split(',')]
# print(IntcodeProgram(prog).execute([5]))
