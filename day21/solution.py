from aoc2019.intcode import IntcodeProgram

program = [int(s) for s in open("day21/input1.txt").read().strip().split(',')]

inputs = []
outputs = []
p = IntcodeProgram(program, inputs, outputs)
lines = [
    # can land safely and there is something to jump over
    "NOT A T",
    "OR T J",
    "NOT B T",
    "OR T J",
    "NOT C T",
    "OR T J",
    "AND D J",
    # and could immediately jump again if needed
    "NOT T T", # resetting T to false, since it is always true at this point
    "OR E T", # next cell is ground
    "OR H T", # immediate jump available
    "AND T J",
    # and could step one step and then jump
    "RUN"
]
for line in lines:
    inputs.extend([ord(ch) for ch in line])
    inputs.append(10)
p.execute()
message = []
damage = None
for i in outputs:
    if i < 255:
        message.append(chr(i))
    else:
        damage = i

print(''.join(message))
print(damage if damage is not None else "CRASH")
