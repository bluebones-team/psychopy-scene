from typing import Any, Callable, Generic, Literal, Protocol, TypeVar
from typing_extensions import Self
from dataclasses import dataclass
from psychopy import core, logging
from psychopy.visual import Window
from psychopy.hardware.keyboard import Keyboard, KeyPress
from psychopy.event import Mouse
from psychopy.data import ExperimentHandler

T = TypeVar("T", bound="EventEmitter")
LIFECYCLE_STAGE = Literal["setup", "drawn", "frame"]


@dataclass
class Event(Generic[T]):
    target: T
    """who emitted this event"""
    keys: list[str | KeyPress]
    """captured keys"""


class Listener(Protocol, Generic[T]):
    def __call__(self, e: Event[T]) -> Any: ...
class EventEmitter:
    __mouse_key_map = {"mouse_left": 0, "mouse_middle": 1, "mouse_right": 2}

    def __init__(self, kbd: Keyboard, mouse: Mouse):
        self.kbd = kbd
        self.mouse = mouse
        self.listeners: dict[str, Listener[Self]] = {}

    def on(self, **kfs: Listener[Self]):
        """
        add listeners for keys, includes keyboard keys and mouse buttons.

        keyborad keys: the return value of `keyboard.getKeys()`

        mouse buttons: `mouse_left`, `mouse_middle`, `mouse_right`
        """
        self.listeners.update(kfs)
        return self

    def off(self, **kfs: Listener[Self]):
        """remove listeners for keys"""
        for k in kfs:
            if k in self.listeners:
                del self.listeners[k]
            else:
                raise KeyError(f"{k} is not in listeners")
        return self

    def emit(self, keys: list[str | KeyPress]):
        """emit an event with captured keys"""
        if self.listeners and keys:
            for key, listener in self.listeners.items():
                if key == "_" or key in keys:
                    listener(Event(self, keys))
        return self

    def clearEvents(self):
        """clear all captured events"""
        self.kbd.clearEvents()
        self.mouse.clickReset()

    def listen(self):
        """listen to keyboard and mouse events"""
        kbd_keys: list[KeyPress] = self.kbd.getKeys()
        buttons: list[int] = self.mouse.getPressed()  # type: ignore
        mouse_keys = [k for k, v in self.__mouse_key_map.items() if buttons[v] == 1]
        self.emit(kbd_keys + mouse_keys)


class StateManager:
    def __init__(self):
        self.state: dict[str, Any] = {}

    def get(self, key: str):
        """get state, raise `KeyError` if value is None"""
        value = self.state.get(key)
        if value is None:
            raise KeyError(f"{key} is not in self.data")
        return value

    def set(self, **kwargs):
        """set state"""
        self.state.update(kwargs)
        return self

    def reset(self):
        """reset state"""
        self.state.clear()
        return self


class Task(Protocol):
    def __call__(self) -> Any: ...
class Lifecycle:
    def __init__(self):
        self.lifecycles: dict[LIFECYCLE_STAGE, list[Task]] = {
            "setup": [],
            "drawn": [],
            "frame": [],
        }

    def hook(self, stage: LIFECYCLE_STAGE) -> Callable[[Task], Self]:
        """add lifecycle hook"""
        if stage not in self.lifecycles:
            raise KeyError(
                f"{stage} is not in lifecycles, should be one of {self.lifecycles.keys()}"
            )
        return lambda task: self.lifecycles[stage].append(task) or self

    def run_hooks(self, stage: LIFECYCLE_STAGE):
        """execute lifecycle hooks"""
        logging.debug(f"emit {stage} hook")
        for task in self.lifecycles[stage]:
            task()
        return self


class Drawable(Protocol):
    def draw(self): ...
