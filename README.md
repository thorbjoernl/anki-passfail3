# TITLE: Pass/Fail 3

This addon builds on the Anki [Pass/Fail](https://github.com/lambdadog/passfail2).
Whereas the original addon always grades a card as Good when Pass is clicked, this
addon will grade it as easy/hard automatically based on time spent relative to
historical performance. 

- Spending less time than `mean-stdev` will be graded Easy.
- Spending more time than `mean+stdev` will be graded Hard.

This will start to apply only after 5 reviews, to have meaningful values.

## Original Readme
Please also see the original readme for additional details: `README.org`