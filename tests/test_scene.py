from psychopy.visual import Window, TextStim
from psychopy_scene import Context, Drawable
from . import util


def test_duration():
    ctx = Context(Window())
    stim = TextStim(ctx.win)

    # test fixed duration
    @(ctx.Scene(stim).duration(0.01).hook("setup"))
    def scene_1():
        assert scene_1.get("duration") == 0.01

    scene_1.show()

    # test fixed duration won't override dynamic duration
    @(ctx.Scene(stim).duration(0.01).hook("setup"))
    def scene_2():
        assert scene_2.get("duration") == 0.01

    scene_2.show(duration=0.02)

    # test dynamic duration
    @(ctx.Scene(stim).duration().hook("setup"))
    def scene_3():
        assert scene_3.get("duration") == 0.01

    scene_3.show(duration=0.01)

    # test dynamic duration won't override fixed duration
    try:
        ctx.Scene(stim).duration().show()
    except KeyError:
        assert True
    else:
        assert False

    # test multiple calls to duration
    try:
        ctx.Scene(stim).duration(0.01).duration(0.02)
    except Exception:
        assert True
    else:
        assert False


def test_on():
    ctx = Context(Window())
    stim = TextStim(ctx.win)
    listener_1 = lambda e: e
    listener_2 = lambda e: e

    # test multiple keys
    @(ctx.Scene(stim).close_on("q", "escape").hook("setup"))
    def scene_1():
        assert scene_1.listeners.keys() == {"q", "escape"}
        scene_1.close()

    scene_1.show()

    # test multiple calls
    @(ctx.Scene(stim).close_on("a", "b").close_on("c", "d").hook("setup"))
    def scene_2():
        assert scene_2.listeners.keys() == {"a", "b", "c", "d"}
        scene_2.close()

    scene_2.show()

    # test keys override previous keys
    @(ctx.Scene(stim).close_on("e", "f").on(f=listener_1, g=listener_2).hook("setup"))
    def scene_3():
        assert scene_3.listeners.keys() == {"e", "f", "g"}
        assert scene_3.listeners["f"] is listener_1
        scene_3.close()

    scene_3.show()

    # test keys override previous keys
    @(ctx.Scene(stim).on(f=listener_1, g=listener_2).close_on("e", "f").hook("setup"))
    def scene_4():
        assert scene_4.listeners.keys() == {"e", "f", "g"}
        assert scene_4.listeners["f"] is not listener_1
        scene_4.close()

    scene_4.show()

    # test keys override previous keys
    @(ctx.Scene(stim).on(f=listener_1).close_on("f").on(f=listener_2).hook("setup"))
    def scene_5():
        assert scene_5.listeners.keys() == {"f"}
        assert scene_5.listeners["f"] is listener_2
        scene_5.close()

    scene_5.show()


def test_draw():
    ctx = Context(Window())

    class TestDrawable(Drawable):
        results = []

        def __init__(self, value):
            self.value = value

        def draw(self):
            TestDrawable.results.append(self.value)

    results = util.generate_random_list()
    scene = ctx.Scene([TestDrawable(r) for r in results])
    scene.draw()
    assert TestDrawable.results == results


def test_show():
    ctx = Context(Window())
    scene = ctx.Scene().duration(0)
    results = []

    @scene.hook("setup")
    def _():
        results.append(1)
        assert scene.get("duration") == 0
        try:
            scene.get("show_time")
        except KeyError:
            assert True
        else:
            assert False

    @scene.hook("drawn")
    def _():
        results.append(2)
        assert scene.get("show_time") is not None
        try:
            scene.get("close_time")
        except KeyError:
            assert True
        else:
            assert False

    @scene.hook("frame")
    def _():
        results.append(3)
        assert scene.get("close_time") is not None

    scene.show()
    assert results == [1, 2, 3]
