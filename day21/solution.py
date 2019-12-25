from aoc2019.intcode import IntcodeProgram

program = [int(s) for s in open("day21/input1.txt").read().strip().split(',')]

inputs = []
outputs = []
p = IntcodeProgram(program, inputs, outputs)
lines = [
    "NOT A T",
    "OR T J",
    "NOT B T",
    "OR T J",
    "NOT C T",
    "OR T J",
    "AND D J",
    "WALK"
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
print(damage)
