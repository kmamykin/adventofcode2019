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


@dataclass
class CutNCardsShuffle:
    n: int

    def forward(self, idx, size):
        return (size - self.n + idx) % size

    def backward(self, idx, size):
        return (self.n + idx) % size


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
        m = 0
        while (m * size + idx) % self.n != 0:
            m += 1
        return (m * size + idx) // self.n


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


def part2():
    DECK_SIZE = 119315717514047
    NUMBER_OF_INTERATIONS = 101741582076661
    lines = [line.strip() for line in open("day22/input1.txt").read().splitlines() if len(line)]
    shufflers = list(reversed([Deck.parse_shuffler(line) for line in lines]))
    n_shufflers = len(shufflers)
    assert n_shufflers == 100
    idx_out = 2020
    # idx = starting_idx
    saved_results = {}
    saved_steps = {}
    total_number_of_steps = NUMBER_OF_INTERATIONS * n_shufflers
    step = 0
    while True:
        shuffler = shufflers[step % n_shufflers]
        idx_in = idx_out
        idx_out = shuffler.backward(idx_in, DECK_SIZE)

        if idx_in in saved_results and idx_out == saved_results[idx_in]:
            print(f"Found cycle @step={step} shuffle={step%n_shufflers} [{idx_in}]->{idx_out} {(step - saved_steps[idx_in])} steps back")
            if (step - saved_steps[idx_in]) % n_shufflers == 0:
                print(f"FAST FORWARDING!")
                break
        saved_results[idx_in] = idx_out
        saved_steps[idx_in] = step
        step += 1
        if step >= total_number_of_steps:
            break
    print(idx_out)

part2()