import numpy as np
from tqdm import tqdm
import time

def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print('%r %2.2f sec' % (method.__name__, te-ts))
        return result

    return timed


# @timeit
def fft_matrix(base_pattern, number_of_digits):
    fft = []
    for i in tqdm(range(1, number_of_digits+1), desc='fft_matrix'):
        expanded_pattern = []
        for p in base_pattern:
            expanded_pattern.extend([p]*i)
        repeat_num = ((number_of_digits+1) // len(expanded_pattern)) + 1
        repeated_pattern = expanded_pattern * repeat_num
        fft.append(repeated_pattern[1:number_of_digits+1])
    return np.array(fft, dtype=np.int64)


# @timeit
def str_to_digits(s, shape=(-1,1)):
    return np.array([int(c) for c in s], dtype=np.int64).reshape(shape)


def phase(digs, m):
    mult = m @ digs
    return np.mod(np.abs(mult), 10)


# @timeit
def multi_phase(digs, m, n, st, l):
    d = digs
    print(f"{0:3} - {digits_to_str(d[:50,:])}...{digits_to_str(d[-100:,:])}")
    for i in range(n):
        # for i in tqdm(range(n), desc='phase'):
        d = phase(d, m)
        print(f"{i+1:3} - {digits_to_str(d[:50, :])}...{digits_to_str(d[-100:, :])}")
    return d[st:st+l, :]

@timeit
def upper_triangular_matrix(n):
    print('start upper triang matrix...')
    return np.triu(np.ones(n, dtype=np.int64), 0)

# @timeit
def digits_to_str(digits):
    return "".join([str(i) for i in digits.flatten().tolist()])

def part2(inputs):
    offset = int(inputs[:7])
    print(f"offset {offset}")
    big_input = inputs * 10000
    truncated_input = big_input[offset:]
    matrix = upper_triangular_matrix(len(truncated_input))
    interated = multi_phase(str_to_digits(truncated_input), matrix, 100, 0, 8)
    joined = digits_to_str(interated)
    print(f"---{joined}---")
    return joined

def phase3(digs):
    reverse_cumsum = np.flip(np.flip(digs).cumsum())
    return np.mod(np.abs(reverse_cumsum), 10)


def multi_phase3(digs, n, st, l):
    d = digs
    print(f"{0:3} - {digits_to_str(d[:50])}...{digits_to_str(d[-100:])}")
    for i in range(n):
        d = phase3(d)
        print(f"{i+1:3} - {digits_to_str(d[:50])}...{digits_to_str(d[-100:])}")
    return d[st:st+l]


def part3(inputs):
    offset = int(inputs[:7])
    print(f"offset {offset}")
    big_input = inputs * 10000
    truncated_input = big_input[offset:]
    input_ndarr = str_to_digits(truncated_input, shape=(-1))
    print(input_ndarr)
    interated = multi_phase3(input_ndarr, 100, 0, 8)
    joined = digits_to_str(interated)
    print(f"---{joined}---")
    return joined


# assert digits_to_str(multi_phase3(str_to_digits('80871224585914546619083218645595'), 100, 0, 8)) == '24176176'
# assert digits_to_str(multi_phase3(str_to_digits('19617804207202209144916044189917'), 100, 0, 8)) == '73745418'
# assert digits_to_str(multi_phase3(str_to_digits('69317163492948606335995924319873'), 100, 0, 8)) == '52432133'

input = open("day16/input1.txt").read().strip()


# print(part3('02935109699940807407585447034323'))
print(part3(input))

# print(len(input))
# print(len(input*10000))
# print(int(input[:7]))
# print(len(input*10000) - int(input[:7]))
