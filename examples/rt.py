from psychopy_scene import Context, Event
from psychopy import data
import random

handler = data.TrialHandler(
    trialList=random.sample(range(100), 10), nReps=1, method="sequential"
)


def simple_rt(ctx: Context):
    """
    Simple reaction time task.
    """
    from psychopy.visual import TextStim
    import random

    stim = TextStim(ctx.win)

    @ctx.scene(duration=1, close_on="key_space")
    def reaction(text):
        stim.text = text
        return stim

    guide = ctx.text("Please press space when the stimulus appears.").config(
        close_on="key_space"
    )
    fixation = ctx.fixation(duration=1)
    blank = ctx.blank()

    guide.show()
    for text in handler:
        fixation.show()
        blank.config(duration=random.random()).show()
        reaction.show(text=text)
        evts: list[Event] = reaction.get("events")
        ctx.addRow(
            text=str(text),
            rt=evts[-1].timestamp - reaction.get("show_time") if evts else "",
        )


def identification_rt(ctx: Context):
    """
    Identification reaction time task.
    """
    from psychopy.visual import TextStim
    import random

    colors = ["red", "green"]
    stim = TextStim(ctx.win)

    @ctx.scene(duration=1, close_on="key_space")
    def reaction(text, color):
        stim.text = text
        stim.color = color
        return stim

    guide = ctx.text("Please press space when the green stimulus appears.").config(
        close_on="key_space"
    )
    fixation = ctx.fixation(duration=1)
    blank = ctx.blank()

    guide.show()
    for text in handler:
        color = random.choice(colors)

        fixation.show()
        blank.config(duration=random.random()).show()
        reaction.show(text=text, color=color)

        evts: list[Event] = reaction.get("events")
        ctx.addRow(
            text=str(text),
            color=color,
            rt=evts[-1].timestamp - reaction.get("show_time") if evts else "",
        )


def selection_rt(ctx: Context):
    """
    Selection reaction time task.
    """
    from psychopy.visual import TextStim
    import random

    key_color_map = {"f": "green", "j": "red"}
    stim = TextStim(ctx.win)

    @ctx.scene(duration=1, close_on=(f"key_{k}" for k in key_color_map.keys()))
    def reaction(text, color):
        stim.text = text
        stim.color = color
        return stim

    guide = ctx.text(
        "Please "
        + "\n".join(
            f"press {k} when the {v} stimulus appears."
            for k, v in key_color_map.items()
        )
    ).config(close_on="key_space")
    fixation = ctx.fixation(duration=1)
    blank = ctx.blank()

    guide.show()
    for text in handler:
        color = random.choice([*key_color_map.values()])

        fixation.show()
        blank.config(duration=random.random()).show()
        reaction.show(text=text, color=color)
        evts: list[Event] = reaction.get("events")
        ctx.addRow(
            text=str(text),
            color=color,
            rt=evts[-1].timestamp - reaction.get("show_time") if evts else "",
            correct=key_color_map[evts[-1].key.value] == color if evts else "",  # type: ignore
        )
