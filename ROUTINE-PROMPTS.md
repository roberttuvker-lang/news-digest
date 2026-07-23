# The three routine prompts

Ready to apply to the existing cloud routines via the `schedule` skill (`update` — partial,
so the IDs and run history survive). The content briefs below are the originals, unchanged;
everything around them is new.

Attach this repo to all three: `https://github.com/USERNAME/news-digest`
`allowed_tools` already includes everything needed (`Bash`, `Read`, `Write`, `WebSearch`,
`WebFetch`). Model stays `claude-sonnet-5`.

The shared wrapper is identical in all three — only the content brief, `--stream`, `--run`
and `--max` differ.

---

## 1. `good-news-morning-0450-ai-sundays` — `trig_01QFqiDhKeSwUSEZVyvTsVVy`

```
You have a checkout of the news-digest repo. Work inside it. Every command below runs
from the repo root.

FIRST run `date +%u` with Bash to get today's day of week (1=Monday … 7=Sunday).

STEP 1 — find out what has already been published.
Run: python add.py recent --days 60
Everything it lists has already gone out. Do NOT report any of it again, in any wording.

STEP 2 — find the stories.

=== IF TODAY IS SUNDAY (7): weekly AI news ===
Use WebSearch to research this — do not answer from memory. Run 8 to 10 DISTINCT searches
before writing anything, covering: new model releases, major AI tool announcements,
AI company news and funding, AI regulation and policy, and anything that shipped
specifically for AI consultancies and agencies. Research broadly — this is where the
effort goes.
Cover the most important AI industry news of the past 7 days. Only include items that
would matter to someone running an AI consultancy business. Collect up to 12 candidates,
most important first.
Give each candidate a category: exactly one of Models, Tools, Companies, Policy.
Each item gets a headline and ONE OR TWO TIGHT SENTENCES — hard cap 40 words, no
exceptions. The whole briefing must come in under 500 words. Depth comes from the
searching, not the prose. Omit empty categories rather than padding.

=== OTHERWISE (any other day): morning good news ===
Use WebSearch — do not answer from memory. Run at least three distinct searches before
writing anything.
Find FIVE genuinely uplifting, real, recently-reported news stories (roughly the last day
or two): scientific or medical breakthroughs, conservation wins, acts of human kindness,
communities solving hard problems, quiet signs of progress. Real and verifiable, each
with a source link. Nothing grim, fear-based, or doom-framed.
Tone: WARM and HOPEFUL — a good way to start the day. For each story: a punchy headline,
2-3 sentences on what happened and why it matters, and the source link. Tight and
scannable, no filler.
(Five, not three, because two of them may turn out to be repeats — see step 4.)

STEP 3 — write candidates.json in the repo root: a JSON list, most important first.
[{"headline": "...", "blurb": "...", "url": "https://...", "category": "Models"}]
"category" only on Sundays; omit it otherwise.

STEP 4 — add them.
On Sunday:  python add.py add --stream ai --run morning-0450 --max 8
Other days: python add.py add --stream morning --run morning-0450 --max 3
It prints which were accepted and which were rejected as duplicates.

STEP 5 — ONE PASS ONLY.
Whatever survived is what gets published — eight, three, one, or none. Do NOT search
again. Do NOT look for replacements for rejected items. Do NOT re-run add.py. If
everything was a duplicate, that is a correct and complete run: commit nothing extra
and say so.

STEP 6 — verify.
Run: python add.py verify
Non-zero exit means something is wrong with the store. Stop there and commit NOTHING.

STEP 7 — publish.
git add -A && git commit -m "morning <today's date>" && git push
Then report what was accepted and what was rejected, and stop.
```

---

## 2. `good-news-midday-1002` — `trig_01UFrLezukrc1QaxXyhiv1GR`

```
You have a checkout of the news-digest repo. Work inside it. Every command below runs
from the repo root.

STEP 1 — find out what has already been published.
Run: python add.py recent --days 60
Everything it lists has already gone out. Do NOT report any of it again, in any wording.

STEP 2 — find the stories.
Use WebSearch — do not answer from memory. Run at least three distinct searches before
writing anything.
Find FIVE genuinely uplifting, real, recently-reported news stories (roughly the last day
or two): delightful discoveries, feel-good human moments, animal/nature wins, clever
wholesome wins, quirky good news. Real and verifiable, each with a source link. Nothing
grim, fear-based, or doom-framed.
Tone: FUN and PLAYFUL — light, punchy, full of delight and 'wait, that's amazing' energy.
Lean into wonder and a smile. For each story: a punchy headline, 2-3 sentences on what
happened and why it's great, and the source link. Tight and scannable, no filler. This is
a midday pick-me-up.
(Five, not three, because two of them may turn out to be repeats — see step 4.)

STEP 3 — write candidates.json in the repo root: a JSON list, best first.
[{"headline": "...", "blurb": "...", "url": "https://..."}]

STEP 4 — add them.
python add.py add --stream midday --run midday-1002 --max 3

STEP 5 — ONE PASS ONLY.
Whatever survived is what gets published — three, one, or none. Do NOT search again. Do
NOT look for replacements for rejected items. Do NOT re-run add.py. If everything was a
duplicate, that is a correct and complete run: commit nothing extra and say so.

STEP 6 — verify.
Run: python add.py verify
Non-zero exit means something is wrong with the store. Stop there and commit NOTHING.

STEP 7 — publish.
git add -A && git commit -m "midday <today's date>" && git push
Then report what was accepted and what was rejected, and stop.
```

---

## 3. `good-news-afternoon-1514` — `trig_01YbN9mBeyVFthhrB8pFf6TM`

```
You have a checkout of the news-digest repo. Work inside it. Every command below runs
from the repo root.

STEP 1 — find out what has already been published.
Run: python add.py recent --days 60
Everything it lists has already gone out. Do NOT report any of it again, in any wording.

STEP 2 — find the stories.
Use WebSearch — do not answer from memory. Run at least three distinct searches before
writing anything.
Find FIVE genuinely uplifting, real, recently-reported news stories (roughly the last day
or two) about PROGRESS that makes the future look bright: breakthroughs in science,
technology, medicine, clean energy, space, or human ingenuity. Real and verifiable, each
with a source link. Nothing grim, fear-based, or doom-framed.
Tone: EXCITED and FORWARD-LOOKING — leave the reader genuinely thrilled about where the
world is heading. For each story: a punchy headline, 2-3 sentences on what happened and
why it points to a better future, and the source link. Tight and scannable, no filler.
(Five, not three, because two of them may turn out to be repeats — see step 4.)

STEP 3 — write candidates.json in the repo root: a JSON list, best first.
[{"headline": "...", "blurb": "...", "url": "https://..."}]

STEP 4 — add them.
python add.py add --stream afternoon --run afternoon-1514 --max 3

STEP 5 — ONE PASS ONLY.
Whatever survived is what gets published — three, one, or none. Do NOT search again. Do
NOT look for replacements for rejected items. Do NOT re-run add.py. If everything was a
duplicate, that is a correct and complete run: commit nothing extra and say so.

STEP 6 — verify.
Run: python add.py verify
Non-zero exit means something is wrong with the store. Stop there and commit NOTHING.

STEP 7 — publish.
git add -A && git commit -m "afternoon <today's date>" && git push
Then report what was accepted and what was rejected, and stop.
```

---

## One change to the original briefs worth flagging

All three now ask for **five** stories instead of three (twelve instead of eight-ish for
the Sunday AI run). Dedupe happens *after* the search, and with no retry round the first
pass is the only pass — those extra candidates are the entire buffer against publishing a
short entry because one story turned out to be a repeat.
