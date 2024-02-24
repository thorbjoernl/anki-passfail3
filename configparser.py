import logging
from aqt import mw


class PassfailConfigParser:
    def __init__(self):
        self.config = mw.addonManager.getConfig(__name__)

    def get_button_labels(self):
        """
        Returns a tuple with the configured button labels.
        """
        raw_labels = self.config["button_labels"]

        if len(raw_labels) == 2:
            return tuple(raw_labels)

        return ("Fail", "Pass")

    def get_mode(self):
        """
        Returns the mode as a canonicalized string (Either whitelist or blacklist), or
        None if configuration is invalid.
        """
        raw_mode = self.config["mode"].lower()

        if raw_mode in ["blacklist", "exclude"]:
            return "blacklist"

        if raw_mode in ["whitelist", "include"]:
            return "whitelist"

        return None

    def get_decks_as_names(self):
        """
        Returns the decks configuration option as a list of names.
        """
        return self.config["decks"]

    def get_decks_as_deck_ids(self):
        """
        Returns a tuple, (deck_ids, invalid_decks).

        deck_ids is the decks configuration option as Anki deck ids.

        invalid_decks is a list of strings with the deck names that
        could not be converted.
        """
        deck_names = self.get_decks_as_names()

        invalid_deck_names = []
        deck_ids = []
        for d in deck_names:
            did = mw.col.id_for_name(d)
            if not did:
                invalid_deck_names.append(d)
                continue

            deck_ids.append(did)

        return (deck_ids, invalid_deck_names)

    def is_debug_mode(self):
        """
        Returns a boolean indiciating if the addon is configured to
        be in debug mode.
        """
        return bool(self.config["debug"])
