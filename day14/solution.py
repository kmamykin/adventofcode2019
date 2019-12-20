from dataclasses import dataclass
from enum import Enum
import math
import random
import pulp

@dataclass
class Ingredient:
    quantity: int
    chemical: str

    @classmethod
    def parse(cls, s):
        quantity, chemical = s.split(' ')
        return cls(int(quantity), chemical.strip())


@dataclass
class Reaction:
    encoded: str
    inputs: [Ingredient]
    output: Ingredient

    @classmethod
    def parse(cls, line):
        inputs, output = line.strip().split(" => ")
        output = Ingredient.parse(output)
        inputs = [Ingredient.parse(input_str) for input_str in inputs.split(", ")]
        return cls(line.strip(), inputs, output)

    @property
    def var_name(self):
        return self.encoded.replace(' ', '').replace('=>', '|')

@dataclass
class NanoFactory:
    reactions: [Reaction]

    def chemical_list(self):
        l = [i.chemical for r in self.reactions for i in r.inputs] + [r.output.chemical for r in self.reactions]
        return set(l)

    @classmethod
    def read(cls, lines):
        reactions = [Reaction.parse(line) for line in lines.splitlines() if len(line)]
        return NanoFactory(reactions)

    def min_cost_of_fuel_in_ores(self, fuel):
        prob = pulp.LpProblem("ProblemMinORE", pulp.LpMinimize)
        vars = [pulp.LpVariable(r.var_name, 0, None, pulp.LpInteger) for r in self.reactions]
        # The objective function is added to 'prob' first
        prob += pulp.lpSum([v*i.quantity for v, r in zip(vars, self.reactions) for i in r.inputs if i.chemical == 'ORE']), "ORE"
        for c in (self.chemical_list() - {'FUEL', 'ORE'}):
            prob += pulp.lpSum([v*r.output.quantity for v, r in zip(vars, self.reactions) if r.output.chemical == c]) - \
                    pulp.lpSum([v*i.quantity for v, r in zip(vars, self.reactions) for i in r.inputs if i.chemical == c]) >= 0, \
                    f"{c}"
        prob += pulp.lpSum([v*r.output.quantity for v, r in zip(vars, self.reactions) if r.output.chemical == 'FUEL']) == fuel, "FUEL=1"
        # prob.writeLP("day14/problem1.lp")
        prob.solve()
        print("Status:", pulp.LpStatus[prob.status])
        # Each of the variables is printed with it's resolved optimum value
        for v in prob.variables():
            print(v.name, "=", v.varValue)

        # The optimised objective function value is printed to the screen
        print("Total quantity of ORE for 1 FUEL = ", pulp.value(prob.objective))
        return pulp.value(prob.objective)

    def max_fuel_from_ores(self, ore):
        prob = pulp.LpProblem("ProblemMaxFUEL", pulp.LpMaximize)
        vars = [pulp.LpVariable(r.var_name, 0, None, pulp.LpInteger) for r in self.reactions]
        # The objective function is added to 'prob' first
        prob += pulp.lpSum([v*r.output.quantity for v, r in zip(vars, self.reactions) if r.output.chemical == 'FUEL']), "FUEL"
        for c in (self.chemical_list() - {'FUEL', 'ORE'}):
            prob += pulp.lpSum([v*r.output.quantity for v, r in zip(vars, self.reactions) if r.output.chemical == c]) - \
                    pulp.lpSum([v*i.quantity for v, r in zip(vars, self.reactions) for i in r.inputs if i.chemical == c]) >= 0, \
                    f"{c}"
        prob += pulp.lpSum([v*i.quantity for v, r in zip(vars, self.reactions) for i in r.inputs if i.chemical == 'ORE']) == ore, "ORE"

        # prob.writeLP("day14/problem1.lp")
        prob.solve()
        print("Status:", pulp.LpStatus[prob.status])
        # Each of the variables is printed with it's resolved optimum value
        for v in prob.variables():
            print(v.name, "=", v.varValue)

        # The optimised objective function value is printed to the screen
        print(f"Total quantity of FUEL = ", pulp.value(prob.objective))
        return pulp.value(prob.objective)

factory = NanoFactory.read("""
10 ORE => 10 A
1 ORE => 1 B
7 A, 1 B => 1 C
7 A, 1 C => 1 D
7 A, 1 D => 1 E
7 A, 1 E => 1 FUEL
""")
print(factory.reactions)
print(factory.chemical_list())
print(factory.min_cost_of_fuel_in_ores(1))

print(NanoFactory.read("""
9 ORE => 2 A
8 ORE => 3 B
7 ORE => 5 C
3 A, 4 B => 1 AB
5 B, 7 C => 1 BC
4 C, 1 A => 1 CA
2 AB, 3 BC, 4 CA => 1 FUEL
""").min_cost_of_fuel_in_ores(1))

print(NanoFactory.read(open("day14/input1.txt").read()).min_cost_of_fuel_in_ores(1))
print(NanoFactory.read(open("day14/input1.txt").read()).max_fuel_from_ores(1000000000000))
