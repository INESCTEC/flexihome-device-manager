import string, random


def generate_random_sequence_id():
    sequence_id = ""
    for i, n in zip(range(5), [8, 5, 5, 5, 12]):
        part = "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(n)
        )
        sequence_id = sequence_id + "-" + part

    return sequence_id[1:]