class Showable(EventEmitter, StateManager, Lifecycle, Drawable):
    def __init__(
        self,
        win: Window,
        kbd: Keyboard,
        mouse: Mouse,
        *drawables: Drawable,
    ):
        """
        draw stimuli and handle keyboard and mouse interaction

        :params drawables: will be drawn after setup stage
        """
        EventEmitter.__init__(self, kbd, mouse)
        StateManager.__init__(self)
        Lifecycle.__init__(self)
        self.win = win
        self.drawables = drawables
        self.__has_showed = False

    def draw(self):
        """draw all self.drawables"""
        for drawable in self.drawables:
            drawable.draw()
        return self

    def show(self, **inital_state):
        """initlize state and show the scene"""
        if self.__has_showed:
            raise Exception(f"{self.__class__.__name__} is showing")
        self.__has_showed = True
        self.reset().set(**inital_state)
        self.clearEvents()
        self.run_hooks("setup")
        self.draw().win.flip()  # first draw
        self.set(show_time=core.getTime())
        self.run_hooks("drawn")
        while self.__has_showed:
            self.run_hooks("frame")
            self.draw().win.flip()  # redraw
            self.listen()
        self.set(close_time=core.getTime())
        return self

    def close(self):
        if not self.__has_showed:
            raise Exception(f"{self.__class__.__name__} is closed")
        self.__has_showed = False
        return self


class Env(Protocol):
    win: Window
    kbd: Keyboard
    mouse: Mouse


class Scene(Showable):
    def __init__(self, env: Env, *drawables: Drawable):
        super().__init__(env.win, env.kbd, env.mouse, *drawables)

    def duration(self, duration: float | None = None):
        """
        close the scene when the duration is over, shouldn't be called twice

        Example
        >>> scene.duration(3)  # close the scene after 3 seconds
        >>> scene.duration()  # should set duration state when called show method
        ... scene.show(duration=3)

        """
        if duration is not None:
            self.hook("setup")(lambda: self.set(duration=duration))
        self.hook("frame")(
            lambda: core.getTime() - self.get("show_time") >= self.get("duration")
            and self.close()
        )
        return self

    def close_on(self, *keys: str):
        """close when keys are pressed, log pressed keys and response time"""
        cbs: dict[str, Listener[Self]] = {
            key: lambda e: self.set(keys=e.keys, response_time=core.getTime()).close()
            for key in keys
        }
        self.on(**cbs)
        return self


@dataclass
class SceneTool(Env):
    win: Window
    kbd: Keyboard
    mouse: Mouse

    def Scene(self, *drawables: Drawable):
        """create a scene"""
        return Scene(self, *drawables)

    def text(self, *args, **kwargs):
        """create a text scene quickly"""
        from psychopy.visual import TextStim

        stim = TextStim(self.win, *args, **kwargs)
        return self.Scene(stim)

    def fixation(self, duration: float):
        """create a fixation cross"""
        return self.text("+").duration(duration)

    def blank(self, duration: float):
        """create a blank screen"""
        return self.text("").duration(duration)


class IterableHandler(Protocol):
    def setExp(self, exp: ExperimentHandler): ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> Any: ...
class ResponseHandler(IterableHandler):
    def addResponse(self, response): ...
class DataHandler:
    def __init__(
        self,
        handler: IterableHandler | None = None,
        expHandler: ExperimentHandler | None = None,
    ):
        self.__handler = handler
        self.expHandler = expHandler or ExperimentHandler()
        if self.__handler is not None:
            self.__handler.setExp(self.expHandler)

    @property
    def handler(self):
        """assert the handler is not None and return it, otherwise raise an exception"""
        if self.__handler is None:
            raise Exception("handler should be set")
        return self.__handler

    @property
    def responseHandler(self) -> ResponseHandler:
        """assert the handler has addResponse method and return it, otherwise raise an exception"""
        handler = self.handler
        if not hasattr(handler, "addResponse"):
            raise Exception("handler should has addResponse method")
        return handler  # type: ignore


class Context(SceneTool, DataHandler):
    def __init__(
        self,
        win: Window,
        kbd: Keyboard | None = None,
        mouse: Mouse | None = None,
        handler: IterableHandler | None = None,
        expHandler: ExperimentHandler | None = None,
    ):
        """
        shared parameters for each task

        :params win:
        :params kbd:
        :params mouse:
        :param handler: generate stimuli for each trial
        :param expHandler:
        """
        SceneTool.__init__(self, win, kbd or Keyboard(), mouse or Mouse(win))
        DataHandler.__init__(self, handler, expHandler)

    def addLine(self, **kwargs: float | str):
        for k, v in kwargs.items():
            self.expHandler.addData(k, v)
        self.expHandler.nextEntry()
