from psychopy.visual import TextStim
from . import util


def test_drawables():
    ctx = util.get_ctx()
    stim_1 = TextStim(win=ctx.win)
    stim_2 = TextStim(win=ctx.win)

    def setup_1():
        return stim_1

    def setup_2():
        return [stim_1]

    def setup_3():
        return stim_1, stim_2

    def setup_4():
        return [stim_1, stim_2]

    assert ctx.scene(0, on_scene_setup=setup_1).show().drawables == (stim_1,)
    assert ctx.scene(0, on_scene_setup=setup_2).show().drawables == [stim_1]
    assert ctx.scene(0, on_scene_setup=setup_3).show().drawables == (stim_1, stim_2)
    assert ctx.scene(0, on_scene_setup=setup_4).show().drawables == [stim_1, stim_2]
    assert ctx.scene(0)(setup_1).show().drawables == (stim_1,)
    assert ctx.scene(0)(setup_2).show().drawables == [stim_1]
    assert ctx.scene(0)(setup_3).show().drawables == (stim_1, stim_2)
    assert ctx.scene(0)(setup_4).show().drawables == [stim_1, stim_2]


def test_text():
    ctx = util.get_ctx()
    scene = ctx.text("test text").config(duration=0.01).show()
    drawables = list(scene.drawables)
    assert len(drawables) == 1
    assert isinstance(drawables[0], TextStim)
    assert getattr(drawables[0], "text") == "test text"


def test_fixation():
    ctx = util.get_ctx()
    scene = ctx.fixation(0.01).show()
    assert scene.duration == 0.01
    drawables = list(scene.drawables)
    assert len(drawables) == 1
    assert isinstance(drawables[0], TextStim)
    assert getattr(drawables[0], "text") == "+"


def test_blank():
    ctx = util.get_ctx()
    scene = ctx.blank(0.01).show()
    assert scene.duration == 0.01
    drawables = list(scene.drawables)
    assert len(drawables) == 1
    assert isinstance(drawables[0], TextStim)
    assert getattr(drawables[0], "text") == ""
