from dataclasses import dataclass
from itertools import groupby

@dataclass
class Code:
    number: int
    str: str
    digits: [int]

    @classmethod
    def from_number(cls, number):
        s = str(number)
        return Code(number, s, [int(c) for c in s])

    def next(self):
        return Code.from_number(self.number + 1)

    def equals(self, another) -> bool:
        return self.number == another.number


def non_decreasing_digits(c: Code) -> bool:
    for i in range(1,6):
        if c.digits[i-1] > c.digits[i]:
            return False
    return True


def same_adjasent_digits(c: Code) -> bool:
    for i in range(1,6):
        if c.digits[i-1] == c.digits[i]:
            return True
    return False

def same_adjasent_digits2(c: Code) -> bool:
    doubled_digits = []
    for i in range(1,6):
        if c.digits[i-1] == c.digits[i]:
            doubled_digits.append(c.digits[i])
    freqs = {key: len(list(group)) for key, group in groupby(doubled_digits)}
    group_sizes = sorted(freqs.values())
    return 1 in group_sizes


def generator(start, end):
    code = Code.from_number(start)
    end_code = Code.from_number(end)
    while code.number <= end_code.number:
        yield code
        code = code.next()

assert non_decreasing_digits(Code.from_number(123456))
assert not non_decreasing_digits(Code.from_number(121430))

assert same_adjasent_digits(Code.from_number(122345))
assert not same_adjasent_digits(Code.from_number(123456))

assert same_adjasent_digits2(Code.from_number(123455))
assert same_adjasent_digits2(Code.from_number(112233))
assert same_adjasent_digits2(Code.from_number(111122))
assert not same_adjasent_digits2(Code.from_number(111222))
assert same_adjasent_digits2(Code.from_number(112222))
assert not same_adjasent_digits2(Code.from_number(111111))
assert not same_adjasent_digits2(Code.from_number(122222))
assert not same_adjasent_digits2(Code.from_number(123333))
assert not same_adjasent_digits2(Code.from_number(123444))
assert same_adjasent_digits2(Code.from_number(123455))
assert not same_adjasent_digits2(Code.from_number(123456))

l = generator(109165, 576723)
l = filter(non_decreasing_digits, l)
l = filter(same_adjasent_digits2, l)
l = list(l)
print(len(l))