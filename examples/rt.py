from psychopy_scene import Context


def simple_rt(ctx: Context):
    """
    Simple reaction time task.
    """
    from psychopy.visual import TextStim
    import random

    stim = TextStim(ctx.win)

    @(ctx.Scene(stim).close_on("space").hook("setup"))
    def reaction():
        stim.text = reaction.get("text")

    guide = ctx.text("Please press space when the stimulus appears.").close_on("space")
    fixation = ctx.fixation(duration=1)  # create a fixation cross
    blank = ctx.blank()  # create a blank screen

    guide.show()
    for text in ctx.handler:
        fixation.show()
        blank.show(duration=random.random())
        reaction.show(text=text)
        ctx.addLine(
            text=text,
            rt=reaction.get("response_time") - reaction.get("show_time"),
        )
    return ctx.expHandler.getAllEntries()


def identification_rt(ctx: Context):
    """
    Identification reaction time task.
    """
    from psychopy.visual import TextStim
    import random

    colors = ["red", "green"]
    stim = TextStim(ctx.win)

    @(ctx.Scene(stim).close_on("space").hook("setup"))
    def reaction():
        stim.text = reaction.get("text")
        stim.color = reaction.get("color")

    guide = ctx.text("Please press space when the green stimulus appears.").close_on(
        "space"
    )
    fixation = ctx.fixation(duration=1)
    blank = ctx.blank()

    guide.show()
    for text in ctx.handler:
        color = random.choice(colors)

        fixation.show()
        blank.show(duration=random.random())
        reaction.show(text=text, color=color)
        ctx.addLine(
            text=text,
            color=color,
            rt=reaction.get("response_time") - reaction.get("show_time"),
        )
    return ctx.expHandler.getAllEntries()


def selection_rt(ctx: Context):
    """
    Selection reaction time task.
    """
    from psychopy.visual import TextStim
    import random

    key_color_map = {"f": "green", "j": "red"}
    stim = TextStim(ctx.win)

    @(ctx.Scene(stim).close_on(*key_color_map.keys()).hook("setup"))
    def reaction():
        stim.text = reaction.get("text")
        stim.color = reaction.get("color")

    guide = ctx.text(
        "Please"
        + "\n".join(
            f"press {k} when the {v} stimulus appears."
            for k, v in key_color_map.items()
        )
    ).close_on("space")
    fixation = ctx.fixation(duration=1)
    blank = ctx.blank()

    guide.show()
    for text in ctx.handler:
        color = random.choice([*key_color_map.values()])

        fixation.show()
        blank.show(duration=random.random())
        reaction.show(text=text, color=color)
        ctx.addLine(
            text=text,
            color=color,
            rt=reaction.get("response_time") - reaction.get("show_time"),
            correct=key_color_map[reaction.get("keys")[0].value] == color,
        )
    return ctx.expHandler.getAllEntries()
