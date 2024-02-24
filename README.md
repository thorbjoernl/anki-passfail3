# Pass/Fail With Automatic time based Easy/Hard Grading

This addon builds on the Anki [Pass/Fail](https://github.com/lambdadog/passfail2).
Whereas the original add-on always grades a card as Good when Pass is clicked, this
addon will grade it as easy or hard automatically based on time spent relative to
historical performance for that card. 

- Spending less time than `mean-stdev` will be graded Easy.
- Spending more time than `mean+stdev` will be graded Hard.

This will start to apply only after 5 reviews, to have meaningful estimates for the
values.

## Releases
The addon can be downloaded on Ankiweb [here](https://ankiweb.net/shared/info/515261413).

The most recent release can be grabbed from the [releases page](https://github.com/thorbjoernl/anki-passfail3/releases).
Keep in mind that these releases may be experimental and may cause problems. Make
backups of your collection before using these.

## Configuration
The add-on provides some options that can be used to configure it.
To access them go to `Tools->Add-ons`. These options are documented in `config.md`.

Setting *mode* to `whitelist` and decks to `[]` should be equivalent to Pass/Fail 2
and is the default.

Setting *mode* to `blacklist` and decks to `[]` applies time-based grading to *all* 
decks. 

## Known Issues & Limitations
These are known issues as currently implemented and may or may not be fixed in the
future.
- The pass button may not show the correct new interval during reviews.
- Listing a parent deck in the configuration options does not apply to child decks (eg.
excluding "Main" will not apply to "Main::A"; each sub-deck must be listed individually).
- Renaming decks will not automatically be updated in the configuration, which may cause
exceptions / errors.

## Original Readme
Please also see the readme of Pass/Fail 2 for additional details: `README.org`

## Changelog
- **v0.1.2:** Allow changing button labels.
- **v0.0.9:** Blacklist and whitelist based on deck. 
- **v0.0.5:** Initial implementation of changed grading.