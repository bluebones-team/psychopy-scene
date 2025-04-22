import sys
import os

current_dir = os.path.dirname(__file__)
sys.path.append(f"{current_dir}/..")

from psychopy_scene import Context
from psychopy.visual import Window
from psychopy.monitors import Monitor

monitor = Monitor(name="testMonitor", width=52.65, distance=57)
monitor.setSizePix((1920, 1080))
win = Window(monitor=monitor, units="deg")
ctx = Context(win)

import rt

rt.simple_rt(ctx)
print(ctx.exp.getAllEntries())
