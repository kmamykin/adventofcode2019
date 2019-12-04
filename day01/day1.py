import itertools as it

def fuel_req(mass: int) -> int:
    result = (mass//3) - 2
    return result if result > 0 else 0

def module_mass_inputs() -> [int]:
    with open("day1-input.txt") as f:
        result = map(lambda s: s.strip(), f.readlines())
        return list(map(int, result))

result = map(fuel_req, module_mass_inputs())
result = sum(result)
print(result)


def any_mass_left(masses: [int]) -> bool:
    return any(list(map(lambda e: e > 0, masses)))


def part2(inputs: [int]) -> int:
    current_masses = inputs
    total_sum = 0
    while any_mass_left(current_masses):
        current_masses = list(map(fuel_req, current_masses))
        print(sum(current_masses))
        total_sum += sum(current_masses)
    return total_sum

print(part2(module_mass_inputs()))