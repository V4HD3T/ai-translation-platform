"""
SM-2 spaced repetition algorithm (the same scheduling algorithm behind
SuperMemo and, in simplified form, Anki).

The core idea: after each review, the learner self-rates how well they
recalled the word (0-5). A good recall pushes the next review further into
the future; a poor one resets progress and schedules a review again
tomorrow. The "ease factor" tracks how easy a given word is *for this
learner* over time, so well-known words drift toward longer and longer
intervals while hard ones keep coming back sooner.

This module is a pure function with no I/O, which makes the trickiest part
of the feature (the scheduling math) directly and cheaply unit-testable
without touching a database.
"""

from dataclasses import dataclass

MIN_EASE_FACTOR = 1.3
DEFAULT_EASE_FACTOR = 2.5


@dataclass
class ReviewOutcome:
    repetitions: int
    ease_factor: float
    interval_days: int


def compute_next_schedule(
    quality: int,
    repetitions: int,
    ease_factor: float,
    interval_days: int,
) -> ReviewOutcome:
    """Given a self-rated recall quality (0=total blackout, 5=perfect) and
    the word's current schedule, returns the next schedule.

    quality < 3 counts as a failed recall: repetitions reset and the word
    comes back tomorrow, regardless of how "easy" it used to be.
    """
    if not 0 <= quality <= 5:
        raise ValueError("quality must be between 0 and 5")

    if quality < 3:
        repetitions = 0
        interval_days = 1
    else:
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 6
        else:
            interval_days = round(interval_days * ease_factor)
        repetitions += 1

    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(MIN_EASE_FACTOR, round(ease_factor, 2))

    return ReviewOutcome(
        repetitions=repetitions, ease_factor=ease_factor, interval_days=interval_days
    )
