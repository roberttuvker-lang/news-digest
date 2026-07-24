# The three routine prompts

**Applied and live as of 2026-07-23.** This file is a copy of what is actually running, so
it can drift — the authority is https://claude.ai/code/routines.

All three have the repo `https://github.com/roberttuvker-lang/news-digest` attached, run
`claude-sonnet-5`, and keep their original schedules:

| Routine | ID | Cron (UTC) | Local | Stream |
|---|---|---|---|---|
| `good-news-morning-0450-ai-sundays` | `trig_01QFqiDhKeSwUSEZVyvTsVVy` | `50 1 * * *` | 04:50 | `ai` Sundays, else `morning` |
| `good-news-midday-1002` | `trig_01UFrLezukrc1QaxXyhiv1GR` | `2 7 * * *` | 10:02 | `midday` |
| `good-news-afternoon-1514` | `trig_01YbN9mBeyVFthhrB8pFf6TM` | `14 12 * * *` | 15:14 | `afternoon` |

The wrapper (steps 1, 3–7) is identical in all three. Only the step 2 content brief,
`--stream`, `--run` and `--max` differ.

---

## The shared wrapper

```
You have a checkout of the news-digest repo. Work inside it. Every command below runs
from the repo root. Read README.md if anything is unclear.

STEP 1 — find out what has already been published.
Run: python add.py recent --days 60
Everything it lists has already gone out. Do NOT report any of it again, in any wording.

STEP 2 — find the stories.
[content brief — see below]

STEP 3 — write candidates.json in the repo root: a JSON list, best first.
[{"headline": "...", "blurb": "...", "url": "https://..."}]

STEP 4 — add them.
Run: python add.py add --stream STREAM --run RUN --max N
It prints which were accepted and which were rejected as duplicates.

STEP 5 — ONE PASS ONLY.
Whatever survived is what gets published — three, one, or none. Do NOT search again. Do
NOT look for replacements for rejected items. Do NOT re-run add.py. If everything was a
duplicate, that is a correct and complete run: say so and continue to step 6.

STEP 6 — verify.
Run: python add.py verify
Non-zero exit means the store is damaged. Stop there and commit NOTHING.

STEP 7 — publish.
Run: git add -A && git commit -m "RUN $(date +%F)"
Then: git pull --rebase origin main && git push origin HEAD:main
The `git pull --rebase` is not optional. This repo is also pushed to from a laptop and
by the other two routines, so the remote may have moved since this session cloned.
Without the rebase a concurrent push is rejected and this run's work is thrown away.
If the rebase reports a conflict in data.json or data.js, do NOT merge them by hand:
`git rebase --abort`, then `git reset --hard origin/main`, then redo STEP 4 and STEP 6
on the fresh checkout and push again. add.py is the only thing allowed to write them.
If nothing was accepted there may be nothing to commit — that is fine, skip the push.
Then report what was accepted and what was rejected, and stop.
```

## The 403 that cost a day — read this before debugging push failures

Cloud runs failed `git push` with a hard 403 four times. The cause was **the Claude
GitHub App being authorized but never installed**. On github.com/settings/installations
those are two different tabs:

- **Authorized GitHub Apps** — shows only a *Revoke* button. Grants **no** repository
  permissions. This is where it was.
- **Installed GitHub Apps** — has *Configure* → Repository access. This is what matters.

Authorized-without-installed produces exactly this symptom: the sandbox clones the repo
fine (it is public, anyone can) and then 403s on push. Fixed by installing at
**https://github.com/apps/claude/installations/new** and selecting `news-digest`.
claude.ai's *organization* settings page is a red herring — that is Team/Enterprise only
and unrelated.

---

## Content briefs

### Morning — `--stream ai --run morning-0450 --max 8` on Sundays, else `--stream morning --run morning-0450 --max 3`

Opens with `date +%u` to find the day of week, then branches.

```
=== IF TODAY IS SUNDAY (7): weekly AI news ===
Use WebSearch to research this — do not answer from memory. Run 8 to 10 DISTINCT searches
before writing anything, covering: new model releases, major AI tool announcements, AI
company news and funding, AI regulation and policy, and anything that shipped
specifically for AI consultancies and agencies. Research broadly — this is where the
effort goes.
Cover the most important AI industry news of the past 7 days. Only include items that
would matter to someone running an AI consultancy business. Collect up to 12 candidates,
most important first.
Give every candidate a "category" field: exactly one of Models, Tools, Companies, Policy.
Each item gets a headline and ONE OR TWO TIGHT SENTENCES — hard cap 40 words per item, no
exceptions. The whole briefing must come in under 500 words. Depth comes from the
searching, not the prose.

=== OTHERWISE (any other day): morning good news ===
Find FIVE genuinely uplifting, real, recently-reported news stories (roughly the last day
or two): scientific or medical breakthroughs, conservation wins, acts of human kindness,
communities solving hard problems, quiet signs of progress.
Tone: WARM and OPTIMISTIC — a gentle, hopeful way to start the morning.
```

`category` goes in `candidates.json` on Sundays only.

### Midday — `--stream midday --run midday-1002 --max 3`

```
Find FIVE genuinely uplifting, real, recently-reported news stories (roughly the last day
or two): delightful discoveries, feel-good human moments, animal/nature wins, clever
wholesome wins, quirky good news.
Tone: FUN and PLAYFUL — light, punchy, full of delight and 'wait, that's amazing' energy.
Lean into wonder and a smile. This is a midday pick-me-up.
```

### Afternoon — `--stream afternoon --run afternoon-1514 --max 3`

```
Find FIVE genuinely uplifting, real, recently-reported news stories (roughly the last day
or two) about PROGRESS that makes the future look bright: breakthroughs in science,
technology, medicine, clean energy, space, or human ingenuity.
Tone: EXCITED and FORWARD-LOOKING — leave the reader genuinely thrilled about where the
world is heading.
```

---

## Two changes to the original briefs, both deliberate

**Five stories requested instead of three** (twelve instead of eight-ish on Sundays).
Dedupe happens *after* the search, and with no retry round the first pass is the only pass
— those extra candidates are the entire buffer against publishing a short entry because
one story turned out to be a repeat.

**The closing summary line is gone.** All three briefs used to end with something like
"End with one short line on why the future looks brighter than the headlines suggest."
That line has nowhere to live now: the page stores stories, and a wrap-up sentence is not
a story. It would have been written into the cloud transcript and thrown away. Say the
word if you want it back and I'll add a slot for it in the data model.
