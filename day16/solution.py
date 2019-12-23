import numpy as np


def fft_matrix(base_pattern, number_of_digits):
    fft = []
    for i in range(1, number_of_digits+1):
        expanded_pattern = []
        for p in base_pattern:
            expanded_pattern.extend([p]*i)
        repeat_num = ((number_of_digits+1) // len(expanded_pattern)) + 1
        repeated_pattern = expanded_pattern * repeat_num
        fft.append(repeated_pattern[1:number_of_digits+1])
    return np.array(fft, dtype=np.int32)


def str_to_digits(s):
    return np.array([int(c) for c in s], dtype=np.int32).reshape((-1, 1))


def phase(digs, m):
    mult = m @ digs
    return np.mod(np.abs(mult), 10)


def multi_phase(digs, n):
    d = digs
    m = fft_matrix([0, 1, 0, -1], len(digs))
    for i in range(n):
        d = phase(d, m)
    return d

def digits_to_str(digits, l):
    [str(i) for i in digits.reshape((-1)).tolist()]
    return "".join([str(i) for i in digits.reshape((-1)).tolist()[:l]])

example1 = str_to_digits('12345678')
m = fft_matrix([0, 1, 0, -1], len(example1))
# print(example1)
print(m)
# print(m @ example1)
# print(phase(example1, m))
assert digits_to_str(multi_phase(str_to_digits('12345678'), 4), 8) == '01029498'
assert digits_to_str(multi_phase(str_to_digits('80871224585914546619083218645595'), 100), 8) == '24176176'
assert digits_to_str(multi_phase(str_to_digits('19617804207202209144916044189917'), 100), 8) == '73745418'
assert digits_to_str(multi_phase(str_to_digits('69317163492948606335995924319873'), 100), 8) == '52432133'

input = open("day16/input1.txt").read().strip()
print(digits_to_str(multi_phase(str_to_digits(input), 100), 8))

