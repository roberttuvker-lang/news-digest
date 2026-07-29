#!/usr/bin/env python3
"""Assign a topic to every story that has not got one.

Written for the one-off backfill of the stories logged before `topic` existed,
but kept in the repo as the repair tool: if anything ever lands untagged, this
puts it right.

    python backfill_topics.py            # show what it would do, change nothing
    python backfill_topics.py --write    # apply

Stdlib only, no API calls, no cost. Keyword rules do the obvious cases and
anything ambiguous is printed for a human rather than guessed at, because a
wrong topic is worse than a missing one: it makes the filter lie.
"""

import argparse
import re
import sys

import add

# Order matters. The first rule that matches wins, so the specific topics are
# listed before the broad ones — otherwise "Society" would swallow half of them.
RULES = [
    ("Space", r"""
        nasa|space ?x|spacex|rocket|satellit|orbit|astronaut|telescope|webb|
        lunar|moon landing|mars|asteroid|comet|galax|cosmic|spacecraft|
        launch pad|iss\b|starship
    """),
    ("Health", r"""
        cancer|tumou?r|vaccin|patient|clinical trial|therap|treatment|disease|
        diagnos|surger|hospital|alzheimer|dementia|diabet|malaria|hiv\b|
        antibiotic|drug|medicin|health|mental health|blind|deaf|transplant|
        stem cell|gene therapy|obesity|stroke|heart|nhs\b|who\b|mortality
    """),
    ("Nature", r"""
        species|wildlife|whale|dolphin|elephant|tiger|panda|rhino|gorilla|
        turtle|bird|bee|butterfl|wolf|wolves|otter|beaver|coral|reef|
        endangered|extinct|conservation|habitat|rewild|forest|rainforest|
        wetland|animal|penguin|shark|lion|sea ?bird|salmon|orchid|
        eagle|\bbear\b|kangaroo|wallaby|moose|deer|fox\b|seal\b|horse
    """),
    ("Environment", r"""
        climate|emission|carbon|solar|wind (?:farm|power|turbine)|renewable|
        clean energy|fossil|coal|recycl|plastic|pollut|ocean clean|
        deforest|reforest|tree.planting|green energy|net zero|sustainab|
        battery storage|geothermal|hydrogen|electric vehicle|ev sales
    """),
    ("Science", r"""
        research|scientist|study|physic|chemist|quantum|fusion|particle|
        discover|experiment|laborator|breakthrough|university|professor|
        journal|nature\b|dna|genome|biolog|neuroscien|archaeolog|fossil record|
        mathemat|superconduct|material science
    """),
    ("Technology", r"""
        robot|chip|semiconductor|software|app\b|internet|broadband|
        computer|engineer|startup|device|hardware|3d.print|drone|
        battery|self.driving|autonomous vehicle|smartphone|open.source|
        cyber|encryption|prosthetic|exoskeleton|refrigerat|cooling
    """),
    ("AI", r"""
        \bai\b|artificial intelligence|machine learning|neural net|llm\b|
        language model|openai|anthropic|deepmind|chatgpt|claude|gemini|
        transformer model
    """),
    ("Society", r"""
        povert|homeless|refugee|education|school|literacy|charit|donat|
        volunteer|communit|hunger|famine|water access|human rights|
        peace|equality|crime rate|prison reform|housing|wage|economy|
        unemploy|democrac|vote|law|court|policy|government|
        rescu|saved|saving|stranger|neighbou?r|kindness|hero|world record|
        firefighter|drown|good samaritan|celebrat|festival|awareness
    """),
]

COMPILED = [(topic, re.compile(pat, re.I | re.X)) for topic, pat in RULES]


def text_of(story):
    parts = [story.get("headline", ""), story.get("blurb", ""),
             story.get("source", "")]
    parts.extend(story.get("bullets") or [])
    for link in story.get("links") or []:
        parts.append(link.get("text", ""))
    return " ".join(parts)


def guess(story):
    """Return a topic, or None if nothing matched confidently."""
    # The AI briefing is the AI briefing. No rule needed.
    if story.get("stream") == "ai":
        return "AI"
    haystack = text_of(story)
    for topic, pattern in COMPILED:
        if pattern.search(haystack):
            return topic
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true",
                    help="apply the changes; without it, nothing is written")
    ap.add_argument("--default", default=None, choices=add.TOPICS,
                    help="assign this topic to whatever the rules could not "
                         "place, instead of leaving it for a human")
    args = ap.parse_args()

    data = add.load()
    stories = data.get("stories", [])

    assigned, unmatched, already = [], [], 0
    for i, s in enumerate(stories):
        if s.get("topic") in add.TOPICS:
            already += 1
            continue
        topic = guess(s)
        if topic:
            assigned.append((i, topic, s["headline"]))
        else:
            unmatched.append((i, s["headline"]))

    counts = {}
    for _, topic, _ in assigned:
        counts[topic] = counts.get(topic, 0) + 1

    print("%d stories: %d already tagged, %d matched by rule, %d unmatched"
          % (len(stories), already, len(assigned), len(unmatched)))
    for topic in add.TOPICS:
        if counts.get(topic):
            print("  %-12s %d" % (topic, counts[topic]))

    if unmatched:
        print("\nNo rule matched these — assign by hand, or re-run with "
              "--default TOPIC:")
        for i, headline in unmatched:
            print("  [%d] %s" % (i, headline))

    if not args.write:
        print("\n(dry run — nothing written. Re-run with --write to apply.)")
        return 0

    for i, topic, _ in assigned:
        stories[i]["topic"] = topic
    if args.default:
        for i, _ in unmatched:
            stories[i]["topic"] = args.default

    still = [i for i, s in enumerate(stories) if s.get("topic") not in add.TOPICS]
    if still:
        print("\n%d stories are still untagged. Not writing — `add.py verify` "
              "would fail and a half-tagged store is worse than an untagged "
              "one." % len(still), file=sys.stderr)
        return 1

    add.save(data)
    print("\nWritten. Now run: python add.py verify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
