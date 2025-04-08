import sys
import os

current_dir = os.path.dirname(__file__)
sys.path.append(f"{current_dir}/..")

from psychopy_scene import Context
from psychopy.visual import Window
from psychopy.monitors import Monitor
from psychopy.data import TrialHandler, ExperimentHandler
import random

monitor = Monitor(name="testMonitor", width=52.65, distance=57)
monitor.setSizePix((1920, 1080))

win = Window(monitor=monitor, units="deg", fullscr=True, size=(1920, 1080))
ctx = Context(
    win,
    handler=TrialHandler(
        trialList=random.sample(range(100), 10),
        nReps=1,
        method="sequential",
    ),
    expHandler=ExperimentHandler(extraInfo={"user_id": "zs123"}),
)

import examples.rt

examples.rt.simple_rt(ctx)
ctx.expHandler.saveAsWideText(f"{current_dir}/test.csv")
