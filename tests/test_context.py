from psychopy.visual import Window, TextStim
from psychopy_scene import Context
from . import util


def test_drawables():
    ctx = Context(Window())
    stim = TextStim(win=ctx.win)
    assert ctx.Scene(stim).drawables == [stim]
    assert ctx.Scene([stim]).drawables == [stim]
    assert ctx.Scene().drawables == []
    assert ctx.Scene(stim, stim).drawables == [stim, stim]


def test_text():
    ctx = Context(Window())
    scene = ctx.text("test text")
    assert len(scene.drawables) == 1
    assert isinstance(scene.drawables[0], TextStim)
    assert getattr(scene.drawables[0], "text") == "test text"


def test_fixation():
    ctx = Context(Window())

    @(ctx.fixation(0.01).hook("setup"))
    def scene():
        assert scene.get("duration") == 0.01

    assert len(scene.drawables) == 1
    assert isinstance(scene.drawables[0], TextStim)
    assert getattr(scene.drawables[0], "text") == "+"
    scene.show()


def test_blank():
    ctx = Context(Window())

    @(ctx.blank(0.01).hook("setup"))
    def scene():
        assert scene.get("duration") == 0.01

    assert len(scene.drawables) == 1
    assert isinstance(scene.drawables[0], TextStim)
    assert getattr(scene.drawables[0], "text") == ""
    scene.show()


def test_on():
    # test multiple listeners
    listener_1 = lambda e: e
    ctx = Context(Window())
    scene_1 = ctx.Scene().on(f=listener_1).on(j=listener_1)
    assert scene_1.listeners == {"f": listener_1, "j": listener_1}

    # test override listener
    listener_2 = lambda e: e
    scene_2 = ctx.Scene().on(f=listener_1).on(f=listener_2)
    assert scene_2.listeners == {"f": listener_2}


def test_handler():
    from psychopy.data import TrialHandler, StairHandler
    from psychopy_scene import IterableHandler, ResponseHandler

    # test handler
    ctx = Context(Window())
    try:
        ctx.handler
    except Exception:
        assert True
    else:
        assert False

    # test responseHandler with TrialHandler
    trial_list = util.generate_random_list()
    ctx = Context(Window(), handler=TrialHandler(trial_list, 1, "sequential"))
    assert [e for e in ctx.handler] == trial_list
    try:
        ctx.responseHandler
    except Exception:
        assert True
    else:
        assert False

    # test responseHandler with StairHandler
    ctx = Context(Window(), handler=StairHandler(startVal=1))
    try:
        ctx.responseHandler
    except Exception:
        assert False
    else:
        assert True

    # test responseHandler with custom iterable handler
    class TestIterableHandler(IterableHandler):
        def setExp(self, exp): ...
        def __next__(self): ...
        def __iter__(self):
            return self

    ctx = Context(Window(), handler=TestIterableHandler())
    try:
        ctx.responseHandler
    except Exception:
        assert True
    else:
        assert False

    # test responseHandler with custom response handler
    class TestResponseHandler(ResponseHandler, TestIterableHandler):
        def addResponse(self, response): ...

    ctx = Context(Window(), handler=TestResponseHandler())
    try:
        ctx.responseHandler
    except Exception:
        assert False
    else:
        assert True


def test_expHandler():
    from psychopy.data import TrialHandler, ExperimentHandler
    import random

    # test addLine
    trial_list = util.generate_random_list()
    ctx = Context(Window(), handler=TrialHandler(trial_list, 1, "sequential"))
    to_row = lambda e: {"field_1": e, "field_2": str(e), "field_3": e > 5}
    for e in ctx.handler:
        ctx.addLine(**to_row(e))
    data = ctx.expHandler.getAllEntries()
    assert len(data) == len(trial_list)
    assert data == [to_row(e) for e in trial_list]

    # test addLine with extraInfo
    extraInfo = {
        "field_3": random.random() > 0.5,
        "extra_field": random.random(),
    }
    ctx = Context(
        Window(),
        handler=TrialHandler(trial_list, 1, "sequential"),
        expHandler=ExperimentHandler(extraInfo=extraInfo),
    )
    for e in ctx.handler:
        ctx.addLine(**to_row(e))
    data = ctx.expHandler.getAllEntries()
    assert len(data) == len(trial_list)
    assert data == [{**to_row(e), **extraInfo} for e in trial_list]
