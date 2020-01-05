from aoc2019.intcode import IntcodeProgram, ExecutionInterrupt
from dataclasses import dataclass

class Droid:
    def __init__(self, prog):
        self.inputs = []
        self.outputs = []
        self.program = IntcodeProgram(prog, self.inputs, self.outputs)

    def report(self):
        result = self.program.execute_until_interrupt()
        if result == ExecutionInterrupt.HAS_OUTPUT:
            out = ''
            while result == ExecutionInterrupt.HAS_OUTPUT:
                out += ''.join([chr(i) for i in self.outputs])
                self.outputs.clear()
                result = self.program.execute_until_interrupt()
            print(out)

    def command(self, cmd, interactive = False):
        if interactive:
            print(f"{cmd}")
        for c in cmd:
            self.inputs.append(ord(c))
        self.inputs.append(10) # end of line
        result = self.program.execute_until_interrupt()
        if result == ExecutionInterrupt.HALT:
            return
        if result == ExecutionInterrupt.NEED_INPUT:
            return
        if result == ExecutionInterrupt.HAS_OUTPUT:
            out = ''
            while result == ExecutionInterrupt.HAS_OUTPUT:
                out += ''.join([chr(i) for i in self.outputs])
                self.outputs.clear()
                result = self.program.execute_until_interrupt()
            if interactive:
                print(out)
            return out

    def play(self):
        while True:
            cmd = input()
            self.command(cmd, interactive=True)

    def play_script(self, lines):
        lines = [line.strip() for line in lines.splitlines() if len(line.strip())]
        for cmd in lines:
            self.command(cmd)

    def brute_force(self):
        def parse_inv(text):
            inv = []
            for line in text.splitlines():
                if line.startswith('- '):
                    inv.append(line[2:])
            return inv

        def all_combinations():
            for i in range(pow(2, 8)):
                yield i
        all_items = parse_inv(self.command('inv'))
        for combo in all_combinations():
            mask = [combo & pow(2, i) == pow(2, i) for i in range(8)]
            for item, pick in zip(all_items, mask):
                if pick:
                    pick_out = self.command(f"take {item}")
                else:
                    pick_out = self.command(f"drop {item}")
            taken_items = parse_inv(self.command('inv'))
            west_out = self.command('west')
            result = ''
            if 'heavier' in west_out:
                result = 'heavier'
            if  'lighter' in west_out:
                result = 'lighter'
            print(f"{taken_items} -> {result}")


p = [int(s) for s in open("day25/input1.txt").read().strip().split(',')]
droid = Droid(p)
droid.report()
droid.play_script("""
south
take fixed point
north
north
take spool of cat6
north
take monolith
west
take planetoid
east
north
take hypercube
south
south
east
north
take candy cane
south
east
take easter egg
east
south
take ornament
west
south
inv
""")
# droid.brute_force()
droid.play()
# ['ornament', 'easter egg', 'hypercube', 'monolith']

# droid.command('north')
# droid.command('north')
# droid.command('north')
# droid.command('south')
# droid.command('west')
# droid.command('east')
# droid.command('south')
# droid.command('east')
# droid.command('north')
# droid.command('west')
# droid.command('east')
# droid.command('east')
# droid.command('west')
# droid.command('south')
# droid.command('east')
# droid.command('east')
# droid.command('east')
# droid.command('west')
# droid.command('south')
# droid.command('east')
# droid.command('west')
# droid.command('west')
# droid.command('south')
# droid.command('west')

# droid.command('east')
# droid.command('east')
# droid.command('west')
# droid.command('west')
# droid.command('south')
#
