from collections.abc import Iterable
import re
from typing import Any, Callable, Generic, ParamSpec, Protocol
from psychopy import core
from psychopy.visual import Window, TextStim
from psychopy.hardware.keyboard import Keyboard, KeyPress
from psychopy.event import Mouse
from psychopy.data import ExperimentHandler

SP = ParamSpec("SP")
P = ParamSpec("P")


class Event:
    def __init__(self, key: str | KeyPress):
        self.key = key
        self.timestamp = core.getTime()


class Callback(Protocol):
    def __call__(self) -> Any: ...
class PubSub:
    __callback_regex = r"^scene_(setup|drawn|frame)|mouse_(left|middle|right)|key_(any|(num_)?(\d|[a-z]+))$"

    def __init__(self, callbacks: dict[str, Callback]):
        self.callbacks: dict[str, Callback] = {}
        for k, v in callbacks.items():
            self.on(k, v)

    def on(self, name: str, callback: Callback):
        """add callback by name, raise if name is already defined"""
        cb = self.callbacks.get(name)
        if cb is not None:
            raise Exception(f"{name} is already defined")
        if re.fullmatch(PubSub.__callback_regex, name) is None:
            raise ValueError(f"{name} is not a valid callback name")
        if not callable(callback):
            raise TypeError(f"{callback} should be a callable, but got {type(v)}")
        self.callbacks[name] = callback
        return self

    def off(self, name: str):
        self.callbacks.pop(name)
        return self

    def emit(self, name: str):
        """emit callback by name"""
        cb = self.callbacks.get(name)
        if cb is not None:
            cb()
        return self


class DataCollector:
    def __init__(self):
        self.data: dict[str, Any] = {}

    def get(self, key: str):
        """get data. if value is `None`, raise `KeyError`.

        if you want to process `None` manually, use `self.data.get()` instead."""
        value = self.data.get(key)
        if value is None:
            raise KeyError(f"{key} is not in self.data")
        return value

    def set(self, key: str, value):
        """set data"""
        self.data[key] = value
        return self


class Drawable(Protocol):
    def draw(self) -> Any: ...
class Scene(Generic[SP], DataCollector, PubSub):
    __mouse_key_map = {"left": 0, "middle": 1, "right": 2}
    duration: float | None = None
    drawables: Iterable[Drawable] = []

    def __init__(self, env: "Context"):
        DataCollector.__init__(self)
        PubSub.__init__(self, {})
        self.win = env.win
        self.kbd = env.kbd
        self.mouse = env.mouse
        self.__is_showing = False
        self.config()

    def __call__(self, setup: Callable[P, Drawable | Iterable[Drawable]]) -> "Scene[P]":
        return self.on("scene_setup", setup)  # type: ignore

    def config(
        self,
        duration: float | None = None,
        close_on: str | Iterable[str] | None = None,
        **callbacks: Callback,
    ):
        """configure the scene

        :param duration: duration of the scene in seconds.
        :param close_on: a iterable of event names to close the scene.

        Example:
        >>> scene.config(duration=1, close_on=["key_escape", "mouse_left"])
        """
        if duration is not None:
            self.duration = duration
        if close_on:
            if isinstance(close_on, str):
                close_on = (close_on,)
            for k in close_on:
                self.on(k, self.close)
        for k, v in callbacks.items():
            if not k.startswith("on_"):
                raise ValueError(f"{k} should start with 'on_'")
            self.on(k[3:], v)
        return self  # type: ignore

    def draw(self):
        """draw all self.drawables"""
        for drawable in self.drawables:
            drawable.draw()
        return self

    def show(self, *args: SP.args, **kwargs: SP.kwargs):
        """show the scene with stimulus params"""
        if self.__is_showing:
            raise Exception(f"{self.__class__.__name__} is showing")
        self.__is_showing = True
        self.data = {}
        self.kbd.clearEvents()
        self.mouse.clickReset()
        # emit on_scene_setup
        cb = self.callbacks.get("scene_setup")
        if cb is None:
            raise Exception(f"on_scene_setup is not defined")
        results = cb(*args, **kwargs)
        if results is None:
            raise Exception(f"on_scene_setup should return drawables")
        self.drawables = results if isinstance(results, Iterable) else (results,)
        # first draw
        self.draw().win.flip()
        self.set("show_time", core.getTime())
        self.emit("scene_drawn")
        # capture interaction events
        events = []
        self.set("events", events)
        while self.__is_showing:
            # redraw
            self.emit("scene_frame")
            self.draw().win.flip()
            # listen to keyboard and mouse events
            buttons = self.mouse.getPressed()
            for k in self.kbd.getKeys():
                events.append(Event(k))
                self.emit(f"key_{k.value}")
                self.emit("key_any")
            for k, v in self.__mouse_key_map.items():
                if buttons[v] == 1:
                    events.append(Event(k))
                    self.emit(f"mouse_{k}")
            if (
                self.duration is not None
                and core.getTime() - self.get("show_time") >= self.duration
            ):
                self.close()
        return self

    def close(self):
        if not self.__is_showing:
            raise Exception(f"{self.__class__.__name__} is closed")
        self.__is_showing = False
        return self


class Context:
    def __init__(
        self,
        win: Window,
        kbd: Keyboard | None = None,
        mouse: Mouse | None = None,
        exp: ExperimentHandler | None = None,
    ):
        """global parameters for each task"""
        self.win = win
        self.kbd = kbd or Keyboard()
        self.mouse = mouse or Mouse(win)
        self.exp = exp or ExperimentHandler()

    @property
    def scene(self):
        return Scene(self).config

    def text(self, *args, **kwargs):
        """create static text scene quickly"""
        stim = TextStim(self.win, *args, **kwargs)
        return self.scene()(lambda: stim)

    def fixation(self, duration: float | None = None):
        return self.text("+").config(duration=duration)

    def blank(self, duration: float | None = None):
        return self.text("").config(duration=duration)

    def addRow(self, **kwargs: float | str | bool):
        """add a row to the data"""
        for k, v in kwargs.items():
            self.exp.addData(k, v)
        self.exp.nextEntry()
