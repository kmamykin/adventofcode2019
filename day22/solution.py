import re
from dataclasses import dataclass


# Fermat's little theorem gives a simple inv:
# Meaning (a * inv(a, n)) % n = 1
def inv(a, n): return pow(a, n - 2, n)
assert (5 * inv(5, 7))%7 == 1
print([inv(i, 11) for i in range(11)])


@dataclass
class Shuffle:
    a: int
    b: int

    def forward(self, idx, size):
        return (self.a * idx + self.b) % size

    def backward(self, idx, size):
        # inverting the forward equasion:
        # x' = (a * x + b) mod n
        return ((idx - self.b)*inv(self.a, size)) % size

    def compose(self, other, size):
        # la * (a * x + b) + lb == la * a * x + la*b + lb
        # The `% size` doesn't change the result, but keeps the numbers small.
        return Shuffle((self.a * other.a) % size, (self.a * other.b + self.b) % size)

    def apply(self, number_of_applications, size):
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

        Ma = pow(self.a, number_of_applications, size)
        Mb = (self.b * (Ma - 1) * inv(self.a - 1, size)) % size

        return Shuffle(Ma, Mb)


@dataclass
class Deck:
    shuffler: Shuffle
    size: int

    def __repr__(self):
        return f"Deck({self.size}, {self.shuffler})"

    def __getitem__(self, position):
        return self.at(position)

    def at(self, position):
        return self.shuffler.backward(position, self.size)

    def where(self, card):
        return self.shuffler.forward(card, self.size)

    def at_list(self):
        """
        :return: an image of the deck, with cards in their respective positions
        """
        return [self.at(i) for i in range(self.size)]

    def at_list2(self):
        """
        Same semantic as at_list() but calculated with forward shuffler's function
        at_list2() should always == at_list() and is used to validate forward and backward (inverse) function
        """
        result = list([0 for i in range(self.size)])
        for i in range(self.size):
            result[self.where(i)] = i
        return result

    def where_list(self):
        """
        :return: an array where each card ends up
        """
        return [self.where(i) for i in range(self.size)]

    def debug(self):
        print(f"{self} => {self.at_list()}")
        return self

    @classmethod
    def new_deck(cls, size):
        return cls(identity_shuffle(), size)

    @staticmethod
    def parse_shuffler(line):
        line = line.strip()
        cut_n_match = re.compile('cut (.+)').match(line)
        deal_with_incr_match = re.compile('deal with increment (.+)').match(line)
        if line == 'deal into new stack':
            return new_stack_shuffle()
        elif cut_n_match:
            return cut_n_cards_shuffle(int(cut_n_match.group(1)))
        elif deal_with_incr_match:
            return with_n_increments_shuffle(int(deal_with_incr_match.group(1)))
        else:
            assert False, "Could not parse line"

    def shuffle(self, line):
        new_shuffle = Deck.parse_shuffler(line)
        combined = new_shuffle.compose(self.shuffler, self.size)
        return Deck(combined, self.size)

    def reshuffle(self, number_of_applications):
        return Deck(self.shuffler.apply(number_of_applications, self.size), self.size)


def identity_shuffle():
    return Shuffle(1, 0)


def new_stack_shuffle():
    return Shuffle(-1, -1)


def cut_n_cards_shuffle(n):
    return Shuffle(1, -n)


def with_n_increments_shuffle(n):
    return Shuffle(n, 0)

# IMPORTANT! Need to use a prime size for the deck, otherwise the inverse transform does not work
deck = Deck.new_deck(11)
assert deck[0] == 0
assert deck[9] == 9
assert deck.where(0) == 0
assert deck.where(9) == 9
deck = Deck.new_deck(11).shuffle('deal into new stack')
print(deck)
assert deck.at_list() == [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
assert deck.at_list2() == [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
assert deck.where_list() == [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

deck = Deck.new_deck(11).shuffle('cut 3')
print(deck)
assert deck.at_list() == [3, 4, 5, 6, 7, 8, 9, 10, 0, 1, 2]
assert deck.at_list2() == [3, 4, 5, 6, 7, 8, 9, 10, 0, 1, 2]
assert deck.where_list() == [8, 9, 10, 0, 1, 2, 3, 4, 5, 6, 7]

deck = Deck.new_deck(11).shuffle('deal with increment 3')
print(deck)
assert deck.at_list() == [0, 4, 8, 1, 5, 9, 2, 6, 10, 3, 7]
assert deck.at_list2() == [0, 4, 8, 1, 5, 9, 2, 6, 10, 3, 7]
assert deck.where_list() == [0, 3, 6, 9, 1, 4, 7, 10, 2, 5, 8]

deck = (
    Deck.new_deck(11)
    .shuffle('deal with increment 7')
    .debug()
    .shuffle('deal into new stack')
    .debug()
    .shuffle('deal into new stack')
    .debug()
)
assert deck.at_list() == [0, 8, 5, 2, 10, 7, 4, 1, 9, 6, 3]

deck = (
    deck
    .shuffle('cut 6')
    .debug()
    .shuffle('deal with increment 7')
    .debug()
    .shuffle('deal into new stack')
    .debug()
)
assert deck.at_list() == [6, 8, 10, 1, 3, 5, 7, 9, 0, 2, 4]


def part1():
    lines = [line.strip() for line in open("day22/input1.txt").read().splitlines() if len(line)]
    deck = Deck.new_deck(10007)
    for line in lines:
        deck = deck.shuffle(line)
    return deck


deck = part1()
assert deck.where(2019) == 4775
assert deck.at(4775) == 2019


def part2(deck_size, number_of_applications):
    lines = [line.strip() for line in open("day22/input1.txt").read().splitlines() if len(line)]
    deck = Deck.new_deck(deck_size)
    for line in lines:
        deck = deck.shuffle(line)

    deck = deck.reshuffle(number_of_applications)
    return deck


DECK_SIZE = 119315717514047
NUMBER_OF_INTERATIONS = 101741582076661
deck = part2(DECK_SIZE, NUMBER_OF_INTERATIONS)
print(f"At position 2020 there will be {deck.at(2020)} card")
# 37889219674304