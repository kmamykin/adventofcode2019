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
        self.halted = False
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
        while not self.halted:
            instruction = self.next_instruction()
            self.address = instruction.execute(self.memory, self.address, io)
            self.halted = isinstance(instruction, HaltInstruction)
        return io.outputs

    def execute_until_output_or_halt(self, io):
        while True:
            instruction = self.next_instruction()
            self.address = instruction.execute(self.memory, self.address, io)
            if isinstance(instruction, HaltInstruction):
                self.halted = True
                break
            if isinstance(instruction, OutputInstruction):
                break

        return io


def generate_phase_settings(settings_range):
    for p in itertools.permutations(list(settings_range)):
        yield p


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


class FeedbackIO:

    def __init__(self, buffer01, buffer12, buffer23, buffer34, buffer40):
        self.buffer01 = buffer01
        self.buffer12 = buffer12
        self.buffer23 = buffer23
        self.buffer34 = buffer34
        self.buffer40 = buffer40
        self.io0 = IO(self.buffer40, self.buffer01)
        self.io1 = IO(self.buffer01, self.buffer12)
        self.io2 = IO(self.buffer12, self.buffer23)
        self.io3 = IO(self.buffer23, self.buffer34)
        self.io4 = IO(self.buffer34, self.buffer40)


def thruster_signal_with_feedback(prog, phase_settings):

    fio = FeedbackIO(
        [phase_settings[1]],
        [phase_settings[2]],
        [phase_settings[3]],
        [phase_settings[4]],
        [phase_settings[0], 0] # plus initial input
    )

    a0 = IntcodeProgram(prog)
    a1 = IntcodeProgram(prog)
    a2 = IntcodeProgram(prog)
    a3 = IntcodeProgram(prog)
    a4 = IntcodeProgram(prog)

    while not all([a0.halted, a1.halted, a2.halted, a3.halted, a4.halted]):
        a0.execute_until_output_or_halt(fio.io0)
        a1.execute_until_output_or_halt(fio.io1)
        a2.execute_until_output_or_halt(fio.io2)
        a3.execute_until_output_or_halt(fio.io3)
        a4.execute_until_output_or_halt(fio.io4)
    return fio.buffer40[0]


def max_thruster_signal(program_string, settings_range=range(5)):
    prog = [int(s) for s in program_string.strip().split(',')]
    max_signal = -9999
    max_settings = None
    for phase_settings in generate_phase_settings(settings_range):
        signal = thruster_signal(prog, phase_settings)
        if signal > max_signal:
            max_signal = signal
            max_settings = phase_settings
    return max_signal, max_settings


def max_thruster_signal_with_feedback(program_string, settings_range=range(5, 10)):
    prog = [int(s) for s in program_string.strip().split(',')]
    max_signal = -9999
    max_settings = None
    for phase_settings in generate_phase_settings(settings_range):
        signal = thruster_signal_with_feedback(prog, phase_settings)
        if signal > max_signal:
            max_signal = signal
            max_settings = phase_settings
    return max_signal, max_settings

print(list(generate_phase_settings(range(5))))
# assert max_thruster_signal("3,15,3,16,1002,16,10,16,1,16,15,15,4,15,99,0,0") == (43210, (4,3,2,1,0))
# assert max_thruster_signal("3,23,3,24,1002,24,10,24,1002,23,-1,23,101,5,23,23,1,24,23,23,4,23,99,0,0") == (54321, (0,1,2,3,4))
# assert max_thruster_signal("3,31,3,32,1002,32,10,32,1001,31,-2,31,1007,31,0,33,1002,33,7,33,1,33,31,31,1,32,31,31,4,31,99,0,0,0") == (65210, (1,0,4,3,2))
print(max_thruster_signal(open("day07/input.txt").read()))

print(list(generate_phase_settings(range(5, 10))))

assert max_thruster_signal_with_feedback("3,26,1001,26,-4,26,3,27,1002,27,2,27,1,27,26,27,4,27,1001,28,-1,28,1005,28,6,99,0,0,5") == (139629729, (9,8,7,6,5))
assert max_thruster_signal_with_feedback("3,52,1001,52,-5,52,3,53,1,52,56,54,1007,54,5,55,1005,55,26,1001,54,-5,54,1105,1,12,1,53,54,53,1008,54,0,55,1001,55,1,55,2,53,55,53,4,53,1001,56,-1,56,1005,56,6,99,0,0,0,0,10") == (18216, (9,7,8,5,6))
print(max_thruster_signal_with_feedback(open("day07/input2.txt").read()))



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
