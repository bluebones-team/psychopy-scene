from typing import Any, Callable, Generic, Literal, Protocol, TypeVar
from typing_extensions import Self
from dataclasses import dataclass
from psychopy import core, logging
from psychopy.visual import Window
from psychopy.hardware.keyboard import Keyboard, KeyPress
from psychopy.event import Mouse
from psychopy.data import ExperimentHandler

T = TypeVar("T", bound="EventEmitter")


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

        keyborad keys: the return value of `keyboard.getKeys()`,
        mouse buttons: `mouse_left`, `mouse_middle`, `mouse_right`

        Example:
        >>> self.on(
        ...     space=lambda e: print(f"space key is pressed, keys: {e.keys}"),
        ...     mouse_left=lambda e: print(f"mouse left button is pressed, keys: {e.keys}"),
        ... )
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
        """get state. if value is `None`, raise `KeyError`.

        if you want to process `None` manually, use `self.state.get()` instead."""
        value = self.state.get(key)
        if value is None:
            raise KeyError(f"{key} is not in self.state")
        return value

    def set(self, **kwargs):
        """set state

        Example:
        >>> self.set(rt=1.1, correct=True, stim="A")"""
        self.state.update(kwargs)
        return self

    def reset(self):
        """reset state"""
        self.state.clear()
        return self


class Lifecycle:
    Stage = Literal["setup", "drawn", "frame"]

    def __init__(self):
        self.lifecycles: dict[Lifecycle.Stage, list[Callable[[], Any]]] = {
            "setup": [],
            "drawn": [],
            "frame": [],
        }

    def hook(self, stage: "Lifecycle.Stage") -> Callable[[Callable[[], Any]], Self]:
        """add lifecycle hook

        Example:
        >>> self.hook("setup")(lambda: print("setup stage is called"))
        >>> @(self.hook("setup"))
        ... def _():
        ...     print("setup stage is called")
        """
        if stage not in self.lifecycles:
            raise KeyError(f"expected one of {self.lifecycles.keys()}, but got {stage}")
        return lambda task: self.lifecycles[stage].append(task) or self

    def run_hooks(self, stage: "Lifecycle.Stage"):
        """execute lifecycle hooks"""
        logging.debug(f"emit {stage} hook")
        for task in self.lifecycles[stage]:
            task()
        return self


class Env(Protocol):
    win: Window
    kbd: Keyboard
    mouse: Mouse


class Drawable(Protocol):
    def draw(self) -> Any: ...
class Showable(EventEmitter, StateManager, Lifecycle, Drawable):
    def __init__(self, env: Env, drawables: list[Drawable]):
        """draw stimulus and handle keyboard and mouse interaction"""
        EventEmitter.__init__(self, env.kbd, env.mouse)
        StateManager.__init__(self)
        Lifecycle.__init__(self)
        self.win = env.win
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
        logging.debug("initialization")
        self.reset().set(**inital_state)
        self.clearEvents()
        self.run_hooks("setup")
        logging.debug("first draw")
        self.draw().win.flip()  # first draw
        self.set(show_time=core.getTime())
        self.run_hooks("drawn")
        while self.__has_showed:
            self.run_hooks("frame")
            self.draw().win.flip()  # redraw
            self.listen()
        return self

    def close(self):
        if not self.__has_showed:
            raise Exception(f"{self.__class__.__name__} is closed")
        self.__has_showed = False
        self.set(close_time=core.getTime())
        return self


class Scene(Showable):
    def __time_checker(self):
        if core.getTime() - self.get("show_time") >= self.get("duration"):
            self.close()

    def duration(self, duration: float | None = None):
        """
        close the scene when the duration is over, shouldn't be called twice

        Example:
        >>> self.duration(3)  # close the scene after 3 seconds
        >>> self.duration()  # should set duration state when called show method
        ... self.show(duration=3)"""
        if self.__time_checker in self.lifecycles["frame"]:
            raise Exception("duration shouldn't be multiple called")
        if duration is not None:
            self.hook("setup")(lambda: self.set(duration=duration))
        self.hook("frame")(self.__time_checker)
        return self

    def close_on(self, *keys: str):
        """close when keys are pressed, log pressed keys and response time

        Example:
        >>> self.close_on("space", "escape")"""
        cbs: dict[str, Listener[Self]] = {
            key: lambda e: self.set(keys=e.keys, response_time=core.getTime()).close()
            for key in keys
        }
        self.on(**cbs)
        return self


class SceneTool(Env):
    def __init__(self, win: Window, kbd: Keyboard, mouse: Mouse):
        self.win = win
        self.kbd = kbd
        self.mouse = mouse

    def Scene(
        self,
        drawables: Drawable | list[Drawable] | None = None,
        *deprecated_args: Drawable,
    ):
        """create a scene

        Example:
        >>> self.Scene(stim)
        >>> self.Scene([stim1, stim2])"""
        drawables = (
            drawables
            if isinstance(drawables, list)
            else [drawables] if drawables is not None else []
        )
        if deprecated_args:
            drawables.extend(deprecated_args)
            logging.warning(
                "ctx.Scene(stim1, stim2, ...) will be deprecated in psychopy_scene>=0.1.0rc2 version. Please pass multiple stimuli through a Iterable object: ctx.Scene([stim1, stim2, ...])"
            )
        return Scene(self, drawables)

    def text(self, *args, **kwargs):
        """create a text scene quickly"""
        from psychopy.visual import TextStim

        return self.Scene(TextStim(self.win, *args, **kwargs))

    def fixation(self, duration: float | None = None):
        """create a fixation cross"""
        return self.text("+").duration(duration)

    def blank(self, duration: float | None = None):
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

    def addLine(self, **kwargs: float | str):
        """add a row to the data"""
        for k, v in kwargs.items():
            self.expHandler.addData(k, v)
        self.expHandler.nextEntry()


class Context(SceneTool, DataHandler):
    def __init__(
        self,
        win: Window,
        kbd: Keyboard | None = None,
        mouse: Mouse | None = None,
        handler: IterableHandler | None = None,
        expHandler: ExperimentHandler | None = None,
    ):
        """shared parameters for each task"""
        SceneTool.__init__(self, win, kbd or Keyboard(), mouse or Mouse(win))
        DataHandler.__init__(self, handler, expHandler)
