from psychopy.visual import TextStim
from psychopy import core
from psychopy_scene import Drawable
from . import util


def test_duration():
    ctx = util.get_ctx()
    stim = TextStim(ctx.win)
    scene = ctx.scene(duration=0.1)(lambda: stim)
    assert scene.duration == 0.1
    scene.config(duration=0.2)
    assert scene.duration == 0.2
    scene.config(duration=None)
    assert scene.duration == 0.2
    scene.show()
    duration = core.getTime() - scene.get("show_time")
    diff = duration - scene.duration
    print(f"duration diff: {diff}")
    assert abs(diff) < 0.05


def test_close_on():
    ctx = util.get_ctx()
    stim = TextStim(ctx.win)

    _ = ctx.scene(close_on="key_space")(lambda: stim)
    assert _.callbacks["key_space"] == _.close

    nums = [1, 2, 3]
    _ = ctx.scene(close_on=(f"key_{k}" for k in nums))(lambda: stim)
    for k in nums:
        assert _.callbacks[f"key_{k}"] == _.close

    _ = ctx.scene(close_on=("key_q", "mouse_middle"))(lambda: stim)
    _.config(close_on=["scene_drawn"])
    assert _.callbacks["key_q"] == _.close
    assert _.callbacks["mouse_middle"] == _.close
    assert _.callbacks["scene_drawn"] == _.close

    util.except_error(lambda: ctx.scene(close_on="key_e_"), ValueError)
    util.except_error(lambda: ctx.scene(close_on="ke_space"), ValueError)
    util.except_error(lambda: ctx.scene(close_on="mOuse_middle"), ValueError)
    util.except_error(lambda: ctx.scene(close_on="mouse_any"), ValueError)
    util.except_error(lambda: ctx.scene(close_on="scene_setu"), ValueError)
    util.except_error(lambda: ctx.scene(close_on="scene_draw"), ValueError)
    util.except_error(lambda: ctx.scene(close_on="scene_framee"), ValueError)

    stim.text = "should close on: key_q"
    ctx.scene(close_on=["key_escape", "key_q"])(lambda: stim).show()

    stim.text = "should close on: mouse_middle"
    ctx.scene(close_on=["key_escape", "mouse_middle"])(lambda: stim).show()

    stim.text = "shouldn't show on screen"
    ctx.scene(close_on=["key_escape", "scene_drawn"])(lambda: stim).show()


def test_on():
    ctx = util.get_ctx()
    stim = TextStim(ctx.win)
    cb_1 = lambda: None
    cb_2 = lambda: None

    # invalid event name
    util.except_error(lambda: ctx.scene().on("key_Q", cb_1), ValueError)
    util.except_error(lambda: ctx.scene().on("keY_space", cb_1), ValueError)
    util.except_error(lambda: ctx.scene().on("on_mouse_middle", cb_1), ValueError)
    util.except_error(lambda: ctx.scene().on("_mouse_right", cb_1), ValueError)
    util.except_error(lambda: ctx.scene().on("scene_sEtup", cb_1), ValueError)
    util.except_error(lambda: ctx.scene().on("onscene_drawn", cb_1), ValueError)
    util.except_error(lambda: ctx.scene().on("Scene_frame", cb_1), ValueError)

    # overlap event name
    util.except_error(lambda: ctx.scene(close_on=["key_a"], on_key_a=cb_1), Exception)
    util.except_error(
        lambda: ctx.scene(on_mouse_right=cb_1).on("mouse_right", cb_2), Exception
    )
    util.except_error(
        lambda: ctx.scene(close_on=["scene_frame"]).on("scene_frame", cb_2), Exception
    )
    util.except_error(
        lambda: ctx.scene().on("key_c", cb_2).config(close_on=["key_c"]), Exception
    )
    util.except_error(
        lambda: ctx.scene(close_on=["scene_setup"])(lambda: stim), Exception
    )
    util.except_error(lambda: ctx.scene(on_scene_setup=cb_1)(lambda: stim), Exception)
    util.except_error(
        lambda: ctx.scene()(lambda: stim).on("scene_setup", cb_2), Exception
    )

    stim.text = "text should follow mouse"
    ctx.scene(
        close_on="key_escape", on_scene_frame=lambda: stim.setPos(ctx.mouse.getPos())
    )(lambda: stim).show()

    stim.text = "text should be colored on: key_space, mouse_right"
    ctx.scene(
        close_on="key_escape",
        on_key_space=lambda: stim.setColor("red"),
        on_mouse_right=lambda: stim.setColor("green"),
    )(lambda: stim).show()

    stim.text = "should show any key you press"
    _ = ctx.scene(
        close_on="key_escape",
        on_key_any=lambda: stim.setText(f"key: {_.get('events')[-1].key}"),
    )(lambda: stim)
    _.show()


def test_draw():
    class TestDrawable(Drawable):
        results = []

        def __init__(self, value):
            self.value = value

        def draw(self):
            TestDrawable.results.append(self.value)

    results = util.generate_random_list()
    ctx = util.get_ctx()
    ctx.scene(duration=0)(lambda: (TestDrawable(r) for r in results)).show()
    assert TestDrawable.results == results


def test_show():
    ctx = util.get_ctx()
    results = []

    def on_setup():
        results.append(1)
        assert scene.duration == 0
        util.except_error(lambda: scene.get("show_time"), KeyError)
        return []

    def on_drawn():
        results.append(2)
        assert scene.get("show_time") is not None
        util.except_error(lambda: scene.get("events"), KeyError)

    def on_frame():
        results.append(3)
        assert scene.get("events") is not None

    scene = ctx.scene(
        duration=1,
        on_scene_setup=on_setup,
        on_scene_drawn=on_drawn,
        on_scene_frame=on_frame,
    )
    scene.config(duration=0).show()
    assert results == [1, 2, 3]
