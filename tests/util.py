import random

ctx = None


def get_ctx():
    from psychopy_scene import Context
    from psychopy.visual import Window

    global ctx
    if ctx is None:
        ctx = Context(Window())
    return ctx


def generate_random_list(max_length=30):
    length = random.randint(1, max_length)
    return random.choices(range(length), k=random.randint(1, length))


def except_error(fn, expected_error):
    try:
        fn()
        assert False, f"Expected {expected_error} but no error was raised"
    except expected_error:
        assert True, f"Expected {expected_error} and it was raised"
