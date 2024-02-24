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

from .configparser import PassfailConfigParser


def show_debug_message(amessage: str):
    """
    Logs a debug message, and shows it as a popup message if
    the debug option is enabled.
    """
    config = PassfailConfigParser()
    if config.is_debug_mode():
        showInfo(amessage)

    logging.debug(amessage)


# Hooks
def pf2_hook_replace_buttons(
    buttons_tuple,  # type: tuple[tuple[int, str], ...]
    reviewer,  # type: Reviewer
    card,  # type: Card
):  # type: (...) -> tuple[tuple[int,str], ...]
    config = PassfailConfigParser()

    fail_lbl, pass_lbl = config.get_button_labels()
    return ((1, fail_lbl), (reviewer._defaultEase(), pass_lbl))


def pf2_hook_remap_answer_ease(
    ease_tuple,  # type: tuple[bool, Literal[1, 2, 3, 4]]
    reviewer,  # type: Reviewer
    card,  # type: Card
):  # type: (...) -> tuple[bool, Literal[1, 2, 3, 4]]
    (cont, ease) = ease_tuple
    # We do not want to modify again gradings.
    if ease == 1:
        return ease_tuple

    config = PassfailConfigParser()

    mode = config.get_mode()
    if not mode:
        logging.error(f"Unexpected mode: {config.config['mode']}")
        raise ValueError(
            f"Unexpected mode, {config.config['mode']}. Must be one of 'blacklist', 'whitelist'"
        )

    logging.info(f"Operating in {mode} mode, with decks {config['decks']}.")

    decks, invalid_decks = config.get_decks_as_deck_ids()

    if not invalid_decks:
        showInfo(
            f"The following deck names could not be found in your collection: {invalid_decks}."
        )
        logging.error(f"Decks, {invalid_decks}, was not found.")

    # Check for blacklist and whitelist conditions and grade pass if current card is excluded.
    if ((mode == "blacklist") and (card.did in decks)) or (
        (mode == "whitelist") and not (card.did in decks)
    ):
        show_debug_message(
            f"{card.id} excluded from time-based grading due to {mode} settings. Graded good."
        )
        return (cont, 3)  # Good.

    show_debug_message(
        f"{card.id} not excluded due to {mode} settings and will be graded based on time."
    )

    # Autograding based on time.
    review_history = mw.col.db.execute(
        "SELECT ease, time FROM revlog where cid = ?", card.id
    )
    logging.debug(f"Reps: {card.reps}")
    logging.debug(f"History: {review_history}")

    if (
        len([x for x in review_history if x[0] != 1]) < 5
    ):  # Count revlog entries with a passing grade.
        # Too few data points to meaningfully set ease based on mean/stddev.
        show_debug_message("Not enough reviews for time-based grading. Graded GOOD.")
        return (cont, 3)  # Good

    # Calculate the mean and stdev of time spent on reviews, counting only
    # passing grades.
    mean_time = statistics.mean([x[1] for x in review_history if x[0] != 1])
    stdev_time = statistics.stdev([x[1] for x in review_history if x[0] != 1])
    logging.debug(f"cid{card.id} - {int(mean_time)}±{int(stdev_time)}")
    logging.debug(f"Time taken: {card.time_taken()}")

    if card.time_taken() <= mean_time - stdev_time:
        show_debug_message("Graded EASY.")
        return (cont, 4)  # Easy
    elif card.time_taken() >= mean_time + stdev_time:
        show_debug_message("Graded HARD.")
        return (cont, 2)  # Hard

    show_debug_message("Graded GOOD.")
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
        filename=os.path.join(
            mw.addonManager.addonsFolder(), "515261413", "passfail3.log"
        ),
        encoding="utf-8",
        level=logging.DEBUG,
        format="[%(levelname)s] %(asctime)s: %(message)s",
    )

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
