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
        return size - ((idx * self.n) % size)


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
# assert deck.as_list() == [3, 0, 7, 4, 1, 8, 5, 2, 9, 6]
# assert deck.where(9) == 8
# assert Deck.new_deck(20).shuffle('deal with increment 3').debug().as_list() == [0, 7, 14, 1, 8, 15, 2, 9, 16, 3, 10, 17, 4, 11, 18, 5, 12, 19, 6, 13]
lines = [line.strip() for line in open("day22/input1.txt").read().splitlines() if len(line)]
deck = Deck.new_deck(10007)
for line in lines:
    deck = deck.shuffle(line)

print(deck.where(2019))

SIZE = 119315717514047
NUMBER_OF_APPLICATIONS = 101741582076661
deck = Deck.new_deck(SIZE)
shufflers = [Deck.parse_shuffler(line) for line in lines]
# idx = 2020
# applications_map = {}
# for i in tqdm(range(NUMBER_OF_APPLICATIONS)):
#     if idx in applications_map:
#         print(f"Already calculated {idx} to equal {applications_map[idx]}")
#         idx = applications_map[idx]
#     else:
#         starting_idx = idx
#         for shuffler in reversed(shufflers):
#             idx = shuffler.backward(idx, SIZE)
#         applications_map[starting_idx] = idx
starting_idx = 2020
idx = starting_idx
applications_map = {}
counter = 0
cycles_found = 0
for i in tqdm(range(NUMBER_OF_APPLICATIONS)):
    if cycles_found > 5:
        break
    for shuffler in shufflers:
        prev_idx = idx
        idx = shuffler.forward(prev_idx, SIZE)
        applications_map[prev_idx] = idx
        counter += 1
        if idx in applications_map:
            print(f"Already calculated {idx}->{applications_map[idx]} in {counter} steps")
            cycles_found += 1
            break
        if idx == 2020:
            print(f"Found 2020 {idx} in {counter} steps")
            cycles_found += 1
            break
    # print(f"{starting_idx} -> {idx} diff {idx - starting_idx}")
print(idx)

# TODO: Find a verify the backward logic for "with N increments" shuffle
# TODO: Calculate the cycle shuffling bach