import re


class Deck:

    def __init__(self, cards, size):
        self.cards = cards
        self.size = size

    def __repr__(self):
        return f"{self.cards}"

    def __getitem__(self, item):
        return self.cards[item]

    def where(self, card):
        return self.cards.where(card)

    def as_list(self):
        return [self[i] for i in range(self.size)]

    def debug(self):
        print(f"{self} = {self.as_list()}")
        return self

    @classmethod
    def new_deck(cls, size):
        return cls(FactoryOrder(size), size)

    def shuffle(self, line):
        line = line.strip()
        cut_n_match = re.compile('cut (.+)').match(line)
        deal_with_incr_match = re.compile('deal with increment (.+)').match(line)
        if line == 'deal into new stack':
            return Deck(NewStackShuffle(self), self.size)
        elif cut_n_match:
            return Deck(CutNCardsShuffle(self, int(cut_n_match.group(1))), self.size)
        elif deal_with_incr_match:
            return Deck(WithNIncrementsShuffle(self, int(deal_with_incr_match.group(1))), self.size)
        else:
            assert False, "Could not parse line"


class FactoryOrder:
    def __init__(self, size):
        self.size = size

    def __repr__(self):
        return f"[0, ..., {self.size-1}]"

    def __getitem__(self, position):
        return position

    def where(self, card):
        # In factory order card value == card index
        return card


class NewStackShuffle:
    def __init__(self, deck):
        self.deck = deck

    def __repr__(self):
        return f"{self.deck} -> new_stack()"

    def __getitem__(self, idx):
        return self.deck[self.deck.size - idx - 1]

    def where(self, card):
        return self.deck.size - self.deck.where(card) - 1


class CutNCardsShuffle:
    def __init__(self, deck, n):
        self.deck = deck
        self.n = n
        deck_indices = list(range(self.deck.size))
        shuffled_indices = [(self.deck.size - self.n + i) % self.deck.size for i in deck_indices]
        self.shuffled_to_deck = dict(zip(shuffled_indices, deck_indices))
        self.deck_to_shuffled = dict(zip(deck_indices, shuffled_indices))

    def __repr__(self):
        return f"{self.deck} -> cut({self.n})"

    def __getitem__(self, idx):
        return self.deck[self.shuffled_to_deck[idx]]

    def where(self, card):
        return self.deck_to_shuffled[self.deck.where(card)]


class WithNIncrementsShuffle:
    def __init__(self, deck, n):
        self.deck = deck
        self.n = n
        deck_indices = list(range(self.deck.size))
        shuffled_indices = [(i * self.n) % self.deck.size for i in deck_indices]
        self.shuffled_to_deck = dict(zip(shuffled_indices, deck_indices))
        self.deck_to_shuffled = dict(zip(deck_indices, shuffled_indices))

    def __repr__(self):
        return f"{self.deck} -> incr({self.n})"

    def __getitem__(self, idx):
        return self.deck[self.shuffled_to_deck[idx]]

    def where(self, card):
        return self.deck_to_shuffled[self.deck.where(card)]


deck = Deck.new_deck(10)
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

lines = [line.strip() for line in open("day22/input1.txt").read().splitlines() if len(line)]
deck = Deck.new_deck(10007)
for line in lines:
    deck = deck.shuffle(line)

print(deck.where(2019))

deck = Deck.new_deck(101741582076661)
for line in lines:
    deck = deck.shuffle(line)
print(deck[2020])
