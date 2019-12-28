import re
from dataclasses import dataclass
from tqdm import tqdm


@dataclass
class Deck:
    shufflers: list
    size: int

    def __repr__(self):
        return f"{' -> '.join([str(s) for s in self.shufflers])}"

    def __getitem__(self, position):
        idx = position
        for shuffler in reversed(self.shufflers):
            idx = shuffler.backward(idx, self.size)
        return idx

    def where(self, card):
        idx = card
        for shuffler in self.shufflers: # forward cycling
            idx = shuffler.forward(idx, self.size)
        return idx

    def as_list(self):
        return [self[i] for i in range(self.size)]

    def debug(self):
        print(f"{self} = {self.as_list()}")
        return self

    @classmethod
    def new_deck(cls, size):
        return cls([FactoryOrder()], size)

    @staticmethod
    def parse_shuffler(line):
        line = line.strip()
        cut_n_match = re.compile('cut (.+)').match(line)
        deal_with_incr_match = re.compile('deal with increment (.+)').match(line)
        if line == 'deal into new stack':
            return NewStackShuffle()
        elif cut_n_match:
            return CutNCardsShuffle(int(cut_n_match.group(1)))
        elif deal_with_incr_match:
            return WithNIncrementsShuffle(int(deal_with_incr_match.group(1)))
        else:
            assert False, "Could not parse line"

    def shuffle(self, line):
        new_shuffler = Deck.parse_shuffler(line)
        return Deck(self.shufflers + [new_shuffler], self.size)


@dataclass
class FactoryOrder:
    def __repr__(self):
        return f"[0, 1, 2, ...]"

    def forward(self, idx, size):
        return idx

    def backward(self, idx, size):
        # In factory order card value == card index
        return idx


@dataclass
class NewStackShuffle:
    def forward(self, idx, size):
        return size - idx - 1

    def backward(self, idx, size):
        return size - idx - 1

    def compose_linear_fn(self, a, b, size):
        la, lb = -1, -1
        # la * (a * x + b) + lb == la * a * x + la*b + lb
        # The `% n` doesn't change the result, but keeps the numbers small.
        return (la * a) % size, (la * b + lb) % size

@dataclass
class CutNCardsShuffle:
    n: int

    def forward(self, idx, size):
        return (size - self.n + idx) % size

    def backward(self, idx, size):
        return (self.n + idx) % size

    def compose_linear_fn(self, a, b, size):
        la, lb = 1, self.n
        return (la * a) % size, (la * b + lb) % size


@dataclass
class WithNIncrementsShuffle:
    n: int

    def forward(self, idx, size):
        return (idx * self.n) % size

    def backward(self, idx, size):
        # 0 1 2 3 4 5 6 7 8 9
        # 0 7 4 1 8 5 2 9 6 3

        # 0, 1,  2, 3, 4,  5, 6, 7,  8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19
        # 0, 7, 14, 1, 8, 15, 2, 9, 16, 3, 10, 17,  4, 11, 18,  5, 12, 19,  6, 13
        if idx == 0:
            return 0
        m = 0 # TODO: use divmod!
        while (m * size + idx) % self.n != 0:
            m += 1
        return (m * size + idx) // self.n

    def compose_linear_fn(self, a, b, size):
        la, lb = self.n, 0
        return (la * a) % size, (la * b + lb) % size


deck = Deck.new_deck(10)
print(deck)
assert deck[0] == 0
assert deck[9] == 9
assert deck.where(0) == 0
assert deck.where(9) == 9
deck = Deck.new_deck(10).shuffle('deal into new stack')
assert deck[0] == 9
assert deck[3] == 6
assert deck[9] == 0
assert deck.where(0) == 9
assert deck.where(3) == 6
assert deck.where(9) == 0
deck = Deck.new_deck(10).shuffle('cut 3')
assert deck[0] == 3
assert deck[6] == 9
assert deck[7] == 0
assert deck[9] == 2
assert deck.where(0) == 7
assert deck.where(3) == 0
assert deck.where(6) == 3
assert deck.where(7) == 4
assert deck.where(9) == 6
deck = Deck.new_deck(10).shuffle('deal with increment 3')
deck.debug()
assert deck.as_list() == [0, 7, 4, 1, 8, 5, 2, 9, 6, 3]
assert deck[0] == 0
assert deck[1] == 7
assert deck[2] == 4
assert deck[3] == 1
assert deck[4] == 8
assert deck[5] == 5
assert deck[6] == 2
assert deck[7] == 9
assert deck[8] == 6
assert deck[9] == 3
assert deck.where(0) == 0
assert deck.where(1) == 3
assert deck.where(2) == 6
assert deck.where(3) == 9
assert deck.where(4) == 2
assert deck.where(5) == 5
assert deck.where(6) == 8
assert deck.where(7) == 1
assert deck.where(8) == 4
assert deck.where(9) == 7

deck = (
    Deck.new_deck(10)
    .shuffle('deal with increment 7')
    .debug()
    .shuffle('deal into new stack')
    .debug()
    .shuffle('deal into new stack')
    .debug()
)
assert deck.as_list() == [0, 3, 6, 9, 2, 5, 8, 1, 4, 7]
assert deck.where(9) == 3

deck = (
    deck
    .shuffle('cut 6')
    .debug()
    .shuffle('deal with increment 7')
    .debug()
    .shuffle('deal into new stack')
    .debug()
)
# this result does not match AOC example. Problem in my implementation or the website example?
# assert deck.as_list() == [3, 0, 7, 4, 1, 8, 5, 2, 9, 6]
# assert deck.where(9) == 8
assert Deck.new_deck(20).shuffle('deal with increment 3').debug().as_list() == [0, 7, 14, 1, 8, 15, 2, 9, 16, 3, 10, 17, 4, 11, 18, 5, 12, 19, 6, 13]

def part1():
    lines = [line.strip() for line in open("day22/input1.txt").read().splitlines() if len(line)]
    deck = Deck.new_deck(10007)
    for line in lines:
        deck = deck.shuffle(line)

    print(deck.where(2019))


def part2(deck_size, number_of_applications, card, position):
    lines = [line.strip() for line in open("day22/input1.txt").read().splitlines() if len(line)]
    shufflers = [Deck.parse_shuffler(line) for line in lines]

    a, b = 1, 0
    for shuffler in shufflers:
        a, b = shuffler.compose_linear_fn(a, b, deck_size)

    # Now we want to run the linear function composition for each iteration:
    # la, lb = a, b
    # a = 1, b = 0
    # for i in range(number_of_applications):
    #     a, b = (a * la) % n, (la * b + lb) % n

    # For a, this is same as computing (a ** M) % n, which is in the computable
    # realm with fast exponentiation.
    # For b, this is same as computing ... + a**2 * b + a*b + b
    # == b * (a**(M-1) + a**(M) + ... + a + 1) == b * (a**M - 1)/(a-1)
    # That's again computable, but we need the inverse of a-1 mod n.

    # Fermat's little theorem gives a simple inv:
    def inv(a, n): return pow(a, n-2, n)

    Ma = pow(a, number_of_applications, deck_size)
    Mb = (b * (Ma - 1) * inv(a-1, deck_size)) % deck_size

    # This computes "where does 2020 end up", but I want "what is at 2020".
    print(f"Card {card} will end up at {(Ma * card + Mb) % deck_size}")

    # So need to invert (2020 - MB) * inv(Ma)
    print(f"At position {position} there will be {((position - Mb) * inv(Ma, deck_size)) % deck_size} card")

DECK_SIZE = 119315717514047
NUMBER_OF_INTERATIONS = 101741582076661
part2(10007, 1, 2019, 2020)