input_seq = [1, 0, 0, 3, 1, 1, 2, 3, 1, 3, 4, 3, 1, 5, 0, 3, 2, 13, 1, 19, 1, 6, 19, 23, 2, 6, 23, 27, 1, 5, 27,
             31, 2, 31, 9, 35, 1, 35, 5, 39, 1, 39, 5, 43, 1, 43, 10, 47, 2, 6, 47, 51, 1, 51, 5, 55, 2, 55,
             6, 59, 1, 5, 59, 63, 2, 63, 6, 67, 1, 5, 67, 71, 1, 71, 6, 75, 2, 75, 10, 79, 1, 79, 5, 83, 2, 83,
             6, 87, 1, 87, 5, 91, 2, 9, 91, 95, 1, 95, 6, 99, 2, 9, 99, 103, 2, 9, 103, 107, 1, 5, 107, 111, 1,
             111, 5, 115, 1, 115, 13, 119, 1, 13, 119, 123, 2, 6, 123, 127, 1, 5, 127, 131, 1, 9, 131, 135, 1,
             135, 9, 139, 2, 139, 6, 143, 1, 143, 5, 147, 2, 147, 6, 151, 1, 5, 151, 155, 2, 6, 155, 159, 1, 159,
             2, 163, 1, 9, 163, 0, 99, 2, 0, 14, 0]

input_seq[1] = 12
input_seq[2] = 2


def execute_seq(input_seq: [int]) -> [int]:
    seq = input_seq.copy()
    position = 0
    while seq[position] != 99:
        if seq[position] == 1:
            seq[seq[position + 3]] = seq[seq[position + 1]] + seq[seq[position + 2]]
        elif seq[position] == 2:
            seq[seq[position + 3]] = seq[seq[position + 1]] * seq[seq[position + 2]]
        else:
            raise Exception(f"Wrong opcode at position {position}")
        position += 4
    return seq


def find_noun_verb(nouns: [int], verbs: [int], desired_output: int, input_seq: [int]) -> (int, int):
    for noun in nouns:
        for verb in verbs:
            modified_seq = input_seq.copy()
            modified_seq[1] = noun
            modified_seq[2] = verb
            out_seq = execute_seq(modified_seq)
            if out_seq[0] == desired_output:
                return noun, verb
    return None, None


print(execute_seq(input_seq)[0])

print(find_noun_verb(range(100), range(100), 19690720, input_seq))