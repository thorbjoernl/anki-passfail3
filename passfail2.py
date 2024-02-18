# Pass/Fail 2
#
# Only offers 2 buttons to press: Pass, and Fail. Fail is equivalent
# to "Again", whereas Pass is equivalent to "Good". This helps remove
# decision paralysis while reviewing and also avoids the fallacy of
# the "Hard" button, which lengthens the amount of time between
# reviewing Hard cards, making them more difficult to acquire.
#
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Copyright (c) 2022 Ashlynn Anderson
#
# Regards to Dmitry Mikheev for writing the original add-on this was
# derived from, and the Anki team.

import os
import logging
import statistics

try:
    from typing import Literal, Callable
except ImportError:
    ()

try:
    from anki.utils import point_version
except ImportError:
    try:
        from anki.utils import pointVersion as point_version
    except:
        from anki import version  # pyright: ignore

        def point_version():
            return int(version.split(".")[-1])


from anki.hooks import wrap
from aqt import mw
from aqt.utils import showInfo
from aqt.reviewer import Reviewer
from anki.cards import Card

if point_version() >= 20:
    import aqt.gui_hooks as gui_hooks

if point_version() >= 45:
    from aqt.utils import tr
elif point_version() >= 36:
    from aqt.utils import tr
    from anki.lang import TR
else:
    from anki.lang import _


# Hooks
def pf2_hook_replace_buttons(
    buttons_tuple,  # type: tuple[tuple[int, str], ...]
    reviewer,  # type: Reviewer
    card,  # type: Card
):  # type: (...) -> tuple[tuple[int,str], ...]
    return ((1, "Fail"), (reviewer._defaultEase(), "Pass"))


def pf2_hook_remap_answer_ease(
    ease_tuple,  # type: tuple[bool, Literal[1, 2, 3, 4]]
    reviewer,  # type: Reviewer
    card,  # type: Card
):  # type: (...) -> tuple[bool, Literal[1, 2, 3, 4]]
    (cont, ease) = ease_tuple
    # We do not want to modify again gradings.
    if ease == 1:
        return ease_tuple

    if ((mode == "blacklist") and (card.did in decks)) or (
        (mode == "whitelist") and not (card.did in decks)
    ):
        logging.info(
            f"{card.cid} excluded from time-based grading due to {mode} settings. Graded good."
        )
        return (cont, 3)

    review_history = mw.col.db.execute("select * from revlog where cid = ?", card.id)
    logging.debug(f"Reps: {card.reps}")
    logging.debug(f"History: {review_history}")

    if (
        len([x for x in review_history if x[3] != 1]) < 5
    ):  # Count revlog entries with a passing grade.
        # Too few data points to meaningfully set ease based on mean/stddev.
        return (cont, 3)  # Good

    # Calculate the mean and stdev of time spent on reviews, counting only
    # passing grades.
    mean_time = statistics.mean([x[7] for x in review_history if x[3] != 1])
    stdev_time = statistics.stdev([x[7] for x in review_history if x[3] != 1])
    logging.debug(f"cid{card.id} - {int(mean_time)}±{int(stdev_time)}")
    logging.debug(f"Time taken: {card.time_taken()}")

    if card.time_taken() <= mean_time - stdev_time:
        return (cont, 4)  # Easy
    elif card.time_taken() >= mean_time + stdev_time:
        return (cont, 2)  # Hard

    return (cont, 3)  # Good


# Shims for old versions of anki
def pf2_shim_answerButtonList(
    self,  # type: Reviewer
    _old,  # type: Callable[[Reviewer], tuple[tuple[int, str], ...]]
):  # type: (...) -> tuple[tuple[int, str], ...]
    result = _old(self)
    if self.card:
        return pf2_hook_replace_buttons(result, self, self.card)
    else:
        return result


def pf2_shim_answerCard(
    self,  # type: Reviewer
    ease,  # type: Literal[1, 2, 3, 4]
    _old,  # type: Callable[[Reviewer, Literal[1, 2, 3, 4]], None]
):  # type: (...) -> None
    if self.card:  # Should always be true
        (_, new_ease) = pf2_hook_remap_answer_ease((True, ease), self, self.card)
        return _old(self, new_ease)
    else:
        return _old(self, ease)


# Run after drawing ease buttons
def pf2_fix_pass_title(
    self,  # type: Reviewer
):  # type: (...) -> None
    title = None
    if point_version() >= 45:
        title = tr.actions_shortcut_key(val=2)
    elif point_version() >= 36:
        title = tr(TR.ACTIONS_SHORTCUT_KEY, val=2)
    else:
        title = _("Shortcut key: %s") % 2

    self.bottom.web.eval(f'document.getElementById("defease").title = "{title}";')


# Init
def init():
    logging.basicConfig(
        filename=os.path.join(mw.addonManager.addonsFolder(), "passfail3.log"),
        encoding="utf-8",
        level=logging.DEBUG,
    )

    config = mw.addonManager.getConfig(__name__)

    mode = config["mode"]
    if not (mode in ["whitelist", "blacklist"]):
        logging.error(f"Unexpected mode: {mode}")
        raise ValueError(
            f"Unexpected mode, {mode}. Must be one of 'blacklist', 'whitelist'"
        )

    decks = [mw.col.decks.id_for_name(x) for x in config["decks"]]

    logging.info(f"Operating in {mode} mode, with decks {config['decks']} | {decks}.")

    version = point_version()

    # Answer button list
    if version >= 31:
        gui_hooks.reviewer_will_init_answer_buttons.append(pf2_hook_replace_buttons)
    else:
        Reviewer._answerButtonList = wrap(
            Reviewer._answerButtonList, pf2_shim_answerButtonList, "around"
        )

    # Remap ease for keybinds
    if version >= 20:
        gui_hooks.reviewer_will_answer_card.append(pf2_hook_remap_answer_ease)
    else:
        Reviewer._answerCard = wrap(Reviewer._answerCard, pf2_shim_answerCard, "around")

    # Show "Shortcut key: 2" rather than "Shortcut key: 3" for "Pass" button
    Reviewer._showEaseButtons = wrap(
        Reviewer._showEaseButtons, pf2_fix_pass_title, "after"
    )
