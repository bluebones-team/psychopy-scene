import random


def generate_random_list(max_length=30):
    length = random.randint(1, max_length)
    return random.choices(range(length), k=random.randint(1, length))
